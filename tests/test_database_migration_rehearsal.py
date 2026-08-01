# -*- coding: utf-8 -*-
"""R4 contracts for synthetic-only database compatibility rehearsals."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

try:
    from src.services.database_migration_rehearsal_service import (
        DatabaseMigrationRehearsalError,
        DatabaseMigrationRehearsalService,
    )
except ModuleNotFoundError:
    DatabaseMigrationRehearsalError = None  # type: ignore[assignment,misc]
    DatabaseMigrationRehearsalService = None  # type: ignore[assignment,misc]


FAKE_EXCLUDED_SECRET = "r4-fake-excluded-secret-7b8d1f"
TARGET_NAME = "pp02-r4-migrated.db"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_attestation(source: Path, path: Path, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "attestation_version": 1,
        "project_id": "PP02",
        "scope": "R4_DATABASE_REHEARSAL",
        "classification": "synthetic",
        "contains_real_data": False,
        "source_sha256": _sha256(source),
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _create_empty_sqlite(path: Path) -> Path:
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=1")
    return path


def _create_portfolio_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE portfolio_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id VARCHAR(64),
            name VARCHAR(64) NOT NULL,
            broker VARCHAR(64),
            market VARCHAR(8) NOT NULL DEFAULT 'cn',
            base_currency VARCHAR(8) NOT NULL DEFAULT 'CNY',
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME,
            updated_at DATETIME
        );
        CREATE TABLE portfolio_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            trade_uid VARCHAR(128),
            symbol VARCHAR(16) NOT NULL,
            market VARCHAR(8) NOT NULL DEFAULT 'cn',
            currency VARCHAR(8) NOT NULL DEFAULT 'CNY',
            trade_date DATE NOT NULL,
            side VARCHAR(8) NOT NULL,
            quantity FLOAT NOT NULL,
            price FLOAT NOT NULL,
            fee FLOAT DEFAULT 0,
            tax FLOAT DEFAULT 0,
            note VARCHAR(255),
            dedup_hash VARCHAR(64),
            created_at DATETIME
        );
        CREATE TABLE portfolio_cash_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            event_date DATE NOT NULL,
            direction VARCHAR(8) NOT NULL,
            amount FLOAT NOT NULL,
            currency VARCHAR(8) NOT NULL DEFAULT 'CNY',
            note VARCHAR(255),
            created_at DATETIME
        );
        CREATE TABLE portfolio_corporate_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            symbol VARCHAR(16) NOT NULL,
            market VARCHAR(8) NOT NULL DEFAULT 'cn',
            currency VARCHAR(8) NOT NULL DEFAULT 'CNY',
            effective_date DATE NOT NULL,
            action_type VARCHAR(24) NOT NULL,
            cash_dividend_per_share FLOAT,
            split_ratio FLOAT,
            note VARCHAR(255),
            created_at DATETIME
        );
        """
    )


