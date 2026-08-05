"""Configuration file manager with atomic read/write behavior."""

from __future__ import annotations

import errno
import hashlib
import io
import logging
import os
import re
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Set, Tuple

if os.name == "nt":  # pragma: no cover - exercised on Windows builds
    import msvcrt
else:  # pragma: no branch - selected once per platform
    import fcntl

from dotenv import dotenv_values

from src.core.durable_file import durable_replace, durable_unlink

_ASSIGNMENT_PATTERN = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$"
)
_FALLBACK_REWRITE_ERRNOS = {errno.EBUSY, errno.EXDEV}
_COMPOSE_ESCAPED_ENV_VALUE_KEYS = frozenset({"CUSTOM_WEBHOOK_BODY_TEMPLATE"})
_APPLICATION_TEMPLATE_PLACEHOLDER_PATTERN = re.compile(
    r"(?<!\$)\$(?:"
    r"\{(content_json|title_json|content|title)\}"
    r"|(content_json|title_json|content|title)\b"
    r")"
)
_ESCAPED_APPLICATION_TEMPLATE_PLACEHOLDER_PATTERN = re.compile(
    r"\$\$(?:"
    r"\{(content_json|title_json|content|title)\}"
    r"|(content_json|title_json|content|title)\b"
    r")"
)

logger = logging.getLogger(__name__)


class ConfigManagerVersionConflict(RuntimeError):
    """Raised when a locked raw-file compare-and-swap observes a stale version."""

    def __init__(self, current_version: str):
        super().__init__("Configuration version conflict")
        self.current_version = current_version


class ConfigManagerPublicationUncertain(RuntimeError):
    """Carry only an opaque receipt when publication cannot be classified."""

    def __init__(self, receipt: Any, current_version: Optional[str]):
        super().__init__("Configuration publication outcome is uncertain")
        self.receipt = receipt
        self.current_version = current_version


@dataclass(frozen=True)
class _RawConfigSnapshot:
    """One exact open-file generation of the configuration path."""

    exists: bool
    content: bytes
    version: str
    updated_at: Optional[str]


class _PathLockState:
    """Share thread recursion and one advisory lock per resolved config path."""

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


def escape_compose_sensitive_env_value(key: str, value: str) -> str:
    """Escape app template placeholders that Docker Compose would interpolate."""
    if key.upper() not in _COMPOSE_ESCAPED_ENV_VALUE_KEYS:
        return value

    def _replace(match: re.Match[str]) -> str:
        braced_name = match.group(1)
        plain_name = match.group(2)
        if braced_name is not None:
            return f"$${{{braced_name}}}"
        return f"$${plain_name}"

    return _APPLICATION_TEMPLATE_PLACEHOLDER_PATTERN.sub(_replace, value)


def unescape_compose_sensitive_env_value(key: str, value: str) -> str:
    """Restore app template placeholders escaped for Docker Compose storage."""
    if key.upper() not in _COMPOSE_ESCAPED_ENV_VALUE_KEYS:
        return value

    def _replace(match: re.Match[str]) -> str:
        braced_name = match.group(1)
        plain_name = match.group(2)
        if braced_name is not None:
            return f"${{{braced_name}}}"
        return f"${plain_name}"

    return _ESCAPED_APPLICATION_TEMPLATE_PLACEHOLDER_PATTERN.sub(_replace, value)


@dataclass
class ConfigLineEntry:
    """Structured representation of a single `.env` line."""

    kind: Literal["assignment", "comment", "blank", "raw"]
    raw_line: str
    key: Optional[str] = None
    value: str = ""
    updated: bool = False

    @classmethod
    def parse(cls, raw_line: str) -> "ConfigLineEntry":
        stripped = raw_line.strip()
        if not stripped:
            return cls(kind="blank", raw_line=raw_line)
        if stripped.startswith("#"):
            return cls(kind="comment", raw_line=raw_line)

        matched = _ASSIGNMENT_PATTERN.match(raw_line)
        if matched:
            return cls(
                kind="assignment",
                raw_line=raw_line,
                key=matched.group(1),
                value=matched.group(2),
            )

        return cls(kind="raw", raw_line=raw_line)

    @classmethod
    def assignment(cls, key: str, value: str) -> "ConfigLineEntry":
        return cls(
            kind="assignment",
            raw_line=f"{key}={value}",
            key=key,
            value=value,
            updated=True,
        )

    def render(self) -> str:
        if self.kind == "assignment" and self.updated and self.key is not None:
            return f"{self.key}={self.value}"
        return self.raw_line


