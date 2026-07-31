# -*- coding: utf-8 -*-
"""Synthetic-only SQLite migration rehearsal for the PP02 portfolio ledger."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Iterable, Tuple

from src.services.portfolio_backup_service import (
    PortfolioBackupConflictError,
    PortfolioBackupService,
)
from src.storage import (
    DatabaseManager,
    PortfolioAccount,
    PortfolioCashLedger,
    PortfolioCorporateAction,
    PortfolioTrade,
)


TARGET_DATABASE_NAME = "pp02-r4-migrated.db"
EXPECTED_ATTESTATION_KEYS = {
    "attestation_version",
    "project_id",
    "scope",
    "classification",
    "contains_real_data",
    "source_sha256",
}
PORTFOLIO_MODELS = (
    PortfolioAccount,
    PortfolioTrade,
    PortfolioCashLedger,
    PortfolioCorporateAction,
)
OFFICIAL_EVENT_TABLES = tuple(model.__tablename__ for model in PORTFOLIO_MODELS)
DERIVED_PORTFOLIO_TABLES = (
    "portfolio_positions",
    "portfolio_position_lots",
    "portfolio_daily_snapshots",
)


class DatabaseMigrationRehearsalError(RuntimeError):
    """Fail-closed rehearsal error carrying only a stable public code."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class DatabaseMigrationRehearsalService:
    """Rehearse a stock-ledger migration without touching real data."""

    def run(
        self,
        *,
        source_path: Path,
        attestation_path: Path,
        workspace_dir: Path,
    ) -> Dict[str, Any]:
        source = Path(source_path)
        attestation = Path(attestation_path)
        workspace = Path(workspace_dir)
        target = workspace / TARGET_DATABASE_NAME

        self._validate_source_path(source)
        source_digest = self._sha256(source)
        self._validate_attestation(attestation, source_digest)
        source_tables, excluded_tables = self._preflight_source(source)
        self._validate_workspace(workspace)
        if target.exists() or target.is_symlink():
            raise DatabaseMigrationRehearsalError("target_exists")

        target_started = False
        try:
            workspace.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                raise DatabaseMigrationRehearsalError("target_exists")

            with TemporaryDirectory(prefix="pp02-r4-", dir=workspace) as temporary:
                source_copy = Path(temporary) / "synthetic-source-copy.db"
                shutil.copy2(source, source_copy)
                backup = self._export_from_upgraded_copy(source_copy)

            target_started = True
            migration = self._restore_and_verify_target(target, backup)

            source_unchanged = self._sha256(source) == source_digest
            if not source_unchanged:
                raise DatabaseMigrationRehearsalError("source_changed")

            return {
                "report_version": 1,
                "status": "pass",
                "source_sha256": source_digest,
                "source_unchanged": True,
                "schema": {
                    "compatible": True,
                    "source_tables": list(source_tables),
                    "excluded_tables": list(excluded_tables),
                },
                "migration": {
                    "counts": migration["counts"],
                    "portfolio_digest_match": True,
                    "excluded_table_data_present": False,
                },
                "rollback": {
                    "stale_preview_rejected": True,
                    "target_unchanged": True,
                },
                "privacy": {
                    "real_data_used": False,
                    "backup_payload_persisted": False,
                },
                "target_database": TARGET_DATABASE_NAME,
            }
        except DatabaseMigrationRehearsalError:
            if target_started:
                self._cleanup_target(target)
            raise
        except Exception as exc:
            if target_started:
                self._cleanup_target(target)
            raise DatabaseMigrationRehearsalError("rehearsal_failed") from exc

    @staticmethod
    def _validate_source_path(source: Path) -> None:
        if source.is_symlink() or not source.is_file():
            raise DatabaseMigrationRehearsalError("source_path_invalid")

    @staticmethod
    def _validate_workspace(workspace: Path) -> None:
        if workspace.is_symlink() or (workspace.exists() and not workspace.is_dir()):
            raise DatabaseMigrationRehearsalError("workspace_path_invalid")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        try:
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
        except OSError as exc:
            raise DatabaseMigrationRehearsalError("source_read_failed") from exc
        return digest.hexdigest()

    @staticmethod
    def _validate_attestation(attestation_path: Path, source_digest: str) -> None:
        if not attestation_path.exists():
            raise DatabaseMigrationRehearsalError("attestation_missing")
        if attestation_path.is_symlink() or not attestation_path.is_file():
            raise DatabaseMigrationRehearsalError("attestation_contract_invalid")
        try:
            payload = json.loads(attestation_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DatabaseMigrationRehearsalError("attestation_contract_invalid") from exc
        if not isinstance(payload, dict) or set(payload) != EXPECTED_ATTESTATION_KEYS:
            raise DatabaseMigrationRehearsalError("attestation_contract_invalid")
        if payload["classification"] != "synthetic" or payload["contains_real_data"] is not False:
            raise DatabaseMigrationRehearsalError("real_data_forbidden")
        if (
            type(payload["attestation_version"]) is not int
            or payload["attestation_version"] != 1
            or payload["project_id"] != "PP02"
            or payload["scope"] != "R4_DATABASE_REHEARSAL"
            or not isinstance(payload["source_sha256"], str)
        ):
            raise DatabaseMigrationRehearsalError("attestation_contract_invalid")
        if payload["source_sha256"] != source_digest:
            raise DatabaseMigrationRehearsalError("attestation_hash_mismatch")

    @classmethod
    def _preflight_source(cls, source: Path) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
        if source.stat().st_size:
            try:
                with source.open("rb") as stream:
                    if stream.read(16) != b"SQLite format 3\x00":
                        raise DatabaseMigrationRehearsalError("source_sqlite_invalid")
            except OSError as exc:
                raise DatabaseMigrationRehearsalError("source_read_failed") from exc

        try:
            uri = source.resolve().as_uri() + "?mode=ro&immutable=1"
            with sqlite3.connect(uri, uri=True) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchall()
                if integrity != [("ok",)]:
                    raise DatabaseMigrationRehearsalError("source_integrity_failed")
                source_tables = tuple(
                    sorted(
                        str(row[0])
                        for row in connection.execute(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        ).fetchall()
                    )
                )
                cls._validate_event_schema(connection, source_tables)
        except DatabaseMigrationRehearsalError:
            raise
        except sqlite3.DatabaseError as exc:
            raise DatabaseMigrationRehearsalError("source_sqlite_invalid") from exc
        except OSError as exc:
            raise DatabaseMigrationRehearsalError("source_read_failed") from exc

        official = set(OFFICIAL_EVENT_TABLES)
        excluded = tuple(name for name in source_tables if name not in official)
        return source_tables, excluded

    @staticmethod
    def _validate_event_schema(
        connection: sqlite3.Connection,
        source_tables: Iterable[str],
    ) -> None:
        present = set(source_tables) & set(OFFICIAL_EVENT_TABLES)
        if not present:
            return
        if present != set(OFFICIAL_EVENT_TABLES):
            raise DatabaseMigrationRehearsalError("partial_portfolio_schema")
        for model in PORTFOLIO_MODELS:
            required = {column.name for column in model.__table__.columns}
            actual = {
                str(row[1])
                for row in connection.execute(
                    f'PRAGMA table_info("{model.__tablename__}")'
                ).fetchall()
            }
            if not required.issubset(actual):
                raise DatabaseMigrationRehearsalError("partial_portfolio_schema")

    @classmethod
    def _export_from_upgraded_copy(cls, source_copy: Path) -> Dict[str, Any]:
        manager = cls._open_database(source_copy)
        try:
            return PortfolioBackupService(db_manager=manager).export_backup()
        finally:
            DatabaseManager.reset_instance()

    @classmethod
    def _restore_and_verify_target(
        cls,
        target: Path,
        backup: Dict[str, Any],
    ) -> Dict[str, Any]:
        manager = cls._open_database(target)
        try:
            service = PortfolioBackupService(db_manager=manager)
            preview = service.preview_restore(backup)
            service.restore_backup(backup, preview_token=preview["preview_token"])

            restored = service.export_backup()
            source_portfolio_digest = cls._digest(backup["portfolio"])
            restored_portfolio_digest = cls._digest(restored["portfolio"])
            if source_portfolio_digest != restored_portfolio_digest:
                raise DatabaseMigrationRehearsalError("portfolio_digest_mismatch")

            valid_preview = service.preview_restore(backup)
            stale_backup = copy.deepcopy(backup)
            stale_backup["metadata"]["created_at"] = "2000-01-01T00:00:00Z"
            stale_preview_rejected = False
            try:
                service.restore_backup(
                    stale_backup,
                    preview_token=valid_preview["preview_token"],
                )
            except PortfolioBackupConflictError:
                stale_preview_rejected = True
            if not stale_preview_rejected:
                raise DatabaseMigrationRehearsalError("rollback_probe_accepted")

            after_probe = service.export_backup()
            if cls._digest(after_probe["portfolio"]) != restored_portfolio_digest:
                raise DatabaseMigrationRehearsalError("rollback_probe_changed_target")

            counts = PortfolioBackupService._counts(restored["portfolio"])
        finally:
            DatabaseManager.reset_instance()

        if cls._derived_data_present(target):
            raise DatabaseMigrationRehearsalError("excluded_data_migrated")
        return {"counts": counts}

    @staticmethod
    def _open_database(path: Path) -> DatabaseManager:
        DatabaseManager.reset_instance()
        return DatabaseManager(db_url=f"sqlite:///{path.resolve().as_posix()}")

    @staticmethod
    def _digest(value: Dict[str, Any]) -> str:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=PortfolioBackupService._json_default,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _derived_data_present(target: Path) -> bool:
        try:
            with sqlite3.connect(target) as connection:
                tables = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                for table in DERIVED_PORTFOLIO_TABLES:
                    if table not in tables:
                        continue
                    quoted = table.replace('"', '""')
                    if connection.execute(
                        f'SELECT 1 FROM "{quoted}" LIMIT 1'
                    ).fetchone():
                        return True
        except sqlite3.DatabaseError as exc:
            raise DatabaseMigrationRehearsalError("target_verification_failed") from exc
        return False

    @staticmethod
    def _cleanup_target(target: Path) -> None:
        for candidate in (
            target,
            Path(str(target) + "-wal"),
            Path(str(target) + "-shm"),
        ):
            try:
                if candidate.is_file() or candidate.is_symlink():
                    candidate.unlink()
            except OSError:
                pass
