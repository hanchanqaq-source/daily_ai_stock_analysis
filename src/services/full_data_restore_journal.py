"""Durable intent journal for full-data restore across SQLite and `.env`."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Set

from sqlalchemy import delete, select

from src.core.config_manager import ConfigManagerVersionConflict
from src.core.durable_file import durable_replace, durable_unlink
from src.services.system_config_service import SystemConfigService
from src.storage import FullDataRestoreCommitMarker

if os.name == "nt":  # pragma: no cover - exercised on Windows builds
    import msvcrt
else:  # pragma: no branch - selected once per platform
    import fcntl


JOURNAL_FORMAT = "pp02.full-data.restore-transaction"
JOURNAL_VERSION = 1
JOURNAL_FILENAME = ".pp02-full-data-restore-transaction.json"
LOCK_FILENAME = ".pp02-full-data-restore.lock"
JOURNAL_KEYS = {
    "format",
    "format_version",
    "project_id",
    "application_version",
    "database_schema_version",
    "tx_id",
    "created_at",
    "managed_keys",
    "prior_values",
    "incoming_values",
    "prior_digest",
    "incoming_digest",
    "integrity",
}


class FullDataRestoreJournalError(RuntimeError):
    """Fail startup/restore closed when a durable intent cannot be trusted."""


class _RestorePathLockState:
    """Share recursion state while keeping the advisory lock process-scoped."""

    def __init__(self) -> None:
        self.thread_lock = threading.RLock()
        self.local = threading.local()

    @contextmanager
    def acquire(self, lock_path: Path):
        with self.thread_lock:
            depth = int(getattr(self.local, "depth", 0))
            if depth:
                self.local.depth = depth + 1
                try:
                    yield
                finally:
                    self.local.depth -= 1
                return

            lock_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
            try:
                if os.name != "nt":
                    os.fchmod(descriptor, 0o600)
                if os.name == "nt":  # pragma: no cover - Windows-only branch
                    if os.fstat(descriptor).st_size == 0:
                        os.write(descriptor, b"\0")
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
                else:
                    fcntl.flock(descriptor, fcntl.LOCK_EX)
                self.local.depth = 1
                try:
                    yield
                finally:
                    self.local.depth = 0
                    if os.name == "nt":  # pragma: no cover - Windows-only branch
                        os.lseek(descriptor, 0, os.SEEK_SET)
                        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)


class FullDataRestoreJournal:
    """Write, validate, resolve, and clear one discoverable restore intent."""

    _path_locks: Dict[Path, _RestorePathLockState] = {}
    _path_locks_guard = threading.Lock()

    def __init__(
        self,
        *,
        db_manager,
        config_service: SystemConfigService,
        application_version: str,
        database_schema_version: str,
        managed_keys: Set[str],
        value_validator: Callable[[str], None],
    ) -> None:
        self.db = db_manager
        self.config_service = config_service
        self.application_version = str(application_version)
        self.database_schema_version = str(database_schema_version)
        self.managed_keys = frozenset(str(key).upper() for key in managed_keys)
        self.value_validator = value_validator
        self.path = self._journal_path()
        self.lock_path = self.path.parent / LOCK_FILENAME
        lock_key = self.lock_path.resolve()
        with self._path_locks_guard:
            self._lock_state = self._path_locks.setdefault(
                lock_key,
                _RestorePathLockState(),
            )

    @contextmanager
    def transaction_lock(self):
        """Serialize the complete restore/recovery state machine across processes."""
        with self._lock_state.acquire(self.lock_path):
            yield

    def _journal_path(self) -> Path:
        database = getattr(self.db._engine.url, "database", None)
        if not database or str(database) == ":memory:":
            raise FullDataRestoreJournalError(
                "Full-data restore transaction journal requires file-backed SQLite."
            )
        database_path = Path(str(database)).expanduser().resolve()
        return (
            database_path.parent
            / f"{database_path.stem}_restore_recovery"
            / JOURNAL_FILENAME
        )

    @staticmethod
    def _values_digest(values: Mapping[str, str]) -> str:
        return hashlib.sha256(
            json.dumps(
                dict(values),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    @classmethod
    def canonical_sha256(cls, document: Mapping[str, Any]) -> str:
        envelope = dict(document)
        integrity = dict(envelope["integrity"])
        integrity.pop("value", None)
        envelope["integrity"] = integrity
        return hashlib.sha256(
            json.dumps(
                envelope,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def begin(
        self,
        *,
        prior_values: Mapping[str, str],
        incoming_values: Mapping[str, str],
    ) -> str:
        with self.transaction_lock():
            if self.path.exists():
                raise FullDataRestoreJournalError(
                    "A pending full-data restore transaction journal must be recovered first."
                )
            prior = self._canonical_values(prior_values)
            incoming = self._canonical_values(incoming_values)
            tx_id = secrets.token_hex(32)
            document: Dict[str, Any] = {
                "format": JOURNAL_FORMAT,
                "format_version": JOURNAL_VERSION,
                "project_id": "PP02",
                "application_version": self.application_version,
                "database_schema_version": self.database_schema_version,
                "tx_id": tx_id,
                "created_at": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "managed_keys": sorted(self.managed_keys),
                "prior_values": prior,
                "incoming_values": incoming,
                "prior_digest": self._values_digest(prior),
                "incoming_digest": self._values_digest(incoming),
                "integrity": {"algorithm": "sha256", "value": ""},
            }
            document["integrity"]["value"] = self.canonical_sha256(document)
            self._write_document(document)
            return tx_id

    def preflight(self) -> Optional[Dict[str, Any]]:
        if not self.path.exists():
            return None
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(document, dict) or set(document) != JOURNAL_KEYS:
                raise ValueError("closed journal fields do not match")
            if (
                document["format"] != JOURNAL_FORMAT
                or type(document["format_version"]) is not int
                or document["format_version"] != JOURNAL_VERSION
                or document["project_id"] != "PP02"
                or document["application_version"] != self.application_version
                or document["database_schema_version"] != self.database_schema_version
                or not isinstance(document["tx_id"], str)
                or re.fullmatch(r"[0-9a-f]{64}", document["tx_id"]) is None
                or document["managed_keys"] != sorted(self.managed_keys)
            ):
                raise ValueError("journal identity or compatibility does not match")
            datetime.fromisoformat(str(document["created_at"]).replace("Z", "+00:00"))
            prior = self._canonical_values(document["prior_values"])
            incoming = self._canonical_values(document["incoming_values"])
            if prior != document["prior_values"] or incoming != document["incoming_values"]:
                raise ValueError("journal values are not canonical")
            if (
                document["prior_digest"] != self._values_digest(prior)
                or document["incoming_digest"] != self._values_digest(incoming)
            ):
                raise ValueError("journal subset digest does not match")
            integrity = document["integrity"]
            if (
                not isinstance(integrity, dict)
                or set(integrity) != {"algorithm", "value"}
                or integrity["algorithm"] != "sha256"
                or integrity["value"] != self.canonical_sha256(document)
            ):
                raise ValueError("journal integrity does not match")
            return document
        except Exception as exc:
            raise FullDataRestoreJournalError(
                "Full-data restore transaction journal is corrupt or incompatible."
            ) from exc

    def mark_committed(self, session, tx_id: str) -> None:
        session.add(FullDataRestoreCommitMarker(tx_id=tx_id))
        session.flush()

    def is_committed(self, tx_id: str) -> bool:
        """Read a restore marker on an independent connection.

        Callers use this after a commit call raises, while still holding the
        transaction lock, because the driver exception alone cannot reveal
        whether SQLite made the transaction durable.
        """
        with self.db._engine.connect() as connection:
            return connection.execute(
                select(FullDataRestoreCommitMarker.tx_id).where(
                    FullDataRestoreCommitMarker.tx_id == tx_id
                )
            ).scalar_one_or_none() is not None

    def recover_pending(self) -> bool:
        with self.transaction_lock():
            document = self.preflight()
            if document is None:
                return False
            tx_id = document["tx_id"]
            committed = self.is_committed(tx_id)
            try:
                self.config_service._manager.reconcile_managed_values_atomically(
                    prior_values=document["prior_values"],
                    incoming_values=document["incoming_values"],
                    managed_keys=set(self.managed_keys),
                    committed=committed,
                    max_attempts=3,
                )
            except ConfigManagerVersionConflict as exc:
                raise FullDataRestoreJournalError(
                    "Full-data restore transaction journal recovery could not acquire stable config."
                ) from exc
            self._clear_journal()
            self._delete_marker(tx_id)
            return True

    def abort(self, tx_id: str) -> None:
        with self.transaction_lock():
            document = self.preflight()
            if document is None:
                return
            if document["tx_id"] != tx_id:
                raise FullDataRestoreJournalError(
                    "Full-data restore transaction journal ID changed unexpectedly."
                )
            self.config_service._manager.reconcile_managed_values_atomically(
                prior_values=document["prior_values"],
                incoming_values=document["incoming_values"],
                managed_keys=set(self.managed_keys),
                committed=False,
                max_attempts=3,
            )
            self._clear_journal()
            self._delete_marker(tx_id)

    def cancel(self, tx_id: str) -> None:
        """Clear an intent after another mechanism restored the exact prior state."""
        with self.transaction_lock():
            document = self.preflight()
            if document is None or document["tx_id"] != tx_id:
                raise FullDataRestoreJournalError(
                    "Full-data restore transaction journal cancellation mismatch."
                )
            self._clear_journal()
            self._delete_marker(tx_id)

    def finish(self, tx_id: str) -> None:
        with self.transaction_lock():
            document = self.preflight()
            if document is None or document["tx_id"] != tx_id:
                raise FullDataRestoreJournalError(
                    "Full-data restore transaction journal finalization mismatch."
                )
            self._clear_journal()
            self._delete_marker(tx_id)

    def _canonical_values(self, values: Mapping[str, str]) -> Dict[str, str]:
        if not isinstance(values, Mapping):
            raise ValueError("journal values must be an object")
        normalized = self.config_service.normalize_env_subset_values(
            values=values,
            managed_keys=set(self.managed_keys),
        )
        for value in normalized.values():
            self.value_validator(value)
        return {key: normalized[key] for key in sorted(normalized)}

    def _write_document(self, document: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        temporary = self.path.parent / f".{self.path.name}.{os.getpid()}.tmp"
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            with os.fdopen(descriptor, "wb") as file_obj:
                file_obj.write(serialized)
                file_obj.flush()
                os.fsync(file_obj.fileno())
            durable_replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _clear_journal(self) -> None:
        durable_unlink(self.path)

    def _delete_marker(self, tx_id: str) -> None:
        with self.db._engine.begin() as connection:
            connection.execute(
                delete(FullDataRestoreCommitMarker).where(
                    FullDataRestoreCommitMarker.tx_id == tx_id
                )
            )
