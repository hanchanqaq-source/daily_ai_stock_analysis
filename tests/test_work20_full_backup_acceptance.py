"""End-to-end Work20 journey from a fixed manual v3.29.2 install."""

from __future__ import annotations

import copy
import json
import hashlib
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.endpoints import full_data_backup, period_report
from src.config import Config
from src.services.full_data_backup_service import FullDataBackupService
from src.services.period_report_service import PeriodReportService
from src.services.system_config_service import SystemConfigService
from src.storage import (
    AgentProviderTurn,
    AnalysisHistory,
    ConversationMessage,
    ConversationSummary,
    DatabaseManager,
    PeriodReportRecord,
    PortfolioAccount,
    PortfolioCashLedger,
    PortfolioCorporateAction,
    PortfolioTrade,
)


def _create_manual_v3292_database(path: Path) -> None:
    """Create only the fixed v3.29.2 user-data tables, without Work20 tables."""
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, query_id VARCHAR(64),
                code VARCHAR(10) NOT NULL, name VARCHAR(50), report_type VARCHAR(16),
                sentiment_score INTEGER, operation_advice VARCHAR(20),
                trend_prediction VARCHAR(50), analysis_summary TEXT, raw_result TEXT,
                news_content TEXT, context_snapshot TEXT, ideal_buy FLOAT,
                secondary_buy FLOAT, stop_loss FLOAT, take_profit FLOAT,
                created_at DATETIME
            );
            CREATE TABLE portfolio_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id VARCHAR(64),
                name VARCHAR(64) NOT NULL, broker VARCHAR(64), market VARCHAR(8) NOT NULL,
                base_currency VARCHAR(8) NOT NULL, is_active BOOLEAN NOT NULL,
                created_at DATETIME, updated_at DATETIME
            );
            CREATE TABLE portfolio_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
                trade_uid VARCHAR(128), symbol VARCHAR(16) NOT NULL, market VARCHAR(8) NOT NULL,
                currency VARCHAR(8) NOT NULL, trade_date DATE NOT NULL, side VARCHAR(8) NOT NULL,
                quantity FLOAT NOT NULL, price FLOAT NOT NULL, fee FLOAT, tax FLOAT,
                note VARCHAR(255), dedup_hash VARCHAR(64), created_at DATETIME,
                UNIQUE(account_id, trade_uid), UNIQUE(account_id, dedup_hash),
                FOREIGN KEY(account_id) REFERENCES portfolio_accounts(id)
            );
            CREATE TABLE portfolio_cash_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
                event_date DATE NOT NULL, direction VARCHAR(8) NOT NULL, amount FLOAT NOT NULL,
                currency VARCHAR(8) NOT NULL, note VARCHAR(255), created_at DATETIME,
                FOREIGN KEY(account_id) REFERENCES portfolio_accounts(id)
            );
            CREATE TABLE portfolio_corporate_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL,
                symbol VARCHAR(16) NOT NULL, market VARCHAR(8) NOT NULL,
                currency VARCHAR(8) NOT NULL, effective_date DATE NOT NULL,
                action_type VARCHAR(24) NOT NULL, cash_dividend_per_share FLOAT,
                split_ratio FLOAT, note VARCHAR(255), created_at DATETIME,
                FOREIGN KEY(account_id) REFERENCES portfolio_accounts(id)
            );
            CREATE TABLE conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL, content TEXT NOT NULL, created_at DATETIME
            );
            CREATE TABLE conversation_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id VARCHAR(100) NOT NULL UNIQUE,
                summary TEXT NOT NULL, covered_message_id INTEGER NOT NULL,
                source_message_count INTEGER NOT NULL, estimated_tokens INTEGER NOT NULL,
                created_at DATETIME, updated_at DATETIME
            );
            """
        )
        connection.executemany(
            """INSERT INTO analysis_history
            (id, query_id, code, name, report_type, sentiment_score, operation_advice,
             trend_prediction, analysis_summary, raw_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                (
                    4101, "work20-fixed-stock-query", "600519", "Synthetic Stock",
                    "detailed", 70, "持有", "看多", "fixed stock digest content",
                    '{"result":"fixed-stock"}', "2026-07-30 09:00:00",
                ),
                (
                    4201, "work20-fixed-market-query", "MARKET", "Synthetic Market",
                    "market_review", None, None, "中性", "fixed market digest content",
                    '{}', "2026-07-30 10:00:00",
                ),
            ),
        )
        connection.execute(
            """INSERT INTO portfolio_accounts VALUES
            (4301, 'fixed-owner-4301', 'Fixed Account', 'Synthetic Broker', 'cn',
             'CNY', 1, '2026-07-30 11:00:00', '2026-07-30 11:00:00')"""
        )
        connection.execute(
            """INSERT INTO portfolio_trades VALUES
            (4302, 4301, 'fixed-trade-4302', '600519', 'cn', 'CNY', '2026-07-30',
             'buy', 1, 100, 1, 0, 'fixed trade', 'fixed-dedup-4302',
             '2026-07-30 11:01:00')"""
        )
        connection.execute(
            """INSERT INTO portfolio_cash_ledger VALUES
            (4303, 4301, '2026-07-30', 'in', 1000, 'CNY', 'fixed cash',
             '2026-07-30 11:02:00')"""
        )
        connection.execute(
            """INSERT INTO portfolio_corporate_actions VALUES
            (4304, 4301, '600519', 'cn', 'CNY', '2026-07-31', 'cash_dividend',
             1, NULL, 'fixed action', '2026-07-30 11:03:00')"""
        )
        connection.executemany(
            "INSERT INTO conversation_messages VALUES (?, ?, ?, ?, ?)",
            (
                (4401, "fixed-session", "user", "fixed visible question", "2026-07-30 12:00:00"),
                (4402, "fixed-session", "assistant", "fixed visible answer", "2026-07-30 12:01:00"),
                (4404, "fixed-session", "system", "fixed persisted system context", "2026-07-30 12:01:30"),
            ),
        )
        connection.execute(
            """INSERT INTO conversation_summaries VALUES
            (4403, 'fixed-session', 'fixed visible summary', 4402, 2, 10,
             '2026-07-30 12:02:00', '2026-07-30 12:02:00')"""
        )


