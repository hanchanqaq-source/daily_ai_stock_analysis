# -*- coding: utf-8 -*-
"""Regression contracts for PP02 Windows portable staging and final ZIP smoke."""

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_portable_stage_excludes_only_root_runtime_state(tmp_path: Path) -> None:
    source = tmp_path / "win-unpacked"
    stage = tmp_path / "stage"
    nested_data = (
        source
        / "resources"
        / "backend"
        / "stock_analysis"
        / "_internal"
        / "fake_useragent"
        / "data"
        / "browsers.jsonl"
    )
    nested_data.parent.mkdir(parents=True)
    nested_data.write_text('{"browser": "Edge"}\n', encoding="utf-8")
    (source / "PP02 AI Daily Stock Analysis.exe").write_bytes(b"exe")
    (source / ".env").write_text("secret", encoding="utf-8")
    for directory in ("data", "logs"):
        (source / directory).mkdir()
        (source / directory / "user-state.txt").write_text(
            "private", encoding="utf-8"
        )

    result = subprocess.run(
        [
            "node",
            "scripts/prepare-portable-release.js",
            "stage",
            "v3.21.0",
            str(source),
            str(stage),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert not (stage / ".env").exists()
    assert not (stage / "data").exists()
    assert not (stage / "logs").exists()
    staged_nested = stage / nested_data.relative_to(source)
    assert staged_nested.is_file()
    manifest = json.loads(
        (stage / "pp02-portable-release.json").read_text(encoding="utf-8")
    )
    managed = {item["relativePath"] for item in manifest["managedFiles"]}
    assert nested_data.relative_to(source).as_posix() in managed


def test_windows_ci_smokes_the_final_extracted_portable_zip() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "Expand-Archive -LiteralPath $zip -DestinationPath $finalExtract" in workflow
    assert "fake_useragent/data/browsers.jsonl" in workflow
    assert "$finalManifestPath" in workflow
    assert "$finalManifest.managedFiles" in workflow
    assert "$requiredBrowserRelativePath" in workflow
    assert "Final portable manifest does not manage exactly one" in workflow
    assert "-PackagedEntry $finalPackagedEntry" in workflow
    assert "win-unpacked/resources/backend/stock_analysis/stock_analysis.exe" not in workflow


def test_windows_release_smokes_the_final_extracted_portable_zip() -> None:
    workflow = (
        REPO_ROOT / ".github" / "workflows" / "desktop-release.yml"
    ).read_text(encoding="utf-8")

    assert "Expand-Archive -LiteralPath $zipTarget" in workflow
    assert "$releaseFinalManifest.managedFiles" in workflow
    assert "$requiredBrowserRelativePath" in workflow
    assert "Final Release portable manifest does not manage exactly one" in workflow
    assert "-PackagedEntry $releaseFinalPackagedEntry" in workflow
    assert "Remove-Item -LiteralPath $releaseFinalExtract" in workflow
