"""Contract tests for the PP02 complete non-secret data backup document."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import tempfile
import threading
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import MetaData, Table

from src.config import Config
from src.core.config_manager import ConfigManager
from src.services.system_config_service import SystemConfigService
from src.storage import (
    CURRENT_SCHEMA_VERSION,
    AlertCooldownRecord,
    AlertNotificationRecord,
    AlertRuleRecord,
    AlertTriggerRecord,
    AnalysisHistory,
    BacktestResult,
    BacktestSummary,
    ConversationMessage,
    ConversationSummary,
    DatabaseManager,
    DecisionSignalFeedbackRecord,
    DecisionSignalOutcomeRecord,
    DecisionSignalRecord,
    FundamentalSnapshot,
    PeriodReportRecord,
    PortfolioAccount,
    PortfolioCashLedger,
    PortfolioCorporateAction,
    PortfolioTrade,
    SkillOpinionSampleRecord,
    StockDaily,
)

try:
    from src.services.full_data_backup_service import (
        FullDataBackupConflictError,
        FullDataBackupService,
        FullDataBackupValidationError,
    )
except ModuleNotFoundError:
    FullDataBackupConflictError = ValueError  # type: ignore[assignment,misc]
    FullDataBackupService = None  # type: ignore[assignment]
    FullDataBackupValidationError = ValueError  # type: ignore[assignment,misc]


def _canonical_sha256(document: dict) -> str:
    """Hand-derived digest: the integrity value itself is the only omission."""
    envelope = copy.deepcopy(document)
    del envelope["integrity"]["value"]
    raw = json.dumps(
        envelope,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _restore_process_environment(snapshot: dict[str, str]) -> None:
    os.environ.clear()
    os.environ.update(snapshot)


def test_period_report_enum_contract_is_static_at_import_boundary() -> None:
    """Backup import must not depend on Pydantic's runtime field metadata."""
    from src.services import full_data_backup_service as backup

    assert backup.PERIOD_REPORT_STATUSES == frozenset(
        {"ready", "insufficient_data"}
    )
    assert backup.PERIOD_REPORT_KINDS == frozenset({"historical", "outlook"})
    assert (
        backup.ENUM_COLUMNS["period_reports"]["status"]
        is backup.PERIOD_REPORT_STATUSES
    )
    assert (
        backup.ENUM_COLUMNS["period_reports"]["report_kind"]
        is backup.PERIOD_REPORT_KINDS
    )


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
                    "latest_summary": "stock history",
                    "direction_counts": {
                        "bullish": 0,
                        "neutral": 0,
                        "bearish": 0,
                        "unknown": 1,
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
                    "summary": "market history",
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


def test_period_report_validation_rebuilds_schema_after_lazy_import() -> None:
    """A prior API import cycle must not leave backup validation incomplete."""
    from api.v1.schemas.period_report import PeriodReportResponse
    from src.services import full_data_backup_service as backup

    row = {
        "id": 303,
        "status": "ready",
        "period": "previous_week",
        "report_kind": "historical",
        "start_date": "2026-07-20",
        "end_date": "2026-07-24",
        "generated_at": "2026-08-01T11:00:00",
        "source_record_ids_json": "[101, 202]",
        "content_json": _stored_period_report_content(),
    }

    with patch.object(
        PeriodReportResponse,
        "model_rebuild",
        wraps=PeriodReportResponse.model_rebuild,
    ) as rebuild:
        backup.FullDataBackupService._validate_period_report_content(row)

    rebuild.assert_called_once_with(force=True)


def _valid_outlook_period_content() -> dict:
    return {
        "report_id": 303,
        "status": "ready",
        "period": "next_week",
        "report_kind": "outlook",
        "start_date": "2026-08-03",
        "end_date": "2026-08-09",
        "generated_at": "2026-08-02T12:00:00Z",
        "source_record_count": 2,
        "stock_summaries": [],
        "etf_summaries": [],
        "market_reviews": [],
        "outlook": {
            "snapshot_version": 1,
            "snapshot_id": 999,
            "snapshot_created_at": None,
            "status": "ready",
            "message": None,
            "target_period": {
                "start_date": "2026-08-03",
                "end_date": "2026-08-09",
            },
            "generated_at": "2026-08-02T12:00:00Z",
            "overall_tendency": "看多",
            "stocks": [
                {
                    "stock_code": "600519",
                    "stock_name": "Moutai",
                    "asset_type": "stock",
                    "tendency": "看多",
                    "confidence": "中",
                    "historical_signals": ["fixed formal signal"],
                    "risks": ["fixed synthetic risk"],
                    "invalidation_conditions": ["fixed invalidation"],
                    "data_as_of": "2026-08-01T09:00:00Z",
                    "source_record_count": 1,
                    "source_record_ids": [101],
                }
            ],
            "etfs": [],
            "market_signals": [
                {
                    "record_id": 202,
                    "region": "cn",
                    "created_at": "2026-08-01T10:00:00Z",
                    "summary": "fixed market signal",
                }
            ],
            "data_as_of": "2026-08-01T10:00:00Z",
            "source_record_count": 2,
            "source_record_ids": [101, 202],
            "disclaimer": "fixed synthetic disclaimer",
        },
        "matched_outlook": None,
        "disclaimer": "fixed synthetic disclaimer",
    }


class TestFullDataBackupService:
    def setup_method(self) -> None:
        self.original_environment = dict(os.environ)
        self._cleanup_stack = ExitStack()
        self._cleanup_stack.callback(
            _restore_process_environment,
            self.original_environment,
        )
        try:
            self.temp_dir = tempfile.TemporaryDirectory()
            self._cleanup_stack.callback(self.temp_dir.cleanup)
            self._cleanup_stack.callback(Config.reset_instance)
            self._cleanup_stack.callback(DatabaseManager.reset_instance)
            directory = Path(self.temp_dir.name)
            self.env_path = directory / ".env"
            self.db_path = directory / "full_data_backup.db"
            self.env_path.write_text(
                "\n".join(
                    (
                        "STOCK_LIST=600519",
                        "OPENAI_API_KEY=credential-marker",
                        "API_TOKEN=token-marker",
                        "SESSION_COOKIE=cookie-marker",
                        "VAULT_CIPHERTEXT=ciphertext-marker",
                        "DINGTALK_APP_KEY=dingtalk-registry-marker",
                        "PUSHOVER_USER_KEY=pushover-registry-marker",
                        "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/registry/marker/value",
                        "LOG_DIR=/private/runtime/logs",
                        "REPORT_TEMPLATES_DIR=/private/runtime/templates",
                        "AGENT_SKILL_DIR=/private/runtime/skills",
                        "LITELLM_CONFIG=/private/runtime/litellm.yaml",
                        f"DATABASE_PATH={self.db_path}",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            os.environ["ENV_FILE"] = str(self.env_path)
            os.environ["DATABASE_PATH"] = str(self.db_path)
            Config.reset_instance()
            DatabaseManager.reset_instance()
            self.db = DatabaseManager.get_instance()
            self._seed_rows()
        except BaseException as setup_error:
            try:
                self._cleanup_stack.close()
            except BaseException as cleanup_error:
                add_note = getattr(setup_error, "add_note", None)
                if callable(add_note):
                    add_note(f"Cleanup after setup failure also failed: {cleanup_error!r}")
            raise

    def teardown_method(self) -> None:
        self._cleanup_stack.close()

    def _service(self):
        assert FullDataBackupService is not None, (
            "Work20 requires src.services.full_data_backup_service.FullDataBackupService"
        )
        return FullDataBackupService(
            db_manager=self.db,
            config_service=SystemConfigService(),
            application_version="test-app-7.4.1",
        )

    def _seed_rows(self) -> None:
        with self.db.get_session() as session:
            session.add_all(
                (
                    AnalysisHistory(
                        id=101,
                        query_id="analysis-fixed-101",
                        code="600519",
                        name="Moutai",
                        report_type="stock",
                        analysis_summary="stock history",
                        raw_result='{"result":"ok"}',
                        context_snapshot='{"context":"ok"}',
                        created_at=datetime(2026, 8, 1, 9, 0, 0),
                    ),
                    AnalysisHistory(
                        id=202,
                        query_id="market-fixed-202",
                        code="MARKET",
                        name="Market review",
                        report_type="market",
                        analysis_summary="market history",
                        created_at=datetime(2026, 8, 1, 10, 0, 0),
                    ),
                    FundamentalSnapshot(
                        id=203,
                        query_id="analysis-fixed-101",
                        code="600519",
                        payload='{"revenue":123456}',
                        source_chain='["provider-a"]',
                        coverage='{"financials":true}',
                        created_at=datetime(2026, 8, 1, 10, 1, 0),
                    ),
                    StockDaily(
                        id=204,
                        code="600519",
                        date=date(2026, 8, 1),
                        close=1500.0,
                        data_source="rebuildable-fixture",
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
                        owner_id="owner-private-marker",
                        name="Synthetic account",
                        market="cn",
                        base_currency="CNY",
                        is_active=True,
                        created_at=datetime(2026, 8, 1, 12, 0, 0),
                        updated_at=datetime(2026, 8, 1, 12, 0, 0),
                    ),
                    ConversationMessage(
                        id=901,
                        session_id="work20-visible-session",
                        role="user",
                        content="fixed visible user question",
                        created_at=datetime(2026, 8, 1, 16, 1, 0),
                    ),
                    ConversationMessage(
                        id=902,
                        session_id="work20-visible-session",
                        role="assistant",
                        content="fixed visible assistant answer",
                        created_at=datetime(2026, 8, 1, 16, 2, 0),
                    ),
                    ConversationSummary(
                        id=903,
                        session_id="work20-visible-session",
                        summary="fixed visible conversation summary",
                        covered_message_id=902,
                        source_message_count=2,
                        estimated_tokens=12,
                        created_at=datetime(2026, 8, 1, 16, 3, 0),
                        updated_at=datetime(2026, 8, 1, 16, 3, 0),
                    ),
                    ConversationMessage(
                        id=904,
                        session_id="work20-visible-session",
                        role="system",
                        content="fixed persisted system context",
                        created_at=datetime(2026, 8, 1, 16, 4, 0),
                    ),
                    PortfolioCashLedger(
                        id=402,
                        account_id=401,
                        event_date=date(2026, 8, 1),
                        direction="in",
                        amount=1000.0,
                        currency="CNY",
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
                        created_at=datetime(2026, 8, 1, 12, 3, 0),
                    ),
                    BacktestResult(
                        id=501,
                        analysis_history_id=101,
                        code="600519",
                        eval_window_days=10,
                        engine_version="v1",
                        eval_status="completed",
                        evaluated_at=datetime(2026, 8, 1, 13, 0, 0),
                    ),
                    BacktestSummary(
                        id=502,
                        scope="overall",
                        code=None,
                        eval_window_days=10,
                        engine_version="v1",
                        computed_at=datetime(2026, 8, 1, 13, 1, 0),
                        advice_breakdown_json="{}",
                        diagnostics_json="{}",
                    ),
                    AlertRuleRecord(
                        id=601,
                        name="Synthetic alert",
                        target="600519",
                        alert_type="price_cross",
                        parameters="{}",
                        cooldown_policy="{}",
                        notification_policy="{}",
                        created_at=datetime(2026, 8, 1, 14, 0, 0),
                        updated_at=datetime(2026, 8, 1, 14, 0, 0),
                    ),
                    AlertTriggerRecord(
                        id=602,
                        rule_id=601,
                        target="600519",
                        diagnostics='{"status":"ok"}',
                        triggered_at=datetime(2026, 8, 1, 14, 1, 0),
                    ),
                    AlertNotificationRecord(
                        id=603,
                        trigger_id=602,
                        channel="test",
                        attempt=1,
                        success=True,
                        retryable=False,
                        latency_ms=12,
                        diagnostics='{"status":"ok"}',
                        created_at=datetime(2026, 8, 1, 14, 2, 0),
                    ),
                    AlertCooldownRecord(
                        id=604,
                        rule_id=601,
                        rule_key="rule:601",
                        target="600519",
                        severity="warning",
                        last_triggered_at=datetime(2026, 8, 1, 14, 1, 0),
                        cooldown_until=datetime(2026, 8, 1, 14, 31, 0),
                        state="active",
                        updated_at=datetime(2026, 8, 1, 14, 2, 0),
                    ),
                    DecisionSignalRecord(
                        id=701,
                        stock_code="600519",
                        market="cn",
                        source_type="analysis",
                        trigger_source="test",
                        action="hold",
                        evidence_json="[]",
                        data_quality_summary_json="{}",
                        metadata_json="{}",
                        created_at=datetime(2026, 8, 1, 15, 0, 0),
                        updated_at=datetime(2026, 8, 1, 15, 0, 0),
                    ),
                    DecisionSignalOutcomeRecord(
                        id=702,
                        signal_id=701,
                        horizon="5d",
                        engine_version="decision-signal-v1",
                        created_at=datetime(2026, 8, 1, 15, 1, 0),
                        updated_at=datetime(2026, 8, 1, 15, 1, 0),
                    ),
                    DecisionSignalFeedbackRecord(
                        id=703,
                        signal_id=701,
                        feedback_value="useful",
                        created_at=datetime(2026, 8, 1, 15, 2, 0),
                        updated_at=datetime(2026, 8, 1, 15, 2, 0),
                    ),
                    SkillOpinionSampleRecord(
                        id=801,
                        analysis_history_id=101,
                        stock_code="600519",
                        skill_id="test-skill",
                        signal="buy",
                        confidence=0.8,
                        sample_schema_version="skill-opinion-sample-v1",
                        created_at=datetime(2026, 8, 1, 16, 0, 0),
                    ),
                )
            )
            session.commit()

    def test_exports_complete_allow_list_with_canonical_integrity_and_no_secrets(self) -> None:
        backup = self._service().export_backup()

        assert backup["format"] == "pp02.full-data.backup"
        assert backup["format_version"] == 1
        assert backup["metadata"] == {
            "application_version": "test-app-7.4.1",
            "created_at": backup["metadata"]["created_at"],
            "database_schema_version": CURRENT_SCHEMA_VERSION,
            "project_id": "PP02",
            "project_name": "AI 每日股票分析",
        }
        assert backup["manifest"] == {
            "categories": {
                "agent_conversations": {
                    "status": "supported",
                    "row_count": 4,
                    "tables": ["conversation_messages", "conversation_summaries"],
                },
                "analysis": {
                    "status": "supported",
                    "row_count": 3,
                    "tables": ["analysis_history", "fundamental_snapshot"],
                },
                "configuration": {"status": "supported", "row_count": 1, "tables": ["configuration"]},
                "fund": {"status": "not_applicable", "row_count": 0, "tables": []},
                "period_reports": {"status": "supported", "row_count": 1, "tables": ["period_reports"]},
                "portfolio_events": {
                    "status": "supported",
                    "row_count": 4,
                    "tables": [
                        "portfolio_accounts",
                        "portfolio_trades",
                        "portfolio_cash_ledger",
                        "portfolio_corporate_actions",
                    ],
                },
                "structured_user_records": {
                    "status": "supported",
                    "row_count": 10,
                    "tables": [
                        "backtest_results",
                        "backtest_summaries",
                        "alert_rules",
                        "alert_triggers",
                        "alert_notifications",
                        "alert_cooldowns",
                        "decision_signals",
                        "decision_signal_outcomes",
                        "decision_signal_feedback",
                        "skill_opinion_samples",
                    ],
                },
            },
            "excluded": [
                "derived_portfolio_caches",
                "rebuildable_price_news_caches",
                "scheduler_runtime_state",
                "provider_traces",
                "logs",
                "drafts",
                "schema_bookkeeping",
                "credentials_tokens_cookies_vault_ciphertext",
            ],
            "excluded_tables": {
                "stock_daily": {
                    "classification": "rebuildable_market_data_cache",
                    "contains_user_data": False,
                    "restore_behavior": "cleared_then_rebuilt_on_demand",
                    "rebuild_entrypoint": "get_daily_history",
                },
            },
            "table_row_counts": {
                "alert_cooldowns": 1,
                "alert_notifications": 1,
                "alert_rules": 1,
                "alert_triggers": 1,
                "analysis_history": 2,
                "backtest_results": 1,
                "backtest_summaries": 1,
                "decision_signal_feedback": 1,
                "decision_signal_outcomes": 1,
                "decision_signals": 1,
                "fundamental_snapshot": 1,
                "conversation_messages": 3,
                "conversation_summaries": 1,
                "period_reports": 1,
                "portfolio_accounts": 1,
                "portfolio_cash_ledger": 1,
                "portfolio_corporate_actions": 1,
                "portfolio_trades": 1,
                "skill_opinion_samples": 1,
            },
        }
        assert [row["id"] for row in backup["data"]["tables"]["analysis_history"]] == [101, 202]
        assert backup["data"]["tables"]["fundamental_snapshot"] == [
            {
                "id": 203,
                "query_id": "analysis-fixed-101",
                "code": "600519",
                "payload": '{"revenue":123456}',
                "source_chain": '["provider-a"]',
                "coverage": '{"financials":true}',
                "created_at": "2026-08-01T10:01:00",
            }
        ]
        assert "stock_daily" not in backup["data"]["tables"]
        assert backup["data"]["tables"]["period_reports"][0]["id"] == 303
        assert backup["data"]["tables"]["portfolio_accounts"][0]["id"] == 401
        assert backup["data"]["tables"]["alert_notifications"][0]["id"] == 603
        assert backup["data"]["tables"]["alert_cooldowns"][0]["id"] == 604
        assert backup["data"]["tables"]["portfolio_accounts"][0]["owner_id"] == (
            "owner-private-marker"
        )
        assert [row["id"] for row in backup["data"]["tables"]["conversation_messages"]] == [
            901,
            902,
            904,
        ]
        assert backup["data"]["tables"]["conversation_summaries"][0] == {
            "id": 903,
            "session_id": "work20-visible-session",
            "summary": "fixed visible conversation summary",
            "covered_message_id": 902,
            "source_message_count": 2,
            "estimated_tokens": 12,
            "created_at": "2026-08-01T16:03:00",
            "updated_at": "2026-08-01T16:03:00",
        }
        assert backup["data"]["configuration"]["values"] == {"STOCK_LIST": "600519"}
        assert backup["integrity"] == {"algorithm": "sha256", "value": _canonical_sha256(backup)}

        serialized = json.dumps(backup, ensure_ascii=False).lower()
        for marker in (
            "credential-marker",
            "token-marker",
            "cookie-marker",
            "ciphertext-marker",
            "dingtalk-registry-marker",
            "pushover-registry-marker",
            "/private/runtime/",
        ):
            assert marker not in serialized

    def test_export_and_validator_reject_url_userinfo_without_echoing_credentials(self) -> None:
        ordinary = self.env_path.read_text(encoding="utf-8") + (
            "HTTP_PROXY=http://127.0.0.1:7890\n"
        )
        self.env_path.write_text(ordinary, encoding="utf-8")
        backup = self._service().export_backup()
        assert backup["data"]["configuration"]["values"]["HTTP_PROXY"] == (
            "http://127.0.0.1:7890"
        )

        credential_url = "http://explicit-fake-user:explicit-fake-password@proxy.invalid:7890"
        backup["data"]["configuration"]["values"]["HTTP_PROXY"] = credential_url
        backup["integrity"]["value"] = _canonical_sha256(backup)
        with pytest.raises(FullDataBackupValidationError) as validation_error:
            self._service().validate_backup(backup)
        assert credential_url not in str(validation_error.value)
        assert "explicit-fake-password" not in str(validation_error.value)

        self.env_path.write_text(
            ordinary.replace("http://127.0.0.1:7890", credential_url),
            encoding="utf-8",
        )
        with pytest.raises(FullDataBackupValidationError) as export_error:
            self._service().export_backup()
        assert credential_url not in str(export_error.value)
        assert "explicit-fake-password" not in str(export_error.value)

    def test_json_config_export_is_storage_canonical_and_roundtrips(self) -> None:
        spaced_rules = (
            '[ { "stock_code": "600519", "alert_type": "price_cross", '
            '"direction": "above", "price": 1800 } ]'
        )
        self.env_path.write_text(
            self.env_path.read_text(encoding="utf-8")
            + f"AGENT_EVENT_ALERT_RULES_JSON={spaced_rules}\n",
            encoding="utf-8",
        )

        backup = self._service().export_backup()

        assert backup["data"]["configuration"]["values"][
            "AGENT_EVENT_ALERT_RULES_JSON"
        ] == (
            '[{"stock_code":"600519","alert_type":"price_cross",'
            '"direction":"above","price":1800}]'
        )
        self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "raw_assignment",
        (
            "AGENT_EVENT_ALERT_RULES_JSON='[{\"stock_code\":\"600519\","
            "\"alert_type\":\"price_cross\",\"direction\":\"above\","
            "\"price\":1800}]'",
            'AGENT_EVENT_ALERT_RULES_JSON="[{\\"stock_code\\":\\"600519\\",'
            '\\"alert_type\\":\\"price_cross\\",\\"direction\\":\\"above\\",'
            '\\"price\\":1800}]"',
        ),
    )
    def test_quoted_json_config_uses_one_logical_snapshot_through_restore(
        self,
        raw_assignment,
    ) -> None:
        expected = (
            '[{"stock_code":"600519","alert_type":"price_cross",'
            '"direction":"above","price":1800}]'
        )
        self.env_path.write_text(
            self.env_path.read_text(encoding="utf-8") + raw_assignment + "\n",
            encoding="utf-8",
        )
        service = self._service()
        backup = service.export_backup()
        assert backup["data"]["configuration"]["values"][
            "AGENT_EVENT_ALERT_RULES_JSON"
        ] == expected
        assert service.validate_backup(backup)["integrity"]["value"] == backup[
            "integrity"
        ]["value"]

        self.env_path.write_text(
            self.env_path.read_text(encoding="utf-8").replace(
                raw_assignment,
                "AGENT_EVENT_ALERT_RULES_JSON=[]",
            ),
            encoding="utf-8",
        )
        preview = service.preview_restore(backup)
        result = service.restore_backup(
            backup,
            preview_token=preview["preview_token"],
        )

        assert preview["incoming_digest"] == backup["integrity"]["value"]
        assert result["incoming_digest"] == backup["integrity"]["value"]
        assert ConfigManager(env_path=self.env_path).read_config_map()[
            "AGENT_EVENT_ALERT_RULES_JSON"
        ] == expected

    def test_validator_rejects_noncanonical_json_config_after_checksum_recomputed(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["configuration"]["values"][
            "AGENT_EVENT_ALERT_RULES_JSON"
        ] = (
            '[ { "stock_code": "600519", "alert_type": "price_cross", '
            '"direction": "above", "price": 1800 } ]'
        )
        backup["manifest"]["categories"]["configuration"]["row_count"] += 1
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError, match="canonical"):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "credential_value",
        (
            "Authorization: Bearer explicit-fake-config-bearer-marker",
            "sk-proj-explicit-fake-config-provider-marker-1234567890",
            "cookie-marker-explicit-fake-config-cookie",
            "ghp_0123456789abcdefghijklmnopqrstuvwxyzAB",
            "gho_0123456789abcdefghijklmnopqrstuvwxyzAB",
            "ghu_0123456789abcdefghijklmnopqrstuvwxyzAB",
            "ghs_0123456789abcdefghijklmnopqrstuvwxyzAB",
            "ghr_0123456789abcdefghijklmnopqrstuvwxyzAB",
            "github_pat_0123456789_abcdefghijklmnopqrstuvwxyzAB",
            "AKIA0123456789ABCDEF",
            "ASIA0123456789ABCDEF",
            "AIza0123456789abcdefghijklmnopqrstuvwxyzAB",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaXhlZC10ZXN0In0.0123456789abcdef",
            "-----BEGIN PRIVATE KEY-----",
        ),
    )
    def test_allowed_config_key_rejects_embedded_credential_material_without_echo(
        self,
        credential_value,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["configuration"]["values"]["STOCK_LIST"] = credential_value
        backup["integrity"]["value"] = _canonical_sha256(backup)
        with pytest.raises(FullDataBackupValidationError) as validation_error:
            self._service().validate_backup(backup)
        assert credential_value not in str(validation_error.value)

        env_text = self.env_path.read_text(encoding="utf-8").replace(
            "STOCK_LIST=600519",
            f"STOCK_LIST={credential_value}",
        )
        self.env_path.write_text(env_text, encoding="utf-8")
        with pytest.raises(FullDataBackupValidationError) as export_error:
            self._service().export_backup()
        assert credential_value not in str(export_error.value)

    @pytest.mark.parametrize(
        "ordinary_value",
        (
            "ghp_short-reference",
            "gho_short-reference",
            "ghu_short-reference",
            "ghs_short-reference",
            "ghr_short-reference",
            "github_pat_short-reference",
            "AKIA0123456789ABCDE",
            "ASIA0123456789ABCDE",
            "AIza-short-reference",
            "eyJshort.short.short",
            "-----BEGIN PUBLIC KEY-----",
        ),
    )
    def test_secret_family_near_misses_remain_exportable(self, ordinary_value) -> None:
        self.env_path.write_text(
            self.env_path.read_text(encoding="utf-8").replace(
                "STOCK_LIST=600519",
                f"STOCK_LIST={ordinary_value}",
            ),
            encoding="utf-8",
        )

        backup = self._service().export_backup()

        assert backup["data"]["configuration"]["values"]["STOCK_LIST"] == ordinary_value

    def test_export_reads_all_tables_from_one_sqlite_snapshot(self, monkeypatch) -> None:
        service = self._service()
        with sqlite3.connect(self.db_path) as connection:
            assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
        first_table_read = threading.Event()
        writer_committed = threading.Event()
        original_read = service._read_table

        def pause_after_first_table(session, table_name):
            rows = original_read(session, table_name)
            if table_name == "analysis_history":
                first_table_read.set()
                assert writer_committed.wait(timeout=5)
            return rows

        def writer() -> None:
            assert first_table_read.wait(timeout=5)
            with self.db.get_session() as session:
                session.add_all(
                    (
                        AnalysisHistory(
                            id=9991,
                            query_id="snapshot-writer-analysis",
                            code="000001",
                            report_type="detailed",
                            analysis_summary="committed between table reads",
                            created_at=datetime(2026, 8, 2, 9, 0, 0),
                        ),
                        PortfolioAccount(
                            id=9992,
                            owner_id="snapshot-writer-owner",
                            name="Committed between table reads",
                            market="cn",
                            base_currency="CNY",
                            is_active=True,
                        ),
                    )
                )
                session.commit()
            writer_committed.set()

        monkeypatch.setattr(service, "_read_table", pause_after_first_table)
        thread = threading.Thread(target=writer, daemon=True)
        thread.start()
        backup = service.export_backup()
        thread.join(timeout=5)
        assert not thread.is_alive()

        analysis_ids = {row["id"] for row in backup["data"]["tables"]["analysis_history"]}
        account_ids = {row["id"] for row in backup["data"]["tables"]["portfolio_accounts"]}
        assert 9991 not in analysis_ids
        assert 9992 not in account_ids

    @pytest.mark.parametrize(
        ("column", "value"),
        (
            ("period", "week_to_date"),
            ("report_kind", "outlook"),
            ("start_date", "2026-07-19"),
            ("end_date", "2026-07-25"),
            ("status", "insufficient_data"),
            ("generated_at", "2026-08-01T11:01:00"),
            ("source_record_ids_json", "[101]"),
        ),
    )
    def test_validator_rejects_period_report_row_content_mismatch(self, column, value) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["period_reports"][0][column] = value
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_malformed_period_report_content(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["period_reports"][0]["content_json"] = '{"title":"bad"}'
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_accepts_matched_outlook_without_inflating_current_source_count(self) -> None:
        backup = self._service().export_backup()
        row = backup["data"]["tables"]["period_reports"][0]
        content = json.loads(row["content_json"])
        content["matched_outlook"] = {
            "snapshot_version": 1,
            "snapshot_id": 999,
            "snapshot_created_at": "2026-07-19T12:00:00",
            "status": "insufficient_data",
            "message": "近期有效数据不足，暂不能形成下周展望。",
            "target_period": {
                "start_date": "2026-07-20",
                "end_date": "2026-07-24",
            },
            "generated_at": "2026-07-19T12:00:00",
            "overall_tendency": None,
            "stocks": [],
            "etfs": [],
            "market_signals": [
                {
                    "record_id": 999,
                    "region": "cn",
                    "created_at": "2026-07-19T10:00:00",
                    "summary": "fixed matched outlook source",
                }
            ],
            "data_as_of": "2026-07-19T10:00:00",
            "source_record_count": 1,
            "source_record_ids": [999],
            "disclaimer": "fixed synthetic disclaimer",
        }
        row["content_json"] = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        row["source_record_ids_json"] = "[101, 202, 999]"
        backup["integrity"]["value"] = _canonical_sha256(backup)

        validated = self._service().validate_backup(backup)
        assert validated["data"]["tables"]["period_reports"][0][
            "source_record_ids_json"
        ] == "[101, 202, 999]"

    def test_validator_accepts_fixed_formal_outlook_shape(self) -> None:
        backup = self._service().export_backup()
        row = backup["data"]["tables"]["period_reports"][0]
        content = _valid_outlook_period_content()
        row.update(
            period=content["period"],
            report_kind=content["report_kind"],
            start_date=content["start_date"],
            end_date=content["end_date"],
            status=content["status"],
            generated_at=content["generated_at"],
            source_record_ids_json="[101, 202]",
            content_json=json.dumps(
                content,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "case",
        (
            "historical_asset_type_mismatch",
            "historical_duplicate_source_across_summaries",
            "historical_source_before_window",
            "historical_source_after_report",
            "outlook_asset_type_mismatch",
            "outlook_duplicate_source_across_items",
            "outlook_item_after_snapshot",
            "outlook_market_after_snapshot",
            "outlook_data_as_of_after_snapshot",
            "outlook_snapshot_created_after_generated",
            "outlook_insufficient_with_items",
            "outlook_ready_with_message",
            "outlook_wrong_overall_tendency",
        ),
    )
    def test_validator_rejects_formal_period_generator_semantic_mutations(
        self,
        case,
    ) -> None:
        backup = self._service().export_backup()
        row = backup["data"]["tables"]["period_reports"][0]
        if case.startswith("historical_"):
            content = json.loads(row["content_json"])
            if case == "historical_asset_type_mismatch":
                content["stock_summaries"][0]["asset_type"] = "etf"
            elif case == "historical_duplicate_source_across_summaries":
                duplicate = copy.deepcopy(content["stock_summaries"][0])
                duplicate["stock_code"] = "000001"
                content["stock_summaries"].append(duplicate)
            elif case == "historical_source_before_window":
                content["stock_summaries"][0]["latest_created_at"] = (
                    "2026-07-19T23:59:59+07:00"
                )
            else:
                content["market_reviews"][0]["created_at"] = (
                    "2026-08-01T11:00:01Z"
                )
        else:
            content = _valid_outlook_period_content()
            row.update(
                period=content["period"],
                report_kind=content["report_kind"],
                start_date=content["start_date"],
                end_date=content["end_date"],
                status=content["status"],
                generated_at=content["generated_at"],
                source_record_ids_json="[101, 202]",
            )
            outlook = content["outlook"]
            assert outlook is not None
            if case == "outlook_asset_type_mismatch":
                outlook["stocks"][0]["asset_type"] = "etf"
            elif case == "outlook_duplicate_source_across_items":
                duplicate = copy.deepcopy(outlook["stocks"][0])
                duplicate["stock_code"] = "510300"
                duplicate["asset_type"] = "etf"
                outlook["etfs"].append(duplicate)
            elif case == "outlook_item_after_snapshot":
                outlook["stocks"][0]["data_as_of"] = "2026-08-02T11:30:00-01:00"
            elif case == "outlook_market_after_snapshot":
                outlook["market_signals"][0]["created_at"] = "2026-08-02T12:00:01Z"
            elif case == "outlook_data_as_of_after_snapshot":
                outlook["data_as_of"] = "2026-08-02T12:00:01Z"
            elif case == "outlook_snapshot_created_after_generated":
                outlook["snapshot_created_at"] = "2026-08-02T12:00:01Z"
            elif case == "outlook_insufficient_with_items":
                content["status"] = "insufficient_data"
                row["status"] = "insufficient_data"
                outlook["status"] = "insufficient_data"
                outlook["message"] = "近期有效数据不足，暂不能形成下周展望。"
                outlook["overall_tendency"] = None
            elif case == "outlook_ready_with_message":
                outlook["message"] = "unexpected message"
            else:
                outlook["overall_tendency"] = "看空"

        row["content_json"] = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "mutate_content",
        (
            lambda content: content.update(extra_field="not-allowed"),
            lambda content: content.update(report_id="303"),
            lambda content: content.pop("disclaimer"),
            lambda content: content.update(generated_at="not-a-timestamp"),
            lambda content: content["stock_summaries"][0].update(record_count=2),
            lambda content: content["stock_summaries"][0].update(latest_record_id=202),
            lambda content: content["stock_summaries"][0]["direction_counts"].update(
                bullish=1
            ),
            lambda content: content["stock_summaries"][0].update(
                latest_created_at="not-a-timestamp"
            ),
        ),
    )
    def test_validator_rejects_noncanonical_period_content_semantics(
        self,
        mutate_content,
    ) -> None:
        backup = self._service().export_backup()
        row = backup["data"]["tables"]["period_reports"][0]
        content = json.loads(row["content_json"])
        mutate_content(content)
        row["content_json"] = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "matched_mutation",
        (
            lambda matched: matched["target_period"].update(start_date="2026-07-21"),
            lambda matched: matched.update(source_record_count=2),
            lambda matched: matched.update(generated_at="not-a-timestamp"),
            lambda matched: matched["market_signals"][0].update(record_id=998),
        ),
    )
    def test_validator_rejects_invalid_matched_outlook_semantics(
        self,
        matched_mutation,
    ) -> None:
        backup = self._service().export_backup()
        row = backup["data"]["tables"]["period_reports"][0]
        content = json.loads(row["content_json"])
        content["matched_outlook"] = {
            "snapshot_version": 1,
            "snapshot_id": 999,
            "snapshot_created_at": "2026-07-19T12:00:00",
            "status": "insufficient_data",
            "message": "近期有效数据不足，暂不能形成下周展望。",
            "target_period": {"start_date": "2026-07-20", "end_date": "2026-07-24"},
            "generated_at": "2026-07-19T12:00:00",
            "overall_tendency": None,
            "stocks": [],
            "etfs": [],
            "market_signals": [
                {
                    "record_id": 999,
                    "region": "cn",
                    "created_at": "2026-07-19T10:00:00",
                    "summary": "fixed matched outlook source",
                }
            ],
            "data_as_of": "2026-07-19T10:00:00",
            "source_record_count": 1,
            "source_record_ids": [999],
            "disclaimer": "fixed synthetic disclaimer",
        }
        matched_mutation(content["matched_outlook"])
        row["content_json"] = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        row["source_record_ids_json"] = "[101, 202, 998, 999]" if (
            content["matched_outlook"]["market_signals"][0]["record_id"] == 998
        ) else "[101, 202, 999]"
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_scans_visible_conversation_content_for_secrets(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["conversation_messages"][0]["content"] = (
            "Authorization: Bearer explicit-fake-visible-conversation-marker"
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_summary_covering_message_from_another_session(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["conversation_summaries"][0]["session_id"] = (
            "different-session"
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "mutation",
        (
            lambda document: document["integrity"].update(value="0" * 64),
            lambda document: document.pop("manifest"),
            lambda document: document.update(unexpected="not-allowed"),
            lambda document: document["data"]["tables"].update(unknown_fund_table=[]),
            lambda document: document["manifest"]["excluded_tables"]["stock_daily"].update(
                contains_user_data=True
            ),
            lambda document: document["manifest"]["excluded_tables"]["stock_daily"].update(
                rebuild_entrypoint="uncontrolled_rebuild"
            ),
            lambda document: document["metadata"].update(database_schema_version="unsupported-schema"),
        ),
    )
    def test_validator_fails_closed_for_corruption_unknown_sections_and_incompatible_versions(self, mutation) -> None:
        backup = self._service().export_backup()
        mutation(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_restore_rejects_a_missing_preview_without_writing_recovery(self) -> None:
        service = self._service()
        backup = service.export_backup()
        before = service.current_state_digest()

        with pytest.raises(FullDataBackupConflictError):
            service.restore_backup(backup, preview_token="not-a-preview-token")

        assert service.current_state_digest() == before
        assert not service.recovery_directory.exists()

    def test_validator_rejects_secret_like_config_even_with_recomputed_checksum(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["configuration"]["values"]["SESSION_COOKIE"] = "cookie-marker"
        backup["manifest"]["categories"]["configuration"]["row_count"] = 2
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("key", "value"),
        (
            ("DATABASE_PATH", "/private/runtime/database.db"),
            ("ENV_FILE", "/private/runtime/.env"),
            ("LOG_DIR", "/private/runtime/logs"),
            ("REPORT_TEMPLATES_DIR", "/private/runtime/templates"),
            ("AGENT_SKILL_DIR", "/private/runtime/skills"),
            ("LITELLM_CONFIG", "/private/runtime/litellm.yaml"),
        ),
    )
    def test_validator_rejects_runtime_config_after_checksum_recomputed(self, key, value) -> None:
        backup = self._service().export_backup()
        backup["data"]["configuration"]["values"] = {
            "STOCK_LIST": "600519",
            key: value,
        }
        backup["manifest"]["categories"]["configuration"]["row_count"] = 2
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_export_excludes_litellm_runtime_config_path(self) -> None:
        backup = self._service().export_backup()

        assert "LITELLM_CONFIG" not in backup["data"]["configuration"]["values"]
        assert "/private/runtime/litellm.yaml" not in json.dumps(backup, ensure_ascii=False)

    @pytest.mark.parametrize(
        ("key", "value"),
        (
            ("DINGTALK_APP_KEY", "dingtalk-registry-marker"),
            ("PUSHOVER_USER_KEY", "pushover-registry-marker"),
            ("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/registry/marker/value"),
        ),
    )
    def test_validator_rejects_registry_sensitive_config_after_checksum_recomputed(self, key, value) -> None:
        backup = self._service().export_backup()
        backup["data"]["configuration"]["values"] = {
            "STOCK_LIST": "600519",
            key: value,
        }
        backup["manifest"]["categories"]["configuration"]["row_count"] = 2
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_export_rejects_embedded_secret_in_formal_row(self) -> None:
        with self.db.get_session() as session:
            row = session.get(AnalysisHistory, 101)
            row.raw_result = '{"api_token":"row-api-token-marker"}'
            session.commit()

        with pytest.raises(FullDataBackupValidationError):
            self._service().export_backup()

    @pytest.mark.parametrize(
        ("table_name", "column_name", "value"),
        (
            ("analysis_history", "raw_result", '{"api_token":"row-api-token-marker"}'),
            ("analysis_history", "context_snapshot", '{"session_cookie":"row-cookie-marker"}'),
            ("analysis_history", "news_content", "token-marker-row-secret"),
            (
                "alert_triggers",
                "diagnostics",
                "Authorization: Bearer explicit-fake-bearer-marker",
            ),
            ("decision_signals", "evidence_json", '{"nested":{"vault_ciphertext":"row-ciphertext-marker"}}'),
            ("decision_signals", "metadata_json", '{"credential":"row-credential-marker"}'),
            ("analysis_history", "analysis_summary", "ghp_1234567890abcdefghijklmnopqrstuv"),
            ("analysis_history", "analysis_summary", "github_pat_11AA22BB33CC44DD55EE66FF77GG88HH"),
            ("analysis_history", "analysis_summary", "AKIAIOSFODNN7EXAMPLE"),
            ("analysis_history", "analysis_summary", "AIzaSyA1234567890abcdefghijklmnopqrst"),
            (
                "analysis_history",
                "analysis_summary",
                "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature1234567890",
            ),
            (
                "analysis_history",
                "analysis_summary",
                "-----BEGIN PRIVATE KEY----- embedded private material",
            ),
        ),
    )
    def test_validator_rejects_embedded_row_secrets_after_checksum_recomputed(
        self,
        table_name,
        column_name,
        value,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"][table_name][0][column_name] = value
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_preserves_ordinary_analysis_prose_about_tokens(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["analysis_history"][0]["analysis_summary"] = (
            "The analysis explains why API token usage is unavailable without storing a credential."
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        validated = self._service().validate_backup(backup)

        assert validated["data"]["tables"]["analysis_history"][0]["analysis_summary"].startswith(
            "The analysis explains"
        )

    def test_validator_preserves_non_secret_structured_keys_containing_key_or_token(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["analysis_history"][0]["context_snapshot"] = json.dumps(
            {
                "monkey": "animal",
                "tokenized_text": "ordinary analysis content",
                "token_count": 42,
            }
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        validated = self._service().validate_backup(backup)

        assert "ordinary analysis content" in validated["data"]["tables"]["analysis_history"][0][
            "context_snapshot"
        ]

    @pytest.mark.parametrize(
        "key",
        ("github_token", "database_password", "oauth_client_secret"),
    )
    def test_validator_rejects_segmented_secret_keys_with_opaque_values(
        self,
        key,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["analysis_history"][0]["context_snapshot"] = json.dumps(
            {key: "explicit-fake-opaque-secret-marker"}
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("column_name", "value"),
        (
            (
                "raw_result",
                '{"model_output":"sk-proj-explicit-fake-openai-marker-1234567890"}',
            ),
            (
                "raw_result",
                '{"model_output":"sk-proj-explicit-fake-openai-marker-1234567890"',
            ),
            (
                "news_content",
                "Slack response contained xoxb-explicit-fake-slack-marker-1234567890",
            ),
        ),
    )
    def test_validator_rejects_provider_tokens_in_valid_or_malformed_formal_text(
        self,
        column_name,
        value,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["analysis_history"][0][column_name] = value
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_preserves_legitimate_security_metadata_and_generic_webhook_urls(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["analysis_history"][0]["context_snapshot"] = json.dumps(
            {
                "token_type": "documentation category",
                "password_policy": "minimum length is twelve",
                "secret_risk": "No credential was stored.",
                "documentation_url": "https://example.com/docs/webhook/setup",
            }
        )
        backup["data"]["tables"]["analysis_history"][0]["news_content"] = (
            "See https://example.com/reference/hooks/overview for generic integration documentation."
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        validated = self._service().validate_backup(backup)

        assert "password_policy" in validated["data"]["tables"]["analysis_history"][0][
            "context_snapshot"
        ]

    def test_validator_preserves_harmless_malformed_json_like_analysis_text(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["analysis_history"][0]["raw_result"] = (
            '{"documentation":"https://example.com/hooks/setup"'
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        validated = self._service().validate_backup(backup)

        assert validated["data"]["tables"]["analysis_history"][0]["raw_result"].startswith("{")

    def test_export_does_not_adopt_a_future_sensitive_column_from_live_metadata(self, monkeypatch) -> None:
        """A later database migration must not silently extend the version-1 document."""
        from src.services import full_data_backup_service as backup_module

        with self.db._engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE analysis_history ADD COLUMN api_token TEXT")
            connection.exec_driver_sql("UPDATE analysis_history SET api_token = 'future-token-marker'")
        reflected_history = Table(
            "analysis_history",
            MetaData(),
            autoload_with=self.db._engine,
        )
        reflected_tables = dict(backup_module.Base.metadata.tables)
        reflected_tables["analysis_history"] = reflected_history
        fake_base = type("FakeBase", (), {"metadata": type("FakeMetadata", (), {"tables": reflected_tables})})
        monkeypatch.setattr(backup_module, "Base", fake_base)

        backup = self._service().export_backup()

        assert "api_token" not in backup["data"]["tables"]["analysis_history"][0]
        assert "future-token-marker" not in json.dumps(backup, ensure_ascii=False)

    def test_validator_rejects_malformed_datetime_after_checksum_is_recomputed(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["period_reports"][0]["generated_at"] = "not-a-datetime"
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_missing_required_portfolio_event_date_after_checksum_recomputed(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["portfolio_trades"][0]["trade_date"] = None
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("table_name", "column_name"),
        (
            ("portfolio_accounts", "name"),
            ("portfolio_trades", "account_id"),
            ("portfolio_cash_ledger", "event_date"),
            ("portfolio_corporate_actions", "effective_date"),
        ),
    )
    def test_validator_rejects_null_required_portfolio_fields_after_checksum_recomputed(
        self,
        table_name,
        column_name,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"][table_name][0][column_name] = None
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("table_name", "column_name"),
        (
            ("analysis_history", "code"),
            ("backtest_results", "analysis_history_id"),
            ("backtest_summaries", "scope"),
            ("alert_rules", "parameters"),
            ("alert_triggers", "target"),
            ("alert_notifications", "channel"),
            ("alert_cooldowns", "state"),
            ("decision_signals", "stock_code"),
            ("decision_signal_outcomes", "signal_id"),
            ("decision_signal_feedback", "feedback_value"),
            ("skill_opinion_samples", "stock_code"),
        ),
    )
    def test_validator_rejects_null_required_structured_fields_after_checksum_recomputed(
        self,
        table_name,
        column_name,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"][table_name][0][column_name] = None
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_orphan_portfolio_trade_after_checksum_recomputed(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["portfolio_trades"][0]["account_id"] = 999999
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("table_name", "column_name"),
        (
            ("backtest_results", "analysis_history_id"),
            ("decision_signal_outcomes", "signal_id"),
            ("decision_signal_feedback", "signal_id"),
            ("skill_opinion_samples", "analysis_history_id"),
        ),
    )
    def test_validator_rejects_orphan_structured_references_after_checksum_recomputed(
        self,
        table_name,
        column_name,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"][table_name][0][column_name] = 999999
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_export_preserves_weak_audit_references_after_sources_are_deleted(self) -> None:
        with self.db.get_session() as session:
            session.delete(session.get(AlertRuleRecord, 601))
            session.delete(session.get(AlertTriggerRecord, 602))
            period_report = session.get(PeriodReportRecord, 303)
            content = json.loads(period_report.content_json)
            content["source_record_count"] = 1
            content["stock_summaries"][0]["latest_record_id"] = 999999
            content["stock_summaries"][0]["source_record_ids"] = [999999]
            content["market_reviews"] = []
            period_report.content_json = json.dumps(
                content,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            period_report.source_record_ids_json = "[999999]"
            decision_signal = session.get(DecisionSignalRecord, 701)
            decision_signal.source_type = "market_review"
            decision_signal.source_report_id = 999999
            session.commit()

        backup = self._service().export_backup()
        validated = self._service().validate_backup(backup)

        assert validated["data"]["tables"]["alert_rules"] == []
        assert validated["data"]["tables"]["alert_triggers"] == []
        assert validated["data"]["tables"]["alert_notifications"][0]["trigger_id"] == 602
        assert validated["data"]["tables"]["alert_cooldowns"][0]["rule_id"] == 601
        assert validated["data"]["tables"]["period_reports"][0]["source_record_ids_json"] == "[999999]"
        assert validated["data"]["tables"]["decision_signals"][0]["source_report_id"] == 999999

    @pytest.mark.parametrize(
        ("column_name", "value"),
        (("side", "short"), ("market", "mars")),
    )
    def test_validator_rejects_illegal_portfolio_trade_domains_after_checksum_recomputed(
        self,
        column_name,
        value,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["portfolio_trades"][0][column_name] = value
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize("column_name", ("quantity", "price"))
    def test_validator_rejects_non_positive_trade_values_after_checksum_recomputed(
        self,
        column_name,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["portfolio_trades"][0][column_name] = -1
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("table_name", "column_name", "value"),
        (
            ("alert_rules", "parameters", "not-json"),
            ("period_reports", "content_json", "[]"),
            ("period_reports", "source_record_ids_json", "{}"),
            ("decision_signals", "metadata_json", "[]"),
        ),
    )
    def test_validator_rejects_invalid_json_columns_after_checksum_recomputed(
        self,
        table_name,
        column_name,
        value,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"][table_name][0][column_name] = value
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_reversed_period_dates_after_checksum_recomputed(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["period_reports"][0].update(
            start_date="2026-07-25",
            end_date="2026-07-24",
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("column_name", "value"),
        (
            ("period", "quarter_to_date"),
            ("report_kind", "forecast"),
            ("status", "published"),
        ),
    )
    def test_validator_rejects_unsupported_period_report_domains_after_checksum_recomputed(
        self,
        column_name,
        value,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["period_reports"][0][column_name] = value
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_reversed_decision_signal_entry_range_after_checksum_recomputed(
        self,
    ) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["decision_signals"][0].update(
            entry_low=200.0,
            entry_high=100.0,
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_wraps_mixed_timezone_cooldown_ordering_error(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["alert_cooldowns"][0].update(
            last_triggered_at="2026-08-01T15:01:00",
            cooldown_until="2026-08-01T14:31:00+00:00",
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_duplicate_period_identity_after_checksum_recomputed(self) -> None:
        backup = self._service().export_backup()
        duplicate = copy.deepcopy(backup["data"]["tables"]["period_reports"][0])
        duplicate["id"] = 304
        backup["data"]["tables"]["period_reports"].append(duplicate)
        backup["manifest"]["table_row_counts"]["period_reports"] = 2
        backup["manifest"]["categories"]["period_reports"]["row_count"] = 2
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_rejects_duplicate_primary_id_after_checksum_recomputed(self) -> None:
        backup = self._service().export_backup()
        duplicate = copy.deepcopy(backup["data"]["tables"]["portfolio_trades"][0])
        backup["data"]["tables"]["portfolio_trades"].append(duplicate)
        backup["manifest"]["table_row_counts"]["portfolio_trades"] = 2
        backup["manifest"]["categories"]["portfolio_events"]["row_count"] = 5
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "mutation",
        (
            lambda document: document.update(format_version=True),
            lambda document: document["manifest"]["table_row_counts"].update(period_reports=True),
            lambda document: document["manifest"]["categories"]["period_reports"].update(
                row_count=True
            ),
        ),
    )
    def test_validator_rejects_boolean_integer_primitives_after_checksum_recomputed(self, mutation) -> None:
        backup = self._service().export_backup()
        mutation(backup)
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    def test_validator_wraps_huge_integer_numeric_errors(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["portfolio_trades"][0]["quantity"] = 10**1000
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        "mutation",
        (
            lambda document: document["metadata"].update(created_at="not-a-datetime"),
            lambda document: document["data"]["tables"]["period_reports"][0].update(
                generated_at="2026-08-01"
            ),
            lambda document: document["data"]["tables"]["period_reports"][0].update(
                start_date=None
            ),
        ),
    )
    def test_validator_rejects_missing_or_non_timestamp_required_dates_after_checksum_recomputed(self, mutation) -> None:
        backup = self._service().export_backup()
        mutation(backup)
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)


def test_setup_failure_restores_process_environment_before_following_test(
    monkeypatch,
) -> None:
    original_environment = dict(os.environ)
    case = TestFullDataBackupService()

    def fail_after_environment_mutation() -> None:
        raise RuntimeError("synthetic setup failure")

    monkeypatch.setattr(case, "_seed_rows", fail_after_environment_mutation)
    try:
        with pytest.raises(RuntimeError, match="synthetic setup failure"):
            case.setup_method()
        assert dict(os.environ) == original_environment
    finally:
        # Keep the deliberate RED case isolated even before setup cleanup is fixed.
        DatabaseManager.reset_instance()
        Config.reset_instance()
        os.environ.clear()
        os.environ.update(original_environment)
        temp_dir = getattr(case, "temp_dir", None)
        if temp_dir is not None:
            temp_dir.cleanup()
