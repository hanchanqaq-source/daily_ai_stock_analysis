"""Strict, non-secret PP02 full-data backup export and validation contract."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import threading
import time as time_module
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from urllib.parse import urlsplit

from sqlalchemy import delete, insert, select

from src.core.config_registry import get_registered_field_keys, is_sensitive_config_key
from src.core.durable_file import durable_replace
from src.services.alert_service import (
    SUPPORTED_ALERT_TYPES,
    SUPPORTED_SEVERITIES,
    SUPPORTED_TARGET_SCOPES,
)
from src.services.decision_signal_outcome_service import (
    EVAL_STATUSES,
    FEEDBACK_SOURCES,
    FEEDBACK_VALUES,
    HOLDING_STATES,
    OUTCOME_VALUES,
    SUPPORTED_OUTCOME_HORIZONS,
)
from src.services.decision_signal_service import (
    DECISION_ACTIONS,
    HORIZONS,
    PLAN_QUALITIES,
    SIGNAL_STATUSES,
    SOURCE_TYPES,
)
from src.services.portfolio_service import (
    VALID_CASH_DIRECTIONS,
    VALID_CORPORATE_ACTIONS,
    VALID_MARKETS,
    VALID_SIDES,
)
from src.services.period_report_service import (
    INSUFFICIENT_OUTLOOK_MESSAGE,
    SUPPORTED_PERIODS,
)
from src.services.system_config_service import ConfigConflictError, SystemConfigService
from src.storage import CURRENT_SCHEMA_VERSION, Base, DatabaseManager
from src.services.full_data_restore_journal import FullDataRestoreJournal


BACKUP_FORMAT = "pp02.full-data.backup"
BACKUP_FORMAT_VERSION = 1
PROJECT_ID = "PP02"
PROJECT_NAME = "AI 每日股票分析"
DEFAULT_APPLICATION_VERSION = "3.29.2"
DEFAULT_PREVIEW_TOKEN_TTL_SECONDS = 300.0
PERIOD_REPORT_KINDS = frozenset({"historical", "outlook"})
PERIOD_REPORT_STATUSES = frozenset({"ready", "insufficient_data"})

TABLE_GROUPS = {
    "analysis": ("analysis_history",),
    "portfolio_events": (
        "portfolio_accounts",
        "portfolio_trades",
        "portfolio_cash_ledger",
        "portfolio_corporate_actions",
    ),
    "period_reports": ("period_reports",),
    "agent_conversations": (
        "conversation_messages",
        "conversation_summaries",
    ),
    "structured_user_records": (
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
    ),
}
TABLE_NAMES = tuple(table for tables in TABLE_GROUPS.values() for table in tables)
DERIVED_PORTFOLIO_TABLES = (
    "portfolio_daily_snapshots",
    "portfolio_position_lots",
    "portfolio_positions",
)
TABLE_COLUMN_ALLOWLIST = {
    "analysis_history": (
        "id", "query_id", "code", "name", "report_type", "sentiment_score", "operation_advice",
        "trend_prediction", "analysis_summary", "raw_result", "news_content", "context_snapshot",
        "ideal_buy", "secondary_buy", "stop_loss", "take_profit", "created_at",
    ),
    "portfolio_accounts": (
        "id", "owner_id", "name", "broker", "market", "base_currency", "is_active", "created_at",
        "updated_at",
    ),
    "portfolio_trades": (
        "id", "account_id", "trade_uid", "symbol", "market", "currency", "trade_date", "side",
        "quantity", "price", "fee", "tax", "note", "dedup_hash", "created_at",
    ),
    "portfolio_cash_ledger": (
        "id", "account_id", "event_date", "direction", "amount", "currency", "note", "created_at",
    ),
    "portfolio_corporate_actions": (
        "id", "account_id", "symbol", "market", "currency", "effective_date", "action_type",
        "cash_dividend_per_share", "split_ratio", "note", "created_at",
    ),
    "period_reports": (
        "id", "period", "report_kind", "start_date", "end_date", "content_json", "source_record_ids_json",
        "status", "generated_at", "updated_at",
    ),
    "conversation_messages": (
        "id", "session_id", "role", "content", "created_at",
    ),
    "conversation_summaries": (
        "id", "session_id", "summary", "covered_message_id", "source_message_count",
        "estimated_tokens", "created_at", "updated_at",
    ),
    "backtest_results": (
        "id", "analysis_history_id", "code", "analysis_date", "eval_window_days", "engine_version",
        "eval_status", "evaluated_at", "operation_advice", "position_recommendation", "start_price",
        "end_close", "max_high", "min_low", "stock_return_pct", "direction_expected", "direction_correct",
        "outcome", "stop_loss", "take_profit", "hit_stop_loss", "hit_take_profit", "first_hit",
        "first_hit_date", "first_hit_trading_days", "simulated_entry_price", "simulated_exit_price",
        "simulated_exit_reason", "simulated_return_pct",
    ),
    "backtest_summaries": (
        "id", "scope", "code", "eval_window_days", "engine_version", "computed_at", "total_evaluations",
        "completed_count", "insufficient_count", "long_count", "cash_count", "win_count", "loss_count",
        "neutral_count", "direction_accuracy_pct", "win_rate_pct", "neutral_rate_pct", "avg_stock_return_pct",
        "avg_simulated_return_pct", "stop_loss_trigger_rate", "take_profit_trigger_rate", "ambiguous_rate",
        "avg_days_to_first_hit", "advice_breakdown_json", "diagnostics_json",
    ),
    "alert_rules": (
        "id", "name", "target_scope", "target", "alert_type", "parameters", "severity", "enabled",
        "source", "cooldown_policy", "notification_policy", "created_at", "updated_at",
    ),
    "alert_triggers": (
        "id", "rule_id", "target", "observed_value", "threshold", "reason", "data_source",
        "data_timestamp", "triggered_at", "status", "diagnostics",
    ),
    "alert_notifications": (
        "id", "trigger_id", "channel", "attempt", "success", "error_code", "retryable", "latency_ms",
        "diagnostics", "created_at",
    ),
    "alert_cooldowns": (
        "id", "rule_id", "rule_key", "target", "severity", "last_triggered_at", "cooldown_until",
        "reason", "state", "updated_at",
    ),
    "decision_signals": (
        "id", "stock_code", "stock_name", "market", "source_type", "source_agent", "source_report_id",
        "trace_id", "decision_profile", "market_phase", "trigger_source", "action", "action_label",
        "confidence", "score", "horizon", "entry_low", "entry_high", "stop_loss", "target_price",
        "invalidation", "watch_conditions", "reason", "risk_summary", "catalyst_summary", "evidence_json",
        "data_quality_summary_json", "plan_quality", "status", "expires_at", "created_at", "updated_at",
        "metadata_json",
    ),
    "decision_signal_outcomes": (
        "id", "signal_id", "horizon", "engine_version", "eval_status", "outcome", "direction_expected",
        "direction_correct", "unable_reason", "anchor_date", "eval_window_days", "start_price", "end_close",
        "max_high", "min_low", "stock_return_pct", "action", "market", "market_phase", "source_type",
        "source_agent", "plan_quality", "data_quality_level", "holding_state", "created_at", "updated_at",
    ),
    "decision_signal_feedback": (
        "id", "signal_id", "feedback_value", "reason_code", "note", "source", "created_at", "updated_at",
    ),
    "skill_opinion_samples": (
        "id", "analysis_history_id", "stock_code", "skill_id", "skill_version", "signal", "confidence",
        "horizon", "data_quality_level", "opinion_created_at", "sample_schema_version", "created_at",
    ),
}
DATE_COLUMNS = {
    "portfolio_trades": frozenset({"trade_date"}),
    "portfolio_cash_ledger": frozenset({"event_date"}),
    "portfolio_corporate_actions": frozenset({"effective_date"}),
    "period_reports": frozenset({"start_date", "end_date"}),
    "backtest_results": frozenset({"analysis_date", "first_hit_date"}),
    "decision_signal_outcomes": frozenset({"anchor_date"}),
}
DATETIME_COLUMNS = {
    "analysis_history": frozenset({"created_at"}),
    "portfolio_accounts": frozenset({"created_at", "updated_at"}),
    "portfolio_trades": frozenset({"created_at"}),
    "portfolio_cash_ledger": frozenset({"created_at"}),
    "portfolio_corporate_actions": frozenset({"created_at"}),
    "period_reports": frozenset({"generated_at", "updated_at"}),
    "conversation_messages": frozenset({"created_at"}),
    "conversation_summaries": frozenset({"created_at", "updated_at"}),
    "backtest_results": frozenset({"evaluated_at"}),
    "backtest_summaries": frozenset({"computed_at"}),
    "alert_rules": frozenset({"created_at", "updated_at"}),
    "alert_triggers": frozenset({"data_timestamp", "triggered_at"}),
    "alert_notifications": frozenset({"created_at"}),
    "alert_cooldowns": frozenset({"last_triggered_at", "cooldown_until", "updated_at"}),
    "decision_signals": frozenset({"expires_at", "created_at", "updated_at"}),
    "decision_signal_outcomes": frozenset({"created_at", "updated_at"}),
    "decision_signal_feedback": frozenset({"created_at", "updated_at"}),
    "skill_opinion_samples": frozenset({"opinion_created_at", "created_at"}),
}
INTEGER_COLUMNS = {
    "analysis_history": frozenset({"id", "sentiment_score"}),
    "portfolio_accounts": frozenset({"id"}),
    "portfolio_trades": frozenset({"id", "account_id"}),
    "portfolio_cash_ledger": frozenset({"id", "account_id"}),
    "portfolio_corporate_actions": frozenset({"id", "account_id"}),
    "period_reports": frozenset({"id"}),
    "conversation_messages": frozenset({"id"}),
    "conversation_summaries": frozenset({
        "id", "covered_message_id", "source_message_count", "estimated_tokens",
    }),
    "backtest_results": frozenset({"id", "analysis_history_id", "eval_window_days", "first_hit_trading_days"}),
    "backtest_summaries": frozenset({"id", "eval_window_days", "total_evaluations", "completed_count", "insufficient_count", "long_count", "cash_count", "win_count", "loss_count", "neutral_count"}),
    "alert_rules": frozenset({"id"}),
    "alert_triggers": frozenset({"id", "rule_id"}),
    "alert_notifications": frozenset({"id", "trigger_id", "attempt", "latency_ms"}),
    "alert_cooldowns": frozenset({"id", "rule_id"}),
    "decision_signals": frozenset({"id", "source_report_id", "score"}),
    "decision_signal_outcomes": frozenset({"id", "signal_id", "eval_window_days"}),
    "decision_signal_feedback": frozenset({"id", "signal_id"}),
    "skill_opinion_samples": frozenset({"id", "analysis_history_id"}),
}
FLOAT_COLUMNS = {
    "analysis_history": frozenset({"ideal_buy", "secondary_buy", "stop_loss", "take_profit"}),
    "portfolio_trades": frozenset({"quantity", "price", "fee", "tax"}),
    "portfolio_cash_ledger": frozenset({"amount"}),
    "portfolio_corporate_actions": frozenset({"cash_dividend_per_share", "split_ratio"}),
    "backtest_results": frozenset({"start_price", "end_close", "max_high", "min_low", "stock_return_pct", "stop_loss", "take_profit", "simulated_entry_price", "simulated_exit_price", "simulated_return_pct"}),
    "backtest_summaries": frozenset({"direction_accuracy_pct", "win_rate_pct", "neutral_rate_pct", "avg_stock_return_pct", "avg_simulated_return_pct", "stop_loss_trigger_rate", "take_profit_trigger_rate", "ambiguous_rate", "avg_days_to_first_hit"}),
    "alert_triggers": frozenset({"observed_value", "threshold"}),
    "decision_signals": frozenset({"confidence", "entry_low", "entry_high", "stop_loss", "target_price"}),
    "decision_signal_outcomes": frozenset({"start_price", "end_close", "max_high", "min_low", "stock_return_pct"}),
    "skill_opinion_samples": frozenset({"confidence"}),
}
BOOLEAN_COLUMNS = {
    "portfolio_accounts": frozenset({"is_active"}),
    "backtest_results": frozenset({"direction_correct", "hit_stop_loss", "hit_take_profit"}),
    "alert_rules": frozenset({"enabled"}),
    "alert_notifications": frozenset({"success", "retryable"}),
    "decision_signal_outcomes": frozenset({"direction_correct"}),
}
REQUIRED_COLUMNS = {
    "analysis_history": frozenset({"id", "code"}),
    "portfolio_accounts": frozenset({"id", "name", "market", "base_currency", "is_active"}),
    "portfolio_trades": frozenset({
        "id", "account_id", "symbol", "market", "currency", "trade_date", "side", "quantity", "price",
    }),
    "portfolio_cash_ledger": frozenset({
        "id", "account_id", "event_date", "direction", "amount", "currency",
    }),
    "portfolio_corporate_actions": frozenset({
        "id", "account_id", "symbol", "market", "currency", "effective_date", "action_type",
    }),
    "period_reports": frozenset(TABLE_COLUMN_ALLOWLIST["period_reports"]),
    "conversation_messages": frozenset({"id", "session_id", "role", "content", "created_at"}),
    "conversation_summaries": frozenset(TABLE_COLUMN_ALLOWLIST["conversation_summaries"]),
    "backtest_results": frozenset({
        "id", "analysis_history_id", "code", "eval_window_days", "engine_version", "eval_status",
    }),
    "backtest_summaries": frozenset({"id", "scope", "eval_window_days", "engine_version"}),
    "alert_rules": frozenset({
        "id", "name", "target_scope", "target", "alert_type", "parameters", "severity", "enabled", "source",
    }),
    "alert_triggers": frozenset({"id", "target", "status"}),
    "alert_notifications": frozenset({"id", "channel", "attempt", "success", "retryable"}),
    "alert_cooldowns": frozenset({"id", "target", "severity", "state"}),
    "decision_signals": frozenset({
        "id", "stock_code", "market", "source_type", "trigger_source", "action", "plan_quality", "status",
    }),
    "decision_signal_outcomes": frozenset({
        "id", "signal_id", "horizon", "engine_version", "eval_status", "holding_state",
    }),
    "decision_signal_feedback": frozenset({"id", "signal_id", "feedback_value", "source"}),
    "skill_opinion_samples": frozenset({
        "id", "analysis_history_id", "stock_code", "skill_id", "signal", "confidence", "sample_schema_version",
    }),
}
JSON_OBJECT_COLUMNS = {
    "analysis_history": frozenset({"context_snapshot"}),
    "period_reports": frozenset({"content_json"}),
    "backtest_summaries": frozenset({"advice_breakdown_json", "diagnostics_json"}),
    "alert_rules": frozenset({"parameters", "cooldown_policy", "notification_policy"}),
    "decision_signals": frozenset({"metadata_json"}),
}
JSON_ARRAY_COLUMNS = {
    "period_reports": frozenset({"source_record_ids_json"}),
}
JSON_VALUE_COLUMNS = {
    "decision_signals": frozenset({"evidence_json", "data_quality_summary_json"}),
}
ENUM_COLUMNS = {
    "period_reports": {
        "period": frozenset(SUPPORTED_PERIODS),
        "report_kind": PERIOD_REPORT_KINDS,
        "status": PERIOD_REPORT_STATUSES,
    },
    "conversation_messages": {"role": frozenset({"user", "assistant", "system"})},
    "portfolio_accounts": {"market": frozenset(VALID_MARKETS)},
    "portfolio_trades": {
        "market": frozenset(VALID_MARKETS),
        "side": frozenset(VALID_SIDES),
    },
    "portfolio_cash_ledger": {"direction": frozenset(VALID_CASH_DIRECTIONS)},
    "portfolio_corporate_actions": {
        "market": frozenset(VALID_MARKETS),
        "action_type": frozenset(VALID_CORPORATE_ACTIONS),
    },
    "backtest_summaries": {"scope": frozenset({"overall", "stock"})},
    "alert_rules": {
        "target_scope": frozenset(SUPPORTED_TARGET_SCOPES),
        "alert_type": frozenset(SUPPORTED_ALERT_TYPES),
        "severity": frozenset(SUPPORTED_SEVERITIES),
    },
    "decision_signals": {
        "market": frozenset(VALID_MARKETS),
        "source_type": frozenset(SOURCE_TYPES),
        "action": frozenset(DECISION_ACTIONS),
        "plan_quality": frozenset(PLAN_QUALITIES),
        "status": frozenset(SIGNAL_STATUSES),
        "horizon": frozenset(HORIZONS),
    },
    "decision_signal_outcomes": {
        "horizon": frozenset(SUPPORTED_OUTCOME_HORIZONS),
        "eval_status": frozenset(EVAL_STATUSES),
        "outcome": frozenset(OUTCOME_VALUES),
        "holding_state": frozenset(HOLDING_STATES),
        "action": frozenset(DECISION_ACTIONS),
        "market": frozenset(VALID_MARKETS),
        "source_type": frozenset(SOURCE_TYPES),
    },
    "decision_signal_feedback": {
        "feedback_value": frozenset(FEEDBACK_VALUES),
        "source": frozenset(FEEDBACK_SOURCES),
    },
    "skill_opinion_samples": {
        "signal": frozenset({"strong_buy", "buy", "hold", "sell", "strong_sell"}),
    },
}
POSITIVE_NUMERIC_COLUMNS = {
    "portfolio_trades": frozenset({"quantity", "price"}),
    "portfolio_cash_ledger": frozenset({"amount"}),
    "backtest_results": frozenset({"eval_window_days", "start_price", "end_close", "max_high", "min_low", "stop_loss", "take_profit", "simulated_entry_price", "simulated_exit_price"}),
    "backtest_summaries": frozenset({"eval_window_days"}),
    "alert_notifications": frozenset({"attempt"}),
    "decision_signals": frozenset({"entry_low", "entry_high", "stop_loss", "target_price"}),
    "decision_signal_outcomes": frozenset({"eval_window_days", "start_price", "end_close", "max_high", "min_low"}),
}
NON_NEGATIVE_NUMERIC_COLUMNS = {
    "portfolio_trades": frozenset({"fee", "tax"}),
    "portfolio_corporate_actions": frozenset({"cash_dividend_per_share"}),
    "backtest_results": frozenset({"first_hit_trading_days"}),
    "backtest_summaries": frozenset({
        "total_evaluations", "completed_count", "insufficient_count", "long_count", "cash_count",
        "win_count", "loss_count", "neutral_count", "stop_loss_trigger_rate", "take_profit_trigger_rate",
        "ambiguous_rate", "avg_days_to_first_hit",
    }),
    "alert_notifications": frozenset({"latency_ms"}),
    "conversation_summaries": frozenset({
        "covered_message_id", "source_message_count", "estimated_tokens",
    }),
}
RANGED_NUMERIC_COLUMNS = {
    "decision_signals": {"confidence": (0.0, 1.0), "score": (0.0, 100.0)},
    "skill_opinion_samples": {"confidence": (0.0, 1.0)},
}
UNIQUE_IDENTITIES = {
    "portfolio_trades": (
        ("account_id", "trade_uid"),
        ("account_id", "dedup_hash"),
    ),
    "period_reports": (("period", "report_kind", "start_date", "end_date"),),
    "backtest_results": (("analysis_history_id", "eval_window_days", "engine_version"),),
    "backtest_summaries": (("scope", "code", "eval_window_days", "engine_version"),),
    "alert_cooldowns": (("rule_id", "target", "severity"),),
    "decision_signal_outcomes": (("signal_id", "horizon", "engine_version"),),
    "decision_signal_feedback": (("signal_id",),),
    "skill_opinion_samples": (("analysis_history_id", "skill_id", "sample_schema_version"),),
    "conversation_summaries": (("session_id",),),
}
REFERENCE_COLUMNS = (
    ("portfolio_trades", "account_id", "portfolio_accounts"),
    ("portfolio_cash_ledger", "account_id", "portfolio_accounts"),
    ("portfolio_corporate_actions", "account_id", "portfolio_accounts"),
    ("backtest_results", "analysis_history_id", "analysis_history"),
    ("decision_signal_outcomes", "signal_id", "decision_signals"),
    ("decision_signal_feedback", "signal_id", "decision_signals"),
    ("skill_opinion_samples", "analysis_history_id", "analysis_history"),
)
EXCLUDED_CONTENT = (
    "derived_portfolio_caches",
    "price_news_fundamental_caches",
    "scheduler_runtime_state",
    "provider_traces",
    "logs",
    "drafts",
    "schema_bookkeeping",
    "credentials_tokens_cookies_vault_ciphertext",
)
ROOT_KEYS = {"format", "format_version", "metadata", "manifest", "data", "integrity"}
_ASSIGNMENT_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
_SENSITIVE_EMBEDDED_KEYS = frozenset({
    "ACCESS_TOKEN", "API_KEY", "API_SECRET", "API_TOKEN", "AUTHORIZATION", "AUTH_TOKEN",
    "BEARER_TOKEN", "CIPHERTEXT", "CLIENT_SECRET", "COOKIE", "COOKIES", "CREDENTIAL",
    "CREDENTIALS", "ID_TOKEN", "PASSWORD", "PASSWD", "PRIVATE_KEY", "REFRESH_TOKEN",
    "SECRET", "SESSION_COOKIE", "SESSION_TOKEN", "SIGNING_SECRET", "VAULT_CIPHERTEXT",
})
_SENSITIVE_EMBEDDED_KEY_SEGMENTS = frozenset({
    "AUTHORIZATION", "CIPHERTEXT", "COOKIE", "COOKIES", "CREDENTIAL", "CREDENTIALS",
    "PASSWORD", "PASSWD", "SECRET", "TOKEN",
})
_SAFE_EMBEDDED_METADATA_SUFFIXES = frozenset({
    "PASSWORD_POLICY", "SECRET_RISK", "TOKEN_COUNT", "TOKEN_COUNTS", "TOKEN_TYPE",
    "TOKEN_USAGE",
})
_HIGH_CONFIDENCE_SECRET_VALUE_RE = re.compile(
    r"(?:\bBearer\s+[A-Za-z0-9._~+/=-]{8,}|"
    r"(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])|"
    r"(?<![A-Za-z0-9-])xox[baprs]-[A-Za-z0-9-]{20,}(?![A-Za-z0-9-])|"
    r"(?:credential|token|cookie|ciphertext)[- _]?marker(?:[-_A-Za-z0-9]*)|"
    r"(?:api[- _]?key|access[- _]?token|auth[- _]?token|password|secret|cookie|ciphertext)"
    r"\s*[:=]\s*[\"']?[^\s\"']{8,}|"
    r"https://hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9_-]{20,}|"
    r"https?://[^\s]+/api/webhooks/\d+/[A-Za-z0-9._-]{20,}|"
    r"https?://[^\s]+/robot/send\?access_token=[A-Za-z0-9_-]{20,})",
    re.IGNORECASE,
)
_HIGH_CONFIDENCE_TOKEN_FAMILY_RE = re.compile(
    r"(?:"
    r"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{30,}(?![A-Za-z0-9])|"
    r"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{24,}(?![A-Za-z0-9_])|"
    r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])|"
    r"(?<![A-Za-z0-9_-])AIza[A-Za-z0-9_-]{30,}(?![A-Za-z0-9_-])|"
    r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."
    r"[A-Za-z0-9_-]{8,}(?![A-Za-z0-9_-])|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r")"
)
_RUNTIME_CONFIG_KEYS = frozenset({
    "DATABASE_PATH", "ENV_FILE", "LOG_DIR", "REPORT_TEMPLATES_DIR", "AGENT_SKILL_DIR",
    "LITELLM_CONFIG",
})
REGISTERED_CONFIG_KEYS = frozenset(get_registered_field_keys())
BACKUP_CONFIG_ALLOWLIST = frozenset(
    key
    for key in REGISTERED_CONFIG_KEYS
    if key not in _RUNTIME_CONFIG_KEYS and not is_sensitive_config_key(key)
)


class FullDataBackupValidationError(ValueError):
    """Raised when a complete data backup document is not exactly supported."""


class FullDataBackupConflictError(RuntimeError):
    """Raised when a preview token no longer matches input or destination state."""


class FullDataBackupRestoreError(RuntimeError):
    """Raised after a restore attempt is rolled back or cannot be recovered."""


class FullDataBackupService:
    """Export only formal PP02 data through a closed, deterministic allow-list."""

    _preview_tokens: Dict[str, Dict[str, Any]] = {}
    _preview_lock = threading.RLock()

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        config_service: Optional[SystemConfigService] = None,
        application_version: Optional[str] = None,
        preview_token_ttl_seconds: float = DEFAULT_PREVIEW_TOKEN_TTL_SECONDS,
        crash_test_hook: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.db = db_manager or DatabaseManager.get_instance()
        self.config_service = config_service or SystemConfigService()
        self.application_version = (
            str(application_version or os.getenv("PP02_APPLICATION_VERSION", DEFAULT_APPLICATION_VERSION)).strip()
            or DEFAULT_APPLICATION_VERSION
        )
        self.preview_token_ttl_seconds = float(preview_token_ttl_seconds)
        self._crash_test_hook = crash_test_hook
        if (
            not math.isfinite(self.preview_token_ttl_seconds)
            or self.preview_token_ttl_seconds <= 0
        ):
            raise ValueError(
                "preview_token_ttl_seconds must be finite and positive"
            )

    def export_backup(self) -> Dict[str, Any]:
        """Return a complete, deterministic-in-content document with canonical integrity."""
        tables = self._read_tables_snapshot()
        configuration = self._read_sanitized_configuration()
        return self._build_backup_document(tables=tables, configuration=configuration)

    def _build_backup_document(
        self,
        *,
        tables: Mapping[str, Any],
        configuration: Mapping[str, Any],
    ) -> Dict[str, Any]:
        data = {"configuration": configuration, "tables": tables}
        self._validate_data(data)
        manifest = self._manifest(data)
        metadata = {
            "application_version": self.application_version,
            "created_at": self._timestamp(datetime.now(timezone.utc).replace(microsecond=0)),
            "database_schema_version": CURRENT_SCHEMA_VERSION,
            "project_id": PROJECT_ID,
            "project_name": PROJECT_NAME,
        }
        document = {
            "format": BACKUP_FORMAT,
            "format_version": BACKUP_FORMAT_VERSION,
            "metadata": metadata,
            "manifest": manifest,
            "data": data,
            "integrity": {"algorithm": "sha256", "value": ""},
        }
        document["integrity"]["value"] = self.canonical_sha256(document)
        return document

    @property
    def recovery_directory(self) -> Path:
        """Return the dedicated recovery directory beside the active SQLite file."""
        engine = getattr(self.db, "_engine", None)
        if engine is None or engine.url.get_backend_name() != "sqlite":
            raise FullDataBackupRestoreError("Full-data restore requires SQLite.")
        database = str(engine.url.database or "").strip()
        if not database or database.lower() == ":memory:":
            raise FullDataBackupRestoreError(
                "Full-data restore requires a file-backed SQLite database."
            )
        database_path = Path(database).expanduser().resolve()
        return database_path.parent / f"{database_path.stem}_restore_recovery"

    def export_configuration_values(self) -> Dict[str, str]:
        """Return the current complete-backup config subset without volatile metadata."""
        return dict(self._read_sanitized_configuration()["values"])

    def current_state_digest(self) -> str:
        """Return a stable digest of allow-listed database rows and config values."""
        tables = self._read_tables_snapshot()
        return self._state_digest(tables, self._read_sanitized_configuration())

    def preview_restore(self, backup: Mapping[str, Any]) -> Dict[str, Any]:
        """Validate fully and issue a short-lived token bound to both states."""
        validated = self.validate_backup(backup)
        incoming_digest = self.canonical_sha256(validated)
        current_tables = self._read_tables_snapshot()
        current_configuration = self._read_sanitized_configuration()
        destination_digest = self._state_digest(
            current_tables,
            current_configuration,
        )
        issued_monotonic = time_module.monotonic()
        issued_at = datetime.now(timezone.utc)
        token_payload = {
            "destination_digest": destination_digest,
            "incoming_digest": incoming_digest,
            "issued_at_ns": time_module.time_ns(),
            "nonce": secrets.token_hex(16),
        }
        preview_token = hashlib.sha256(
            json.dumps(
                token_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        with self._preview_lock:
            self._prune_preview_tokens(issued_monotonic)
            self._preview_tokens[preview_token] = {
                "destination_digest": destination_digest,
                "expires_monotonic": issued_monotonic + self.preview_token_ttl_seconds,
                "incoming_digest": incoming_digest,
            }
        return {
            "preview_token": preview_token,
            "incoming_digest": incoming_digest,
            "destination_digest": destination_digest,
            "issued_at": self._timestamp(issued_at),
            "expires_at": self._timestamp(
                issued_at + timedelta(seconds=self.preview_token_ttl_seconds)
            ),
            "incoming_table_row_counts": dict(
                validated["manifest"]["table_row_counts"]
            ),
            "destination_table_row_counts": {
                table_name: len(current_tables[table_name])
                for table_name in sorted(TABLE_NAMES)
            },
            "restart_required": True,
        }

    def restore_backup(
        self,
        backup: Mapping[str, Any],
        *,
        preview_token: str,
    ) -> Dict[str, Any]:
        """Replace allow-listed state transactionally after a matching preview."""
        validated = self.validate_backup(backup)
        incoming_digest = self.canonical_sha256(validated)
        preview = self._consume_preview_token(preview_token, incoming_digest)
        if not getattr(self.db, "_is_sqlite_engine", False):
            raise FullDataBackupRestoreError("Full-data restore requires SQLite.")

        journal = FullDataRestoreJournal(
            db_manager=self.db,
            config_service=self.config_service,
            application_version=self.application_version,
            database_schema_version=CURRENT_SCHEMA_VERSION,
            managed_keys=set(BACKUP_CONFIG_ALLOWLIST),
            value_validator=self._validate_config_value,
        )
        with journal.transaction_lock():
            return self._restore_backup_under_lock(
                validated=validated,
                incoming_digest=incoming_digest,
                preview=preview,
                journal=journal,
            )

    def _restore_backup_under_lock(
        self,
        *,
        validated: Mapping[str, Any],
        incoming_digest: str,
        preview: Mapping[str, Any],
        journal: FullDataRestoreJournal,
    ) -> Dict[str, Any]:
        """Run one restore while holding the cross-process journal lock."""
        session = self.db.get_session()
        journal_tx_id: Optional[str] = None
        recovery: Optional[Dict[str, Any]] = None
        prior_configuration: Optional[Dict[str, Any]] = None
        configuration_receipt = None
        database_committed = False
        database_commit_attempted = False
        try:
            connection = session.connection()
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            foreign_keys_enabled = connection.exec_driver_sql(
                "PRAGMA foreign_keys"
            ).scalar_one()
            if foreign_keys_enabled != 1:
                raise FullDataBackupRestoreError(
                    "SQLite foreign-key enforcement could not be enabled."
                )
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            current_tables = {
                table_name: self._read_table(session, table_name)
                for table_name in TABLE_NAMES
            }
            prior_configuration = self._read_sanitized_configuration()
            destination_digest = self._state_digest(
                current_tables,
                prior_configuration,
            )
            if destination_digest != preview["destination_digest"]:
                raise FullDataBackupConflictError(
                    "Destination data or configuration changed after preview."
                )

            recovery_document = self._build_backup_document(
                tables=current_tables,
                configuration=prior_configuration,
            )
            recovery = self._write_recovery_artifact(
                recovery_document,
                destination_digest=destination_digest,
            )
            journal_tx_id = journal.begin(
                prior_values=prior_configuration["values"],
                incoming_values=validated["data"]["configuration"]["values"],
            )

            try:
                configuration_receipt = self._replace_configuration(
                    validated["data"]["configuration"],
                    config_version=prior_configuration["config_version"],
                )
            except ConfigConflictError as exc:
                raise FullDataBackupConflictError(
                    "Destination configuration changed during restore."
                ) from exc
            self._run_crash_test_hook("after_config_publish")
            self._verify_configuration(validated["data"]["configuration"])
            self._replace_tables(session, validated["data"]["tables"])
            restored_tables = self._verify_restored_tables(
                session,
                validated["data"]["tables"],
            )
            restored_configuration = self._read_sanitized_configuration()
            restored_digest = self._state_digest(
                restored_tables,
                restored_configuration,
            )
            expected_digest = self._state_digest(
                validated["data"]["tables"],
                validated["data"]["configuration"],
            )
            if restored_digest != expected_digest:
                raise FullDataBackupRestoreError(
                    "Restored data/config digest does not match the validated backup."
                )
            assert journal_tx_id is not None
            journal.mark_committed(session, journal_tx_id)
            database_commit_attempted = True
            session.commit()
            database_committed = True
            self._run_crash_test_hook("after_db_commit")
        except BaseException as exc:
            rollback_error = None
            try:
                session.rollback()
            except BaseException as rollback_exc:  # pragma: no cover - driver failure
                rollback_error = rollback_exc
            commit_outcome_uncertain = False
            marker_query_error = None
            if (
                not database_committed
                and database_commit_attempted
                and journal_tx_id is not None
            ):
                try:
                    database_committed = journal.is_committed(journal_tx_id)
                except BaseException as marker_exc:
                    # Never compensate when the durable commit result cannot be
                    # observed. The journal and incoming configuration are the
                    # evidence startup recovery needs to settle the transaction.
                    commit_outcome_uncertain = True
                    marker_query_error = marker_exc
            if database_committed or commit_outcome_uncertain:
                if configuration_receipt is not None:
                    try:
                        self.config_service.finalize_env_subset_atomically(
                            configuration_receipt
                        )
                    except BaseException as cleanup_exc:
                        try:
                            self.config_service.discard_env_subset_receipt_after_commit(
                                configuration_receipt
                            )
                        except BaseException:
                            pass
                        add_note = getattr(exc, "add_note", None)
                        if callable(add_note):
                            add_note(
                                "Committed restore receipt cleanup encountered an "
                                f"additional failure: {cleanup_exc!r}"
                            )
                    configuration_receipt = None
                add_note = getattr(exc, "add_note", None)
                if callable(add_note):
                    if marker_query_error is not None:
                        add_note(
                            "Restore commit outcome could not be confirmed; durable "
                            "journal evidence was retained for startup recovery."
                        )
                    if rollback_error is not None:
                        add_note("Session rollback after commit interruption also failed.")
                raise
            compensation_error = None
            compensation_conflict = None
            if configuration_receipt is not None and prior_configuration is not None:
                try:
                    self.config_service.compensate_env_subset_atomically(
                        receipt=configuration_receipt,
                        reload_now=False,
                    )
                    configuration_receipt = None
                    self._verify_configuration(prior_configuration)
                except ConfigConflictError as conflict_exc:
                    compensation_conflict = conflict_exc
                    self.config_service.discard_env_subset_receipt_after_commit(
                        configuration_receipt
                    )
                    configuration_receipt = None
                except BaseException as compensation_exc:  # pragma: no cover - catastrophic path
                    compensation_error = compensation_exc
                    try:
                        self.config_service.discard_env_subset_receipt_after_commit(
                            configuration_receipt
                        )
                    except BaseException:
                        pass
                    configuration_receipt = None
            if journal_tx_id is not None:
                try:
                    current_configuration = self._read_sanitized_configuration()
                    if (
                        prior_configuration is not None
                        and current_configuration["values"]
                        == prior_configuration["values"]
                    ):
                        journal.cancel(journal_tx_id)
                    else:
                        journal.abort(journal_tx_id)
                    journal_tx_id = None
                except BaseException as journal_exc:
                    if compensation_error is None:
                        compensation_error = journal_exc
            if not isinstance(exc, Exception):
                add_note = getattr(exc, "add_note", None)
                if callable(add_note):
                    if compensation_conflict is not None:
                        add_note(
                            "A concurrent configuration edit was preserved while the "
                            "database restore was rolled back."
                        )
                    if compensation_error is not None:
                        add_note("Configuration compensation encountered an additional failure.")
                raise
            if compensation_conflict is not None:
                raise FullDataBackupConflictError(
                    "Configuration changed after restore apply; the concurrent "
                    "edit was not overwritten and database changes were rolled back."
                ) from compensation_conflict
            if isinstance(exc, FullDataBackupConflictError):
                raise
            message = f"Full-data restore failed and database changes were rolled back: {exc}"
            if compensation_error is not None:
                message += f"; configuration compensation also failed: {compensation_error}"
            raise FullDataBackupRestoreError(message) from exc
        finally:
            session.close()

        if configuration_receipt is None:
            raise FullDataBackupRestoreError(
                "Restore committed but configuration receipt is missing."
            )
        warnings: List[str] = []
        try:
            self.config_service.finalize_env_subset_atomically(configuration_receipt)
        except Exception:
            try:
                self.config_service.finalize_env_subset_atomically(configuration_receipt)
            except Exception:
                self.config_service.discard_env_subset_receipt_after_commit(
                    configuration_receipt
                )
            warnings.append(
                "Configuration receipt cleanup required a safe post-commit retry."
            )
        configuration_receipt = None

        assert journal_tx_id is not None
        try:
            journal.finish(journal_tx_id)
        except Exception:
            try:
                journal.recover_pending()
            except Exception:
                warnings.append(
                    "Restore transaction cleanup is pending safe startup recovery."
                )
            else:
                warnings.append(
                    "Restore transaction cleanup required a safe post-commit retry."
                )
        journal_tx_id = None

        assert recovery is not None
        return {
            "success": True,
            "incoming_digest": incoming_digest,
            "destination_digest_before": preview["destination_digest"],
            "destination_digest_after": restored_digest,
            "restored_table_row_counts": dict(
                validated["manifest"]["table_row_counts"]
            ),
            "recovery_filename": recovery["filename"],
            "recovery": recovery,
            "restart_required": True,
            "warnings": warnings,
        }

    def _run_crash_test_hook(self, phase: str) -> None:
        if self._crash_test_hook is not None:
            self._crash_test_hook(phase)

    def _consume_preview_token(
        self,
        preview_token: str,
        incoming_digest: str,
    ) -> Dict[str, Any]:
        now = time_module.monotonic()
        with self._preview_lock:
            preview = self._preview_tokens.pop(str(preview_token or ""), None)
        if preview is None:
            raise FullDataBackupConflictError(
                "A fresh matching restore preview is required."
            )
        if now > preview["expires_monotonic"]:
            raise FullDataBackupConflictError("Restore preview token has expired.")
        if incoming_digest != preview["incoming_digest"]:
            raise FullDataBackupConflictError(
                "Incoming backup changed after preview."
            )
        return preview

    def _prune_preview_tokens(self, now: float) -> None:
        expired = [
            token
            for token, preview in self._preview_tokens.items()
            if now > preview["expires_monotonic"]
        ]
        for token in expired:
            self._preview_tokens.pop(token, None)

    @staticmethod
    def _state_digest(
        tables: Mapping[str, Any],
        configuration: Mapping[str, Any],
    ) -> str:
        payload = {
            "configuration_values": dict(configuration["values"]),
            "tables": tables,
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _write_recovery_artifact(
        self,
        document: Mapping[str, Any],
        *,
        destination_digest: str,
    ) -> Dict[str, Any]:
        directory = self.recovery_directory
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        filename = (
            f"pp02-full-data-recovery-{timestamp}-"
            f"{destination_digest[:12]}-{secrets.token_hex(4)}.json"
        )
        target = directory / filename
        temporary = directory / f".{filename}.{os.getpid()}.tmp"
        serialized = json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        try:
            descriptor = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file_obj:
                file_obj.write(serialized)
                file_obj.write("\n")
                file_obj.flush()
                os.fsync(file_obj.fileno())
            durable_replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()
        return {
            "directory": str(directory),
            "filename": filename,
            "path": str(target),
            "digest": document["integrity"]["value"],
            "destination_digest": destination_digest,
        }

    def _replace_configuration(
        self,
        configuration: Mapping[str, Any],
        *,
        config_version: str,
    ):
        values = dict(configuration["values"])
        return self.config_service.apply_env_subset_atomically(
            expected_version=config_version,
            values=values,
            managed_keys=set(BACKUP_CONFIG_ALLOWLIST),
            reload_now=False,
        )

    def _verify_configuration(self, configuration: Mapping[str, Any]) -> None:
        expected = dict(configuration["values"])
        actual = self.export_configuration_values()
        if actual != expected:
            raise FullDataBackupRestoreError(
                "Restored configuration does not match the validated backup."
            )

    def _replace_tables(self, session, tables: Mapping[str, Any]) -> None:
        for table_name in DERIVED_PORTFOLIO_TABLES:
            session.execute(delete(Base.metadata.tables[table_name]))
        session.execute(delete(Base.metadata.tables["agent_provider_turns"]))
        for table_name in reversed(TABLE_NAMES):
            session.execute(delete(Base.metadata.tables[table_name]))
        session.flush()
        for table_name in TABLE_NAMES:
            rows = [
                self._database_row(table_name, row)
                for row in tables[table_name]
            ]
            if rows:
                session.execute(insert(Base.metadata.tables[table_name]), rows)
        session.flush()

    def _verify_restored_tables(
        self,
        session,
        expected_tables: Mapping[str, Any],
    ) -> Dict[str, Any]:
        actual_tables = {
            table_name: self._read_table(session, table_name)
            for table_name in TABLE_NAMES
        }
        expected_counts = {
            table_name: len(expected_tables[table_name])
            for table_name in TABLE_NAMES
        }
        actual_counts = {
            table_name: len(actual_tables[table_name])
            for table_name in TABLE_NAMES
        }
        if actual_counts != expected_counts:
            raise FullDataBackupRestoreError(
                "Restored table row counts do not match the validated backup."
            )
        expected_digest = self._tables_digest(expected_tables)
        actual_digest = self._tables_digest(actual_tables)
        if actual_digest != expected_digest:
            raise FullDataBackupRestoreError(
                "Restored table digest does not match the validated backup."
            )
        return actual_tables

    @staticmethod
    def _tables_digest(tables: Mapping[str, Any]) -> str:
        raw = json.dumps(
            tables,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def _database_row(
        cls,
        table_name: str,
        row: Mapping[str, Any],
    ) -> Dict[str, Any]:
        converted = dict(row)
        for column_name in DATE_COLUMNS.get(table_name, frozenset()):
            if converted[column_name] is not None:
                converted[column_name] = date.fromisoformat(converted[column_name])
        for column_name in DATETIME_COLUMNS.get(table_name, frozenset()):
            if converted[column_name] is not None:
                normalized = (
                    converted[column_name][:-1] + "+00:00"
                    if converted[column_name].endswith("Z")
                    else converted[column_name]
                )
                converted[column_name] = datetime.fromisoformat(normalized)
        return converted

    def validate_backup(self, backup: Mapping[str, Any]) -> Dict[str, Any]:
        """Fail closed unless every supported section matches this exact v1 contract."""
        try:
            snapshot = json.loads(
                json.dumps(
                    backup,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise FullDataBackupValidationError(
                "Backup must be canonical JSON data."
            ) from exc
        root = self._object(snapshot, "backup")
        self._keys(root, ROOT_KEYS, "backup")
        if root["format"] != BACKUP_FORMAT:
            raise FullDataBackupValidationError("Unsupported complete backup format.")
        if type(root["format_version"]) is not int or root["format_version"] != BACKUP_FORMAT_VERSION:
            raise FullDataBackupValidationError("Unsupported complete backup format version.")
        self._validate_metadata(root["metadata"])
        self._validate_data(root["data"])
        expected_manifest = self._manifest(root["data"])
        self._validate_manifest(root["manifest"])
        if root["manifest"] != expected_manifest:
            raise FullDataBackupValidationError("Backup manifest does not match the exact allow-list.")
        integrity = self._object(root["integrity"], "integrity")
        self._keys(integrity, {"algorithm", "value"}, "integrity")
        if integrity["algorithm"] != "sha256" or not isinstance(integrity["value"], str):
            raise FullDataBackupValidationError("Unsupported backup integrity envelope.")
        expected_checksum = self.canonical_sha256(root)
        if integrity["value"] != expected_checksum:
            raise FullDataBackupValidationError("Backup integrity checksum does not match.")
        return root

    @classmethod
    def canonical_sha256(cls, document: Mapping[str, Any]) -> str:
        """Hash canonical UTF-8 JSON with only ``integrity.value`` omitted."""
        envelope = dict(document)
        integrity = dict(envelope["integrity"])
        integrity.pop("value", None)
        envelope["integrity"] = integrity
        raw = json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _read_table(self, session, table_name: str) -> List[Dict[str, Any]]:
        table = Base.metadata.tables[table_name]
        rows = session.execute(select(table).order_by(table.c.id)).mappings().all()
        return [
            {
                column_name: self._json_value(row[column_name])
                for column_name in TABLE_COLUMN_ALLOWLIST[table_name]
            }
            for row in rows
        ]

    def _read_tables_snapshot(self) -> Dict[str, List[Dict[str, Any]]]:
        """Read every allow-listed table from one explicit database snapshot."""
        session = self.db.get_session()
        try:
            connection = session.connection()
            if getattr(self.db, "_is_sqlite_engine", False):
                connection.exec_driver_sql("BEGIN")
            return {
                table_name: self._read_table(session, table_name)
                for table_name in TABLE_NAMES
            }
        finally:
            session.rollback()
            session.close()

    def _read_sanitized_configuration(self) -> Dict[str, Any]:
        """Read one locked logical config generation through the service boundary."""
        exported = self.config_service.snapshot_non_sensitive_values(
            allowed_keys=set(BACKUP_CONFIG_ALLOWLIST),
        )
        if not isinstance(exported, Mapping):
            raise FullDataBackupValidationError("Configuration export boundary returned an invalid payload.")
        raw_values = exported.get("values")
        if not isinstance(raw_values, Mapping):
            raise FullDataBackupValidationError(
                "Configuration export boundary returned invalid values."
            )
        values: Dict[str, str] = {}
        for raw_key, raw_value in raw_values.items():
            key = str(raw_key).upper()
            if key not in BACKUP_CONFIG_ALLOWLIST or not isinstance(raw_value, str):
                raise FullDataBackupValidationError(
                    "Configuration export boundary returned an invalid allowed value."
                )
            value = raw_value
            self._validate_config_value(value)
            values[key] = value
        try:
            values = self.config_service.normalize_env_subset_values(
                values=values,
                managed_keys=set(BACKUP_CONFIG_ALLOWLIST),
            )
        except Exception as exc:
            raise FullDataBackupValidationError(
                "Configuration export boundary returned noncanonical values."
            ) from exc
        return {
            "config_version": self._plain_scalar(exported.get("config_version"), "config_version"),
            "updated_at": self._plain_scalar(exported.get("updated_at"), "updated_at"),
            "values": {key: values[key] for key in sorted(values)},
        }

    def _manifest(self, data: Mapping[str, Any]) -> Dict[str, Any]:
        tables = data["tables"]
        table_row_counts = {table_name: len(tables[table_name]) for table_name in sorted(TABLE_NAMES)}
        categories = {
            "agent_conversations": self._category("agent_conversations", table_row_counts),
            "analysis": self._category("analysis", table_row_counts),
            "configuration": {
                "status": "supported",
                "row_count": len(data["configuration"]["values"]),
                "tables": ["configuration"],
            },
            "fund": {"status": "not_applicable", "row_count": 0, "tables": []},
            "period_reports": self._category("period_reports", table_row_counts),
            "portfolio_events": self._category("portfolio_events", table_row_counts),
            "structured_user_records": self._category("structured_user_records", table_row_counts),
        }
        return {
            "categories": categories,
            "excluded": list(EXCLUDED_CONTENT),
            "table_row_counts": table_row_counts,
        }

    @staticmethod
    def _category(name: str, table_row_counts: Mapping[str, int]) -> Dict[str, Any]:
        tables = list(TABLE_GROUPS[name])
        return {
            "status": "supported",
            "row_count": sum(table_row_counts[table_name] for table_name in tables),
            "tables": tables,
        }

    def _validate_manifest(self, value: Any) -> None:
        manifest = self._object(value, "manifest")
        self._keys(manifest, {"categories", "excluded", "table_row_counts"}, "manifest")
        categories = self._object(manifest["categories"], "manifest.categories")
        expected_categories = {
            "agent_conversations", "analysis", "configuration", "fund", "period_reports", "portfolio_events",
            "structured_user_records",
        }
        self._keys(categories, expected_categories, "manifest.categories")
        for category_name, category_value in categories.items():
            category = self._object(category_value, f"manifest.categories.{category_name}")
            self._keys(category, {"status", "row_count", "tables"}, f"manifest.categories.{category_name}")
            if not isinstance(category["status"], str):
                raise FullDataBackupValidationError(f"manifest.categories.{category_name}.status is invalid.")
            self._non_negative_integer(
                category["row_count"],
                f"manifest.categories.{category_name}.row_count",
            )
            if not isinstance(category["tables"], list) or not all(
                isinstance(item, str) for item in category["tables"]
            ):
                raise FullDataBackupValidationError(
                    f"manifest.categories.{category_name}.tables must be a string list."
                )
        excluded = manifest["excluded"]
        if not isinstance(excluded, list) or not all(isinstance(item, str) for item in excluded):
            raise FullDataBackupValidationError("manifest.excluded must be a string list.")
        table_counts = self._object(manifest["table_row_counts"], "manifest.table_row_counts")
        self._keys(table_counts, set(TABLE_NAMES), "manifest.table_row_counts")
        for table_name, count in table_counts.items():
            self._non_negative_integer(count, f"manifest.table_row_counts.{table_name}")

    def _validate_metadata(self, value: Any) -> None:
        metadata = self._object(value, "metadata")
        self._keys(
            metadata,
            {"application_version", "created_at", "database_schema_version", "project_id", "project_name"},
            "metadata",
        )
        if metadata["project_id"] != PROJECT_ID or metadata["project_name"] != PROJECT_NAME:
            raise FullDataBackupValidationError("Backup is not a PP02 complete data backup.")
        if metadata["application_version"] != self.application_version:
            raise FullDataBackupValidationError("Unsupported application version.")
        if metadata["database_schema_version"] != CURRENT_SCHEMA_VERSION:
            raise FullDataBackupValidationError("Unsupported database schema version.")
        self._validate_timestamp(metadata["created_at"], "metadata.created_at")

    def _validate_data(self, value: Any) -> None:
        data = self._object(value, "data")
        self._keys(data, {"configuration", "tables"}, "data")
        self._validate_configuration(data["configuration"])
        tables = self._object(data["tables"], "data.tables")
        self._keys(tables, set(TABLE_NAMES), "data.tables")
        for table_name in TABLE_NAMES:
            rows = tables[table_name]
            if not isinstance(rows, list):
                raise FullDataBackupValidationError(f"data.tables.{table_name} must be a list.")
            expected_columns = set(TABLE_COLUMN_ALLOWLIST[table_name])
            prior_id = 0
            for row in rows:
                row_object = self._object(row, f"data.tables.{table_name} row")
                self._keys(row_object, expected_columns, f"data.tables.{table_name} row")
                row_id = row_object.get("id")
                if type(row_id) is not int or row_id <= prior_id:
                    raise FullDataBackupValidationError(
                        f"data.tables.{table_name} rows must be strictly sorted by primary id."
                    )
                prior_id = row_id
                self._validate_row_values(table_name, row_object)
        self._validate_unique_identities(tables)
        self._validate_references(tables)
        self._validate_cross_field_semantics(tables)

    @classmethod
    def _validate_row_values(cls, table_name: str, row: Mapping[str, Any]) -> None:
        for column_name, value in row.items():
            if value is None:
                if column_name in REQUIRED_COLUMNS[table_name]:
                    raise FullDataBackupValidationError(f"{table_name}.{column_name} is required.")
                continue
            if column_name in DATE_COLUMNS.get(table_name, frozenset()):
                if not isinstance(value, str):
                    raise FullDataBackupValidationError(f"{table_name}.{column_name} must be an ISO date.")
                try:
                    date.fromisoformat(value)
                except ValueError as exc:
                    raise FullDataBackupValidationError(
                        f"{table_name}.{column_name} must be an ISO date."
                    ) from exc
            elif column_name in DATETIME_COLUMNS.get(table_name, frozenset()):
                cls._validate_timestamp(value, f"{table_name}.{column_name}")
            elif column_name in INTEGER_COLUMNS.get(table_name, frozenset()):
                if type(value) is not int:
                    raise FullDataBackupValidationError(f"{table_name}.{column_name} must be an integer.")
            elif column_name in FLOAT_COLUMNS.get(table_name, frozenset()):
                cls._finite_number(value, f"{table_name}.{column_name}")
            elif column_name in BOOLEAN_COLUMNS.get(table_name, frozenset()):
                if not isinstance(value, bool):
                    raise FullDataBackupValidationError(f"{table_name}.{column_name} must be a boolean.")
            elif not isinstance(value, str):
                raise FullDataBackupValidationError(f"{table_name}.{column_name} must be a string.")
            cls._validate_enum_value(table_name, column_name, value)
            cls._validate_numeric_semantics(table_name, column_name, value)
            cls._validate_json_column(table_name, column_name, value)
            cls._validate_no_embedded_secrets(value, f"{table_name}.{column_name}")

    @staticmethod
    def _validate_enum_value(table_name: str, column_name: str, value: Any) -> None:
        allowed = ENUM_COLUMNS.get(table_name, {}).get(column_name)
        if allowed is not None and value not in allowed:
            raise FullDataBackupValidationError(
                f"{table_name}.{column_name} is outside the supported version-1 domain."
            )

    @classmethod
    def _validate_numeric_semantics(cls, table_name: str, column_name: str, value: Any) -> None:
        if column_name in POSITIVE_NUMERIC_COLUMNS.get(table_name, frozenset()):
            number = cls._finite_number(value, f"{table_name}.{column_name}")
            if number <= 0:
                raise FullDataBackupValidationError(f"{table_name}.{column_name} must be positive.")
        if column_name in NON_NEGATIVE_NUMERIC_COLUMNS.get(table_name, frozenset()):
            number = cls._finite_number(value, f"{table_name}.{column_name}")
            if number < 0:
                raise FullDataBackupValidationError(f"{table_name}.{column_name} must be non-negative.")
        bounds = RANGED_NUMERIC_COLUMNS.get(table_name, {}).get(column_name)
        if bounds is not None:
            number = cls._finite_number(value, f"{table_name}.{column_name}")
            if not bounds[0] <= number <= bounds[1]:
                raise FullDataBackupValidationError(
                    f"{table_name}.{column_name} is outside its supported numeric range."
                )

    @classmethod
    def _validate_json_column(cls, table_name: str, column_name: str, value: Any) -> None:
        expected_type = None
        if column_name in JSON_OBJECT_COLUMNS.get(table_name, frozenset()):
            expected_type = dict
        elif column_name in JSON_ARRAY_COLUMNS.get(table_name, frozenset()):
            expected_type = list
        elif column_name not in JSON_VALUE_COLUMNS.get(table_name, frozenset()):
            return
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise FullDataBackupValidationError(f"{table_name}.{column_name} must contain valid JSON.") from exc
        if expected_type is not None and not isinstance(parsed, expected_type):
            raise FullDataBackupValidationError(
                f"{table_name}.{column_name} has the wrong JSON container type."
            )
        if table_name == "period_reports" and column_name == "source_record_ids_json":
            if any(type(item) is not int or item <= 0 for item in parsed) or parsed != sorted(set(parsed)):
                raise FullDataBackupValidationError(
                    "period_reports.source_record_ids_json must be a sorted unique list of positive integers."
                )

    @classmethod
    def _validate_no_embedded_secrets(cls, value: Any, label: str) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if cls._is_sensitive_embedded_key(key):
                    raise FullDataBackupValidationError(f"{label} contains a secret-classified key.")
                cls._validate_no_embedded_secrets(nested, f"{label}.{key}")
            return
        if isinstance(value, list):
            for index, nested in enumerate(value):
                cls._validate_no_embedded_secrets(nested, f"{label}[{index}]")
            return
        if not isinstance(value, str):
            return
        if _HIGH_CONFIDENCE_SECRET_VALUE_RE.search(value):
            raise FullDataBackupValidationError(f"{label} contains credential-like material.")
        if _HIGH_CONFIDENCE_TOKEN_FAMILY_RE.search(value):
            raise FullDataBackupValidationError(f"{label} contains credential-like material.")
        stripped = value.strip()
        if not stripped.startswith(("{", "[")):
            return
        try:
            parsed = json.loads(stripped)
        except (TypeError, ValueError, json.JSONDecodeError):
            return
        cls._validate_no_embedded_secrets(parsed, label)

    @staticmethod
    def _is_sensitive_embedded_key(value: Any) -> bool:
        normalized = re.sub(r"[^A-Z0-9]+", "_", str(value or "").strip().upper()).strip("_")
        if normalized in REGISTERED_CONFIG_KEYS and is_sensitive_config_key(normalized):
            return True
        if any(
            normalized == suffix or normalized.endswith(f"_{suffix}")
            for suffix in _SAFE_EMBEDDED_METADATA_SUFFIXES
        ):
            return False
        segments = normalized.split("_")
        return (
            normalized in _SENSITIVE_EMBEDDED_KEYS
            or bool(_SENSITIVE_EMBEDDED_KEY_SEGMENTS.intersection(segments))
            or segments[-2:] in (["API", "KEY"], ["PRIVATE", "KEY"])
        )

    @staticmethod
    def _validate_unique_identities(tables: Mapping[str, Any]) -> None:
        for table_name, identities in UNIQUE_IDENTITIES.items():
            for columns in identities:
                seen = set()
                for row in tables[table_name]:
                    identity = tuple(row[column] for column in columns)
                    if any(item is None for item in identity):
                        continue
                    if identity in seen:
                        raise FullDataBackupValidationError(
                            f"{table_name} contains a duplicate identity for {columns}."
                        )
                    seen.add(identity)

    @staticmethod
    def _validate_references(tables: Mapping[str, Any]) -> None:
        table_ids = {
            table_name: {row["id"] for row in tables[table_name]}
            for table_name in TABLE_NAMES
        }
        for table_name, column_name, target_table in REFERENCE_COLUMNS:
            for row in tables[table_name]:
                reference = row[column_name]
                if reference is not None and reference not in table_ids[target_table]:
                    raise FullDataBackupValidationError(
                        f"{table_name}.{column_name} references a missing {target_table} row."
                    )

    @classmethod
    def _validate_cross_field_semantics(cls, tables: Mapping[str, Any]) -> None:
        conversation_messages = {
            row["id"]: row for row in tables["conversation_messages"]
        }
        for summary in tables["conversation_summaries"]:
            covered_message_id = summary["covered_message_id"]
            if covered_message_id <= 0:
                continue
            covered_message = conversation_messages.get(covered_message_id)
            if (
                covered_message is None
                or covered_message["session_id"] != summary["session_id"]
            ):
                raise FullDataBackupValidationError(
                    "conversation_summaries.covered_message_id must reference an "
                    "included message in the same session."
                )
        for row in tables["period_reports"]:
            cls._validate_period_report_content(row)
            if date.fromisoformat(row["start_date"]) > date.fromisoformat(row["end_date"]):
                raise FullDataBackupValidationError("period_reports.start_date must not follow end_date.")
        for row in tables["portfolio_corporate_actions"]:
            if row["action_type"] == "cash_dividend":
                if row["cash_dividend_per_share"] is None:
                    raise FullDataBackupValidationError(
                        "portfolio_corporate_actions.cash_dividend_per_share is required for cash dividends."
                    )
            elif row["split_ratio"] is None or cls._finite_number(
                row["split_ratio"], "portfolio_corporate_actions.split_ratio"
            ) <= 0:
                raise FullDataBackupValidationError(
                    "portfolio_corporate_actions.split_ratio must be positive for split adjustments."
                )
        for row in tables["alert_cooldowns"]:
            if row["last_triggered_at"] is not None and row["cooldown_until"] is not None:
                if cls._parse_timestamp(row["last_triggered_at"]) > cls._parse_timestamp(row["cooldown_until"]):
                    raise FullDataBackupValidationError(
                        "alert_cooldowns.last_triggered_at must not follow cooldown_until."
                    )
        for row in tables["decision_signals"]:
            if (
                row["entry_low"] is not None
                and row["entry_high"] is not None
                and cls._finite_number(row["entry_low"], "decision_signals.entry_low")
                > cls._finite_number(row["entry_high"], "decision_signals.entry_high")
            ):
                raise FullDataBackupValidationError(
                    "decision_signals.entry_low must not exceed entry_high."
                )

    @classmethod
    def _validate_period_report_content(cls, row: Mapping[str, Any]) -> None:
        try:
            from api.v1.schemas.period_report import PeriodReportResponse

            PeriodReportResponse.model_rebuild(force=True)
            content = json.loads(row["content_json"])
            payload = PeriodReportResponse.model_validate(content, strict=True)
            values = payload.model_dump()
            if content != values:
                raise ValueError("period report content is not a closed canonical shape")
        except Exception as exc:
            raise FullDataBackupValidationError(
                "period_reports.content_json must contain a complete period report."
            ) from exc

        try:
            report_generated_at = cls._require_period_timestamp(
                values["generated_at"],
                "period report generated_at",
            )
            row_generated_at = cls._require_period_timestamp(
                row["generated_at"],
                "period report row generated_at",
            )
        except FullDataBackupValidationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise FullDataBackupValidationError(
                "period report timestamps are invalid."
            ) from exc
        scalar_matches = (
            values["report_id"] == row["id"],
            values["status"] == row["status"],
            values["period"] == row["period"],
            values["report_kind"] == row["report_kind"],
            values["start_date"] == row["start_date"],
            values["end_date"] == row["end_date"],
            # Legacy SQLite rows persist naive local wall time while the
            # canonical payload carries the same wall value with an offset.
            # Keep this identity comparison wall-based for existing databases;
            # all source/snapshot ordering below is normalized to UTC.
            cls._parse_wall_timestamp(values["generated_at"])
            == cls._parse_wall_timestamp(row["generated_at"]),
        )
        if not all(scalar_matches):
            raise FullDataBackupValidationError(
                "period_reports row identity does not match its complete content."
            )
        current_source_ids = cls._validate_period_current_sources(
            values,
            report_generated_at=report_generated_at,
        )
        matched_source_ids: set[int] = set()
        matched = values["matched_outlook"]
        if matched is not None:
            if values["period"] != "previous_week" or values["report_kind"] != "historical":
                raise FullDataBackupValidationError(
                    "matched_outlook is only valid on a previous-week historical report."
                )
            matched_source_ids = cls._validate_period_outlook_snapshot(
                matched,
                row=values,
                label="matched_outlook",
                report_generated_at=report_generated_at,
                require_same_generated_at=False,
            )
            if current_source_ids.intersection(matched_source_ids):
                raise FullDataBackupValidationError(
                    "period_reports source identities must be globally unique."
                )
        stored_source_ids = json.loads(row["source_record_ids_json"])
        if (
            sorted(current_source_ids | matched_source_ids) != stored_source_ids
            or values["source_record_count"] != len(current_source_ids)
        ):
            raise FullDataBackupValidationError(
                "period_reports source identity does not match its complete content."
            )

    @classmethod
    def _validate_period_current_sources(
        cls,
        report: Mapping[str, Any],
        *,
        report_generated_at: datetime,
    ) -> set[int]:
        current_ids: set[int] = set()
        source_occurrences = 0
        start_date = date.fromisoformat(report["start_date"])
        end_date = date.fromisoformat(report["end_date"])
        for collection_name in ("stock_summaries", "etf_summaries"):
            expected_asset_type = "stock" if collection_name == "stock_summaries" else "etf"
            for summary in report[collection_name]:
                source_ids = summary["source_record_ids"]
                if (
                    summary["asset_type"] != expected_asset_type
                    or
                    source_ids != list(dict.fromkeys(source_ids))
                    or any(type(item) is not int or item <= 0 for item in source_ids)
                    or summary["record_count"] != len(source_ids)
                    or summary["latest_record_id"] not in source_ids
                    or sum(summary["direction_counts"].values())
                    != summary["record_count"]
                ):
                    raise FullDataBackupValidationError(
                        f"{collection_name} source/count/latest semantics are invalid."
                    )
                if current_ids.intersection(source_ids):
                    raise FullDataBackupValidationError(
                        "Period report source identities must be globally unique."
                    )
                if summary["latest_created_at"] is not None:
                    created_at = cls._require_period_timestamp(
                        summary["latest_created_at"],
                        f"{collection_name}.latest_created_at",
                    )
                    if (
                        created_at.date() < start_date
                        or created_at.date() > end_date
                        or created_at > report_generated_at
                    ):
                        raise FullDataBackupValidationError(
                            f"{collection_name} source time is outside the report window."
                        )
                current_ids.update(source_ids)
                source_occurrences += len(source_ids)
        for review in report["market_reviews"]:
            record_id = review["record_id"]
            if record_id in current_ids:
                raise FullDataBackupValidationError(
                    "Period report source identities must be globally unique."
                )
            current_ids.add(record_id)
            source_occurrences += 1
            if review["created_at"] is not None:
                created_at = cls._require_period_timestamp(
                    review["created_at"],
                    "market_reviews.created_at",
                )
                if (
                    created_at.date() < start_date
                    or created_at.date() > end_date
                    or created_at > report_generated_at
                ):
                    raise FullDataBackupValidationError(
                        "market review source time is outside the report window."
                    )

        outlook = report["outlook"]
        if report["report_kind"] == "outlook":
            if report["period"] != "next_week" or outlook is None:
                raise FullDataBackupValidationError(
                    "Outlook reports require one next-week outlook snapshot."
                )
            if report["stock_summaries"] or report["etf_summaries"] or report["market_reviews"]:
                raise FullDataBackupValidationError(
                    "Outlook reports cannot contain historical summary sections."
                )
            if report["matched_outlook"] is not None:
                raise FullDataBackupValidationError(
                    "Outlook reports cannot contain matched_outlook."
                )
            current_ids = cls._validate_period_outlook_snapshot(
                outlook,
                row=report,
                label="outlook",
                report_generated_at=report_generated_at,
                require_same_generated_at=True,
            )
            if report["status"] != outlook["status"]:
                raise FullDataBackupValidationError(
                    "Outlook report status must match its snapshot."
                )
        elif outlook is not None:
            raise FullDataBackupValidationError(
                "Historical reports cannot contain outlook."
            )
        elif report["source_record_count"] != source_occurrences:
            raise FullDataBackupValidationError(
                "Historical source count must match formal generator records."
            )
        return current_ids

    @classmethod
    def _validate_period_outlook_snapshot(
        cls,
        snapshot: Mapping[str, Any],
        *,
        row: Mapping[str, Any],
        label: str,
        report_generated_at: datetime,
        require_same_generated_at: bool,
    ) -> set[int]:
        target = snapshot["target_period"]
        if (
            target["start_date"] != row["start_date"]
            or target["end_date"] != row["end_date"]
        ):
            raise FullDataBackupValidationError(
                f"{label} target window must match the report row."
            )
        generated_at = cls._require_period_timestamp(
            snapshot["generated_at"],
            f"{label}.generated_at",
        )
        if require_same_generated_at:
            if generated_at != report_generated_at:
                raise FullDataBackupValidationError(
                    f"{label}.generated_at must match the report generated_at."
                )
        elif generated_at > report_generated_at:
            raise FullDataBackupValidationError(
                f"{label}.generated_at cannot follow the report generated_at."
            )
        parsed_optional_times: Dict[str, Optional[datetime]] = {}
        for optional_timestamp in ("snapshot_created_at", "data_as_of"):
            value = snapshot[optional_timestamp]
            parsed_optional_times[optional_timestamp] = None
            if value is not None:
                parsed = cls._require_period_timestamp(
                    value,
                    f"{label}.{optional_timestamp}",
                )
                if parsed > generated_at:
                    raise FullDataBackupValidationError(
                        f"{label}.{optional_timestamp} cannot follow its generated_at."
                    )
                parsed_optional_times[optional_timestamp] = parsed

        source_ids = snapshot["source_record_ids"]
        if (
            source_ids != sorted(set(source_ids))
            or any(type(item) is not int or item <= 0 for item in source_ids)
            or snapshot["source_record_count"] != len(source_ids)
        ):
            raise FullDataBackupValidationError(
                f"{label} source IDs and count are inconsistent."
            )
        nested_ids: set[int] = set()
        source_occurrences = 0
        outlook_items: List[Mapping[str, Any]] = []
        for collection_name in ("stocks", "etfs"):
            expected_asset_type = "stock" if collection_name == "stocks" else "etf"
            for item in snapshot[collection_name]:
                outlook_items.append(item)
                item_ids = item["source_record_ids"]
                if (
                    item["asset_type"] != expected_asset_type
                    or
                    item_ids != list(dict.fromkeys(item_ids))
                    or any(type(value) is not int or value <= 0 for value in item_ids)
                    or item["source_record_count"] != len(item_ids)
                ):
                    raise FullDataBackupValidationError(
                        f"{label}.{collection_name} source IDs and count are inconsistent."
                    )
                if nested_ids.intersection(item_ids):
                    raise FullDataBackupValidationError(
                        f"{label} source identities must be globally unique."
                    )
                if item["data_as_of"] is not None:
                    item_time = cls._require_period_timestamp(
                        item["data_as_of"],
                        f"{label}.{collection_name}.data_as_of",
                    )
                    if item_time > generated_at or (
                        parsed_optional_times["snapshot_created_at"] is not None
                        and item_time > parsed_optional_times["snapshot_created_at"]
                    ):
                        raise FullDataBackupValidationError(
                            f"{label}.{collection_name}.data_as_of is too recent."
                        )
                nested_ids.update(item_ids)
                source_occurrences += len(item_ids)
        for signal in snapshot["market_signals"]:
            record_id = signal["record_id"]
            if record_id in nested_ids:
                raise FullDataBackupValidationError(
                    f"{label} source identities must be globally unique."
                )
            nested_ids.add(record_id)
            source_occurrences += 1
            if signal["created_at"] is not None:
                signal_time = cls._require_period_timestamp(
                    signal["created_at"],
                    f"{label}.market_signals.created_at",
                )
                if signal_time > generated_at or (
                    parsed_optional_times["snapshot_created_at"] is not None
                    and signal_time > parsed_optional_times["snapshot_created_at"]
                ):
                    raise FullDataBackupValidationError(
                        f"{label}.market_signals.created_at is too recent."
                    )
        if nested_ids != set(source_ids) or source_occurrences != len(source_ids):
            raise FullDataBackupValidationError(
                f"{label} nested source IDs must match its source_record_ids."
            )
        expected_ready = bool(outlook_items)
        if expected_ready:
            tendencies = {"看多": 0, "中性": 0, "看空": 0}
            for item in outlook_items:
                tendencies[item["tendency"]] += 1
            maximum = max(tendencies.values())
            leaders = [
                tendency
                for tendency, count in tendencies.items()
                if count == maximum
            ]
            expected_tendency = leaders[0] if len(leaders) == 1 else "中性"
            if (
                snapshot["status"] != "ready"
                or snapshot["message"] is not None
                or snapshot["overall_tendency"] != expected_tendency
            ):
                raise FullDataBackupValidationError(
                    f"{label} ready semantics do not match the formal generator."
                )
        elif (
            snapshot["status"] != "insufficient_data"
            or snapshot["message"] != INSUFFICIENT_OUTLOOK_MESSAGE
            or snapshot["overall_tendency"] is not None
        ):
            raise FullDataBackupValidationError(
                f"{label} insufficient-data semantics do not match the formal generator."
            )
        return set(source_ids)

    @classmethod
    def _require_period_timestamp(cls, value: Any, label: str) -> datetime:
        if not isinstance(value, str) or "T" not in value:
            raise FullDataBackupValidationError(f"{label} must be an ISO timestamp.")
        try:
            return cls._parse_timestamp(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise FullDataBackupValidationError(
                f"{label} must be an ISO timestamp."
            ) from exc

    @staticmethod
    def _validate_timestamp(value: Any, label: str) -> None:
        if not isinstance(value, str) or "T" not in value:
            raise FullDataBackupValidationError(f"{label} must be an ISO timestamp.")
        try:
            FullDataBackupService._parse_timestamp(value)
        except ValueError as exc:
            raise FullDataBackupValidationError(f"{label} must be an ISO timestamp.") from exc

    @staticmethod
    def _parse_wall_timestamp(value: str) -> datetime:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        return datetime.fromisoformat(normalized).replace(tzinfo=None)

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _finite_number(value: Any, label: str) -> float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise FullDataBackupValidationError(f"{label} must be a finite number.")
        try:
            number = float(value)
        except (OverflowError, TypeError, ValueError) as exc:
            raise FullDataBackupValidationError(f"{label} must be a finite number.") from exc
        if not math.isfinite(number):
            raise FullDataBackupValidationError(f"{label} must be a finite number.")
        return number

    @staticmethod
    def _non_negative_integer(value: Any, label: str) -> int:
        if type(value) is not int or value < 0:
            raise FullDataBackupValidationError(f"{label} must be a non-negative integer.")
        return value

    def _validate_configuration(self, value: Any) -> None:
        configuration = self._object(value, "data.configuration")
        self._keys(configuration, {"config_version", "updated_at", "values"}, "data.configuration")
        if not isinstance(configuration["config_version"], (str, type(None))):
            raise FullDataBackupValidationError("Configuration version is invalid.")
        if not isinstance(configuration["updated_at"], (str, type(None))):
            raise FullDataBackupValidationError("Configuration update time is invalid.")
        values = self._object(configuration["values"], "data.configuration.values")
        for key, item in values.items():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key):
                raise FullDataBackupValidationError("Configuration key is invalid.")
            if key not in BACKUP_CONFIG_ALLOWLIST or is_sensitive_config_key(key):
                raise FullDataBackupValidationError(
                    "Configuration key is not permitted by the complete-backup registry policy."
                )
            if not isinstance(item, str):
                raise FullDataBackupValidationError("Configuration value is invalid.")
            self._validate_config_value(item)
        try:
            canonical = self.config_service.normalize_env_subset_values(
                values=values,
                managed_keys=set(BACKUP_CONFIG_ALLOWLIST),
            )
        except Exception as exc:
            raise FullDataBackupValidationError(
                "Configuration values cannot be normalized safely."
            ) from exc
        if canonical != values:
            raise FullDataBackupValidationError(
                "Configuration values must use their canonical storage representation."
            )

    @staticmethod
    def _validate_config_value(value: str) -> None:
        """Reject URL userinfo without ever interpolating the value into an error."""
        try:
            parsed = urlsplit(value)
            contains_userinfo = bool(parsed.netloc) and parsed.username is not None
        except (TypeError, ValueError):
            contains_userinfo = False
        if contains_userinfo:
            raise FullDataBackupValidationError(
                "Configuration value contains credential-bearing URL userinfo."
            )
        FullDataBackupService._validate_no_embedded_secrets(
            value,
            "configuration value",
        )

    @staticmethod
    def _object(value: Any, label: str) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            raise FullDataBackupValidationError(f"{label} must be an object.")
        return dict(value)

    @staticmethod
    def _keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
        expected_set = set(expected)
        actual = set(value)
        if actual != expected_set:
            raise FullDataBackupValidationError(
                f"{label} fields do not match the backup contract; "
                f"missing={sorted(expected_set - actual)}, extra={sorted(actual - expected_set)}."
            )

    @staticmethod
    def _plain_scalar(value: Any, label: str) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise FullDataBackupValidationError(f"Configuration {label} is invalid.")
        return value

    @staticmethod
    def _json_value(value: Any) -> Any:
        if isinstance(value, datetime):
            return FullDataBackupService._timestamp(value)
        if isinstance(value, (date, time)):
            return value.isoformat()
        if isinstance(value, float) and not math.isfinite(value):
            raise FullDataBackupValidationError("Formal backup values must be finite JSON numbers.")
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        raise FullDataBackupValidationError(
            f"Unsupported value type in formal backup data: {type(value).__name__}."
        )

    @staticmethod
    def _timestamp(value: datetime) -> str:
        if value.tzinfo is not None and value.utcoffset() is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        return value.isoformat()
