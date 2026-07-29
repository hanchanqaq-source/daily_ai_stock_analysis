# -*- coding: utf-8 -*-
"""PP02 R3.2 safety-default contract tests."""

import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import yaml

from tests.litellm_stub import ensure_litellm_stub

ensure_litellm_stub()

import main
from src.config import Config
from src.core.config_registry import build_schema_response, get_field_definition
from src.services.runtime_scheduler import RuntimeSchedulerService


def _analysis_args(**overrides):
    defaults = {
        "portfolio": None,
        "single_notify": False,
        "no_market_review": True,
        "no_context_snapshot": False,
        "workers": 1,
        "dry_run": False,
        "no_notify": False,
        "force_run": True,
        "schedule": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _analysis_config(*, auto_notification_enabled: bool, market_review_enabled: bool = False):
    return SimpleNamespace(
        auto_notification_enabled=auto_notification_enabled,
        market_review_enabled=market_review_enabled,
        market_review_region="cn",
        daily_market_context_enabled=False,
        trading_day_check_enabled=False,
        single_stock_notify=False,
        merge_email_notification=False,
        analysis_delay=0,
        report_type="simple",
        stock_list=["600519"],
        database_path=":memory:",
        refresh_stock_list=MagicMock(),
    )


@patch("src.config.setup_env")
@patch.object(Config, "_parse_litellm_yaml", return_value=[])
def test_auto_notification_config_defaults_off_and_requires_explicit_opt_in(
    _mock_parse_litellm_yaml,
    _mock_setup_env,
):
    with patch.dict(os.environ, {"STOCK_LIST": "600519"}, clear=True):
        default_config = Config._load_from_env()
    with patch.dict(
        os.environ,
        {"STOCK_LIST": "600519", "AUTO_NOTIFICATION_ENABLED": "true"},
        clear=True,
    ):
        enabled_config = Config._load_from_env()

    assert default_config.auto_notification_enabled is False
    assert enabled_config.auto_notification_enabled is True


def test_auto_notification_setting_is_a_visible_editable_off_by_default_switch():
    field = get_field_definition("AUTO_NOTIFICATION_ENABLED")

    assert field["category"] == "notification"
    assert field["data_type"] == "boolean"
    assert field["ui_control"] == "switch"
    assert field["is_sensitive"] is False
    assert field["is_editable"] is True
    assert field["default_value"] == "false"

    schema = build_schema_response()
    notification = next(
        category for category in schema["categories"]
        if category["category"] == "notification"
    )
    assert "AUTO_NOTIFICATION_ENABLED" in {
        item["key"] for item in notification["fields"]
    }


def test_daily_analysis_workflow_is_manual_only():
    workflow_path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "00-daily-analysis.yml"
    )
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    triggers = workflow["on"]

    assert "workflow_dispatch" in triggers
    assert "schedule" not in triggers


def test_full_analysis_requires_notification_opt_in_for_stock_results():
    args = _analysis_args()
    config = _analysis_config(auto_notification_enabled=False)
    pipeline = MagicMock()
    pipeline.run.return_value = []

    with (
        patch.object(main, "_refresh_stock_index_cache_for_analysis"),
        patch.object(
            main,
            "_compute_trading_day_filter",
            return_value=(["600519"], None, False),
        ),
        patch("src.core.pipeline.StockAnalysisPipeline", return_value=pipeline),
        patch.object(main, "_run_auto_backtest"),
    ):
        assert main.run_full_analysis(config, args, ["600519"]) is True

    assert pipeline.run.call_args.kwargs["send_notification"] is False


def test_full_analysis_requires_notification_opt_in_for_market_review():
    args = _analysis_args(no_market_review=False)
    config = _analysis_config(
        auto_notification_enabled=False,
        market_review_enabled=True,
    )
    pipeline = MagicMock()
    pipeline.run.return_value = []

    with (
        patch.object(main, "_refresh_stock_index_cache_for_analysis"),
        patch.object(
            main,
            "_compute_trading_day_filter",
            return_value=([], "cn", False),
        ),
        patch("src.core.pipeline.StockAnalysisPipeline", return_value=pipeline),
        patch.object(
            main,
            "_run_market_review_with_shared_lock",
            return_value=None,
        ) as run_market_review,
        patch.object(main, "_run_auto_backtest"),
    ):
        assert main.run_full_analysis(config, args, []) is True

    assert run_market_review.call_args.kwargs["send_notification"] is False


def test_runtime_scheduler_cannot_bypass_auto_notification_master_switch():
    config = SimpleNamespace(auto_notification_enabled=False)
    runner = MagicMock(return_value=True)
    service = RuntimeSchedulerService(
        config_provider=lambda: config,
        task_runner=runner,
        owns_schedule=True,
    )

    with patch.object(service, "_reload_config", return_value=config):
        service._run_analysis_locked(None)

    schedule_args = runner.call_args.args[1]
    assert schedule_args.no_notify is True


def test_notification_opt_in_allows_automatic_delivery():
    args = _analysis_args()
    config = _analysis_config(auto_notification_enabled=True)
    pipeline = MagicMock()
    pipeline.run.return_value = []

    with (
        patch.object(main, "_refresh_stock_index_cache_for_analysis"),
        patch.object(
            main,
            "_compute_trading_day_filter",
            return_value=(["600519"], None, False),
        ),
        patch("src.core.pipeline.StockAnalysisPipeline", return_value=pipeline),
        patch.object(main, "_run_auto_backtest"),
    ):
        assert main.run_full_analysis(config, args, ["600519"]) is True

    assert pipeline.run.call_args.kwargs["send_notification"] is True
