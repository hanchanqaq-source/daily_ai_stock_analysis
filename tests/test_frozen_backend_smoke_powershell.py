# -*- coding: utf-8 -*-
"""Regression checks for the Windows frozen-backend smoke PowerShell script."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_frozen_backend_smoke_delimits_port_before_colon() -> None:
    verifier = (REPO_ROOT / "scripts" / "verify-frozen-backend.ps1").read_text(
        encoding="utf-8"
    )

    assert "dynamic port ${port}: health=" in verifier
    assert "dynamic port $port: health=" not in verifier
