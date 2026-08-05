# -*- coding: utf-8 -*-
"""Regression coverage for bounded FastAPI background startup waiting."""

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.core.api_server_startup import wait_for_api_server_startup


REPO_ROOT = Path(__file__).resolve().parents[1]


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class _NeverReadyServer:
    started = False


class _LiveThread:
    @staticmethod
    def is_alive() -> bool:
        return True


def _module(name: str, **attributes: object) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_main_with_lightweight_import_boundaries():
    """Load the real main module while replacing unrelated heavy imports."""

    class _Config:
        pass

    stub_modules = {
        "dotenv": _module(
            "dotenv",
            dotenv_values=lambda *_args, **_kwargs: {},
        ),
        "src.config": _module(
            "src.config",
            setup_env=lambda: None,
            Config=_Config,
            get_config=lambda: None,
            should_send_automatic_notification=lambda *_args, **_kwargs: False,
        ),
        "src.webui_frontend": _module(
            "src.webui_frontend",
            prepare_webui_frontend_assets=lambda: True,
        ),
        "src.logging_config": _module(
            "src.logging_config",
            setup_logging=lambda *_args, **_kwargs: None,
        ),
        "src.brokers": _module("src.brokers"),
        "src.brokers.futu": _module("src.brokers.futu"),
        "src.brokers.futu.portfolio": _module(
            "src.brokers.futu.portfolio",
            FutuPortfolioError=RuntimeError,
        ),
        "data_provider": _module("data_provider"),
        "data_provider.base": _module(
            "data_provider.base",
            canonical_stock_code=lambda code: code,
        ),
        "src.services": _module("src.services"),
        "src.services.stock_list_parser": _module(
            "src.services.stock_list_parser",
            split_stock_list=lambda value: value,
        ),
        "src.services.stock_code_utils": _module(
            "src.services.stock_code_utils",
            resolve_index_stock_code_for_analysis=lambda code: code,
        ),
        "src.core.desktop_launch_contract": _module(
            "src.core.desktop_launch_contract",
            enforce_desktop_launch_contract=lambda *_args, **_kwargs: None,
        ),
    }
    for package_name in ("src.brokers", "src.brokers.futu", "data_provider", "src.services"):
        stub_modules[package_name].__path__ = []

    spec = importlib.util.spec_from_file_location(
        "work25_main_startup_test_target",
        REPO_ROOT / "main.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, stub_modules):
        spec.loader.exec_module(module)
    return module


def test_api_server_can_become_ready_after_previous_three_second_limit() -> None:
    """A healthy but slow frozen start must not be killed at three seconds."""
    clock = _Clock()

    class _DelayedServer:
        @property
        def started(self) -> bool:
            return clock.now >= 4.0

    wait_for_api_server_startup(
        server=_DelayedServer(),
        thread=_LiveThread(),
        startup_errors=[],
        host="127.0.0.1",
        port=8000,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )

    assert clock.now >= 4.0


def test_api_server_never_ready_uses_bounded_default() -> None:
    clock = _Clock()

    with pytest.raises(RuntimeError, match=r"30\.0s"):
        wait_for_api_server_startup(
            server=_NeverReadyServer(),
            thread=_LiveThread(),
            startup_errors=[],
            host="127.0.0.1",
            port=8000,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )

    assert 30.0 <= clock.now < 30.1


def test_api_server_surfaces_captured_startup_error_without_waiting() -> None:
    clock = _Clock()

    with pytest.raises(RuntimeError, match="lifespan bootstrap failed"):
        wait_for_api_server_startup(
            server=_NeverReadyServer(),
            thread=_LiveThread(),
            startup_errors=[RuntimeError("lifespan bootstrap failed")],
            host="127.0.0.1",
            port=8000,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )

    assert clock.now == 0.0


def test_api_server_surfaces_dead_thread_without_waiting() -> None:
    clock = _Clock()

    class _DeadThread:
        @staticmethod
        def is_alive() -> bool:
            return False

    with pytest.raises(RuntimeError, match="启动后立即退出"):
        wait_for_api_server_startup(
            server=_NeverReadyServer(),
            thread=_DeadThread(),
            startup_errors=[],
            host="127.0.0.1",
            port=8000,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )

    assert clock.now == 0.0


def test_main_start_api_server_uses_bounded_wait_past_three_seconds() -> None:
    main_module = _load_main_with_lightweight_import_boundaries()
    clock = _Clock()

    class _Socket:
        def bind(self, _address) -> None:
            return None

        def close(self) -> None:
            return None

    class _Config:
        def __init__(self, *_args, **_kwargs) -> None:
            return None

    class _DelayedServer:
        def __init__(self, config) -> None:
            self.config = config

        @property
        def started(self) -> bool:
            return clock.now >= 4.0

        def run(self) -> None:
            return None

    class _Thread:
        def __init__(self, *, target, daemon) -> None:
            self.target = target
            self.daemon = daemon

        def start(self) -> None:
            return None

        def is_alive(self) -> bool:
            return True

    def deterministic_wait(**kwargs) -> None:
        wait_for_api_server_startup(
            **kwargs,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )

    main_module.wait_for_api_server_startup = deterministic_wait
    main_module.time = SimpleNamespace(time=clock.monotonic, sleep=clock.sleep)
    runtime_modules = {
        "socket": _module(
            "socket",
            AF_INET=2,
            AF_INET6=23,
            SOCK_STREAM=1,
            socket=lambda *_args, **_kwargs: _Socket(),
        ),
        "threading": _module("threading", Thread=_Thread),
        "uvicorn": _module("uvicorn", Config=_Config, Server=_DelayedServer),
        "api": _module("api"),
        "api.app": _module("api.app", app=object()),
    }
    runtime_modules["api"].__path__ = []

    with patch.dict(sys.modules, runtime_modules):
        main_module.start_api_server(
            "127.0.0.1",
            8000,
            SimpleNamespace(log_level="INFO"),
        )

    assert clock.now >= 4.0
