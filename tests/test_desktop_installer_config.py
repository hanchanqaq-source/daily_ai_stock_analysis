# -*- coding: utf-8 -*-
"""Regression checks for desktop installer configuration."""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_DIR = REPO_ROOT / "apps" / "dsa-desktop"
WEB_DIR = REPO_ROOT / "apps" / "dsa-web"


def test_work23_candidate_version_is_consistent() -> None:
    desktop = json.loads(
        (DESKTOP_DIR / "package.json").read_text(encoding="utf-8")
    )
    desktop_lock = json.loads(
        (DESKTOP_DIR / "package-lock.json").read_text(encoding="utf-8")
    )
    web = json.loads((WEB_DIR / "package.json").read_text(encoding="utf-8"))
    web_lock = json.loads(
        (WEB_DIR / "package-lock.json").read_text(encoding="utf-8")
    )

    assert desktop["version"] == "3.29.3"
    assert desktop_lock["version"] == desktop["version"]
    assert desktop_lock["packages"][""]["version"] == desktop["version"]
    assert web["version"] == desktop["version"]
    assert web_lock["version"] == desktop["version"]
    assert web_lock["packages"][""]["version"] == desktop["version"]


def test_windows_nsis_build_allows_custom_install_directory() -> None:
    package_json = json.loads((DESKTOP_DIR / "package.json").read_text(encoding="utf-8"))
    nsis = package_json.get("build", {}).get("nsis", {})

    assert nsis.get("oneClick") is False
    assert nsis.get("allowToChangeInstallationDirectory") is True
    assert nsis.get("allowElevation") is False
    assert nsis.get("include") == "installer.nsh"


def test_windows_installer_uses_fixed_electron_builder_line() -> None:
    package = json.loads((DESKTOP_DIR / "package.json").read_text(encoding="utf-8"))
    lock = json.loads(
        (DESKTOP_DIR / "package-lock.json").read_text(encoding="utf-8")
    )

    assert package["devDependencies"]["electron-builder"] == "26.15.7"
    assert lock["packages"][""]["devDependencies"]["electron-builder"] == (
        "26.15.7"
    )
    assert lock["packages"]["node_modules/electron-builder"]["version"] == (
        "26.15.7"
    )


def test_portable_update_fixture_declares_its_archiver_dependency() -> None:
    package = json.loads((DESKTOP_DIR / "package.json").read_text(encoding="utf-8"))
    lock = json.loads(
        (DESKTOP_DIR / "package-lock.json").read_text(encoding="utf-8")
    )

    assert package["devDependencies"]["archiver"] == "5.3.2"
    assert lock["packages"][""]["devDependencies"]["archiver"] == "5.3.2"
    assert lock["packages"]["node_modules/archiver"]["version"] == "5.3.2"


def test_installer_blocks_system_protected_directories() -> None:
    installer_script = (DESKTOP_DIR / "installer.nsh").read_text(encoding="utf-8")

    assert "Function .onVerifyInstDir" in installer_script
    assert "$PROGRAMFILES" in installer_script
    assert "$PROGRAMFILES64" in installer_script
    assert "$PROGRAMFILES32" in installer_script
    assert "$WINDIR" in installer_script
    assert "Abort" in installer_script


def test_old_uninstaller_retry_quotes_install_location_parameter() -> None:
    installer_script = (DESKTOP_DIR / "installer.nsh").read_text(encoding="utf-8")

    assert '"_?=$R8"' in installer_script
    assert "Retrying old uninstaller with quoted _? installation directory." in installer_script


def test_official_uninstaller_closes_only_exact_product_owned_processes() -> None:
    package = json.loads((DESKTOP_DIR / "package.json").read_text(encoding="utf-8"))
    installer_script = (DESKTOP_DIR / "installer.nsh").read_text(encoding="utf-8")
    helper_path = DESKTOP_DIR / "windows" / "close-owned-processes.ps1"
    manifest_path = DESKTOP_DIR / "windows" / "owned-processes.json"

    assert helper_path.is_file()
    assert manifest_path.is_file()
    helper = helper_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    resources = package["build"]["extraResources"]
    assert {
        "from": "windows/close-owned-processes.ps1",
        "to": "close-owned-processes.ps1",
    } in resources
    assert {
        "from": "windows/owned-processes.json",
        "to": "owned-processes.json",
    } in resources
    assert manifest == {
        "schemaVersion": 1,
        "executables": [
            {
                "role": "desktop",
                "relativePath": "PP02 AI Daily Stock Analysis.exe",
                "requestMainWindowClose": True,
            },
            {
                "role": "backend",
                "relativePath": (
                    "resources/backend/stock_analysis/stock_analysis.exe"
                ),
                "requestMainWindowClose": False,
            },
        ],
    }
    assert "!macro _dsaCloseOwnedProcesses" in installer_script
    assert "!macro customCheckAppRunning" in installer_script
    assert "!macro customUnInstall" in installer_script
    assert installer_script.count("!insertmacro _dsaCloseOwnedProcesses") == 2
    assert "$INSTDIR\\resources\\close-owned-processes.ps1" in installer_script
    assert "$EXEDIR\\resources\\close-owned-processes.ps1" in installer_script
    assert "-InstallRoot" not in installer_script
    assert "-ProductExecutableName" not in installer_script
    assert "-BackendRelativePath" not in installer_script
    assert "$PSScriptRoot" in helper
    assert "owned-processes.json" in helper
    assert "DSA_INSTALLER_DIAGNOSTIC_ROOT" in helper
    assert "owned-process-cleanup-evidence.json" in helper
    assert "Get-CimInstance Win32_Process" in helper
    assert "[StringComparison]::OrdinalIgnoreCase" in helper
    assert ".CloseMainWindow()" in helper
    assert "Stop-Process -Id" in helper
    assert "Get-Process -Name" not in helper
    assert "taskkill" not in helper.lower()
    assert "-like" not in helper.lower()


def test_windows_auto_updater_reuses_current_install_directory() -> None:
    main_js = (DESKTOP_DIR / "main.js").read_text(encoding="utf-8")

    assert "const installDirectory = path.dirname(app.getPath('exe'));" in main_js
    assert "updater.installDirectory = installDirectory;" in main_js
    assert 'updater.installDirectory = `"${installDirectory}"`' not in main_js
    assert "quoteNsisDirectoryArgument" not in main_js