def _create_mixed_synthetic_sqlite(path: Path) -> Path:
    with sqlite3.connect(path) as connection:
        _create_portfolio_schema(connection)
        connection.executescript(
            """
            CREATE TABLE legacy_user_profiles (
                id INTEGER PRIMARY KEY,
                display_name TEXT,
                token TEXT
            );
            CREATE TABLE fund_positions (
                id INTEGER PRIMARY KEY,
                fund_code TEXT,
                note TEXT
            );
            CREATE TABLE portfolio_positions (
                id INTEGER PRIMARY KEY,
                account_id INTEGER,
                secret_note TEXT
            );
            """
        )
        connection.execute(
            """
            INSERT INTO portfolio_accounts
                (id, owner_id, name, broker, market, base_currency, is_active,
                 created_at, updated_at)
            VALUES (1, ?, 'Synthetic account', 'Synthetic broker', 'cn', 'CNY', 1,
                    '2026-07-01 00:00:00', '2026-07-01 00:00:00')
            """,
            (FAKE_EXCLUDED_SECRET,),
        )
        connection.execute(
            """
            INSERT INTO portfolio_cash_ledger
                (id, account_id, event_date, direction, amount, currency, note, created_at)
            VALUES (1, 1, '2026-07-01', 'in', 10000, 'CNY', 'synthetic cash',
                    '2026-07-01 00:00:00')
            """
        )
        connection.execute(
            """
            INSERT INTO portfolio_trades
                (id, account_id, trade_uid, symbol, market, currency, trade_date,
                 side, quantity, price, fee, tax, note, dedup_hash, created_at)
            VALUES (1, 1, 'synthetic-trade-1', '600519', 'cn', 'CNY', '2026-07-02',
                    'buy', 10, 100, 1, 0, 'synthetic trade', 'synthetic-dedup-1',
                    '2026-07-02 00:00:00')
            """
        )
        connection.execute(
            """
            INSERT INTO portfolio_corporate_actions
                (id, account_id, symbol, market, currency, effective_date, action_type,
                 cash_dividend_per_share, split_ratio, note, created_at)
            VALUES (1, 1, '600519', 'cn', 'CNY', '2026-07-03', 'cash_dividend',
                    1, NULL, 'synthetic dividend', '2026-07-03 00:00:00')
            """
        )
        connection.execute(
            "INSERT INTO legacy_user_profiles VALUES (1, 'Synthetic user', ?)",
            (FAKE_EXCLUDED_SECRET,),
        )
        connection.execute(
            "INSERT INTO fund_positions VALUES (1, '000001', ?)",
            (FAKE_EXCLUDED_SECRET,),
        )
        connection.execute(
            "INSERT INTO portfolio_positions VALUES (1, 1, ?)",
            (FAKE_EXCLUDED_SECRET,),
        )
    return path


@pytest.fixture()
def service():
    assert DatabaseMigrationRehearsalService is not None, (
        "R4 requires src.services.database_migration_rehearsal_service"
    )
    return DatabaseMigrationRehearsalService()


def test_empty_synthetic_database_rehearsal_passes_without_source_mutation(
    service, tmp_path: Path
) -> None:
    source = _create_empty_sqlite(tmp_path / "empty-source.db")
    attestation = _write_attestation(source, tmp_path / "empty-attestation.json")
    source_before = _sha256(source)

    report = service.run(
        source_path=source,
        attestation_path=attestation,
        workspace_dir=tmp_path / "workspace",
    )

    assert report["status"] == "pass"
    assert report["migration"]["counts"] == {
        "accounts": 0,
        "trades": 0,
        "cash_ledger": 0,
        "corporate_actions": 0,
    }
    assert report["source_unchanged"] is True
    assert _sha256(source) == source_before
    assert report["rollback"] == {
        "stale_preview_rejected": True,
        "target_unchanged": True,
    }
    assert (tmp_path / "workspace" / TARGET_NAME).is_file()


def test_mixed_synthetic_database_migrates_only_official_event_ledger(
    service, tmp_path: Path
) -> None:
    source = _create_mixed_synthetic_sqlite(tmp_path / "mixed-source.db")
    attestation = _write_attestation(source, tmp_path / "mixed-attestation.json")
    source_before = _sha256(source)
    workspace = tmp_path / "workspace"

    report = service.run(
        source_path=source,
        attestation_path=attestation,
        workspace_dir=workspace,
    )

    assert report["migration"]["counts"] == {
        "accounts": 1,
        "trades": 1,
        "cash_ledger": 1,
        "corporate_actions": 1,
    }
    assert report["migration"]["portfolio_digest_match"] is True
    assert report["migration"]["excluded_table_data_present"] is False
    assert set(report["schema"]["excluded_tables"]) >= {
        "legacy_user_profiles",
        "fund_positions",
        "portfolio_positions",
    }
    assert report["privacy"] == {
        "real_data_used": False,
        "backup_payload_persisted": False,
    }
    assert _sha256(source) == source_before

    target = workspace / TARGET_NAME
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT owner_id FROM portfolio_accounts").fetchone() == (None,)
        assert connection.execute("SELECT COUNT(*) FROM portfolio_positions").fetchone() == (0,)
        target_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert "legacy_user_profiles" not in target_tables
    assert "fund_positions" not in target_tables
    serialized_report = json.dumps(report, sort_keys=True)
    assert FAKE_EXCLUDED_SECRET not in serialized_report
    assert FAKE_EXCLUDED_SECRET.encode() not in target.read_bytes()


