"""Side-effect-free validation for packaged Desktop backend launches."""

from __future__ import annotations

import ipaddress
import sys
from typing import Mapping, Optional, TextIO


DESKTOP_LAUNCH_CONTRACT_MARKER = "PP02_DESKTOP_LAUNCH_CONTRACT_REJECTED"
_TRUTHY_DESKTOP_VALUES = frozenset({"1", "true", "yes", "on", "desktop"})
_CONFLICTING_BOOLEAN_MODES = (
    "serve",
    "webui",
    "webui_only",
    "market_review",
    "schedule",
    "backtest",
    "check_notify",
)
_CONFLICTING_VALUE_MODES = ("stocks", "portfolio")


class DesktopLaunchContractError(ValueError):
    """A bounded reason for rejecting a Desktop-mode backend invocation."""

    def __init__(self, reason_code: str):
        self.reason_code = str(reason_code or "unknown")[:80]
        super().__init__(self.reason_code)


def _desktop_mode_enabled(environ: Mapping[str, str]) -> bool:
    value = str(environ.get("DSA_DESKTOP_MODE", "")).strip().lower()
    return value in _TRUTHY_DESKTOP_VALUES


def _is_loopback_host(host: str) -> bool:
    normalized = str(host or "").strip()
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]
    if normalized.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def validate_desktop_launch_contract(args, environ: Mapping[str, str]) -> None:
    """Require Desktop mode to be an explicit loopback serve-only launch."""
    if not _desktop_mode_enabled(environ):
        return
    if not bool(getattr(args, "serve_only", False)):
        raise DesktopLaunchContractError("missing_serve_only")

    host = getattr(args, "host", None)
    if host is None or not str(host).strip():
        raise DesktopLaunchContractError("host_missing")
    if not _is_loopback_host(str(host)):
        raise DesktopLaunchContractError("host_not_loopback")

    port = getattr(args, "port", None)
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise DesktopLaunchContractError("port_invalid")

    if any(bool(getattr(args, name, False)) for name in _CONFLICTING_BOOLEAN_MODES):
        raise DesktopLaunchContractError("conflicting_mode")
    if any(bool(getattr(args, name, None)) for name in _CONFLICTING_VALUE_MODES):
        raise DesktopLaunchContractError("conflicting_mode")


def enforce_desktop_launch_contract(
    args,
    environ: Mapping[str, str],
    *,
    stderr: Optional[TextIO] = None,
) -> Optional[int]:
    """Return exit code 2 and one bounded marker when validation fails."""
    try:
        validate_desktop_launch_contract(args, environ)
    except DesktopLaunchContractError as exc:
        target = stderr if stderr is not None else sys.stderr
        print(
            f"{DESKTOP_LAUNCH_CONTRACT_MARKER} reason={exc.reason_code}",
            file=target,
        )
        return 2
    return None


__all__ = [
    "DESKTOP_LAUNCH_CONTRACT_MARKER",
    "DesktopLaunchContractError",
    "enforce_desktop_launch_contract",
    "validate_desktop_launch_contract",
]
