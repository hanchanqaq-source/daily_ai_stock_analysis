# -*- coding: utf-8 -*-
"""R6-A contracts for the fail-closed formal-data inventory tool."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
import pytest

try:
    import src.services.formal_data_inventory_service as inventory_module
    from src.services.formal_data_inventory_service import (
        INVENTORY_REPORT_NAME,
        FormalDataInventoryError,
        FormalDataInventoryService,
    )
except ModuleNotFoundError:
    inventory_module = None  # type: ignore[assignment]
    INVENTORY_REPORT_NAME = "pp02-formal-data-inventory-report.json"

    class FormalDataInventoryError(RuntimeError):  # type: ignore[no-redef]
        """Test-only import fallback so missing production code is a RED failure."""

    class FormalDataInventoryService:  # type: ignore[no-redef]
        """Test-only import fallback so missing production code is a RED failure."""

        def run(self, **_kwargs):
            pytest.fail("R6 inventory service is not implemented")


OFFICIAL_TABLES = (
    "portfolio_accounts",
    "portfolio_trades",
    "portfolio_cash_ledger",
    "portfolio_corporate_actions",
)
SYNTHETIC_ACCOUNT = "R6 synthetic account 9d771a"
SYNTHETIC_SYMBOL = "R6FAKE88"
SYNTHETIC_NOTE = "r6-synthetic-private-note-54c9"
SYNTHETIC_EXCEPTION = "r6-synthetic-exception-body-2a13"
SYNTHETIC_AMOUNT = "987654.25"
SYNTHETIC_PATH_MARKER = "r6-private-path-marker-4f29"

TABLE_DDL = {
    "portfolio_accounts": """
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
        )
    """,
    "portfolio_trades": """
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
        )
    """,
    "portfolio_cash_ledger": """
        CREATE TABLE portfolio_cash_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            event_date DATE NOT NULL,
            direction VARCHAR(8) NOT NULL,
            amount FLOAT NOT NULL,
            currency VARCHAR(8) NOT NULL DEFAULT 'CNY',
            note VARCHAR(255),
            created_at DATETIME
        )
    """,
    "portfolio_corporate_actions": """
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
        )
    """,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_official_database(
    path: Path,
    *,
    with_rows: bool,
    tables: tuple[str, ...] = OFFICIAL_TABLES,
    missing_account_updated_at: bool = False,
) -> Path:
    with sqlite3.connect(path) as connection:
        for table in tables:
            ddl = TABLE_DDL[table]
            if table == "portfolio_accounts" and missing_account_updated_at:
                ddl = ddl.replace(",\n            updated_at DATETIME", "")
            connection.execute(ddl)
        if with_rows:
            assert tables == OFFICIAL_TABLES
            connection.execute(
                """
                INSERT INTO portfolio_accounts
                    (id, owner_id, name, broker, market, base_currency, is_active,
                     created_at, updated_at)
                VALUES (1, NULL, ?, 'Synthetic broker', 'cn', 'CNY', 1,
                        '2026-08-01 00:00:00', '2026-08-01 00:00:00')
                """,
                (SYNTHETIC_ACCOUNT,),
            )
            connection.execute(
                """
                INSERT INTO portfolio_trades
                    (id, account_id, trade_uid, symbol, market, currency, trade_date,
                     side, quantity, price, fee, tax, note, dedup_hash, created_at)
                VALUES (1, 1, 'r6-synthetic-trade', ?, 'cn', 'CNY', '2026-08-01',
                        'buy', 2, 3, 0, 0, ?, 'r6-synthetic-dedup',
                        '2026-08-01 00:00:00')
                """,
                (SYNTHETIC_SYMBOL, SYNTHETIC_NOTE),
            )
            connection.execute(
                """
                INSERT INTO portfolio_cash_ledger
                    (id, account_id, event_date, direction, amount, currency, note,
                     created_at)
                VALUES (1, 1, '2026-08-01', 'in', ?, 'CNY', ?,
                        '2026-08-01 00:00:00')
                """,
                (float(SYNTHETIC_AMOUNT), SYNTHETIC_NOTE),
            )
            connection.execute(
                """
                INSERT INTO portfolio_corporate_actions
                    (id, account_id, symbol, market, currency, effective_date,
                     action_type, cash_dividend_per_share, split_ratio, note, created_at)
                VALUES (1, 1, ?, 'cn', 'CNY', '2026-08-01', 'cash_dividend',
                        1, NULL, ?, '2026-08-01 00:00:00')
                """,
                (SYNTHETIC_SYMBOL, SYNTHETIC_NOTE),
            )
    return path


def create_unrelated_database(path: Path) -> Path:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE analysis_history (id INTEGER PRIMARY KEY, content TEXT)"
        )
        connection.execute(
            "INSERT INTO analysis_history (content) VALUES (?)",
            (SYNTHETIC_NOTE,),
        )
    return path


def load_report(output_dir: Path) -> dict:
    return json.loads((output_dir / INVENTORY_REPORT_NAME).read_text(encoding="utf-8"))


def load_cli_module():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "pp02_formal_data_inventory.py"
    assert script_path.is_file(), "R6 inventory CLI is not implemented"
    spec = importlib.util.spec_from_file_location(
        "pp02_formal_data_inventory_cli_test",
        script_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def service():
    return FormalDataInventoryService()


def test_complete_empty_ledger_reports_no_formal_data_and_two_verified_backups(
    service, tmp_path: Path
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    source_before = sha256(source)
    output = tmp_path / "inventory"

    report = service.run(source_path=source, output_dir=output)

    assert report["status"] == "NO_FORMAL_DATA_FOUND"
    assert report["database"] == {
        "integrity_ok": True,
        "schema_compatible": True,
        "counts": {name: 0 for name in OFFICIAL_TABLES},
    }
    assert report["backup"] == {
        "copies": 2,
        "verified": True,
        "source_unchanged": True,
        "included_sidecars": [],
    }
    assert sha256(source) == source_before
    assert sha256(output / "backup-a" / source.name) == source_before
    assert sha256(output / "backup-b" / source.name) == source_before
    assert load_report(output) == report
    assert not list(output.glob(".inventory-check-*"))


def test_populated_ledger_reports_only_four_counts(service, tmp_path: Path) -> None:
    source = create_official_database(tmp_path / "private-source.db", with_rows=True)
    output = tmp_path / "inventory"

    report = service.run(source_path=source, output_dir=output)

    assert report["status"] == "FORMAL_DATA_FOUND"
    assert report["database"]["counts"] == {name: 1 for name in OFFICIAL_TABLES}
    assert report["privacy"] == {
        "row_values_selected": False,
        "row_values_reported": False,
        "real_data_uploaded": False,
        "migration_performed": False,
    }
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    for marker in (
        SYNTHETIC_ACCOUNT,
        SYNTHETIC_SYMBOL,
        SYNTHETIC_NOTE,
        SYNTHETIC_AMOUNT,
        str(source),
        source.name,
        str(output),
    ):
        assert marker not in serialized


def test_database_without_official_tables_reports_no_formal_data(
    service, tmp_path: Path
) -> None:
    source = create_unrelated_database(tmp_path / "source.db")

    report = service.run(source_path=source, output_dir=tmp_path / "inventory")

    assert report["status"] == "NO_FORMAL_DATA_FOUND"
    assert report["database"]["counts"] == {name: 0 for name in OFFICIAL_TABLES}
    assert SYNTHETIC_NOTE not in json.dumps(report, ensure_ascii=False)


@pytest.mark.parametrize(
    ("database_factory", "expected_code"),
    [
        (
            lambda path: create_official_database(
                path,
                with_rows=False,
                tables=("portfolio_accounts",),
            ),
            "partial_portfolio_schema",
        ),
        (
            lambda path: create_official_database(
                path,
                with_rows=False,
                missing_account_updated_at=True,
            ),
            "schema_incompatible",
        ),
    ],
)
def test_schema_blockers_preserve_verified_backups_and_write_limited_report(
    service,
    tmp_path: Path,
    database_factory,
    expected_code: str,
) -> None:
    source = database_factory(tmp_path / "source.db")
    output = tmp_path / "inventory"

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == expected_code
    assert captured.value.backups_verified is True
    assert (output / "backup-a" / source.name).is_file()
    assert (output / "backup-b" / source.name).is_file()
    report = load_report(output)
    assert report["status"] == "INVENTORY_BLOCKED"
    assert report["error_code"] == expected_code
    assert report["database"]["counts"] is None
    assert str(source) not in json.dumps(report, ensure_ascii=False)


def test_corrupted_sqlite_preserves_verified_backups_and_blocks(
    service, tmp_path: Path
) -> None:
    source = tmp_path / "source.db"
    source.write_bytes(b"synthetic-not-a-sqlite-database")
    output = tmp_path / "inventory"

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "source_sqlite_invalid"
    assert captured.value.backups_verified is True
    assert (output / "backup-a" / source.name).read_bytes() == source.read_bytes()
    assert load_report(output)["error_code"] == "source_sqlite_invalid"


def test_failed_integrity_check_blocks_without_counting_rows(
    service, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=True)
    output = tmp_path / "inventory"
    assert inventory_module is not None
    monkeypatch.setattr(inventory_module, "_integrity_ok", lambda connection: False)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "source_integrity_failed"
    assert captured.value.backups_verified is True
    serialized = json.dumps(load_report(output), ensure_ascii=False)
    assert SYNTHETIC_ACCOUNT not in serialized
    assert SYNTHETIC_SYMBOL not in serialized


def test_rollback_journal_blocks_before_output_creation(service, tmp_path: Path) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    Path(str(source) + "-journal").write_bytes(b"synthetic-open-transaction")
    output = tmp_path / "inventory"

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "rollback_journal_present"
    assert captured.value.backups_verified is False
    assert not output.exists()


def test_rollback_journal_created_during_backup_removes_untrusted_output(
    service,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"
    original_copy_snapshot = service._copy_snapshot
    copy_calls = 0

    def create_journal_during_first_copy(*args, **kwargs):
        nonlocal copy_calls
        copy_calls += 1
        result = original_copy_snapshot(*args, **kwargs)
        if copy_calls == 1:
            Path(str(source) + "-journal").write_bytes(
                b"synthetic-raced-open-transaction"
            )
        return result

    monkeypatch.setattr(service, "_copy_snapshot", create_journal_during_first_copy)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "rollback_journal_present"
    assert captured.value.backups_verified is False
    assert not output.exists()


def test_real_wal_and_shm_are_included_in_both_verified_backups(
    service, tmp_path: Path
) -> None:
    source = tmp_path / "source.db"
    connection = sqlite3.connect(source)
    try:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        connection.execute("PRAGMA wal_autocheckpoint=0")
        for table in OFFICIAL_TABLES:
            connection.execute(TABLE_DDL[table])
        connection.commit()
        connection.execute(
            "INSERT INTO portfolio_accounts (name, market, base_currency, is_active) "
            "VALUES (?, 'cn', 'CNY', 1)",
            (SYNTHETIC_ACCOUNT,),
        )
        connection.commit()
        wal = Path(str(source) + "-wal")
        shm = Path(str(source) + "-shm")
        assert wal.is_file()
        assert shm.is_file()
        source_hashes = {path.name: sha256(path) for path in (source, wal, shm)}

        output = tmp_path / "inventory"
        report = service.run(source_path=source, output_dir=output)

        assert report["status"] == "FORMAL_DATA_FOUND"
        assert report["backup"]["included_sidecars"] == ["-wal", "-shm"]
        for backup_name in ("backup-a", "backup-b"):
            backup = output / backup_name
            assert {path.name: sha256(path) for path in backup.iterdir()} == source_hashes
    finally:
        connection.close()


def test_source_change_after_copy_removes_untrusted_output(
    service, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"
    assert inventory_module is not None
    original_copy2 = inventory_module.shutil.copy2
    copy_count = 0

    def mutate_after_second_copy(source_path, destination_path):
        nonlocal copy_count
        result = original_copy2(source_path, destination_path)
        copy_count += 1
        if copy_count == 2:
            with source.open("ab") as stream:
                stream.write(b"source-changed-after-two-copies")
        return result

    monkeypatch.setattr(inventory_module.shutil, "copy2", mutate_after_second_copy)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "source_changed_during_backup"
    assert captured.value.backups_verified is False
    assert not output.exists()


def test_backup_hash_mismatch_removes_untrusted_output(
    service, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"
    assert inventory_module is not None
    original_copy2 = inventory_module.shutil.copy2

    def corrupt_backup_b(source_path, destination_path):
        result = original_copy2(source_path, destination_path)
        destination = Path(destination_path)
        if destination.parent.name == "backup-b":
            with destination.open("ab") as stream:
                stream.write(b"corrupted-backup-b")
        return result

    monkeypatch.setattr(inventory_module.shutil, "copy2", corrupt_backup_b)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "backup_mismatch"
    assert captured.value.backups_verified is False
    assert not output.exists()


def test_untrusted_output_cleanup_failure_uses_stable_blocking_code(
    service,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"
    assert inventory_module is not None

    def fail_copy(*_args, **_kwargs):
        raise OSError("synthetic backup copy failure")

    def fail_cleanup(*_args, **_kwargs):
        raise PermissionError("synthetic cleanup failure")

    monkeypatch.setattr(inventory_module.shutil, "copy2", fail_copy)
    monkeypatch.setattr(inventory_module.shutil, "rmtree", fail_cleanup)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "untrusted_output_cleanup_failed"
    assert captured.value.backups_verified is False
    assert output.exists()


def test_existing_output_directory_is_rejected_without_modification(
    service, tmp_path: Path
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "output_path_invalid"
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_source_and_output_path_collision_is_rejected(service, tmp_path: Path) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=source)

    assert captured.value.code == "path_overlap"
    assert source.is_file()


def test_symlink_source_is_rejected_without_output(service, tmp_path: Path) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    source_link = tmp_path / "source-link.db"
    source_link.symlink_to(source)
    output = tmp_path / "inventory"

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source_link, output_dir=output)

    assert captured.value.code == "source_path_invalid"
    assert not output.exists()


def test_reparse_point_source_is_rejected_without_output(
    service, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"
    assert inventory_module is not None
    original_probe = inventory_module._is_reparse_point
    monkeypatch.setattr(
        inventory_module,
        "_is_reparse_point",
        lambda path: Path(path) == source or original_probe(path),
    )

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "source_path_invalid"
    assert not output.exists()


def test_unexpected_inventory_failure_is_redacted_after_verified_backups(
    service, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=True)
    output = tmp_path / "inventory"

    def explode(check_source: Path):
        raise RuntimeError(SYNTHETIC_EXCEPTION)

    monkeypatch.setattr(service, "_inspect_copy", explode)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "inventory_failed"
    assert captured.value.backups_verified is True
    serialized = json.dumps(load_report(output), ensure_ascii=False, sort_keys=True)
    assert SYNTHETIC_EXCEPTION not in serialized
    assert SYNTHETIC_ACCOUNT not in serialized
    assert str(source) not in serialized


def test_inspection_copy_failure_does_not_claim_integrity_passed(
    service,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"

    def fail_before_integrity_check(**_kwargs):
        raise FormalDataInventoryError("inspection_copy_failed")

    monkeypatch.setattr(service, "_inspect_verified_backup", fail_before_integrity_check)

    with pytest.raises(FormalDataInventoryError) as captured:
        service.run(source_path=source, output_dir=output)

    assert captured.value.code == "inspection_copy_failed"
    report = load_report(output)
    assert report["database"]["integrity_ok"] is False
    assert report["database"]["schema_compatible"] is False


def test_report_write_is_atomic_and_leaves_no_temporary_file(service, tmp_path: Path) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"

    service.run(source_path=source, output_dir=output)

    assert (output / INVENTORY_REPORT_NAME).is_file()
    assert not list(output.glob(f".{INVENTORY_REPORT_NAME}.*.tmp"))


def test_service_import_does_not_load_application_database_modules() -> None:
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import src.services.formal_data_inventory_service; "
                "forbidden = {'src.storage', "
                "'src.services.database_migration_rehearsal_service', "
                "'src.services.portfolio_backup_service'}; "
                "loaded = forbidden.intersection(sys.modules); "
                "raise SystemExit(1 if loaded else 0)"
            ),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_cli_unknown_argument_never_echoes_private_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = load_cli_module()
    private_token = str(tmp_path / SYNTHETIC_PATH_MARKER)

    result = cli.main(["--unknown-private-path", private_token])

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "invalid_arguments\n"
    assert SYNTHETIC_PATH_MARKER not in captured.err


def test_cli_duplicate_source_never_echoes_private_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = load_cli_module()
    first_source = tmp_path / "first-source.db"
    private_source = tmp_path / f"{SYNTHETIC_PATH_MARKER}.db"
    output = tmp_path / "inventory"

    result = cli.main(
        [
            "--source",
            str(first_source),
            "--source",
            str(private_source),
            "--output-dir",
            str(output),
            "--confirm-apps-closed",
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "invalid_arguments\n"
    assert SYNTHETIC_PATH_MARKER not in captured.err
    assert not output.exists()


def test_cli_rejects_non_windows_before_creating_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cli = load_cli_module()
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"

    result = cli.main(
        [
            "--source",
            str(source),
            "--output-dir",
            str(output),
            "--confirm-apps-closed",
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "wrong_environment\n"
    assert not output.exists()


def test_cli_rejects_missing_closed_apps_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = load_cli_module()
    monkeypatch.setattr(cli, "_is_native_windows", lambda: True)
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"

    result = cli.main(
        ["--source", str(source), "--output-dir", str(output)]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "apps_not_confirmed_closed\n"
    assert not output.exists()


def test_cli_rejects_output_inside_git_repository(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = load_cli_module()
    monkeypatch.setattr(cli, "_is_native_windows", lambda: True)
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    repository = tmp_path / "repository"
    repository.mkdir()
    git_directory = repository / ".git"
    git_directory.mkdir()
    (git_directory / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (git_directory / "objects").mkdir()
    output = repository / "inventory"

    result = cli.main(
        [
            "--source",
            str(source),
            "--output-dir",
            str(output),
            "--confirm-apps-closed",
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "output_inside_git_repository\n"
    assert not output.exists()


def test_cli_ignores_empty_repository_marker(
    tmp_path: Path,
) -> None:
    cli = load_cli_module()
    ordinary_directory = tmp_path / "ordinary-directory"
    ordinary_directory.mkdir()
    (ordinary_directory / ".git").mkdir()

    assert cli._is_inside_git_repository(ordinary_directory / "inventory") is False


@pytest.mark.parametrize(
    ("with_rows", "expected_status"),
    [
        (False, "NO_FORMAL_DATA_FOUND"),
        (True, "FORMAL_DATA_FOUND"),
    ],
)
def test_cli_native_windows_success_prints_only_final_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    with_rows: bool,
    expected_status: str,
) -> None:
    cli = load_cli_module()
    monkeypatch.setattr(cli, "_is_native_windows", lambda: True)
    source = create_official_database(
        tmp_path / "private-path-marker-source.db",
        with_rows=with_rows,
    )
    output = tmp_path / "private-path-marker-output"

    result = cli.main(
        [
            "--source",
            str(source),
            "--output-dir",
            str(output),
            "--confirm-apps-closed",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == f"{expected_status}\n"
    assert captured.err == ""
    report = load_report(output)
    assert report["status"] == expected_status
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    for marker in (
        SYNTHETIC_ACCOUNT,
        SYNTHETIC_SYMBOL,
        SYNTHETIC_NOTE,
        SYNTHETIC_AMOUNT,
        "private-path-marker",
        str(source),
        str(output),
    ):
        assert marker not in captured.out
        assert marker not in captured.err
        assert marker not in serialized


def test_cli_inventory_blocked_prints_only_stable_code(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = load_cli_module()
    monkeypatch.setattr(cli, "_is_native_windows", lambda: True)
    source = create_official_database(
        tmp_path / "private-partial-source.db",
        with_rows=False,
        tables=("portfolio_accounts",),
    )
    output = tmp_path / "private-partial-output"

    result = cli.main(
        [
            "--source",
            str(source),
            "--output-dir",
            str(output),
            "--confirm-apps-closed",
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "partial_portfolio_schema\n"
    report = load_report(output)
    assert report["status"] == "INVENTORY_BLOCKED"
    assert report["error_code"] == "partial_portfolio_schema"
    assert "private-partial" not in json.dumps(report, ensure_ascii=False)


def test_native_windows_probe_rejects_wsl_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = load_cli_module()
    monkeypatch.setattr(cli.os, "name", "nt")
    monkeypatch.setattr(cli.sys, "platform", "win32")
    monkeypatch.setenv("WSL_INTEROP", "synthetic-wsl-marker")

    assert cli._is_native_windows() is False