class ConfigManager:
    """Manage `.env` read/write operations with optimistic versioning."""

    _path_locks_guard = threading.Lock()
    _path_locks: Dict[Path, _PathLockState] = {}

    def __init__(self, env_path: Optional[Path] = None):
        self._configured_env_path = env_path or self._resolve_env_path()
        self._env_path = self._configured_env_path.expanduser().resolve()
        lock_key = self._env_path
        with self._path_locks_guard:
            self._lock_state = self._path_locks.setdefault(lock_key, _PathLockState())
        self._lock = self._lock_state.thread_lock
        self._advisory_lock_path = lock_key.with_name(lock_key.name + ".lock")

    @contextmanager
    def _transaction_lock(self):
        """Serialize compliant config transactions across threads and processes."""
        with self._lock_state.acquire(self._advisory_lock_path):
            yield

    @property
    def env_path(self) -> Path:
        """Return active `.env` path."""
        return self._env_path

    def read_config_map(self) -> Dict[str, str]:
        """Read key-value mapping from `.env` file."""
        with self._transaction_lock():
            return self._read_config_map(normalize_values=True)

    def snapshot_config_map(self) -> Tuple[Dict[str, str], str, Optional[str]]:
        """Parse one locked raw generation into logical values and metadata."""
        with self._transaction_lock():
            snapshot = self._read_raw_snapshot_unlocked()
            return (
                self._config_map_from_bytes(snapshot.content),
                snapshot.version,
                snapshot.updated_at,
            )

    def _read_config_map(self, *, normalize_values: bool) -> Dict[str, str]:
        """Read key-value mapping from `.env` file."""
        if not self._env_path.exists():
            return {}

        raw_values = dotenv_values(self._env_path, interpolate=False)
        if normalize_values:
            values = dotenv_values(self._env_path)
            for raw_key, raw_value in raw_values.items():
                if (
                    raw_key is not None
                    and str(raw_key).upper() in _COMPOSE_ESCAPED_ENV_VALUE_KEYS
                ):
                    values[raw_key] = raw_value
        else:
            values = raw_values
        config_map: Dict[str, str] = {}
        for key, value in values.items():
            if key is None:
                continue
            normalized_key = str(key)
            normalized_value = "" if value is None else str(value)
            if normalize_values:
                normalized_value = unescape_compose_sensitive_env_value(
                    normalized_key,
                    normalized_value,
                )
            config_map[normalized_key] = normalized_value
        return config_map

    def get_config_version(self) -> str:
        """Return deterministic version string based on file state."""
        with self._transaction_lock():
            return self._get_config_version_unlocked()

    def _get_config_version_unlocked(self) -> str:
        """Return the version while the caller holds this path's lock."""
        return self._read_raw_snapshot_unlocked().version

    def get_updated_at(self) -> Optional[str]:
        """Return `.env` last update time in ISO8601 format."""
        with self._transaction_lock():
            return self._get_updated_at_unlocked()

    def _get_updated_at_unlocked(self) -> Optional[str]:
        """Return the update time while the caller holds this path's lock."""
        return self._read_raw_snapshot_unlocked().updated_at

    def apply_updates(
        self,
        updates: Iterable[Tuple[str, str]],
        sensitive_keys: Set[str],
        mask_token: str,
        expected_version: Optional[str] = None,
    ) -> Tuple[List[str], List[str], str]:
        """Apply updates into `.env` file using atomic replace when possible."""
        with self._transaction_lock():
            current_snapshot = self._read_raw_snapshot_unlocked()
            if (
                expected_version is not None
                and current_snapshot.version != expected_version
            ):
                raise ConfigManagerVersionConflict(current_snapshot.version)
            current_values = self.read_config_map()
            stored_values = self._read_config_map(normalize_values=False)
            mutable_updates: Dict[str, str] = {}
            skipped_masked: List[str] = []

            for key, value in updates:
                key_upper = key.upper()
                current_value = current_values.get(key_upper)

                if key_upper in sensitive_keys and value == mask_token:
                    if current_value not in (None, ""):
                        skipped_masked.append(key_upper)
                    continue

                stored_value = stored_values.get(key_upper)
                canonical_stored_value = escape_compose_sensitive_env_value(
                    key_upper,
                    value.replace("\n", ""),
                )
                if current_value == value and (
                    key_upper not in _COMPOSE_ESCAPED_ENV_VALUE_KEYS
                    or stored_value == canonical_stored_value
                ):
                    continue

                mutable_updates[key_upper] = value

            if mutable_updates:
                self._atomic_upsert(mutable_updates)

            return list(mutable_updates.keys()), skipped_masked, self.get_config_version()

    def _atomic_upsert(self, updates: Dict[str, str]) -> None:
        """Write updates with atomic rename and in-place fallback for mounted files."""
        entries = self._read_entries()
        key_to_index = self._find_last_key_indexes(entries)

        for key, value in updates.items():
            line_value = value.replace("\n", "")
            line_value = escape_compose_sensitive_env_value(key, line_value)
            if key in key_to_index:
                entries[key_to_index[key]] = ConfigLineEntry.assignment(key, line_value)
            else:
                entries.append(ConfigLineEntry.assignment(key, line_value))

        self._atomic_write_content(self._render_entries(entries))

    def render_without_keys(self, excluded_keys: Set[str]) -> str:
        """Render `.env` content without assignments for excluded keys."""
        normalized = {str(key).upper() for key in excluded_keys}
        return self.render_without_matching_keys(lambda key: key in normalized)

    def render_without_matching_keys(self, should_exclude: Callable[[str], bool]) -> str:
        """Render one locked `.env` snapshot while excluding matching assignments."""
        with self._transaction_lock():
            snapshot = self._read_raw_snapshot_unlocked()
            entries = [
                entry
                for entry in self._entries_from_bytes(snapshot.content)
                if not (
                    entry.kind == "assignment"
                    and entry.key is not None
                    and should_exclude(entry.key.upper())
                )
            ]
            return self._render_entries(entries)

    def snapshot_without_matching_keys(
        self,
        should_exclude: Callable[[str], bool],
    ) -> Tuple[str, str, Optional[str]]:
        """Capture sanitized content and its metadata from one locked file state."""
        with self._transaction_lock():
            snapshot = self._read_raw_snapshot_unlocked()
            entries = [
                entry
                for entry in self._entries_from_bytes(snapshot.content)
                if not (
                    entry.kind == "assignment"
                    and entry.key is not None
                    and should_exclude(entry.key.upper())
                )
            ]
            return (
                self._render_entries(entries),
                snapshot.version,
                snapshot.updated_at,
            )

    def replace_managed_assignments_atomically(
        self,
        *,
        expected_version: str,
        managed_keys: Set[str],
        replacements: Dict[str, str],
        prepare_receipt: Callable[..., Any],
        discard_receipt: Callable[[Any], None],
    ) -> Any:
        """CAS-replace a subset and seal its undo state before publication."""
        normalized_managed = {str(key).upper() for key in managed_keys}
        normalized_replacements = {
            str(key).upper(): str(value) for key, value in replacements.items()
        }
        with self._transaction_lock():
            previous = self._read_raw_snapshot_unlocked()
            if previous.version != expected_version:
                raise ConfigManagerVersionConflict(previous.version)
            next_content = self._replace_managed_content(
                previous.content,
                normalized_managed,
                normalized_replacements,
            )
            post_version = self._raw_generation(True, next_content)
            staged_path = self._stage_atomic_bytes(next_content)
            receipt = None
            try:
                rechecked = self._read_raw_snapshot_unlocked()
                if not self._same_raw_snapshot(previous, rechecked):
                    raise ConfigManagerVersionConflict(rechecked.version)
                receipt = prepare_receipt(
                    previous_content=previous.content,
                    previous_exists=previous.exists,
                    applied_content=next_content,
                    managed_keys=frozenset(normalized_managed),
                    prior_version=previous.version,
                    post_version=post_version,
                )
                try:
                    self._publish_staged_bytes(staged_path)
                except BaseException as publish_exc:
                    try:
                        published = self._read_raw_snapshot_unlocked()
                    except BaseException:
                        raise ConfigManagerPublicationUncertain(
                            receipt=receipt,
                            current_version=None,
                        ) from publish_exc
                    if (
                        published.exists
                        and published.version == post_version
                        and published.content == next_content
                    ):
                        if not isinstance(publish_exc, Exception):
                            self._restore_prior_after_interruption(
                                previous=previous,
                                receipt=receipt,
                                discard_receipt=discard_receipt,
                            )
                            raise
                        return receipt
                    if self._same_raw_snapshot(previous, published):
                        discard_receipt(receipt)
                        raise
                    raise ConfigManagerPublicationUncertain(
                        receipt=receipt,
                        current_version=published.version,
                    ) from publish_exc
                return receipt
            finally:
                if staged_path.exists():
                    staged_path.unlink()

    def _restore_prior_after_interruption(
        self,
        *,
        previous: _RawConfigSnapshot,
        receipt: Any,
        discard_receipt: Callable[[Any], None],
    ) -> None:
        """Restore and verify the prior generation before propagating an interrupt."""
        rollback_error: Optional[BaseException] = None
        staged_path: Optional[Path] = None
        try:
            if previous.exists:
                staged_path = self._stage_atomic_bytes(previous.content)
                try:
                    self._publish_staged_bytes(staged_path)
                except BaseException as exc:
                    rollback_error = exc
            elif self._env_path.exists():
                try:
                    durable_unlink(self._env_path)
                except BaseException as exc:
                    rollback_error = exc
        except BaseException as exc:
            rollback_error = exc
        finally:
            if staged_path is not None and staged_path.exists():
                try:
                    staged_path.unlink()
                except BaseException as exc:
                    if rollback_error is None:
                        rollback_error = exc

        try:
            restored = self._read_raw_snapshot_unlocked()
        except BaseException as exc:
            raise ConfigManagerPublicationUncertain(
                receipt=receipt,
                current_version=None,
            ) from exc
        if not self._same_raw_snapshot(previous, restored):
            raise ConfigManagerPublicationUncertain(
                receipt=receipt,
                current_version=restored.version,
            ) from rollback_error
        try:
            discard_receipt(receipt)
        except BaseException as exc:
            raise ConfigManagerPublicationUncertain(
                receipt=receipt,
                current_version=restored.version,
            ) from exc

    def compensate_managed_assignments_atomically(
        self,
        *,
        previous_content: bytes,
        previous_exists: bool,
        applied_content: bytes,
        managed_keys: Set[str],
        post_version: str,
    ) -> Tuple[str, bool]:
        """Undo unchanged restore-owned keys while preserving later writer edits."""
        with self._transaction_lock():
            current = self._read_raw_snapshot_unlocked()
            concurrent_edit = not (
                current.exists
                and current.version == post_version
                and current.content == applied_content
            )
            if concurrent_edit:
                target_content = self._three_way_compensation_content(
                    previous_content=previous_content,
                    applied_content=applied_content,
                    current_content=current.content,
                    managed_keys={str(key).upper() for key in managed_keys},
                )
                target_exists = current.exists or bool(target_content)
            else:
                target_content = previous_content
                target_exists = previous_exists

            target_version = self._raw_generation(target_exists, target_content)
            staged_path = (
                self._stage_atomic_bytes(target_content) if target_exists else None
            )
            try:
                rechecked = self._read_raw_snapshot_unlocked()
                if not self._same_raw_snapshot(current, rechecked):
                    raise ConfigManagerVersionConflict(rechecked.version)
                if staged_path is not None:
                    self._publish_staged_bytes(staged_path)
                elif self._env_path.exists():
                    durable_unlink(self._env_path)
                return target_version, concurrent_edit
            finally:
                if staged_path is not None and staged_path.exists():
                    staged_path.unlink()

    def reconcile_managed_values_atomically(
        self,
        *,
        prior_values: Dict[str, str],
        incoming_values: Dict[str, str],
        managed_keys: Set[str],
        committed: bool,
        max_attempts: int = 3,
    ) -> str:
        """Resolve a durable restore intent with a bounded three-way CAS."""
        normalized_keys = {str(key).upper() for key in managed_keys}
        prior = {str(key).upper(): str(value) for key, value in prior_values.items()}
        incoming = {
            str(key).upper(): str(value) for key, value in incoming_values.items()
        }
        source = prior if committed else incoming
        desired = incoming if committed else prior
        missing = object()
        last_conflict: Optional[ConfigManagerVersionConflict] = None
        for _attempt in range(max(1, int(max_attempts))):
            try:
                with self._transaction_lock():
                    current = self._read_raw_snapshot_unlocked()
                    current_values = self._config_map_from_bytes(current.content)
                    replacements: Dict[str, str] = {}
                    for key in normalized_keys:
                        current_value = current_values.get(key, missing)
                        source_value = source.get(key, missing)
                        desired_value = desired.get(key, missing)
                        target_value = (
                            desired_value
                            if current_value == source_value
                            else current_value
                        )
                        if target_value is not missing:
                            replacements[key] = str(target_value)
                    next_content = self._replace_managed_content(
                        current.content,
                        normalized_keys,
                        replacements,
                    )
                    if current.exists and next_content == current.content:
                        return current.version
                    staged_path = self._stage_atomic_bytes(next_content)
                    try:
                        rechecked = self._read_raw_snapshot_unlocked()
                        if not self._same_raw_snapshot(current, rechecked):
                            raise ConfigManagerVersionConflict(rechecked.version)
                        self._publish_staged_bytes(staged_path)
                        return self._raw_generation(True, next_content)
                    finally:
                        if staged_path.exists():
                            staged_path.unlink()
            except ConfigManagerVersionConflict as exc:
                last_conflict = exc
        assert last_conflict is not None
        raise last_conflict

    @staticmethod
    def _config_map_from_bytes(content: bytes) -> Dict[str, str]:
        parsed = dotenv_values(
            stream=io.StringIO(content.decode("utf-8")),
            interpolate=False,
        )
        return {
            str(key).upper(): unescape_compose_sensitive_env_value(
                str(key),
                "" if value is None else str(value),
            )
            for key, value in parsed.items()
            if key is not None
        }

    def get_assignment_keys(self) -> Set[str]:
        """Return assignment names without parsing their values."""
        with self._transaction_lock():
            return {
                entry.key.upper()
                for entry in self._read_entries()
                if entry.kind == "assignment" and entry.key is not None
            }

    def remove_keys(self, keys: Set[str]) -> Tuple[List[str], str]:
        """Atomically remove all assignments for the requested keys."""
        normalized = {str(key).upper() for key in keys}
        with self._transaction_lock():
            entries = self._read_entries()
            removed = sorted(
                {
                    entry.key.upper()
                    for entry in entries
                    if entry.kind == "assignment"
                    and entry.key is not None
                    and entry.key.upper() in normalized
                }
            )
            if removed:
                retained = [
                    entry
                    for entry in entries
                    if not (
                        entry.kind == "assignment"
                        and entry.key is not None
                        and entry.key.upper() in normalized
                    )
                ]
                self._atomic_write_content(self._render_entries(retained))
            return removed, self.get_config_version()

    @staticmethod
    def _raw_generation(exists: bool, content: bytes) -> str:
        marker = b"present\0" if exists else b"missing\0"
        return "sha256:" + hashlib.sha256(marker + content).hexdigest()

    def _read_raw_snapshot_unlocked(self) -> _RawConfigSnapshot:
        """Read bytes and metadata from one stable open file generation."""
        for _attempt in range(3):
            try:
                descriptor = os.open(self._env_path, os.O_RDONLY)
            except FileNotFoundError:
                if not self._env_path.exists():
                    return _RawConfigSnapshot(
                        exists=False,
                        content=b"",
                        version=self._raw_generation(False, b""),
                        updated_at=None,
                    )
                continue

            with os.fdopen(descriptor, "rb") as file_obj:
                before_stat = os.fstat(file_obj.fileno())
                content = file_obj.read()
                after_stat = os.fstat(file_obj.fileno())
            try:
                path_stat = self._env_path.stat()
            except FileNotFoundError:
                continue
            before_identity = (
                before_stat.st_dev,
                before_stat.st_ino,
                before_stat.st_size,
                before_stat.st_mtime_ns,
            )
            after_identity = (
                after_stat.st_dev,
                after_stat.st_ino,
                after_stat.st_size,
                after_stat.st_mtime_ns,
            )
            path_identity = (
                path_stat.st_dev,
                path_stat.st_ino,
                path_stat.st_size,
                path_stat.st_mtime_ns,
            )
            if before_identity != after_identity or after_identity != path_identity:
                continue
            return _RawConfigSnapshot(
                exists=True,
                content=content,
                version=self._raw_generation(True, content),
                updated_at=datetime.fromtimestamp(
                    after_stat.st_mtime,
                    tz=timezone.utc,
                ).isoformat(),
            )
        raise OSError("Configuration changed while capturing an exact file generation")

    @staticmethod
    def _same_raw_snapshot(
        first: _RawConfigSnapshot,
        second: _RawConfigSnapshot,
    ) -> bool:
        return (
            first.exists == second.exists
            and first.version == second.version
            and first.content == second.content
        )

    @staticmethod
    def _assignment_key(raw_line: bytes) -> Optional[str]:
        decoded_line = raw_line.decode("utf-8").rstrip("\r\n")
        entry = ConfigLineEntry.parse(decoded_line)
        if entry.kind != "assignment" or entry.key is None:
            return None
        return entry.key.upper()

    @classmethod
    def _replace_managed_content(
        cls,
        content: bytes,
        managed_keys: Set[str],
        replacements: Dict[str, str],
    ) -> bytes:
        retained_lines = [
            raw_line
            for raw_line in content.splitlines(keepends=True)
            if cls._assignment_key(raw_line) not in managed_keys
        ]
        next_content = b"".join(retained_lines)
        replacement_lines = [
            (
                f"{key}={escape_compose_sensitive_env_value(key, replacements[key])}\n"
            ).encode("utf-8")
            for key in sorted(replacements)
        ]
        return cls._append_raw_lines(next_content, replacement_lines)

    @classmethod
    def _assignment_bodies(cls, content: bytes) -> Dict[str, Tuple[bytes, ...]]:
        grouped: Dict[str, List[bytes]] = {}
        for raw_line in content.splitlines(keepends=True):
            key = cls._assignment_key(raw_line)
            if key is None:
                continue
            grouped.setdefault(key, []).append(raw_line.rstrip(b"\r\n"))
        return {key: tuple(lines) for key, lines in grouped.items()}

    @classmethod
    def _three_way_compensation_content(
        cls,
        *,
        previous_content: bytes,
        applied_content: bytes,
        current_content: bytes,
        managed_keys: Set[str],
    ) -> bytes:
        applied_bodies = cls._assignment_bodies(applied_content)
        current_bodies = cls._assignment_bodies(current_content)
        restore_keys = {
            key
            for key in managed_keys
            if current_bodies.get(key, ()) == applied_bodies.get(key, ())
        }
        retained = b"".join(
            raw_line
            for raw_line in current_content.splitlines(keepends=True)
            if cls._assignment_key(raw_line) not in restore_keys
        )
        previous_lines = [
            raw_line
            for raw_line in previous_content.splitlines(keepends=True)
            if cls._assignment_key(raw_line) in restore_keys
        ]
        return cls._append_raw_lines(retained, previous_lines)

    @staticmethod
    def _append_raw_lines(content: bytes, raw_lines: Iterable[bytes]) -> bytes:
        result = content
        for raw_line in raw_lines:
            if result and not result.endswith((b"\n", b"\r")):
                result += b"\n"
            result += raw_line
        return result

    @staticmethod
    def _render_entries(entries: List[ConfigLineEntry]) -> str:
        content = "\n".join(entry.render() for entry in entries)
        if content and not content.endswith("\n"):
            content += "\n"
        return content

    def _atomic_write_content(self, content: str) -> None:
        if not self._env_path.parent.exists():
            self._env_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = self._env_path.with_suffix(self._env_path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8", newline="\n") as file_obj:
            file_obj.write(content)
            file_obj.flush()
            os.fsync(file_obj.fileno())

        try:
            os.replace(temp_path, self._env_path)
        except OSError as exc:
            if exc.errno not in _FALLBACK_REWRITE_ERRNOS:
                raise

            logger.warning(
                "Atomic replace for .env failed with errno=%s, falling back to in-place rewrite",
                exc.errno,
            )
            self._rewrite_in_place(content)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def _atomic_replace_bytes(self, content: bytes) -> None:
        """Durably replace `.env` bytes without an in-place fallback."""
        staged_path = self._stage_atomic_bytes(content)
        try:
            self._publish_staged_bytes(staged_path)
        finally:
            if staged_path.exists():
                staged_path.unlink()

    def _stage_atomic_bytes(self, content: bytes) -> Path:
        """Flush exact replacement bytes beside the destination before publication."""
        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(
            prefix=f".{self._env_path.name}.restore-",
            dir=self._env_path.parent,
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(descriptor, "wb") as file_obj:
                file_obj.write(content)
                file_obj.flush()
                os.fsync(file_obj.fileno())
            return temp_path
        except BaseException:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _publish_staged_bytes(self, staged_path: Path) -> None:
        """Publish one already-flushed generation with no later receipt work."""
        durable_replace(staged_path, self._env_path)

    @staticmethod
    def _fsync_parent_directory(directory: Path) -> None:
        try:
            descriptor = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _rewrite_in_place(self, content: str) -> None:
        """Rewrite `.env` content in place when rename is unsupported by mount type."""
        with self._env_path.open("w", encoding="utf-8", newline="\n") as file_obj:
            file_obj.write(content)
            file_obj.flush()
            os.fsync(file_obj.fileno())

    def _read_entries(self) -> List[ConfigLineEntry]:
        if not self._env_path.exists():
            return []
        return self._entries_from_bytes(self._env_path.read_bytes())

    @staticmethod
    def _entries_from_bytes(content: bytes) -> List[ConfigLineEntry]:
        return [
            ConfigLineEntry.parse(raw_line)
            for raw_line in content.decode("utf-8").splitlines()
        ]

    @staticmethod
    def _find_last_key_indexes(entries: List[ConfigLineEntry]) -> Dict[str, int]:
        key_to_index: Dict[str, int] = {}
        for index, entry in enumerate(entries):
            if entry.kind != "assignment" or entry.key is None:
                continue
            key_to_index[entry.key.upper()] = index

        return key_to_index

    @staticmethod
    def _resolve_env_path() -> Path:
        env_file = os.getenv("ENV_FILE")
        if env_file:
            return Path(env_file).resolve()

        return (Path(__file__).resolve().parent.parent.parent / ".env").resolve()
