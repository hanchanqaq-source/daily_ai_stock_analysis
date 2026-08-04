"""Integration tests for fail-closed, recoverable full-data restore."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select

from src.config import Config
from src.core.config_manager import ConfigManager
from src.services import full_data_backup_service as backup_module
from src.services.full_data_backup_service import (
    FullDataBackupConflictError,
    FullDataBackupRestoreError,
    FullDataBackupService,
    FullDataBackupValidationError,
)
from src.services.system_config_service import SystemConfigService
from src.storage import (
    AnalysisHistory,
    DatabaseManager,
    PeriodReportRecord,
    PortfolioAccount,
    PortfolioCashLedger,
    PortfolioCorporateAction,
    PortfolioDailySnapshot,
    PortfolioPosition,
    PortfolioPositionLot,
    PortfolioTrade,
)


APPLICATION_VERSION = "test-app-7.4.1"


@pytest.fixture(autouse=True)
def _reset_singletons():
    original_environment = os.environ.copy()
    yield
    DatabaseManager.reset_instance()
    Config.reset_instance()
    os.environ.clear()
    os.environ.update(original_environment)


def _write_env(path: Path, db_path: Path, *settings: str) -> None:
    path.write_text(
        "\n".join((*settings, f"DATABASE_PATH={db_path}")) + "\n",
        encoding="utf-8",
    )


def _open_install(monkeypatch, env_path: Path, db_path: Path):
    DatabaseManager.reset_instance()
    Config.reset_instance()
    monkeypatch.setenv("ENV_FILE", str(env_path))
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    db = DatabaseManager.get_instance()
    config = SystemConfigService()
    return db, config, FullDataBackupService(
        db_manager=db,
        config_service=config,
        application_version=APPLICATION_VERSION,
    )


def _seed_source(db: DatabaseManager) -> None:
    with db.get_session() as session:
        session.add_all(
            (
                AnalysisHistory(
                    id=101,
                    query_id="analysis-fixed-101",
                    code="600519",
                    name="Moutai",
                    report_type="stock",
                    analysis_summary="fixed stock content summary",
                    raw_result='{"result":"fixed-stock"}',
                    context_snapshot='{"context":"fixed-stock"}',
                    created_at=datetime(2026, 8, 1, 9, 0, 0),
                ),
                AnalysisHistory(
                    id=202,
                    query_id="market-fixed-202",
                    code="MARKET",
                    name="Market review",
                    report_type="market",
                    analysis_summary="fixed market content summary",
                    created_at=datetime(2026, 8, 1, 10, 0, 0),
                ),
                PeriodReportRecord(
                    id=303,
                    period="previous_week",
                    report_kind="historical",
                    start_date=date(2026, 7, 20),
                    end_date=date(2026, 7, 24),
                    content_json='{"title":"fixed persisted period report"}',
                    source_record_ids_json="[101,202]",
                    status="ready",
                    generated_at=datetime(2026, 8, 1, 11, 0, 0),
                    updated_at=datetime(2026, 8, 1, 11, 0, 0),
                ),
                PortfolioAccount(
                    id=401,
                    owner_id="source-owner-is-not-backed-up",
                    name="Fixed synthetic account",
                    market="cn",
                    base_currency="CNY",
                    is_active=True,
                    created_at=datetime(2026, 8, 1, 12, 0, 0),
                    updated_at=datetime(2026, 8, 1, 12, 0, 0),
                ),
                PortfolioCashLedger(
                    id=402,
                    account_id=401,
                    event_date=date(2026, 8, 1),
                    direction="in",
                    amount=1000.0,
                    currency="CNY",
                    note="fixed cash event",
                    created_at=datetime(2026, 8, 1, 12, 1, 0),
                ),
                PortfolioTrade(
                    id=403,
                    account_id=401,
                    trade_uid="trade-fixed-403",
                    symbol="600519",
                    market="cn",
                    currency="CNY",
                    trade_date=date(2026, 8, 1),
                    side="buy",
                    quantity=1.0,
                    price=100.0,
                    note="fixed trade event",
                    dedup_hash="dedup-fixed-403",
                    created_at=datetime(2026, 8, 1, 12, 2, 0),
                ),
                PortfolioCorporateAction(
                    id=404,
                    account_id=401,
                    symbol="600519",
                    market="cn",
                    currency="CNY",
                    effective_date=date(2026, 8, 1),
                    action_type="cash_dividend",
                    cash_dividend_per_share=1.0,
                    note="fixed corporate event",
                    created_at=datetime(2026, 8, 1, 12, 3, 0),
                ),
            )
        )
        session.commit()


def _seed_destination(db: DatabaseManager) -> None:
    with db.get_session() as session:
        session.add_all(
            (
                AnalysisHistory(
                    id=9,
                    query_id="destination-fixed-9",
                    code="000001",
                    name="Destination row",
                    report_type="stock",
                    analysis_summary="destination content before restore",
                    created_at=datetime(2026, 8, 2, 9, 0, 0),
                ),
                PortfolioAccount(
                    id=401,
                    name="Stale destination account",
                    market="cn",
                    base_currency="CNY",
                    is_active=True,
                ),
                PortfolioTrade(
                    id=403,
                    account_id=401,
                    trade_uid="stale-destination-trade-403",
                    symbol="000001",
                    market="cn",
                    currency="CNY",
                    trade_date=date(2026, 8, 2),
                    side="buy",
                    quantity=2.0,
                    price=9.0,
                    dedup_hash="stale-destination-dedup-403",
                ),
                PortfolioPosition(
                    id=401,
                    account_id=401,
                    symbol="000001",
                    market="cn",
                    currency="CNY",
                    quantity=2.0,
                    avg_cost=9.0,
                    total_cost=18.0,
                    last_price=9.0,
                    market_value_base=18.0,
                    unrealized_pnl_base=0.0,
                    valuation_currency="CNY",
                ),
                PortfolioPositionLot(
                    id=403,
                    account_id=401,
                    symbol="000001",
                    market="cn",
                    currency="CNY",
                    open_date=date(2026, 8, 2),
                    remaining_quantity=2.0,
                    unit_cost=9.0,
                    source_trade_id=403,
                ),
                PortfolioDailySnapshot(
                    id=404,
                    account_id=401,
                    snapshot_date=date(2026, 8, 2),
                    base_currency="CNY",
                    total_cash=10.0,
                    total_market_value=18.0,
                    total_equity=28.0,
                    payload='{"stale":true}',
                ),
            )
        )
        session.commit()


def _prepare_source_and_destination(tmp_path: Path, monkeypatch, *, seed_destination: bool):
    source_env = tmp_path / "source.env"
    source_db_path = tmp_path / "source.db"
    _write_env(
        source_env,
        source_db_path,
        'STOCK_LIST="600519,AAPL"',
        "OPENAI_API_KEY=source-secret-is-excluded",
    )
    source_db, _, source_service = _open_install(
        monkeypatch,
        source_env,
        source_db_path,
    )
    _seed_source(source_db)
    backup = source_service.export_backup()

    destination_env = tmp_path / "destination.env"
    destination_db_path = tmp_path / "destination.db"
    _write_env(
        destination_env,
        destination_db_path,
        "STOCK_LIST=000001",
        "MAX_WORKERS=2",
        "OPENAI_API_KEY=destination-secret-must-survive",
    )
    destination_db, destination_config, destination_service = _open_install(
        monkeypatch,
        destination_env,
        destination_db_path,
    )
    if seed_destination:
        _seed_destination(destination_db)
    return {
        "backup": backup,
        "db": destination_db,
        "db_path": destination_db_path,
        "env_path": destination_env,
        "config": destination_config,
        "service": destination_service,
    }


def _sqlite_logical_digest(db_path: Path) -> str:
    """Hash a WAL-aware logical snapshot of every SQLite object and row."""
    with sqlite3.connect(db_path) as connection:
        dump = "\n".join(connection.iterdump())
    return hashlib.sha256(dump.encode("utf-8")).hexdigest()


def _derived_counts(session) -> dict[str, int]:
    return {
        model.__tablename__: session.execute(
            select(func.count()).select_from(model)
        ).scalar_one()
        for model in (
            PortfolioPosition,
            PortfolioPositionLot,
            PortfolioDailySnapshot,
        )
    }


def _assert_fixed_source_state(service: FullDataBackupService) -> None:
    data = service.export_backup()["data"]
    histories = data["tables"]["analysis_history"]
    assert [(row["id"], row["query_id"], row["analysis_summary"]) for row in histories] == [
        (101, "analysis-fixed-101", "fixed stock content summary"),
        (202, "market-fixed-202", "fixed market content summary"),
    ]
    assert [row["id"] for row in data["tables"]["period_reports"]] == [303]
    assert data["tables"]["period_reports"][0]["content_json"] == (
        '{"title":"fixed persisted period report"}'
    )
    assert data["tables"]["period_reports"][0]["source_record_ids_json"] == "[101,202]"
    assert [row["id"] for row in data["tables"]["portfolio_accounts"]] == [401]
    assert [row["id"] for row in data["tables"]["portfolio_cash_ledger"]] == [402]
    assert data["tables"]["portfolio_cash_ledger"][0]["note"] == "fixed cash event"
    assert [row["id"] for row in data["tables"]["portfolio_trades"]] == [403]
    assert data["tables"]["portfolio_trades"][0]["trade_uid"] == "trade-fixed-403"
    assert data["tables"]["portfolio_trades"][0]["note"] == "fixed trade event"
    assert [row["id"] for row in data["tables"]["portfolio_corporate_actions"]] == [404]
    assert data["tables"]["portfolio_corporate_actions"][0]["note"] == (
        "fixed corporate event"
    )
    assert data["configuration"]["values"] == {"STOCK_LIST": "600519,AAPL"}


def test_clean_install_restore_writes_recovery_before_replace_and_survives_restart(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )
    service = install["service"]
    original_replace = service._replace_tables
    recovery_seen_before_replace = []
    baseline_receipts = len(SystemConfigService._restore_receipts)

    def replace_with_recovery_observation(session, tables):
        recovery_seen_before_replace.append(list(service.recovery_directory.glob("*.json")))
        return original_replace(session, tables)

    monkeypatch.setattr(service, "_replace_tables", replace_with_recovery_observation)
    preview = service.preview_restore(install["backup"])
    result = service.restore_backup(
        install["backup"],
        preview_token=preview["preview_token"],
    )

    assert preview["incoming_digest"] == install["backup"]["integrity"]["value"]
    assert preview["destination_digest"]
    assert result["restart_required"] is True
    assert result["recovery"]["filename"] == Path(result["recovery"]["path"]).name
    assert Path(result["recovery"]["path"]).is_file()
    assert recovery_seen_before_replace and recovery_seen_before_replace[0]
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    _assert_fixed_source_state(service)
    env_text = install["env_path"].read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=destination-secret-must-survive" in env_text
    assert "MAX_WORKERS=" not in env_text

    _, _, restarted_service = _open_install(
        monkeypatch,
        install["env_path"],
        install["db_path"],
    )
    _assert_fixed_source_state(restarted_service)


def test_restore_recreates_dynamic_monkey_llm_values_and_removes_stale_safe_channel_fields(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )
    service = install["service"]
    backup = install["backup"]
    incoming_values = backup["data"]["configuration"]["values"]
    incoming_values.update(
        {
            "LLM_CHANNELS": "monkey",
            "LLM_MONKEY_PROTOCOL": "openai",
            "LLM_MONKEY_BASE_URL": "https://llm.example.com/v1",
            "LLM_MONKEY_MODELS": "monkey-chat,monkey-reasoner",
            "LLM_MONKEY_ENABLED": "true",
        }
    )
    backup["manifest"]["categories"]["configuration"]["row_count"] = len(incoming_values)
    backup["integrity"]["value"] = service.canonical_sha256(backup)
    install["env_path"].write_text(
        install["env_path"].read_text(encoding="utf-8")
        + "LLM_CHANNELS=stale\n"
        + "LLM_STALE_PROTOCOL=openai\n"
        + "LLM_STALE_BASE_URL=https://stale.example.com/v1\n"
        + "LLM_STALE_MODELS=stale-chat\n"
        + "LLM_STALE_ENABLED=true\n"
        + "LLM_STALE_API_KEY=destination-secret-must-survive\n",
        encoding="utf-8",
    )

    preview = service.preview_restore(backup)
    result = service.restore_backup(backup, preview_token=preview["preview_token"])

    config_map = ConfigManager(env_path=install["env_path"]).read_config_map()
    assert {key: config_map[key] for key in incoming_values} == incoming_values
    for key in (
        "LLM_STALE_PROTOCOL",
        "LLM_STALE_BASE_URL",
        "LLM_STALE_MODELS",
        "LLM_STALE_ENABLED",
    ):
        assert key not in config_map
    assert config_map["LLM_STALE_API_KEY"] == "destination-secret-must-survive"
    expected_state_digest = service._state_digest(
        backup["data"]["tables"],
        backup["data"]["configuration"],
    )
    assert result["destination_digest_after"] == expected_state_digest
    assert service.current_state_digest() == expected_state_digest


def test_post_publish_keyboard_interrupt_rolls_back_and_compensates_before_propagating(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    manager = install["config"]._manager
    original_publish = manager._publish_staged_bytes
    interruption = KeyboardInterrupt("injected interrupt after config publication")
    interrupt_pending = True
    before = service.export_backup()
    before_digest = service.current_state_digest()
    before_database_digest = _sqlite_logical_digest(install["db_path"])
    before_config_bytes = install["env_path"].read_bytes()
    baseline_receipts = len(SystemConfigService._restore_receipts)

    def publish_then_interrupt_once(staged_path):
        nonlocal interrupt_pending
        original_publish(staged_path)
        if interrupt_pending:
            interrupt_pending = False
            raise interruption

    monkeypatch.setattr(manager, "_publish_staged_bytes", publish_then_interrupt_once)
    preview = service.preview_restore(install["backup"])

    with pytest.raises(KeyboardInterrupt) as caught:
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert caught.value is interruption
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert service.current_state_digest() == before_digest
    assert _sqlite_logical_digest(install["db_path"]) == before_database_digest
    assert install["env_path"].read_bytes() == before_config_bytes
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    recovery_paths = list(service.recovery_directory.glob("*.json"))
    assert len(recovery_paths) == 1
    recovery = json.loads(recovery_paths[0].read_text(encoding="utf-8"))
    service.validate_backup(recovery)
    assert recovery["data"] == before["data"]


def test_restore_surfaces_post_commit_receipt_finalization_failure_without_leak(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )
    service = install["service"]
    baseline_receipts = len(SystemConfigService._restore_receipts)
    original_finalize = install["config"].finalize_env_subset_atomically

    def finalize_then_raise(receipt):
        original_finalize(receipt)
        raise RuntimeError("injected finalization failure after receipt cleanup")

    monkeypatch.setattr(
        install["config"],
        "finalize_env_subset_atomically",
        finalize_then_raise,
    )
    preview = service.preview_restore(install["backup"])

    result = service.restore_backup(
        install["backup"],
        preview_token=preview["preview_token"],
    )

    assert result["success"] is True
    assert result["warnings"] == ["Configuration receipt finalization failed after committed restore."]
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    _assert_fixed_source_state(service)


def test_commit_then_raise_keeps_incoming_config_and_returns_truthful_committed_result(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    preview = service.preview_restore(install["backup"])
    original_get_session = service.db.get_session
    injected = False

    def get_session_with_commit_then_raise():
        nonlocal injected
        session = original_get_session()
        if not injected:
            injected = True
            original_commit = session.commit

            def commit_then_raise():
                original_commit()
                raise RuntimeError("injected error after real database commit")

            session.commit = commit_then_raise
        return session

    monkeypatch.setattr(service.db, "get_session", get_session_with_commit_then_raise)

    result = service.restore_backup(
        install["backup"],
        preview_token=preview["preview_token"],
    )

    assert result["success"] is True
    assert result["warnings"] == ["Database commit completed although commit finalization raised an error."]
    assert service.current_state_digest() == result["destination_digest_after"]
    assert service.export_configuration_values() == install["backup"]["data"]["configuration"]["values"]
    _assert_fixed_source_state(service)


def test_restore_uses_validated_immutable_snapshot_when_caller_mutates_during_recovery(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )
    service = install["service"]
    original_write = service._write_recovery_artifact

    def write_then_mutate_caller_document(document, *, destination_digest):
        result = original_write(document, destination_digest=destination_digest)
        install["backup"]["data"]["configuration"]["values"]["STOCK_LIST"] = "300750"
        incoming_row = install["backup"]["data"]["tables"]["analysis_history"][0]
        incoming_row["analysis_summary"] = "unvalidated mutation after restore validation"
        incoming_row["raw_result"] = '{"api_token":"post-validation-secret-marker"}'
        return result

    monkeypatch.setattr(service, "_write_recovery_artifact", write_then_mutate_caller_document)
    preview = service.preview_restore(install["backup"])

    service.restore_backup(
        install["backup"],
        preview_token=preview["preview_token"],
    )

    with install["db"].get_session() as session:
        restored = session.get(AnalysisHistory, 101)
        assert restored.analysis_summary == "fixed stock content summary"
        assert restored.raw_result == '{"result":"fixed-stock"}'
    assert service.export_configuration_values() == {"STOCK_LIST": "600519,AAPL"}
    assert "post-validation-secret-marker" not in install["env_path"].read_text(
        encoding="utf-8"
    )


def test_restore_clears_derived_portfolio_caches_with_foreign_keys_enabled(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    with install["db"].get_session() as session:
        assert _derived_counts(session) == {
            "portfolio_positions": 1,
            "portfolio_position_lots": 1,
            "portfolio_daily_snapshots": 1,
        }
    foreign_key_states = []
    original_replace = service._replace_tables

    def observe_foreign_keys(session, tables):
        foreign_key_states.append(
            session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar_one()
        )
        return original_replace(session, tables)

    monkeypatch.setattr(service, "_replace_tables", observe_foreign_keys)
    preview = service.preview_restore(install["backup"])
    service.restore_backup(
        install["backup"],
        preview_token=preview["preview_token"],
    )

    assert foreign_key_states == [1]
    with install["db"].get_session() as session:
        assert _derived_counts(session) == {
            "portfolio_positions": 0,
            "portfolio_position_lots": 0,
            "portfolio_daily_snapshots": 0,
        }


@pytest.mark.parametrize(
    "mutation",
    (
        lambda document: document["integrity"].update(value="0" * 64),
        lambda document: document.pop("manifest"),
        lambda document: document["metadata"].update(
            database_schema_version="incompatible-schema"
        ),
    ),
)
def test_preview_validation_rejections_preserve_destination_without_recovery(
    tmp_path,
    monkeypatch,
    mutation,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    malformed = copy.deepcopy(install["backup"])
    mutation(malformed)
    before = service.current_state_digest()

    with pytest.raises(FullDataBackupValidationError):
        service.preview_restore(malformed)

    assert service.current_state_digest() == before
    assert not service.recovery_directory.exists()


def test_restore_rejects_stale_destination_and_stale_input_without_side_effects(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    destination_preview = service.preview_restore(install["backup"])
    with install["db"].get_session() as session:
        session.add(
            AnalysisHistory(
                id=10,
                query_id="destination-changed-10",
                code="000002",
                analysis_summary="destination changed after preview",
                created_at=datetime(2026, 8, 2, 10, 0, 0),
            )
        )
        session.commit()
    changed_destination_digest = service.current_state_digest()

    with pytest.raises(FullDataBackupConflictError):
        service.restore_backup(
            install["backup"],
            preview_token=destination_preview["preview_token"],
        )

    assert service.current_state_digest() == changed_destination_digest
    assert not service.recovery_directory.exists()

    input_preview = service.preview_restore(install["backup"])
    changed_input = copy.deepcopy(install["backup"])
    changed_input["data"]["tables"]["analysis_history"][0]["analysis_summary"] = (
        "different valid incoming summary"
    )
    changed_input["integrity"]["value"] = service.canonical_sha256(changed_input)
    before_input_rejection = service.current_state_digest()

    with pytest.raises(FullDataBackupConflictError):
        service.restore_backup(
            changed_input,
            preview_token=input_preview["preview_token"],
        )

    assert service.current_state_digest() == before_input_rejection
    assert not service.recovery_directory.exists()

    configuration_preview = service.preview_restore(install["backup"])
    install["env_path"].write_text(
        install["env_path"].read_text(encoding="utf-8").replace(
            "STOCK_LIST=000001",
            "STOCK_LIST=300750",
        ),
        encoding="utf-8",
    )
    changed_configuration_digest = service.current_state_digest()

    with pytest.raises(FullDataBackupConflictError):
        service.restore_backup(
            install["backup"],
            preview_token=configuration_preview["preview_token"],
        )

    assert service.current_state_digest() == changed_configuration_digest
    assert not service.recovery_directory.exists()


@pytest.mark.parametrize("ttl", (float("nan"), float("inf"), float("-inf")))
def test_preview_rejects_non_finite_ttl(tmp_path, monkeypatch, ttl) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )

    with pytest.raises(ValueError, match="finite"):
        FullDataBackupService(
            db_manager=install["db"],
            config_service=install["config"],
            application_version=APPLICATION_VERSION,
            preview_token_ttl_seconds=ttl,
        )


def test_preview_expiry_is_a_prewrite_conflict_without_recovery(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = FullDataBackupService(
        db_manager=install["db"],
        config_service=install["config"],
        application_version=APPLICATION_VERSION,
        preview_token_ttl_seconds=5,
    )
    clock = {"value": 100.0}
    monkeypatch.setattr(backup_module.time_module, "monotonic", lambda: clock["value"])
    preview = service.preview_restore(install["backup"])
    before = service.current_state_digest()
    clock["value"] = 105.001

    with pytest.raises(FullDataBackupConflictError, match="expired"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert service.current_state_digest() == before
    assert not service.recovery_directory.exists()


def test_consumed_preview_token_cannot_be_reused_or_create_another_recovery(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )
    service = install["service"]
    preview = service.preview_restore(install["backup"])
    service.restore_backup(
        install["backup"],
        preview_token=preview["preview_token"],
    )
    before = service.current_state_digest()
    recovery_paths = list(service.recovery_directory.glob("*.json"))

    with pytest.raises(FullDataBackupConflictError, match="fresh"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert service.current_state_digest() == before
    assert list(service.recovery_directory.glob("*.json")) == recovery_paths


def test_injected_restore_failure_rolls_back_database_and_compensates_config(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    before = service.export_backup()
    before_digest = service.current_state_digest()
    before_database_digest = _sqlite_logical_digest(install["db_path"])
    before_config_bytes = install["env_path"].read_bytes()
    reload_calls = []
    monkeypatch.setattr(
        install["config"],
        "_reload_runtime_singletons",
        lambda: reload_calls.append("reload"),
    )

    def interrupt_after_database_replace(session, _tables):
        assert list(service.recovery_directory.glob("*.json"))
        assert service.export_configuration_values() == {"STOCK_LIST": "600519,AAPL"}
        assert _derived_counts(session) == {
            "portfolio_positions": 0,
            "portfolio_position_lots": 0,
            "portfolio_daily_snapshots": 0,
        }
        raise RuntimeError("injected restore interruption")

    monkeypatch.setattr(service, "_verify_restored_tables", interrupt_after_database_replace)
    preview = service.preview_restore(install["backup"])

    with pytest.raises(FullDataBackupRestoreError, match="injected restore interruption"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert service.current_state_digest() == before_digest
    assert _sqlite_logical_digest(install["db_path"]) == before_database_digest
    assert service.export_configuration_values() == before["data"]["configuration"]["values"]
    assert install["env_path"].read_bytes() == before_config_bytes
    assert reload_calls == []
    env_text = before_config_bytes.decode("utf-8")
    assert "OPENAI_API_KEY=destination-secret-must-survive" in env_text
    with install["db"].get_session() as session:
        assert _derived_counts(session) == {
            "portfolio_positions": 1,
            "portfolio_position_lots": 1,
            "portfolio_daily_snapshots": 1,
        }
    recovery_paths = list(service.recovery_directory.glob("*.json"))
    assert len(recovery_paths) == 1
    recovery = json.loads(recovery_paths[0].read_text(encoding="utf-8"))
    service.validate_backup(recovery)
    assert recovery["data"] == before["data"]


def test_config_writer_after_apply_blocks_compensation_without_clobbering_writer(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    before_database_digest = _sqlite_logical_digest(install["db_path"])

    def write_concurrently_then_interrupt(_session, _tables):
        writer_manager = ConfigManager(env_path=install["env_path"])
        writer = SystemConfigService(manager=writer_manager)
        writer.update(
            config_version=writer_manager.get_config_version(),
            items=[{"key": "MAX_WORKERS", "value": "7"}],
            reload_now=False,
        )
        raise RuntimeError("injected failure after concurrent config edit")

    monkeypatch.setattr(service, "_verify_restored_tables", write_concurrently_then_interrupt)
    preview = service.preview_restore(install["backup"])

    with pytest.raises(FullDataBackupConflictError, match="not overwritten"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert _sqlite_logical_digest(install["db_path"]) == before_database_digest
    config_map = ConfigManager(env_path=install["env_path"]).read_config_map()
    assert config_map["STOCK_LIST"] == "000001"
    assert config_map["MAX_WORKERS"] == "7"
    assert config_map["OPENAI_API_KEY"] == "destination-secret-must-survive"


def test_same_managed_key_writer_wins_during_restore_compensation(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    before_database_digest = _sqlite_logical_digest(install["db_path"])

    def write_same_key_then_interrupt(_session, _tables):
        writer_manager = ConfigManager(env_path=install["env_path"])
        writer = SystemConfigService(manager=writer_manager)
        writer.update(
            config_version=writer_manager.get_config_version(),
            items=[{"key": "STOCK_LIST", "value": "300750"}],
            reload_now=False,
        )
        raise RuntimeError("injected failure after same-key config edit")

    monkeypatch.setattr(service, "_verify_restored_tables", write_same_key_then_interrupt)
    preview = service.preview_restore(install["backup"])

    with pytest.raises(FullDataBackupConflictError, match="not overwritten"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert _sqlite_logical_digest(install["db_path"]) == before_database_digest
    config_map = ConfigManager(env_path=install["env_path"]).read_config_map()
    assert config_map["STOCK_LIST"] == "300750"
    assert config_map["MAX_WORKERS"] == "2"
    assert config_map["OPENAI_API_KEY"] == "destination-secret-must-survive"
