"""Integration tests for fail-closed, recoverable full-data restore."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from api.v1.endpoints import full_data_backup
from src.config import Config
from src.core.config_manager import ConfigManager, ConfigManagerVersionConflict
from src.services import full_data_backup_service as backup_module
from src.services.full_data_backup_service import (
    FullDataBackupConflictError,
    FullDataBackupRestoreError,
    FullDataBackupService,
    FullDataBackupValidationError,
)
from src.services.full_data_restore_journal import FullDataRestoreJournal
from src.services.system_config_service import SystemConfigService
from src.storage import (
    AnalysisHistory,
    AgentProviderTurn,
    ConversationMessage,
    ConversationSummary,
    DatabaseManager,
    FullDataRestoreCommitMarker,
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


def _stored_period_report_content() -> str:
    return json.dumps(
        {
            "report_id": 303,
            "status": "ready",
            "period": "previous_week",
            "report_kind": "historical",
            "start_date": "2026-07-20",
            "end_date": "2026-07-24",
            "generated_at": "2026-08-01T11:00:00",
            "source_record_count": 2,
            "stock_summaries": [
                {
                    "stock_code": "600519",
                    "stock_name": "Moutai",
                    "asset_type": "stock",
                    "record_count": 1,
                    "latest_record_id": 101,
                    "latest_created_at": "2026-07-23T09:00:00",
                    "latest_trend": None,
                    "latest_summary": "fixed stock content summary",
                    "direction_counts": {
                        "bullish": 0, "neutral": 0, "bearish": 0, "unknown": 1,
                    },
                    "source_record_ids": [101],
                }
            ],
            "etf_summaries": [],
            "market_reviews": [
                {
                    "record_id": 202,
                    "region": None,
                    "created_at": "2026-07-24T10:00:00",
                    "summary": "fixed market content summary",
                    "trend_prediction": None,
                }
            ],
            "outlook": None,
            "matched_outlook": None,
            "disclaimer": None,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _restore_process_environment(snapshot: dict[str, str]) -> None:
    os.environ.clear()
    os.environ.update(snapshot)


@pytest.fixture(autouse=True)
def _reset_singletons():
    original_environment = dict(os.environ)
    cleanup_stack = ExitStack()
    cleanup_stack.callback(_restore_process_environment, original_environment)
    cleanup_stack.callback(Config.reset_instance)
    cleanup_stack.callback(DatabaseManager.reset_instance)
    try:
        yield
    finally:
        cleanup_stack.close()


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
                    content_json=_stored_period_report_content(),
                    source_record_ids_json="[101,202]",
                    status="ready",
                    generated_at=datetime(2026, 8, 1, 11, 0, 0),
                    updated_at=datetime(2026, 8, 1, 11, 0, 0),
                ),
                PortfolioAccount(
                    id=401,
                    owner_id="source-owner-is-backed-up",
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
                ConversationMessage(
                    id=405,
                    session_id="fixed-visible-session",
                    role="user",
                    content="fixed visible user content",
                    created_at=datetime(2026, 8, 1, 12, 4, 0),
                ),
                ConversationMessage(
                    id=406,
                    session_id="fixed-visible-session",
                    role="assistant",
                    content="fixed visible assistant content",
                    created_at=datetime(2026, 8, 1, 12, 5, 0),
                ),
                ConversationSummary(
                    id=407,
                    session_id="fixed-visible-session",
                    summary="fixed visible summary content",
                    covered_message_id=406,
                    source_message_count=2,
                    estimated_tokens=10,
                    created_at=datetime(2026, 8, 1, 12, 6, 0),
                    updated_at=datetime(2026, 8, 1, 12, 6, 0),
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
        "STOCK_LIST=600519,AAPL",
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
    assert data["tables"]["period_reports"][0]["content_json"] == _stored_period_report_content()
    assert data["tables"]["period_reports"][0]["source_record_ids_json"] == "[101,202]"
    assert [row["id"] for row in data["tables"]["portfolio_accounts"]] == [401]
    assert data["tables"]["portfolio_accounts"][0]["owner_id"] == "source-owner-is-backed-up"
    assert [row["id"] for row in data["tables"]["portfolio_cash_ledger"]] == [402]
    assert data["tables"]["portfolio_cash_ledger"][0]["note"] == "fixed cash event"
    assert [row["id"] for row in data["tables"]["portfolio_trades"]] == [403]
    assert data["tables"]["portfolio_trades"][0]["trade_uid"] == "trade-fixed-403"
    assert data["tables"]["portfolio_trades"][0]["note"] == "fixed trade event"
    assert [row["id"] for row in data["tables"]["portfolio_corporate_actions"]] == [404]
    assert data["tables"]["portfolio_corporate_actions"][0]["note"] == (
        "fixed corporate event"
    )
    assert [row["id"] for row in data["tables"]["conversation_messages"]] == [405, 406]
    assert data["tables"]["conversation_summaries"][0]["id"] == 407
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


def test_restore_roundtrips_storage_canonical_json_configuration(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )
    backup = install["backup"]
    backup["data"]["configuration"]["values"][
        "AGENT_EVENT_ALERT_RULES_JSON"
    ] = (
        '[{"stock_code":"600519","alert_type":"price_cross",'
        '"direction":"above","price":1800}]'
    )
    backup["manifest"]["categories"]["configuration"]["row_count"] += 1
    backup["integrity"]["value"] = install["service"].canonical_sha256(backup)
    preview = install["service"].preview_restore(backup)

    install["service"].restore_backup(
        backup,
        preview_token=preview["preview_token"],
    )

    assert ConfigManager(env_path=install["env_path"]).read_config_map()[
        "AGENT_EVENT_ALERT_RULES_JSON"
    ] == backup["data"]["configuration"]["values"]["AGENT_EVENT_ALERT_RULES_JSON"]


def test_recovery_artifact_durable_publish_failure_is_safe_through_api(
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
    before_configuration = install["env_path"].read_bytes()

    app = FastAPI()
    app.include_router(
        full_data_backup.router,
        prefix="/api/v1/system/full-data-backup",
    )
    app.dependency_overrides[full_data_backup.get_full_data_backup_service] = (
        lambda: service
    )
    client = TestClient(app, raise_server_exceptions=False)
    preview_response = client.post(
        "/api/v1/system/full-data-backup/preview",
        json=install["backup"],
    )
    assert preview_response.status_code == 200

    def reject_durable_publication(_staged_path, _destination) -> None:
        raise OSError("private recovery publication detail")

    monkeypatch.setattr(
        backup_module,
        "durable_replace",
        reject_durable_publication,
        raising=False,
    )
    response = client.post(
        "/api/v1/system/full-data-backup/restore",
        json={
            "backup": install["backup"],
            "preview_token": preview_response.json()["preview_token"],
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "error": "internal_error",
            "message": "Full-data backup operation failed",
        }
    }
    assert "private recovery publication detail" not in response.text
    assert _sqlite_logical_digest(install["db_path"]) == before_database_digest
    assert install["env_path"].read_bytes() == before_configuration
    assert not list(service.recovery_directory.glob("*.json"))


def test_restore_reports_truthful_success_when_post_commit_receipt_finalize_needs_cleanup(
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
    assert result["warnings"] == [
        "Configuration receipt cleanup required a safe post-commit retry."
    ]
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    _assert_fixed_source_state(service)


@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_post_commit_base_exception_preserves_committed_restore_and_propagates(
    tmp_path,
    monkeypatch,
    exception_type,
) -> None:
    monkeypatch.setenv("PP02_APPLICATION_VERSION", APPLICATION_VERSION)
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    baseline_receipts = len(SystemConfigService._restore_receipts)

    def interrupt_after_commit(phase: str) -> None:
        if phase == "after_db_commit":
            raise exception_type("injected post-commit interruption")

    service = FullDataBackupService(
        db_manager=install["db"],
        config_service=install["config"],
        application_version=APPLICATION_VERSION,
        crash_test_hook=interrupt_after_commit,
    )
    preview = service.preview_restore(install["backup"])

    with pytest.raises(exception_type, match="post-commit interruption"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    _assert_fixed_source_state(service)
    assert service.export_configuration_values() == {"STOCK_LIST": "600519,AAPL"}
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    journal_path = (
        service.recovery_directory / ".pp02-full-data-restore-transaction.json"
    )
    assert journal_path.is_file()
    with install["db"].get_session() as session:
        assert session.query(FullDataRestoreCommitMarker).count() == 1

    _, _, restarted_service = _open_install(
        monkeypatch,
        install["env_path"],
        install["db_path"],
    )
    _assert_fixed_source_state(restarted_service)
    assert restarted_service.export_configuration_values() == {
        "STOCK_LIST": "600519,AAPL"
    }
    assert not journal_path.exists()
    with restarted_service.db.get_session() as session:
        assert session.query(FullDataRestoreCommitMarker).count() == 0


@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_commit_result_exception_uses_durable_marker_before_compensation(
    tmp_path,
    monkeypatch,
    exception_type,
) -> None:
    monkeypatch.setenv("PP02_APPLICATION_VERSION", APPLICATION_VERSION)
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    preview = service.preview_restore(install["backup"])
    baseline_receipts = len(SystemConfigService._restore_receipts)
    original_get_session = install["db"].get_session
    restore_session = original_get_session()
    original_commit = restore_session.commit

    def commit_then_interrupt() -> None:
        original_commit()
        raise exception_type("injected uncertain commit result")

    monkeypatch.setattr(restore_session, "commit", commit_then_interrupt)
    monkeypatch.setattr(install["db"], "get_session", lambda: restore_session)

    with pytest.raises(exception_type, match="uncertain commit result"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    monkeypatch.setattr(install["db"], "get_session", original_get_session)
    _assert_fixed_source_state(service)
    assert service.export_configuration_values() == {"STOCK_LIST": "600519,AAPL"}
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    journal_path = (
        service.recovery_directory / ".pp02-full-data-restore-transaction.json"
    )
    assert journal_path.is_file()
    with original_get_session() as session:
        assert session.query(FullDataRestoreCommitMarker).count() == 1


def test_uncertain_commit_marker_query_failure_preserves_incoming_and_evidence(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("PP02_APPLICATION_VERSION", APPLICATION_VERSION)
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    preview = service.preview_restore(install["backup"])
    baseline_receipts = len(SystemConfigService._restore_receipts)
    original_get_session = install["db"].get_session
    restore_session = original_get_session()
    original_commit = restore_session.commit

    def commit_then_interrupt() -> None:
        original_commit()
        raise KeyboardInterrupt("injected uncertain commit with unreadable marker")

    def fail_marker_query(_self, _tx_id: str) -> bool:
        raise RuntimeError("injected independent marker query failure")

    monkeypatch.setattr(restore_session, "commit", commit_then_interrupt)
    monkeypatch.setattr(install["db"], "get_session", lambda: restore_session)
    monkeypatch.setattr(
        FullDataRestoreJournal,
        "is_committed",
        fail_marker_query,
        raising=False,
    )

    with pytest.raises(KeyboardInterrupt, match="unreadable marker"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    monkeypatch.setattr(install["db"], "get_session", original_get_session)
    _assert_fixed_source_state(service)
    assert service.export_configuration_values() == {"STOCK_LIST": "600519,AAPL"}
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    journal_path = (
        service.recovery_directory / ".pp02-full-data-restore-transaction.json"
    )
    assert journal_path.is_file()
    with original_get_session() as session:
        assert session.query(FullDataRestoreCommitMarker).count() == 1


@pytest.mark.parametrize(
    ("interruption_point", "exception_type"),
    (
        ("_verify_configuration", KeyboardInterrupt),
        ("_replace_tables", SystemExit),
        ("_verify_restored_tables", KeyboardInterrupt),
    ),
)
def test_process_interruption_after_config_apply_rolls_back_and_propagates(
    tmp_path,
    monkeypatch,
    interruption_point,
    exception_type,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    before_database = _sqlite_logical_digest(install["db_path"])
    before_config = install["env_path"].read_bytes()
    before_state = service.current_state_digest()
    baseline_receipts = len(SystemConfigService._restore_receipts)
    original = getattr(service, interruption_point)
    calls = 0

    def interrupt_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise exception_type(f"injected {interruption_point} interruption")
        return original(*args, **kwargs)

    monkeypatch.setattr(service, interruption_point, interrupt_once)
    preview = service.preview_restore(install["backup"])

    with pytest.raises(exception_type, match=interruption_point):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert _sqlite_logical_digest(install["db_path"]) == before_database
    assert install["env_path"].read_bytes() == before_config
    assert service.current_state_digest() == before_state
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    assert not (
        service.recovery_directory / ".pp02-full-data-restore-transaction.json"
    ).exists()


def test_process_interruption_compensation_preserves_concurrent_config_writer(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    before_database = _sqlite_logical_digest(install["db_path"])
    baseline_receipts = len(SystemConfigService._restore_receipts)

    def write_concurrently_then_interrupt(_session, _tables):
        writer_manager = ConfigManager(env_path=install["env_path"])
        SystemConfigService(manager=writer_manager).update(
            config_version=writer_manager.get_config_version(),
            items=[{"key": "MAX_WORKERS", "value": "7"}],
            reload_now=False,
        )
        raise KeyboardInterrupt("injected interruption after concurrent config edit")

    monkeypatch.setattr(service, "_verify_restored_tables", write_concurrently_then_interrupt)
    preview = service.preview_restore(install["backup"])

    with pytest.raises(KeyboardInterrupt, match="concurrent config edit"):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert _sqlite_logical_digest(install["db_path"]) == before_database
    config_map = ConfigManager(env_path=install["env_path"]).read_config_map()
    assert config_map["STOCK_LIST"] == "000001"
    assert config_map["MAX_WORKERS"] == "7"
    assert config_map["OPENAI_API_KEY"] == "destination-secret-must-survive"
    assert len(SystemConfigService._restore_receipts) == baseline_receipts


def test_compensation_recheck_conflict_preserves_second_writer_without_receipt_leak(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=True,
    )
    service = install["service"]
    baseline_receipts = len(SystemConfigService._restore_receipts)

    def fail_after_config_apply(_session, _tables):
        raise RuntimeError("force compensation")

    def second_writer_then_recheck_conflict(**_kwargs):
        writer = ConfigManager(env_path=install["env_path"])
        SystemConfigService(manager=writer).update(
            config_version=writer.get_config_version(),
            items=[{"key": "MAX_WORKERS", "value": "9"}],
            reload_now=False,
        )
        raise ConfigManagerVersionConflict(writer.get_config_version())

    monkeypatch.setattr(service, "_replace_tables", fail_after_config_apply)
    monkeypatch.setattr(
        install["config"]._manager,
        "compensate_managed_assignments_atomically",
        second_writer_then_recheck_conflict,
    )
    preview = service.preview_restore(install["backup"])

    with pytest.raises(FullDataBackupConflictError):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    current = ConfigManager(env_path=install["env_path"]).read_config_map()
    assert current["MAX_WORKERS"] == "9"
    assert len(SystemConfigService._restore_receipts) == baseline_receipts


def test_post_publish_keyboard_interrupt_rolls_back_restore_and_config(
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
    before_database = _sqlite_logical_digest(install["db_path"])
    before_state = service.current_state_digest()
    before_config = install["env_path"].read_bytes()
    baseline_receipts = len(SystemConfigService._restore_receipts)
    publish_count = 0

    def publish_then_interrupt(staged_path):
        nonlocal publish_count
        original_publish(staged_path)
        publish_count += 1
        raise KeyboardInterrupt("injected restore interruption after publication")

    monkeypatch.setattr(manager, "_publish_staged_bytes", publish_then_interrupt)
    preview = service.preview_restore(install["backup"])

    with pytest.raises(
        KeyboardInterrupt,
        match="injected restore interruption after publication",
    ):
        service.restore_backup(
            install["backup"],
            preview_token=preview["preview_token"],
        )

    assert publish_count >= 2
    assert install["env_path"].read_bytes() == before_config
    assert _sqlite_logical_digest(install["db_path"]) == before_database
    assert service.current_state_digest() == before_state
    assert len(SystemConfigService._restore_receipts) == baseline_receipts
    recovery_paths = list(service.recovery_directory.glob("*.json"))
    assert len(recovery_paths) == 1
    assert not (
        service.recovery_directory / ".pp02-full-data-restore-transaction.json"
    ).exists()
    service.validate_backup(json.loads(recovery_paths[0].read_text(encoding="utf-8")))


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


def test_restore_purges_excluded_provider_turns_before_conversation_replacement(
    tmp_path,
    monkeypatch,
) -> None:
    install = _prepare_source_and_destination(
        tmp_path,
        monkeypatch,
        seed_destination=False,
    )
    with install["db"].get_session() as session:
        session.add(
            AgentProviderTurn(
                id=999,
                session_id="fixed-visible-session",
                run_id="target-collision",
                provider="synthetic-provider",
                model="synthetic-model",
                anchor_user_message_id=405,
                anchor_assistant_message_id=406,
                messages_json='[{"provider_trace":"target-only"}]',
                contains_reasoning=True,
                contains_tool_calls=False,
                contains_thinking_blocks=False,
                must_roundtrip=True,
                estimated_tokens=1,
                created_at=datetime(2026, 8, 2, 12, 0, 0),
            )
        )
        session.commit()
    preview = install["service"].preview_restore(install["backup"])

    install["service"].restore_backup(
        install["backup"],
        preview_token=preview["preview_token"],
    )

    with install["db"].get_session() as session:
        assert session.query(AgentProviderTurn).count() == 0
        assert session.get(ConversationMessage, 405).content == "fixed visible user content"


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
    assert not list(service.recovery_directory.glob("*.json"))

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
    assert not list(service.recovery_directory.glob("*.json"))

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
    assert not list(service.recovery_directory.glob("*.json"))


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