def _write_env(path: Path, db_path: Path, stock_list: str) -> None:
    path.write_text(
        "\n".join(
            (
                f"STOCK_LIST={stock_list}",
                "HTTP_PROXY=http://127.0.0.1:7890",
                "OPENAI_API_KEY=explicit-fake-local-only-secret",
                f"DATABASE_PATH={db_path}",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _open_install(env_path: Path, db_path: Path):
    DatabaseManager.reset_instance()
    os.environ["ENV_FILE"] = str(env_path)
    os.environ["DATABASE_PATH"] = str(db_path)
    Config.reset_instance()
    db = DatabaseManager(db_url=f"sqlite:///{db_path}")
    config = SystemConfigService()
    service = FullDataBackupService(
        db_manager=db,
        config_service=config,
        application_version="3.29.2",
    )
    return db, service


def _api_client(db: DatabaseManager, backup_service: FullDataBackupService) -> TestClient:
    app = FastAPI()
    app.include_router(full_data_backup.router, prefix="/api/v1/system/full-data-backup")
    app.include_router(period_report.router, prefix="/api/v1/period-report")
    app.dependency_overrides[full_data_backup.get_full_data_backup_service] = (
        lambda: backup_service
    )
    app.dependency_overrides[period_report.get_database_manager] = lambda: db
    return TestClient(app)


def test_v3292_export_clean_restore_restart_through_formal_apis(tmp_path) -> None:
    original_environment = dict(os.environ)
    source_dir = tmp_path / "installed-v3292"
    destination_dir = tmp_path / "clean-current-install"
    external_backup_dir = tmp_path / "external-backups"
    source_dir.mkdir()
    destination_dir.mkdir()
    external_backup_dir.mkdir()
    source_db_path = source_dir / "manual-v3292.db"
    source_env = source_dir / "manual-v3292.env"
    destination_db_path = destination_dir / "clean-current.db"
    destination_env = destination_dir / "clean-current.env"
    try:
        _create_manual_v3292_database(source_db_path)
        _write_env(source_env, source_db_path, "600519,000001")
        source_db, source_backup_service = _open_install(source_env, source_db_path)
        with source_db.get_session() as session:
            session.add(
                AgentProviderTurn(
                    id=4501,
                    session_id="fixed-session",
                    run_id="fixed-provider-run",
                    provider="synthetic-provider",
                    model="synthetic-model",
                    anchor_user_message_id=4401,
                    anchor_assistant_message_id=4402,
                    messages_json='[{"provider_trace":"must-not-export"}]',
                    contains_reasoning=True,
                    contains_tool_calls=False,
                    contains_thinking_blocks=False,
                    must_roundtrip=True,
                    estimated_tokens=20,
                    created_at=datetime(2026, 7, 30, 12, 3, 0),
                )
            )
            session.commit()
        report = PeriodReportService(
            db_manager=source_db,
            now_provider=lambda: datetime(2026, 8, 4, 12, 0, 0),
        ).generate("next_week", as_of=date(2026, 8, 4))
        report_id = report["report_id"]
        assert report["report_kind"] == "outlook"
        assert report["outlook"]["snapshot_id"] == 4202
        assert report["outlook"]["snapshot_created_at"] == report["generated_at"]
        with source_db.get_session() as session:
            stored_report = session.get(PeriodReportRecord, report_id)
            assert json.loads(stored_report.content_json) == report
        source_client = _api_client(source_db, source_backup_service)
        source_backup_service.export_backup()
        exported_response = source_client.get("/api/v1/system/full-data-backup/export")
        assert exported_response.status_code == 200
        backup_path = external_backup_dir / "pp02-work20-fixed-full-data-backup.json"
        backup_path.write_bytes(exported_response.content)
        assert backup_path.is_file()
        assert backup_path.stat().st_size > 0
        exported_file_sha256 = hashlib.sha256(backup_path.read_bytes()).hexdigest()
        assert len(exported_file_sha256) == 64
        backup = json.loads(backup_path.read_text(encoding="utf-8"))
        assert backup["integrity"]["value"] == source_backup_service.canonical_sha256(backup)
        assert "explicit-fake-local-only-secret" not in exported_response.text
        assert "must-not-export" not in exported_response.text
        assert "agent_provider_turns" not in backup["data"]["tables"]

        malformed_period_backup = copy.deepcopy(backup)
        malformed_period_row = malformed_period_backup["data"]["tables"][
            "period_reports"
        ][0]
        malformed_period_content = json.loads(malformed_period_row["content_json"])
        malformed_period_content["generated_at"] = "not-a-timestamp"
        malformed_period_row["content_json"] = json.dumps(
            malformed_period_content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        malformed_period_backup["integrity"]["value"] = (
            source_backup_service.canonical_sha256(malformed_period_backup)
        )
        malformed_preview = source_client.post(
            "/api/v1/system/full-data-backup/preview",
            json=malformed_period_backup,
        )
        assert malformed_preview.status_code == 400

        source_db._engine.dispose()
        source_db_path.unlink()
        source_env.unlink()
        assert backup_path.is_file()

        _write_env(destination_env, destination_db_path, "300750")
        destination_db, destination_backup_service = _open_install(
            destination_env,
            destination_db_path,
        )
        with destination_db.get_session() as session:
            session.add(
                AgentProviderTurn(
                    id=9501,
                    session_id="fixed-session",
                    run_id="target-collision-provider-run",
                    provider="synthetic-target-provider",
                    model="synthetic-target-model",
                    anchor_user_message_id=4401,
                    anchor_assistant_message_id=4402,
                    messages_json='[{"provider_trace":"target-collision-must-clear"}]',
                    contains_reasoning=True,
                    contains_tool_calls=False,
                    contains_thinking_blocks=False,
                    must_roundtrip=True,
                    estimated_tokens=10,
                    created_at=datetime(2026, 8, 4, 12, 0, 0),
                )
            )
            session.commit()
            assert session.query(AgentProviderTurn).count() == 1
        destination_client = _api_client(destination_db, destination_backup_service)
        preview = destination_client.post(
            "/api/v1/system/full-data-backup/preview",
            json=backup,
        )
        assert preview.status_code == 200, preview.text
        restored = destination_client.post(
            "/api/v1/system/full-data-backup/restore",
            json={"backup": backup, "preview_token": preview.json()["preview_token"]},
        )
        assert restored.status_code == 200, restored.text
        assert restored.json()["success"] is True

        restarted_db, restarted_backup_service = _open_install(
            destination_env,
            destination_db_path,
        )
        restarted_client = _api_client(restarted_db, restarted_backup_service)
        formal_report = restarted_client.get(f"/api/v1/period-report/{report_id}")
        assert formal_report.status_code == 200, formal_report.text
        assert formal_report.json() == report
        with restarted_db.get_session() as session:
            histories = session.query(AnalysisHistory).order_by(AnalysisHistory.id).all()
            assert [(row.id, row.query_id, row.analysis_summary) for row in histories] == [
                (4101, "work20-fixed-stock-query", "fixed stock digest content"),
                (4201, "work20-fixed-market-query", "fixed market digest content"),
                (
                    4202,
                    "period-outlook-2026-08-10-2026-08-16",
                    "下周展望 2026-08-10 至 2026-08-16",
                ),
            ]
            assert session.get(PortfolioAccount, 4301).owner_id == "fixed-owner-4301"
            assert session.get(PortfolioTrade, 4302).note == "fixed trade"
            assert session.get(PortfolioCashLedger, 4303).note == "fixed cash"
            assert session.get(PortfolioCorporateAction, 4304).note == "fixed action"
            assert session.get(ConversationMessage, 4401).content == "fixed visible question"
            assert session.get(ConversationMessage, 4402).content == "fixed visible answer"
            assert session.get(ConversationMessage, 4404).content == "fixed persisted system context"
            assert session.get(ConversationSummary, 4403).summary == "fixed visible summary"
            assert session.query(AgentProviderTurn).count() == 0
            assert session.get(PeriodReportRecord, report_id).id == report_id
        assert restarted_backup_service.export_configuration_values() == {
            "HTTP_PROXY": "http://127.0.0.1:7890",
            "STOCK_LIST": "600519,000001",
        }
    finally:
        DatabaseManager.reset_instance()
        Config.reset_instance()
        os.environ.clear()
        os.environ.update(original_environment)
