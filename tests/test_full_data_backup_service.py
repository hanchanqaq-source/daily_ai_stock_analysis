"""Contract tests for the PP02 complete non-secret data backup document."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlalchemy import MetaData, Table

from src.config import Config
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
    DatabaseManager,
    DecisionSignalFeedbackRecord,
    DecisionSignalOutcomeRecord,
    DecisionSignalRecord,
    PeriodReportRecord,
    PortfolioAccount,
    PortfolioCashLedger,
    PortfolioCorporateAction,
    PortfolioTrade,
    SkillOpinionSampleRecord,
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


class TestFullDataBackupService:
    def setup_method(self) -> None:
        self.original_environment = os.environ.copy()
        self.temp_dir = tempfile.TemporaryDirectory()
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
                    "/".join(
                        (
                            "SLACK_WEBHOOK_URL=https:/",
                            "hooks.slack.com",
                            "services",
                            "registry",
                            "marker",
                            "value",
                        )
                    ),
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

    def teardown_method(self) -> None:
        DatabaseManager.reset_instance()
        Config.reset_instance()
        os.environ.clear()
        os.environ.update(self.original_environment)
        self.temp_dir.cleanup()

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
                    PeriodReportRecord(
                        id=303,
                        period="previous_week",
                        report_kind="historical",
                        start_date=date(2026, 7, 20),
                        end_date=date(2026, 7, 24),
                        content_json='{"title":"stored report"}',
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
                "analysis": {"status": "supported", "row_count": 2, "tables": ["analysis_history"]},
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
                "price_news_fundamental_caches",
                "scheduler_runtime_state",
                "provider_traces",
                "logs",
                "drafts",
                "schema_bookkeeping",
                "credentials_tokens_cookies_vault_ciphertext",
            ],
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
                "period_reports": 1,
                "portfolio_accounts": 1,
                "portfolio_cash_ledger": 1,
                "portfolio_corporate_actions": 1,
                "portfolio_trades": 1,
                "skill_opinion_samples": 1,
            },
        }
        assert [row["id"] for row in backup["data"]["tables"]["analysis_history"]] == [101, 202]
        assert backup["data"]["tables"]["period_reports"][0]["id"] == 303
        assert backup["data"]["tables"]["portfolio_accounts"][0]["id"] == 401
        assert backup["data"]["tables"]["alert_notifications"][0]["id"] == 603
        assert backup["data"]["tables"]["alert_cooldowns"][0]["id"] == 604
        assert "owner_id" not in backup["data"]["tables"]["portfolio_accounts"][0]
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
            "owner-private-marker",
        ):
            assert marker not in serialized

    @pytest.mark.parametrize(
        "mutation",
        (
            lambda document: document["integrity"].update(value="0" * 64),
            lambda document: document.pop("manifest"),
            lambda document: document.update(unexpected="not-allowed"),
            lambda document: document["data"]["tables"].update(unknown_fund_table=[]),
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

    def test_export_uses_dotenv_values_and_includes_only_safe_declared_monkey_llm_channel_fields(
        self,
    ) -> None:
        self.env_path.write_text(
            "\n".join(
                (
                    'STOCK_LIST="600519,AAPL"',
                    "LLM_CHANNELS='monkey'",
                    'LLM_MONKEY_PROTOCOL="openai"',
                    'LLM_MONKEY_BASE_URL="https://llm.example.com/v1"',
                    'LLM_MONKEY_MODELS="monkey-chat,monkey-reasoner"',
                    'LLM_MONKEY_ENABLED="true"',
                    "LLM_MONKEY_API_KEY=sk-secret-must-not-export",
                    "LLM_MONKEY_API_KEYS=sk-secret-a,sk-secret-b",
                    'LLM_MONKEY_EXTRA_HEADERS={"Authorization":"Bearer hidden"}',
                    f"DATABASE_PATH={self.db_path}",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        backup = self._service().export_backup()

        assert backup["data"]["configuration"]["values"] == {
            "LLM_CHANNELS": "monkey",
            "LLM_MONKEY_BASE_URL": "https://llm.example.com/v1",
            "LLM_MONKEY_ENABLED": "true",
            "LLM_MONKEY_MODELS": "monkey-chat,monkey-reasoner",
            "LLM_MONKEY_PROTOCOL": "openai",
            "STOCK_LIST": "600519,AAPL",
        }
        canonical = json.dumps(backup, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert "sk-secret" not in canonical
        assert "Authorization" not in canonical
        self._service().validate_backup(backup)

    def test_export_rejects_invalid_configuration_semantics(self) -> None:
        self.env_path.write_text(
            f"STOCK_LIST=600519\nMAX_WORKERS=0\nDATABASE_PATH={self.db_path}\n",
            encoding="utf-8",
        )

        with pytest.raises(FullDataBackupValidationError):
            self._service().export_backup()

    def test_export_accepts_an_empty_non_secret_configuration(self) -> None:
        self.env_path.write_text("", encoding="utf-8")

        backup = self._service().export_backup()

        assert backup["data"]["configuration"]["values"] == {}
        self._service().validate_backup(backup)

    def test_preview_rejects_invalid_configuration_before_token_or_recovery(self) -> None:
        service = self._service()
        backup = service.export_backup()
        backup["data"]["configuration"]["values"]["MAX_WORKERS"] = "0"
        backup["manifest"]["categories"]["configuration"]["row_count"] = 2
        backup["integrity"]["value"] = _canonical_sha256(backup)
        before_digest = service.current_state_digest()
        before_tokens = dict(service._preview_tokens)

        with pytest.raises(FullDataBackupValidationError):
            service.preview_restore(backup)

        assert service.current_state_digest() == before_digest
        assert service._preview_tokens == before_tokens
        assert not service.recovery_directory.exists()

    @pytest.mark.parametrize(
        ("key", "value"),
        (
            ("DINGTALK_APP_KEY", "dingtalk-registry-marker"),
            ("PUSHOVER_USER_KEY", "pushover-registry-marker"),
            (
                "SLACK_WEBHOOK_URL",
                "/".join(
                    ("https:/", "hooks.slack.com", "services", "registry", "marker", "value")
                ),
            ),
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

    def test_export_permits_lowercase_akia_shaped_safe_prose(self) -> None:
        """Lowercase prose is not an AWS access-key identifier."""
        with self.db.get_session() as session:
            session.get(AnalysisHistory, 101).raw_result = (
                "The lowercase example akiaabcdefghijklmnop is safe prose."
            )
            session.commit()

        backup = self._service().export_backup()

        assert (
            backup["data"]["tables"]["analysis_history"][0]["raw_result"]
            == "The lowercase example akiaabcdefghijklmnop is safe prose."
        )

    @pytest.mark.parametrize(
        ("table_name", "column_name", "value"),
        (
            ("analysis_history", "raw_result", '{"api_token":"row-api-token-marker"}'),
            ("analysis_history", "context_snapshot", '{"session_cookie":"row-cookie-marker"}'),
            ("analysis_history", "news_content", "token-marker-row-secret"),
            ("alert_triggers", "diagnostics", "Authorization: Bearer abcdefghijklmnopqrstuvwxyz"),
            ("decision_signals", "evidence_json", '{"nested":{"vault_ciphertext":"row-ciphertext-marker"}}'),
            ("decision_signals", "metadata_json", '{"credential":"row-credential-marker"}'),
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
            {key: "mQ7vN4xZ2pL8cR5tY9wB"}
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

    @pytest.mark.parametrize(
        ("column_name", "value"),
        (
            (
                "raw_result",
                '{"model_output":"sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"}',
            ),
            (
                "raw_result",
                '{"model_output":"sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"',
            ),
            (
                "news_content",
                "Slack response contained "
                + "-".join(
                    ("xoxb", "123456789012", "123456789012", "abcdefghijklmnopqrstuvwx")
                ),
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

    @pytest.mark.parametrize(
        "credential_text",
        (
            "GitHub credential ghp_abcdefghijklmnopqrstuvwxyz1234567890AB",
            "GitHub fine-grained PAT github_pat_abcdefghijklmnopqrstuvwxyz1234567890AB",
            "AWS access key " + "".join(("AK", "IA", "ABCDEFGHIJKLMNOP")),
            "".join(
                (
                    "JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.",
                    "eyJzdWIiOiIxMjM0NTY3ODkwIn0.",
                    "abcdefghijklmnopqrst",
                    "uvwxyz1234567890ABCD",
                )
            ),
            "".join(
                (
                    "JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.",
                    "e30.",
                    "abcdefghijklmnopqrst",
                    "uvwxyz1234567890ABCD",
                )
            ),
            (
                "-----BEGIN PRIVATE KEY-----\n"
                "bW9jay1wcml2YXRlLWtleS1tYXRlcmlhbA==\n"
                "-----END PRIVATE KEY-----"
            ),
        ),
    )
    def test_export_rejects_high_confidence_credentials_before_canonical_generation(
        self,
        credential_text,
    ) -> None:
        """Removing the credential detector must permit formal backup generation."""
        with self.db.get_session() as session:
            session.get(AnalysisHistory, 101).raw_result = credential_text
            session.commit()

        with pytest.raises(FullDataBackupValidationError):
            self._service().export_backup()

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

    def test_validator_rejects_malformed_json_like_analysis_payload(self) -> None:
        backup = self._service().export_backup()
        backup["data"]["tables"]["analysis_history"][0]["raw_result"] = (
            '{"documentation":"https://example.com/hooks/setup"'
        )
        backup["integrity"]["value"] = _canonical_sha256(backup)

        with pytest.raises(FullDataBackupValidationError):
            self._service().validate_backup(backup)

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
