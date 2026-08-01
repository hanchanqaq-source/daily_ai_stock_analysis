# -*- coding: utf-8 -*-
"""Fail-closed, value-free inventory of the PP02 formal portfolio ledger."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping


INVENTORY_REPORT_NAME = "pp02-formal-data-inventory-report.json"
BACKUP_NAMES = ("backup-a", "backup-b")
SIDECAR_SUFFIXES = ("-wal", "-shm")

OFFICIAL_TABLE_COLUMNS = {
    "portfolio_accounts": frozenset(
        {
            "id",
            "owner_id",
            "name",
            "broker",
            "market",
            "base_currency",
            "is_active",
            "created_at",
            "updated_at",
        }
    ),
    "portfolio_trades": frozenset(
        {
            "id",
            "account_id",
            "trade_uid",
            "symbol",
            "market",
            "currency",
            "trade_date",
            "side",
            "quantity",
            "price",
            "fee",
            "tax",
            "note",
            "dedup_hash",
            "created_at",
        }
    ),
    "portfolio_cash_ledger": frozenset(
        {
            "id",
            "account_id",
            "event_date",
            "direction",
            "amount",
            "currency",
            "note",
            "created_at",
        }
    ),
    "portfolio_corporate_actions": frozenset(
        {
            "id",
            "account_id",
            "symbol",
            "market",
            "currency",
            "effective_date",
            "action_type",
            "cash_dividend_per_share",
            "split_ratio",
            "note",
            "created_at",
        }
    ),
}


class FormalDataInventoryError(RuntimeError):
    """Fail-closed inventory error carrying only a stable public code."""

    def __init__(self, code: str, *, backups_verified: bool = False):
        self.code = code
        self.backups_verified = backups_verified
        super().__init__(code)


@dataclass(frozen=True)
class _FileFingerprint:
    size: int
    modified_ns: int
    sha256: str


def _is_reparse_point(path: Path) -> bool:
    """Return whether an existing Windows path carries the reparse attribute."""

    try:
        path_stat = path.stat(follow_symlinks=False)
    except (OSError, ValueError):
        return False
    attribute = getattr(path_stat, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attribute & reparse_flag)


def _integrity_ok(connection: sqlite3.Connection) -> bool:
    """Run SQLite's full integrity check without exposing diagnostic rows."""

    return connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]


