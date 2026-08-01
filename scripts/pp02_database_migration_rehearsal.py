#!/usr/bin/env python3
"""Run the PP02 R4 synthetic-only database migration rehearsal."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.database_migration_rehearsal_service import (  # noqa: E402
    TARGET_DATABASE_NAME,
    DatabaseMigrationRehearsalError,
    DatabaseMigrationRehearsalService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the synthetic-only PP02 R4 SQLite migration rehearsal."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--attestation", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    return parser


def _validate_output_path(
    *,
    source: Path,
    attestation: Path,
    workspace: Path,
    report: Path,
) -> None:
    if report.is_symlink() or (report.exists() and not report.is_file()):
        raise DatabaseMigrationRehearsalError("report_path_invalid")
    report_parent = report.parent
    if report_parent.exists() and not report_parent.is_dir():
        raise DatabaseMigrationRehearsalError("report_path_invalid")

    report_resolved = report.resolve(strict=False)
    protected = {
        source.resolve(strict=False),
        attestation.resolve(strict=False),
        (workspace / TARGET_DATABASE_NAME).resolve(strict=False),
    }
    if report_resolved in protected:
        raise DatabaseMigrationRehearsalError("report_path_invalid")


def _write_report_atomic(report_path: Path, report: dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Optional[Path] = None
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
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass


def _cleanup_target(workspace: Path) -> None:
    target = workspace / TARGET_DATABASE_NAME
    for candidate in (target, Path(str(target) + "-wal"), Path(str(target) + "-shm")):
        try:
            if candidate.is_file() or candidate.is_symlink():
                candidate.unlink()
        except OSError:
            pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    target = args.workspace / TARGET_DATABASE_NAME
    target_existed_before = target.exists() or target.is_symlink()
    try:
        _validate_output_path(
            source=args.source,
            attestation=args.attestation,
            workspace=args.workspace,
            report=args.report,
        )
        report = DatabaseMigrationRehearsalService().run(
            source_path=args.source,
            attestation_path=args.attestation,
            workspace_dir=args.workspace,
        )
        try:
            _write_report_atomic(args.report, report)
        except OSError as exc:
            _cleanup_target(args.workspace)
            raise DatabaseMigrationRehearsalError("report_write_failed") from exc
    except DatabaseMigrationRehearsalError as exc:
        print(
            f"R4_DATABASE_MIGRATION_REHEARSAL=FAIL code={exc.code}",
            file=sys.stderr,
        )
        return 2
    except Exception:
        if not target_existed_before:
            _cleanup_target(args.workspace)
        print(
            "R4_DATABASE_MIGRATION_REHEARSAL=FAIL code=unexpected_failure",
            file=sys.stderr,
        )
        return 2

    print("R4_DATABASE_MIGRATION_REHEARSAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
