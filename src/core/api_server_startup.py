"""Bounded condition wait for the background FastAPI server startup."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from typing import Protocol


# Leave recovery time inside the Desktop (60s) and frozen-smoke (90s) health gates.
DEFAULT_API_SERVER_STARTUP_TIMEOUT_SECONDS = 30.0
API_SERVER_STARTUP_POLL_INTERVAL_SECONDS = 0.05


class _ServerState(Protocol):
    started: bool


class _ThreadState(Protocol):
    def is_alive(self) -> bool: ...


def wait_for_api_server_startup(
    *,
    server: _ServerState,
    thread: _ThreadState,
    startup_errors: Sequence[BaseException],
    host: str,
    port: int,
    timeout_seconds: float = DEFAULT_API_SERVER_STARTUP_TIMEOUT_SECONDS,
    poll_interval_seconds: float = API_SERVER_STARTUP_POLL_INTERVAL_SECONDS,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Wait for real uvicorn readiness while preserving bounded failures."""
    deadline = monotonic() + timeout_seconds

    while monotonic() < deadline:
        if startup_errors:
            raise RuntimeError(
                f"FastAPI server failed to start: {host}:{port}; {startup_errors[0]}"
            )
        if server.started:
            return
        if not thread.is_alive():
            raise RuntimeError(f"FastAPI 服务器启动后立即退出: {host}:{port}")
        sleep(poll_interval_seconds)

    if startup_errors:
        raise RuntimeError(
            f"FastAPI server failed to start: {host}:{port}; {startup_errors[0]}"
        )
    if server.started:
        return
    if not thread.is_alive():
        raise RuntimeError(f"FastAPI 服务器启动后立即退出: {host}:{port}")

    raise RuntimeError(
        f"FastAPI 服务在 {timeout_seconds:.1f}s 内未完成启动: {host}:{port}"
    )


__all__ = [
    "DEFAULT_API_SERVER_STARTUP_TIMEOUT_SECONDS",
    "wait_for_api_server_startup",
]