class FormalDataInventoryService:
    """Create two verified backups, then count fixed ledger tables on a copy."""

    def run(
        self,
        *,
        source_path: Path,
        output_dir: Path,
    ) -> Dict[str, Any]:
        source = Path(source_path)
        output = Path(output_dir)
        self._validate_paths(source, output)
        source_snapshot = self._snapshot_source(source)
        included_sidecars = [
            suffix for suffix in SIDECAR_SUFFIXES if suffix in source_snapshot
        ]

        output_created = False
        try:
            output.mkdir()
            output_created = True
            for backup_name in BACKUP_NAMES:
                backup_dir = output / backup_name
                self._assert_no_rollback_journal(source)
                self._copy_snapshot(source, source_snapshot, backup_dir)
                self._assert_no_rollback_journal(source)
            for backup_name in BACKUP_NAMES:
                self._verify_backup(
                    source,
                    source_snapshot,
                    output / backup_name,
                )
            self._assert_no_rollback_journal(source)
            final_snapshot = self._snapshot_source(source)
            self._assert_no_rollback_journal(source)
            if final_snapshot != source_snapshot:
                raise FormalDataInventoryError("source_changed_during_backup")
        except FormalDataInventoryError:
            if output_created:
                self._remove_untrusted_output(output)
            raise
        except Exception as exc:
            if output_created:
                self._remove_untrusted_output(output)
            raise FormalDataInventoryError("backup_failed") from exc

        try:
            counts = self._inspect_verified_backup(
                source_name=source.name,
                backup_dir=output / BACKUP_NAMES[0],
                output_dir=output,
            )
            status = (
                "FORMAL_DATA_FOUND"
                if any(counts.values())
                else "NO_FORMAL_DATA_FOUND"
            )
            report = self._success_report(
                status=status,
                counts=counts,
                included_sidecars=included_sidecars,
            )
            self._write_report_atomic(output / INVENTORY_REPORT_NAME, report)
            return report
        except FormalDataInventoryError as exc:
            self._persist_blocked_report(
                output=output,
                code=exc.code,
                included_sidecars=included_sidecars,
            )
            raise FormalDataInventoryError(
                exc.code,
                backups_verified=True,
            ) from exc
        except Exception as exc:
            code = "inventory_failed"
            self._persist_blocked_report(
                output=output,
                code=code,
                included_sidecars=included_sidecars,
            )
            raise FormalDataInventoryError(
                code,
                backups_verified=True,
            ) from exc

    @classmethod
    def _validate_paths(cls, source: Path, output: Path) -> None:
        source_absolute = source.absolute()
        output_absolute = output.absolute()
        if source_absolute == output_absolute or cls._is_relative_to(
            source_absolute,
            output_absolute,
        ):
            raise FormalDataInventoryError("path_overlap")
        if cls._has_unsafe_component(source) or not cls._is_regular_file(source):
            raise FormalDataInventoryError("source_path_invalid")
        if output.exists() or output.is_symlink():
            raise FormalDataInventoryError("output_path_invalid")
        if cls._has_unsafe_component(output.parent):
            raise FormalDataInventoryError("output_path_invalid")
        if not output.parent.is_dir():
            raise FormalDataInventoryError("output_path_invalid")
        cls._assert_no_rollback_journal(source)

    @staticmethod
    def _assert_no_rollback_journal(source: Path) -> None:
        rollback_journal = Path(str(source) + "-journal")
        if rollback_journal.exists() or rollback_journal.is_symlink():
            raise FormalDataInventoryError("rollback_journal_present")

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
        except ValueError:
            return False
        return True

    @staticmethod
    def _has_unsafe_component(path: Path) -> bool:
        absolute = path.absolute()
        for candidate in (absolute, *absolute.parents):
            if not candidate.exists() and not candidate.is_symlink():
                continue
            if candidate.is_symlink() or _is_reparse_point(candidate):
                return True
        return False

    @staticmethod
    def _is_regular_file(path: Path) -> bool:
        try:
            return stat.S_ISREG(path.lstat().st_mode)
        except OSError:
            return False

    @classmethod
    def _snapshot_source(cls, source: Path) -> Dict[str, _FileFingerprint]:
        cls._assert_no_rollback_journal(source)
        snapshot: Dict[str, _FileFingerprint] = {}
        for suffix in ("", *SIDECAR_SUFFIXES):
            candidate = cls._source_artifact(source, suffix)
            if suffix and not candidate.exists() and not candidate.is_symlink():
                continue
            if cls._has_unsafe_component(candidate) or not cls._is_regular_file(
                candidate
            ):
                raise FormalDataInventoryError("source_path_invalid")
            try:
                candidate_stat = candidate.stat(follow_symlinks=False)
                snapshot[suffix] = _FileFingerprint(
                    size=candidate_stat.st_size,
                    modified_ns=candidate_stat.st_mtime_ns,
                    sha256=cls._sha256(candidate),
                )
            except OSError as exc:
                raise FormalDataInventoryError("source_read_failed") from exc
        cls._assert_no_rollback_journal(source)
        return snapshot

    @staticmethod
    def _source_artifact(source: Path, suffix: str) -> Path:
        return source if not suffix else Path(str(source) + suffix)

    @classmethod
    def _copy_snapshot(
        cls,
        source: Path,
        snapshot: Mapping[str, _FileFingerprint],
        backup_dir: Path,
    ) -> None:
        try:
            backup_dir.mkdir()
            for suffix in snapshot:
                candidate = cls._source_artifact(source, suffix)
                shutil.copy2(candidate, backup_dir / candidate.name)
        except OSError as exc:
            raise FormalDataInventoryError("backup_failed") from exc

    @classmethod
    def _verify_backup(
        cls,
        source: Path,
        snapshot: Mapping[str, _FileFingerprint],
        backup_dir: Path,
    ) -> None:
        for suffix, expected in snapshot.items():
            destination = backup_dir / cls._source_artifact(source, suffix).name
            if cls._has_unsafe_component(destination) or not cls._is_regular_file(
                destination
            ):
                raise FormalDataInventoryError("backup_mismatch")
            try:
                if destination.stat().st_size != expected.size:
                    raise FormalDataInventoryError("backup_mismatch")
                if cls._sha256(destination) != expected.sha256:
                    raise FormalDataInventoryError("backup_mismatch")
            except OSError as exc:
                raise FormalDataInventoryError("backup_verification_failed") from exc

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _inspect_verified_backup(
        self,
        *,
        source_name: str,
        backup_dir: Path,
        output_dir: Path,
    ) -> Dict[str, int]:
        with tempfile.TemporaryDirectory(
            prefix=".inventory-check-",
            dir=output_dir,
        ) as temporary:
            check_dir = Path(temporary)
            try:
                for source_file in backup_dir.iterdir():
                    shutil.copy2(source_file, check_dir / source_file.name)
            except OSError as exc:
                raise FormalDataInventoryError("inspection_copy_failed") from exc
            return self._inspect_copy(check_dir / source_name)

    @staticmethod
    def _inspect_copy(check_source: Path) -> Dict[str, int]:
        try:
            if check_source.stat().st_size:
                with check_source.open("rb") as stream:
                    if stream.read(16) != b"SQLite format 3\x00":
                        raise FormalDataInventoryError("source_sqlite_invalid")

            uri = check_source.resolve().as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=0) as connection:
                connection.execute("PRAGMA query_only = ON")
                if not _integrity_ok(connection):
                    raise FormalDataInventoryError("source_integrity_failed")
                tables = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                official = set(OFFICIAL_TABLE_COLUMNS)
                present = official & tables
                if present and present != official:
                    raise FormalDataInventoryError("partial_portfolio_schema")
                if not present:
                    return {table: 0 for table in OFFICIAL_TABLE_COLUMNS}

                counts: Dict[str, int] = {}
                for table, required_columns in OFFICIAL_TABLE_COLUMNS.items():
                    actual_columns = {
                        str(row[1])
                        for row in connection.execute(
                            f'PRAGMA table_info("{table}")'
                        ).fetchall()
                    }
                    if not required_columns.issubset(actual_columns):
                        raise FormalDataInventoryError("schema_incompatible")
                    row = connection.execute(
                        f'SELECT COUNT(*) FROM "{table}"'
                    ).fetchone()
                    if row is None or type(row[0]) is not int:
                        raise FormalDataInventoryError("count_failed")
                    counts[table] = row[0]
                return counts
        except FormalDataInventoryError:
            raise
        except sqlite3.DatabaseError as exc:
            raise FormalDataInventoryError("source_sqlite_invalid") from exc
        except OSError as exc:
            raise FormalDataInventoryError("inspection_read_failed") from exc

    @staticmethod
    def _privacy_report() -> Dict[str, bool]:
        return {
            "row_values_selected": False,
            "row_values_reported": False,
            "real_data_uploaded": False,
            "migration_performed": False,
        }

    @classmethod
    def _success_report(
        cls,
        *,
        status: str,
        counts: Mapping[str, int],
        included_sidecars: list[str],
    ) -> Dict[str, Any]:
        return {
            "report_version": 1,
            "project_id": "PP02",
            "status": status,
            "backup": {
                "copies": 2,
                "verified": True,
                "source_unchanged": True,
                "included_sidecars": included_sidecars,
            },
            "database": {
                "integrity_ok": True,
                "schema_compatible": True,
                "counts": dict(counts),
            },
            "privacy": cls._privacy_report(),
        }

    @classmethod
    def _blocked_report(
        cls,
        *,
        code: str,
        included_sidecars: list[str],
    ) -> Dict[str, Any]:
        integrity_ok = code not in {
            "inspection_copy_failed",
            "source_sqlite_invalid",
            "source_integrity_failed",
            "inspection_read_failed",
            "inventory_failed",
        }
        return {
            "report_version": 1,
            "project_id": "PP02",
            "status": "INVENTORY_BLOCKED",
            "error_code": code,
            "backup": {
                "copies": 2,
                "verified": True,
                "source_unchanged": True,
                "included_sidecars": included_sidecars,
            },
            "database": {
                "integrity_ok": integrity_ok,
                "schema_compatible": False,
                "counts": None,
            },
            "privacy": cls._privacy_report(),
        }

    @classmethod
    def _persist_blocked_report(
        cls,
        *,
        output: Path,
        code: str,
        included_sidecars: list[str],
    ) -> None:
        report = cls._blocked_report(
            code=code,
            included_sidecars=included_sidecars,
        )
        try:
            cls._write_report_atomic(output / INVENTORY_REPORT_NAME, report)
        except FormalDataInventoryError:
            raise
        except Exception as exc:
            raise FormalDataInventoryError(
                "report_write_failed",
                backups_verified=True,
            ) from exc

    @staticmethod
    def _write_report_atomic(report_path: Path, report: Mapping[str, Any]) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=report_path.parent,
                prefix=f".{report_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                json.dump(
                    report,
                    stream,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, report_path)
            temporary_path = None
        except OSError as exc:
            raise FormalDataInventoryError(
                "report_write_failed",
                backups_verified=True,
            ) from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def _remove_untrusted_output(output: Path) -> None:
        try:
            shutil.rmtree(output)
        except OSError:
            pass
        if output.exists() or output.is_symlink():
            raise FormalDataInventoryError("untrusted_output_cleanup_failed")
