# -*- coding: utf-8 -*-
"""Static contracts for third-party data bundled in desktop backends."""

from __future__ import annotations

import unittest
from pathlib import Path


class DesktopPackagingAssetsTestCase(unittest.TestCase):
    """Keep Windows and macOS PyInstaller package-data rules aligned."""

    repo_root = Path(__file__).resolve().parent.parent

    def test_orjson_is_declared_bundled_and_probed(self) -> None:
        requirements = (self.repo_root / "requirements.txt").read_text(encoding="utf-8")
        main = (self.repo_root / "main.py").read_text(encoding="utf-8")
        macos_script = (self.repo_root / "scripts" / "build-backend-macos.sh").read_text(
            encoding="utf-8"
        )
        windows_script = (self.repo_root / "scripts" / "build-backend.ps1").read_text(
            encoding="utf-8"
        )

        self.assertIn("orjson>=3.10,<4", requirements)
        self.assertIn('"orjson"', macos_script)
        self.assertIn("'orjson'", windows_script)
        self.assertIn('DSA_PACKAGED_IMPORT_PROBE="${module}"', macos_script)
        self.assertIn("$env:DSA_PACKAGED_IMPORT_PROBE = $module", windows_script)
        self.assertIn('importlib.import_module(_packaged_import_probe)', main)

    def test_scripts_collect_and_verify_akshare_calendar_data(self) -> None:
        macos_script = (self.repo_root / "scripts" / "build-backend-macos.sh").read_text(
            encoding="utf-8"
        )
        windows_script = (self.repo_root / "scripts" / "build-backend.ps1").read_text(
            encoding="utf-8"
        )

        self.assertIn("--collect-data akshare", macos_script)
        self.assertIn("'--collect-data', 'akshare'", windows_script)
        self.assertIn("_internal/akshare/file_fold/calendar.json", macos_script)
        self.assertIn("_internal\\akshare\\file_fold\\calendar.json", windows_script)

    def test_windows_backend_collects_and_checks_mini_racer_runtime(self) -> None:
        windows_script = (self.repo_root / "scripts" / "build-backend.ps1").read_text(
            encoding="utf-8"
        )

        self.assertIn("'--collect-all', 'py_mini_racer'", windows_script)
        self.assertIn("Checking MiniRacer availability", windows_script)
        self.assertIn("import py_mini_racer", windows_script)
        self.assertIn("Verifying packaged MiniRacer assets", windows_script)
        self.assertIn("mini_racer.dll", windows_script)
        self.assertIn("icudtl.dat", windows_script)

    def test_packaged_chip_probe_loads_v8_without_network(self) -> None:
        main = (self.repo_root / "main.py").read_text(encoding="utf-8")

        self.assertIn('os.getenv("DSA_PACKAGED_CHIP_PROBE")', main)
        self.assertIn("import akshare.stock_feature.stock_cyq_em", main)
        self.assertIn("from py_mini_racer import MiniRacer", main)
        self.assertIn('chip_probe.eval("6 * 7")', main)
        self.assertIn("OK: packaged chip runtime probe succeeded", main)

    def test_final_portable_zip_runs_shared_chip_runtime_probe(self) -> None:
        verifier = (
            self.repo_root / "scripts" / "verify-frozen-backend.ps1"
        ).read_text(encoding="utf-8")
        workflow = (
            self.repo_root / ".github" / "workflows" / "ci.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("DSA_PACKAGED_CHIP_PROBE", verifier)
        self.assertIn("Packaged chip runtime probe failed", verifier)
        self.assertIn("$chipProbeProcess.ExitCode", verifier)
        self.assertIn("-PackagedEntry $finalPackagedEntry", workflow)
        self.assertLess(
            workflow.index("Expand-Archive -LiteralPath $zip -DestinationPath $finalExtract"),
            workflow.index("-PackagedEntry $finalPackagedEntry"),
        )

    def test_windows_builder_generates_post_sign_runtime_identity_manifest(self) -> None:
        package_json = (
            self.repo_root / "apps" / "dsa-desktop" / "package.json"
        ).read_text(encoding="utf-8")
        after_sign = (
            self.repo_root
            / "apps"
            / "dsa-desktop"
            / "scripts"
            / "afterSignRuntimeIntegrity.js"
        ).read_text(encoding="utf-8")

        self.assertIn('"afterSign": "scripts/afterSignRuntimeIntegrity.js"', package_json)
        self.assertIn('"runtime-integrity/**/*"', package_json)
        self.assertIn("writeWindowsRuntimeIntegrityManifest", after_sign)
        self.assertIn("context.electronPlatformName", after_sign)

    def test_desktop_loading_failure_is_user_facing_chinese(self) -> None:
        loading_page = (
            self.repo_root / "apps" / "dsa-desktop" / "renderer" / "loading.html"
        ).read_text(encoding="utf-8")

        self.assertIn('lang="zh-CN"', loading_page)
        self.assertIn("启动失败", loading_page)
        self.assertNotIn("Error:", loading_page)


if __name__ == "__main__":
    unittest.main()
