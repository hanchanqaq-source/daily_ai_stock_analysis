# -*- coding: utf-8 -*-
"""Fail-before-side-effect contract for the packaged Desktop backend."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "src" / "core" / "desktop_launch_contract.py"


def _contract_module():
    assert CONTRACT_PATH.is_file(), "desktop launch contract module must exist"
    spec = importlib.util.spec_from_file_location("desktop_launch_contract_test_target", CONTRACT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _args(**overrides) -> SimpleNamespace:
    values = {
        "debug": False,
        "dry_run": False,
        "stocks": None,
        "portfolio": None,
        "no_notify": False,
        "check_notify": False,
        "single_notify": False,
        "workers": None,
        "schedule": False,
        "no_run_immediately": False,
        "market_review": False,
        "no_market_review": False,
        "force_run": False,
        "webui": False,
        "webui_only": False,
        "serve": False,
        "serve_only": True,
        "host": "127.0.0.1",
        "port": 8000,
        "no_context_snapshot": False,
        "backtest": False,
        "backtest_code": None,
        "backtest_days": None,
        "backtest_force": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize("host", ["127.0.0.1", "127.20.30.40", "localhost", "::1", "[::1]"])
def test_valid_desktop_serve_only_contract_passes(host: str) -> None:
    contract = _contract_module()
    contract.validate_desktop_launch_contract(
        _args(host=host),
        {"DSA_DESKTOP_MODE": "true"},
    )


def test_non_desktop_cli_is_unchanged() -> None:
    contract = _contract_module()
    contract.validate_desktop_launch_contract(
        _args(serve_only=False, market_review=True),
        {},
    )


@pytest.mark.parametrize(
    ("overrides", "reason_code"),
    [
        ({"serve_only": False}, "missing_serve_only"),
        ({"host": None}, "host_missing"),
        ({"host": "0.0.0.0"}, "host_not_loopback"),
        ({"host": "192.168.1.8"}, "host_not_loopback"),
        ({"port": None}, "port_invalid"),
        ({"port": 0}, "port_invalid"),
        ({"port": 65536}, "port_invalid"),
        ({"market_review": True}, "conflicting_mode"),
        ({"schedule": True}, "conflicting_mode"),
        ({"stocks": "600519"}, "conflicting_mode"),
        ({"portfolio": "futu"}, "conflicting_mode"),
        ({"backtest": True}, "conflicting_mode"),
        ({"serve": True}, "conflicting_mode"),
        ({"webui": True}, "conflicting_mode"),
        ({"webui_only": True}, "conflicting_mode"),
        ({"check_notify": True}, "conflicting_mode"),
    ],
)
def test_invalid_desktop_contract_is_rejected(
    overrides: dict[str, object],
    reason_code: str,
) -> None:
    contract = _contract_module()
    with pytest.raises(contract.DesktopLaunchContractError) as caught:
        contract.validate_desktop_launch_contract(
            _args(**overrides),
            {"DSA_DESKTOP_MODE": "desktop"},
        )

    assert caught.value.reason_code == reason_code


def test_rejection_marker_is_bounded_and_contains_no_argument_values() -> None:
    contract = _contract_module()
    invalid_args = _args(serve_only=False, market_review=True)
    stderr = io.StringIO()

    exit_code = contract.enforce_desktop_launch_contract(
        invalid_args,
        {"DSA_DESKTOP_MODE": "true", "SECRET": "must-not-render"},
        stderr=stderr,
    )

    assert exit_code == 2
    assert stderr.getvalue() == (
        "PP02_DESKTOP_LAUNCH_CONTRACT_REJECTED reason=missing_serve_only\n"
    )
    assert "must-not-render" not in stderr.getvalue()


def test_main_enforces_desktop_contract_before_logging_database_or_config() -> None:
    source = (REPO_ROOT / "main.py").read_text(encoding="utf-8")

    parse_index = source.index("args = parse_arguments()", source.index("def main()"))
    contract_index = source.index(
        "enforce_desktop_launch_contract(",
        parse_index,
    )
    logging_index = source.index("_setup_bootstrap_logging", parse_index)
    database_index = source.index("DatabaseManager.get_instance()", parse_index)
    config_index = source.index("config = get_config()", parse_index)

    assert parse_index < contract_index < logging_index
    assert contract_index < database_index
    assert contract_index < config_index
