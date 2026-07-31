import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_portable_helper_avoids_powershell_home_variable_collision() -> None:
    script = (
        REPO_ROOT
        / "apps"
        / "dsa-desktop"
        / "portable-update"
        / "portable-update-helper.ps1"
    ).read_text(encoding="utf-8")

    assert re.search(r"(?im)^\s*\$home\s*=", script) is None
    assert "$homeResponse = Invoke-WebRequest" in script
    assert "$homeResponse.StatusCode" in script
