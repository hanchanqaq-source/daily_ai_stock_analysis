# -*- coding: utf-8 -*-
"""Regression checks for the Windows frozen-backend smoke PowerShell script."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_verifier() -> str:
    return (REPO_ROOT / "scripts" / "verify-frozen-backend.ps1").read_text(
        encoding="utf-8"
    )


def test_frozen_backend_smoke_delimits_port_before_colon() -> None:
    verifier = _read_verifier()

    assert "dynamic port ${port}: health=" in verifier
    assert "dynamic port $port: health=" not in verifier


def test_frozen_backend_smoke_does_not_overwrite_read_only_home_variable() -> None:
    verifier = _read_verifier()

    assert "$homeResponse =" in verifier
    assert "$home =" not in verifier
    assert "$home.StatusCode" not in verifier
