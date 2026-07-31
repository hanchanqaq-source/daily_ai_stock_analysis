# -*- coding: utf-8 -*-
"""Cross-runtime contract tests for R3.7 Windows secure credentials."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "src" / "core" / "config_registry.py"
SENSITIVE_KEYS_PATH = (
    REPO_ROOT
    / "apps"
    / "dsa-desktop"
    / "secure-credentials"
    / "sensitiveKeys.js"
)


def _explicit_sensitive_registry_keys() -> list[str]:
    tree = ast.parse(REGISTRY_PATH.read_text(encoding="utf-8"))
    definitions = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "_FIELD_DEFINITIONS"
    )
    assert isinstance(definitions, ast.Dict)

    sensitive: list[str] = []
    for key_node, value_node in zip(definitions.keys, definitions.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(value_node, ast.Dict):
            continue
        metadata = {
            field_key.value: field_value.value
            for field_key, field_value in zip(value_node.keys, value_node.values)
            if isinstance(field_key, ast.Constant)
            and isinstance(field_value, ast.Constant)
        }
        if metadata.get("is_sensitive") is True:
            sensitive.append(str(key_node.value))
    return sensitive


def _desktop_classifies(keys: list[str]) -> dict[str, bool]:
    script = """
const fs = require('node:fs');
const { isSensitiveConfigKey } = require(process.argv[1]);
const keys = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(Object.fromEntries(keys.map((key) => [key, isSensitiveConfigKey(key)]))));
"""
    result = subprocess.run(
        ["node", "-e", script, str(SENSITIVE_KEYS_PATH)],
        input=json.dumps(keys),
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_desktop_classifier_covers_python_registry_and_dynamic_secret_shapes() -> None:
    keys = _explicit_sensitive_registry_keys() + [
        "CUSTOM_WEBHOOK_URLS",
        "LLM_PRIVATE_EXTRA_HEADERS",
        "LLM_PRIVATE_API_KEY",
        "LLM_PRIVATE_API_KEYS",
    ]
    classified = _desktop_classifies(keys)

    assert keys
    assert all(classified[key] for key in keys)


def test_desktop_classifier_does_not_capture_plain_operational_settings() -> None:
    keys = ["STOCK_LIST", "LOG_LEVEL", "WEBUI_PORT", "OPENAI_BASE_URL"]
    classified = _desktop_classifies(keys)

    assert not any(classified.values())


def test_desktop_package_and_preload_expose_write_only_credential_surface() -> None:
    package = json.loads(
        (REPO_ROOT / "apps" / "dsa-desktop" / "package.json").read_text(encoding="utf-8")
    )
    preload = (REPO_ROOT / "apps" / "dsa-desktop" / "preload.js").read_text(encoding="utf-8")
    main = (REPO_ROOT / "apps" / "dsa-desktop" / "main.js").read_text(encoding="utf-8")

    assert "secure-credentials/**/*" in package["build"]["files"]
    for method in (
        "getSecureCredentialStatus",
        "prepareSecureCredentialUpdate",
        "commitSecureCredentialUpdate",
        "rollbackSecureCredentialUpdate",
        "finalizeSecureCredentialUpdate",
    ):
        assert method in preload
    assert "getSecureCredentialValue" not in preload
    assert "decryptSecureCredential" not in preload
    assert "safeStorage" in main
    assert "DSA_SECURE_CREDENTIAL_MODE" in main
    assert "DSA_SECURE_CREDENTIAL_KEYS" in main
    assert "senderFrame" in main and "mainFrame" in main