@pytest.mark.parametrize(
    ("attestation_mode", "expected_code"),
    [
        ("missing", "attestation_missing"),
        ("hash_mismatch", "attestation_hash_mismatch"),
        ("extra_field", "attestation_contract_invalid"),
    ],
)
def test_rehearsal_rejects_missing_or_mismatched_attestation(
    service,
    tmp_path: Path,
    attestation_mode: str,
    expected_code: str,
) -> None:
    source = _create_empty_sqlite(tmp_path / "source.db")
    attestation = tmp_path / "attestation.json"
    if attestation_mode == "hash_mismatch":
        _write_attestation(source, attestation, source_sha256="0" * 64)
    elif attestation_mode == "extra_field":
        _write_attestation(source, attestation, unexpected="not-allowed")

    with pytest.raises(DatabaseMigrationRehearsalError) as captured:
        service.run(
            source_path=source,
            attestation_path=attestation,
            workspace_dir=tmp_path / "workspace",
        )

    assert captured.value.code == expected_code
    assert not (tmp_path / "workspace" / TARGET_NAME).exists()


def test_rehearsal_rejects_real_data_declaration(service, tmp_path: Path) -> None:
    source = _create_empty_sqlite(tmp_path / "source.db")
    attestation = _write_attestation(
        source,
        tmp_path / "attestation.json",
        classification="sanitized",
        contains_real_data=True,
    )

    with pytest.raises(DatabaseMigrationRehearsalError) as captured:
        service.run(
            source_path=source,
            attestation_path=attestation,
            workspace_dir=tmp_path / "workspace",
        )

    assert captured.value.code == "real_data_forbidden"
    assert not (tmp_path / "workspace" / TARGET_NAME).exists()


def test_rehearsal_rejects_partial_portfolio_schema_before_target_write(
    service, tmp_path: Path
) -> None:
    source = tmp_path / "partial.db"
    with sqlite3.connect(source) as connection:
        connection.execute(
            "CREATE TABLE portfolio_accounts (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
    attestation = _write_attestation(source, tmp_path / "attestation.json")

    with pytest.raises(DatabaseMigrationRehearsalError) as captured:
        service.run(
            source_path=source,
            attestation_path=attestation,
            workspace_dir=tmp_path / "workspace",
        )

    assert captured.value.code == "partial_portfolio_schema"
    assert not (tmp_path / "workspace" / TARGET_NAME).exists()


def test_rehearsal_rejects_non_sqlite_source_before_target_write(
    service, tmp_path: Path
) -> None:
    source = tmp_path / "not-a-database.db"
    source.write_bytes(b"synthetic but not sqlite")
    attestation = _write_attestation(source, tmp_path / "attestation.json")

    with pytest.raises(DatabaseMigrationRehearsalError) as captured:
        service.run(
            source_path=source,
            attestation_path=attestation,
            workspace_dir=tmp_path / "workspace",
        )

    assert captured.value.code == "source_sqlite_invalid"
    assert not (tmp_path / "workspace" / TARGET_NAME).exists()


def test_rehearsal_preserves_existing_target_database(service, tmp_path: Path) -> None:
    source = _create_empty_sqlite(tmp_path / "source.db")
    attestation = _write_attestation(source, tmp_path / "attestation.json")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / TARGET_NAME
    target.write_bytes(b"pre-existing synthetic target")

    with pytest.raises(DatabaseMigrationRehearsalError) as captured:
        service.run(
            source_path=source,
            attestation_path=attestation,
            workspace_dir=workspace,
        )

    assert captured.value.code == "target_exists"
    assert target.read_bytes() == b"pre-existing synthetic target"


def test_rehearsal_rejects_symlink_source(service, tmp_path: Path) -> None:
    source = _create_empty_sqlite(tmp_path / "source.db")
    source_link = tmp_path / "source-link.db"
    source_link.symlink_to(source)
    attestation = _write_attestation(source, tmp_path / "attestation.json")

    with pytest.raises(DatabaseMigrationRehearsalError) as captured:
        service.run(
            source_path=source_link,
            attestation_path=attestation,
            workspace_dir=tmp_path / "workspace",
        )

    assert captured.value.code == "source_path_invalid"


def test_cli_writes_atomic_value_free_report(tmp_path: Path) -> None:
    source = _create_mixed_synthetic_sqlite(tmp_path / "mixed-source.db")
    attestation = _write_attestation(source, tmp_path / "attestation.json")
    workspace = tmp_path / "workspace"
    report_path = tmp_path / "report.json"
    root = Path(__file__).resolve().parents[1]

    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "pp02_database_migration_rehearsal.py"),
            "--source",
            str(source),
            "--attestation",
            str(attestation),
            "--workspace",
            str(workspace),
            "--report",
            str(report_path),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "R4_DATABASE_MIGRATION_REHEARSAL=PASS" in completed.stdout
    assert completed.stderr == ""
    assert report_path.is_file()
    assert not Path(str(report_path) + ".tmp").exists()
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "pass"
    visible_output = completed.stdout + completed.stderr + report_path.read_text(encoding="utf-8")
    assert FAKE_EXCLUDED_SECRET not in visible_output


def test_cli_failure_uses_stable_code_without_artifacts(tmp_path: Path) -> None:
    source = _create_empty_sqlite(tmp_path / "synthetic-secret-name.db")
    attestation = _write_attestation(
        source,
        tmp_path / "attestation.json",
        source_sha256="0" * 64,
    )
    workspace = tmp_path / "workspace"
    report_path = tmp_path / "report.json"
    root = Path(__file__).resolve().parents[1]

    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "pp02_database_migration_rehearsal.py"),
            "--source",
            str(source),
            "--attestation",
            str(attestation),
            "--workspace",
            str(workspace),
            "--report",
            str(report_path),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert completed.stdout == ""
    assert completed.stderr == (
        "R4_DATABASE_MIGRATION_REHEARSAL=FAIL code=attestation_hash_mismatch\n"
    )
    assert "synthetic-secret-name" not in completed.stderr
    assert not report_path.exists()
    assert not (workspace / TARGET_NAME).exists()


def test_cli_redacts_unexpected_failure(monkeypatch, capsys, tmp_path: Path) -> None:
    from scripts import pp02_database_migration_rehearsal as cli

    source = _create_empty_sqlite(tmp_path / "source.db")
    attestation = _write_attestation(source, tmp_path / "attestation.json")
    workspace = tmp_path / "workspace"
    report_path = tmp_path / "report.json"

    def fail_without_disclosing(self, **kwargs):
        raise RuntimeError(FAKE_EXCLUDED_SECRET)

    monkeypatch.setattr(
        cli.DatabaseMigrationRehearsalService,
        "run",
        fail_without_disclosing,
    )

    result = cli.main(
        [
            "--source",
            str(source),
            "--attestation",
            str(attestation),
            "--workspace",
            str(workspace),
            "--report",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "R4_DATABASE_MIGRATION_REHEARSAL=FAIL code=unexpected_failure\n"
    assert FAKE_EXCLUDED_SECRET not in captured.err
    assert not report_path.exists()
    assert not (workspace / TARGET_NAME).exists()
