# -*- coding: utf-8 -*-
"""Validation tests for backend packaging scripts."""

import json
import os
import shlex
import subprocess
import hashlib
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _workflow_job(workflow: str, job_name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)",
        workflow,
    )
    assert match is not None, f"workflow job not found: {job_name}"
    return match.group(0)


def _bash_path(path: Path) -> str:
    resolved = path.resolve()
    if os.name != "nt":
        return str(resolved)
    drive = resolved.drive.rstrip(":").lower()
    relative = resolved.relative_to(resolved.anchor).as_posix()
    return f"/mnt/{drive}/{relative}"


def test_windows_backend_build_script_collects_alphasift_adapter() -> None:
    script = _read_text(REPO_ROOT / "scripts" / "build-backend.ps1")
    main_py = _read_text(REPO_ROOT / "main.py")

    assert "Checking AlphaSift adapter availability" in script
    assert "import alphasift.dsa_adapter" in script
    assert "--collect-all" in script
    assert "alphasift.dsa_adapter" in script
    assert "hiddenImports" in script
    assert "Verifying packaged runtime imports" in script
    assert "DSA_PACKAGED_IMPORT_PROBE" in script
    assert (
        "Start-Process -FilePath $packagedEntry "
        "-WorkingDirectory $probeWorkingDirectory -Wait -PassThru"
    ) in script
    assert "$probeProcess.ExitCode" in script
    assert "& $packagedEntry" not in script
    assert "Packaged backend cannot import $module" in script
    assert "DSA_PACKAGED_IMPORT_PROBE" in main_py
    assert "importlib.import_module(_packaged_import_probe)" in main_py


def test_windows_candidate_build_and_installer_verify_one_version_identity() -> None:
    build_script = _read_text(REPO_ROOT / "scripts" / "build-backend.ps1")
    verifier = _read_text(REPO_ROOT / "scripts" / "verify-windows-installer.ps1")
    backup_service = _read_text(
        REPO_ROOT / "src" / "services" / "full_data_backup_service.py"
    )

    assert "$env:DSA_WEB_VERSION" in build_script
    assert "apps\\dsa-desktop\\package.json" in build_script
    assert ".VersionInfo.FileVersion" in verifier
    assert ".VersionInfo.ProductVersion" in verifier
    assert "build-info.json" in verifier
    assert "webBuildInfo.version" in verifier
    assert 'DEFAULT_APPLICATION_VERSION = "3.29.3"' in backup_service


def test_windows_backend_collects_and_exercises_fake_useragent_runtime() -> None:
    script = _read_text(REPO_ROOT / "scripts" / "build-backend.ps1")
    verifier = _read_text(REPO_ROOT / "scripts" / "verify-frozen-backend.ps1")
    workflow = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    requirements = _read_text(REPO_ROOT / "requirements.txt")
    main_py = _read_text(REPO_ROOT / "main.py")

    assert "fake-useragent>=1.4.0,<3.0.0" in requirements
    assert "'--collect-all', 'fake_useragent'" in script
    assert "DSA_PACKAGED_FAKE_USERAGENT_PROBE" in script
    assert "DSA_PACKAGED_IMPORT_PROBE = 'data_provider.efinance_fetcher'" in script
    assert "UserAgent().random" in main_py
    assert 'importlib.resources.files("fake_useragent.data")' in main_py
    assert 'data_root.joinpath("browsers.jsonl")' in main_py
    assert "scripts/verify-frozen-backend.ps1" in workflow
    assert "- 'scripts/verify-frozen-backend.ps1'" in workflow
    assert "Get-FreeTcpPort" in verifier
    assert "[string]$PackagedEntry" in verifier
    assert "/api/health" in verifier
    assert "HttpClient" in verifier
    assert "Add-Type -AssemblyName System.Net.Http" in verifier
    assert "taskkill.exe" in verifier
    assert 'os.getenv("GITHUB_ACTIONS") != "true"' in main_py
    assert "'GITHUB_ACTIONS','PYTHONUTF8','PYTHONIOENCODING'" in verifier
    assert "$env:GITHUB_ACTIONS = 'false'" in verifier
    assert "$env:PYTHONUTF8 = '1'" in verifier
    assert "$env:PYTHONIOENCODING = 'utf-8'" in verifier
    assert "foreach ($name in $saved.Keys)" in verifier
    assert "SetEnvironmentVariable($name, $saved[$name], 'Process')" in verifier
    assert "if (-not $healthy)" in verifier
    assert "[int]$health.StatusCode -eq 200 -and [int]$homeResponse.StatusCode -eq 200" in verifier
    assert "UseProxy = $false" in verifier
    assert "$healthDiagnostic" in verifier
    assert "$homeDiagnostic" in verifier
    assert "health=$healthDiagnostic" in verifier
    assert "home=$homeDiagnostic" in verifier


def test_macos_backend_build_script_collects_alphasift_adapter() -> None:
    script = _read_text(REPO_ROOT / "scripts" / "build-backend-macos.sh")
    main_py = _read_text(REPO_ROOT / "main.py")

    assert "Checking AlphaSift adapter availability..." in script
    assert "import alphasift.dsa_adapter" in script
    assert "--collect-all" in script
    assert "cmd+=(\"--collect-all\" \"alphasift\")" in script
    assert "packaged_entry=\"${packaged_root}/stock_analysis\"" in script
    assert "--help" in script
    assert 'DSA_PACKAGED_IMPORT_PROBE="${module}"' in script
    assert "dsa-packaged-import.log" in script
    assert "PathFinder.find_spec(" not in script
    assert "zipfile" not in script
    assert 'normalized.startswith("alphasift/dsa_adapter.")' not in script
    assert "DSA_PACKAGED_IMPORT_PROBE" in main_py
    assert "importlib.import_module(_packaged_import_probe)" in main_py


def test_packaged_backend_probes_use_safe_runtime_working_directories() -> None:
    macos_script = _read_text(REPO_ROOT / "scripts" / "build-backend-macos.sh")
    windows_script = _read_text(REPO_ROOT / "scripts" / "build-backend.ps1")
    windows_verifier = _read_text(
        REPO_ROOT / "scripts" / "verify-frozen-backend.ps1"
    )

    assert "packaged_probe_dir=" in macos_script
    assert 'cd "${packaged_probe_dir}"' in macos_script
    assert "PYTHONSAFEPATH=1" in macos_script
    assert "$packagedEntry = [IO.Path]::GetFullPath" in windows_script
    assert "-WorkingDirectory $probeWorkingDirectory" in windows_script
    assert "$env:PYTHONSAFEPATH = '1'" in windows_script
    assert "-WorkingDirectory $tempRoot" in windows_verifier
    assert "$env:PYTHONSAFEPATH = '1'" in windows_verifier


def test_macos_backend_collects_and_exercises_fake_useragent_runtime() -> None:
    script = _read_text(REPO_ROOT / "scripts" / "build-backend-macos.sh")
    assert 'cmd+=("--collect-all" "fake_useragent")' in script
    assert "DSA_PACKAGED_FAKE_USERAGENT_PROBE=1" in script
    assert "data_provider.efinance_fetcher" in script


def test_macos_unsigned_packaging_contract_is_explicit() -> None:
    package = json.loads(
        _read_text(REPO_ROOT / "apps" / "dsa-desktop" / "package.json")
    )
    after_pack_hook = _read_text(
        REPO_ROOT / "apps" / "dsa-desktop" / "scripts" / "afterPackMacos.js"
    )
    backend_script = _read_text(REPO_ROOT / "scripts" / "build-backend-macos.sh")
    desktop_script = _read_text(REPO_ROOT / "scripts" / "build-desktop-macos.sh")
    workflow = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")

    assert package["build"]["mac"]["identity"] is None
    assert package["build"]["mac"]["hardenedRuntime"] is False
    assert package["build"]["afterPack"] == "scripts/afterPackMacos.js"
    assert "context.electronPlatformName !== 'darwin'" in after_pack_hook
    assert "'macos-signature-audit.sh'" in after_pack_hook
    assert "execFileSync('bash', [auditScript, 'normalize', appPath]" in after_pack_hook
    normalize_call = (
        'bash "${SCRIPT_DIR}/macos-signature-audit.sh" normalize "${packaged_root}"'
    )
    assert normalize_call in backend_script
    assert backend_script.index(normalize_call) < backend_script.index(
        '"${packaged_entry}" --help'
    )
    assert 'bash "${SCRIPT_DIR}/macos-signature-audit.sh" check "${app_path}"' in (
        desktop_script
    )
    assert "verify_unsigned_dmg" in desktop_script
    assert "code has no resources but signature indicates they must be present" in (
        desktop_script
    )
    assert "- 'scripts/macos-signature-audit.sh'" in workflow
    assert "run: bash scripts/build-backend-macos.sh" in workflow
    assert "run: bash scripts/build-desktop-macos.sh" in workflow


def test_windows_job_runs_head_bound_safe_storage_fake_credential_gate() -> None:
    workflow = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    verifier = _read_text(
        REPO_ROOT / "scripts" / "verify-windows-secure-credentials.ps1"
    )
    harness = _read_text(
        REPO_ROOT
        / "apps"
        / "dsa-desktop"
        / "tests"
        / "windows-secure-credential-harness.js"
    )
    scanner_path = REPO_ROOT / "scripts" / "scan-windows-fake-credential.js"
    package = json.loads(
        _read_text(REPO_ROOT / "apps" / "dsa-desktop" / "package.json")
    )

    assert "Validate Windows safeStorage fake credential" in workflow
    assert "scripts/verify-windows-secure-credentials.ps1" in workflow
    assert "- 'scripts/verify-windows-secure-credentials.ps1'" in workflow
    assert workflow.index("Validate Windows safeStorage fake credential") < workflow.index(
        "Build and verify portable candidate"
    )
    assert package["scripts"]["test:windows-credentials"]
    assert "DSA_EXPECTED_PR_HEAD_SHA" in workflow
    assert "github.event.pull_request.head.sha" in workflow
    assert "ref: ${{ env.DSA_EXPECTED_PR_HEAD_SHA }}" in workflow
    assert "git rev-parse HEAD" in verifier
    assert "DSA_EXPECTED_PR_HEAD_SHA" in verifier
    assert "$currentHead -ne $expectedHead" in verifier
    assert "GITHUB_SHA" not in verifier
    assert "R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS" in verifier
    assert "test:windows-credentials" in verifier
    assert "scan-windows-fake-credential.js" in verifier
    assert "--path ." in verifier
    assert "--path .github --path api" not in verifier
    assert scanner_path.exists()
    scanner = _read_text(scanner_path)
    assert "utf16le" in scanner
    assert "R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN=PASS" in scanner
    assert "Scan Windows fake credential leakage" in workflow
    assert workflow.index("Scan Windows fake credential leakage") < workflow.index(
        "Upload verified Windows candidate"
    )
    assert "$finalExtract" in workflow
    assert "$zip" in workflow
    assert "safeStorage" in harness
    assert "CredentialVault" in harness
    assert "app.whenReady" in harness
    assert "R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS" in harness
    assert "console.log(fake" not in harness
    assert "console.error(fake" not in harness


def test_windows_jobs_execute_the_shared_installer_verifier() -> None:
    ci = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    release = _read_text(
        REPO_ROOT / ".github" / "workflows" / "desktop-release.yml"
    )
    verifier_call = "scripts/verify-windows-installer.ps1"

    assert verifier_call in ci
    assert "Validate Windows installer verifier contracts" in ci
    assert "Validate installed Windows lifecycle" in ci
    assert ci.index(verifier_call) < ci.index("Upload verified Windows candidate")
    assert verifier_call in release
    assert "Validate Windows installer verifier contracts" in release
    assert "Validate installed Windows lifecycle" in release
    assert release.index(verifier_call) < release.index(
        "Prepare release artifact (Windows)"
    )


def test_windows_installer_verifier_is_scoped_and_fail_closed() -> None:
    verifier_path = REPO_ROOT / "scripts" / "verify-windows-installer.ps1"
    contract_path = (
        REPO_ROOT / "scripts" / "tests" / "verify-windows-installer-contract.ps1"
    )

    assert verifier_path.exists()
    assert contract_path.exists()

    verifier = _read_text(verifier_path)
    contract = _read_text(contract_path)
    for parameter in (
        "InstallerPath",
        "ExpectedVersion",
        "InstallRoot",
        "ExpectedCommitSha",
    ):
        assert parameter in verifier

    assert "$env:RUNNER_TEMP" in verifier
    assert "pp02-installer-verify-" in verifier
    assert "Main UI loaded in" in verifier
    assert "RegistryView]::Registry64" in verifier
    assert "RegistryView]::Registry32" in verifier
    assert "UninstallString" in verifier
    assert "QuietUninstallString" in verifier
    assert "Test-UninstallCommandTargetsPath" in verifier
    assert "$entriesByIdentity" in verifier
    assert "RegistryViews" in verifier
    assert "Write-StartupDiagnostics" in verifier
    assert "WINDOWS_INSTALLED_APP_STARTUP_DIAGNOSTIC_BEGIN" in verifier
    assert "WINDOWS_INSTALLED_APP_STARTUP_DIAGNOSTIC_END" in verifier
    assert "Expected exactly one HKCU uninstall entry for the owned uninstaller" in verifier
    assert "Expected exactly one HKCU uninstall entry for the owned root" not in verifier
    assert "WINDOWS_INSTALLER_INSTALL_VALIDATION=PASS" in verifier
    assert "WINDOWS_INSTALLED_APP_STARTUP_VALIDATION=PASS" in verifier
    assert "WINDOWS_UNINSTALL_VALIDATION=PASS" in verifier
    assert "WINDOWS_INSTALLER_VALIDATION=FAIL" in verifier

    assert "created-by-fake-installer.txt" in contract
    assert "return 17;" in contract
    assert "Verifier accepted a failing installer." in contract
    assert "Verifier did not clean its owned install root." in contract
    assert "Verifier removed a parent sentinel." in contract
    assert "WINDOWS_INSTALLER_CONTRACT_VALIDATION=PASS" in contract
    assert "Start-Process" in contract
    assert "-RedirectStandardOutput" in contract
    assert "-RedirectStandardError" in contract
    assert "$contractProcess.ExitCode" in contract
    assert "& $powerShell" not in contract


def test_windows_installer_failure_diagnostics_are_preserved_and_redacted() -> None:
    verifier = _read_text(
        REPO_ROOT / "scripts" / "verify-windows-installer.ps1"
    )
    contract = _read_text(
        REPO_ROOT
        / "scripts"
        / "tests"
        / "verify-windows-installer-contract.ps1"
    )

    assert "DiagnosticRoot" in verifier
    assert "pp02-installer-diagnostics-" in verifier
    assert "Save-InstallerDiagnostics" in verifier
    assert "Protect-DiagnosticText" in verifier
    assert "diagnostic-summary.txt" in verifier
    assert "desktop-startup-sanitized.log" in verifier
    assert "backend-probe-stderr-sanitized.log" in verifier
    assert "backend-probe-summary.txt" in verifier
    assert "port-process-state.txt" in verifier
    assert "windows-application-events-sanitized.log" in verifier
    assert "installed-files.txt" in verifier
    assert "diagnostic-collector-status.txt" in verifier
    assert "Get-NetTCPConnection" in verifier
    assert "Get-WinEvent" in verifier
    assert "-RedirectStandardError" in verifier
    assert "-RedirectStandardOutput" in verifier
    assert "Remove-Item -LiteralPath $rawBackendStderr" in verifier
    assert "Remove-Item -LiteralPath $rawBackendStdout" in verifier
    assert "Environment.GetEnvironmentVariables" not in verifier
    assert "Get-ChildItem Env:" not in verifier
    assert "-eq '.env'" in verifier
    assert "WINDOWS_INSTALLER_DIAGNOSTIC=AVAILABLE" in verifier
    assert "failure_stage=" in verifier
    assert "stage_process_exit_code=" in verifier

    assert "-DiagnosticRoot" in contract
    assert "diagnostic-summary.txt" in contract
    assert "WINDOWS_INSTALLER_DIAGNOSTIC=AVAILABLE" in contract
    assert "Verifier did not preserve diagnostic evidence" in contract
    assert "failure_stage=installer_process" in contract
    assert "stage_process_exit_code=17" in contract
    assert "installed_files=PASS" in contract


def test_windows_jobs_upload_diagnostics_even_after_lifecycle_failure() -> None:
    ci = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    release = _read_text(
        REPO_ROOT / ".github" / "workflows" / "desktop-release.yml"
    )

    for workflow, sha_expression in (
        (ci, "env.DSA_EXPECTED_PR_HEAD_SHA"),
        (release, "env.DSA_RELEASE_COMMIT_SHA"),
    ):
        assert "-DiagnosticRoot $diagnosticRoot" in workflow
        assert "-ArtifactDiagnosticRoot $diagnosticRoot" in workflow
        assert "Upload Windows installer diagnostics" in workflow
        assert "if: always()" in workflow
        assert "actions/upload-artifact@v6" in workflow
        assert "github.run_id" in workflow
        assert sha_expression in workflow
        assert "pp02-windows-installer-diagnostics-" in workflow
        assert "pp02-installer-diagnostics-" in workflow
        assert workflow.index("Validate installed Windows lifecycle") < workflow.index(
            "Upload Windows installer diagnostics"
        )


def test_windows_installer_validates_exit_restart_before_uninstall() -> None:
    verifier = _read_text(
        REPO_ROOT / "scripts" / "verify-windows-installer.ps1"
    )
    contract = _read_text(
        REPO_ROOT
        / "scripts"
        / "tests"
        / "verify-windows-installer-contract.ps1"
    )

    first_start = "WINDOWS_INSTALLED_APP_STARTUP_VALIDATION=PASS"
    first_exit = "WINDOWS_INSTALLED_APP_EXIT_VALIDATION=PASS"
    restart = "WINDOWS_INSTALLED_APP_RESTART_VALIDATION=PASS"
    live_uninstall = "WINDOWS_UNINSTALL_LIVE_PROCESS_VALIDATION=PASS"
    uninstall = "WINDOWS_UNINSTALL_VALIDATION=PASS"

    for marker in (first_start, first_exit, restart, live_uninstall, uninstall):
        assert marker in verifier
    assert "installed_app_restart" in verifier
    assert "$restartReadyMarkerBaseline" in verifier
    assert "Get-ExactOwnedProcesses" in verifier
    assert "WINDOWS_OWNED_PROCESS_COUNT_AFTER_UNINSTALL=0" in verifier
    assert "owned-process-cleanup-evidence.json" in verifier
    assert "WINDOWS_UNINSTALL_HELPER_EXECUTION_VALIDATION=PASS" in verifier
    assert "WINDOWS_OWNED_PROCESS_HELPER_CONTRACT=PASS" in contract
    assert verifier.index(first_start) < verifier.index(first_exit)
    assert verifier.index(first_exit) < verifier.index(restart)
    assert verifier.index(restart) < verifier.index(live_uninstall)
    assert verifier.index(live_uninstall) < verifier.index(uninstall)
    live_segment = verifier[
        verifier.index(restart):verifier.index(live_uninstall)
    ]
    assert "Stop-StartedProcessTree -Process $appProcess" not in live_segment


def test_windows_signing_interface_is_read_only_and_has_an_explicit_identity_gate() -> None:
    verifier = _read_text(
        REPO_ROOT / "scripts" / "verify-windows-installer.ps1"
    )
    workflow = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    package = _read_text(REPO_ROOT / "apps" / "dsa-desktop" / "package.json")

    assert "[switch]$RequireValidSignature" in verifier
    assert "Get-AuthenticodeSignature" in verifier
    assert "WINDOWS_INSTALLER_SIGNATURE_STATUS=" in verifier
    assert "WINDOWS_APP_SIGNATURE_STATUS=" in verifier
    assert "WINDOWS_SIGNATURE_POLICY=AUDIT_ONLY" in verifier
    assert "WINDOWS_SIGNATURE_POLICY=REQUIRE_VALID" in verifier
    assert "Authenticode signature is required but" in verifier
    combined = "\n".join((verifier, workflow, package))
    assert "CSC_LINK" not in combined
    assert "WIN_CSC_LINK" not in combined
    assert "certificatePassword" not in combined
    assert "signtool sign" not in combined.lower()


def test_desktop_build_jobs_use_supported_node_22_runtime() -> None:
    ci = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    release = _read_text(
        REPO_ROOT / ".github" / "workflows" / "desktop-release.yml"
    )

    for job_name in (
        "desktop-test",
        "desktop-futu-package-windows",
        "desktop-futu-package-macos",
    ):
        job = _workflow_job(ci, job_name)
        assert "actions/setup-node@v6" in job
        assert "node-version: '22'" in job

    web_job = _workflow_job(ci, "web-gate")
    assert "node-version: '20'" in web_job

    for job_name in ("build-windows", "build-macos"):
        job = _workflow_job(release, job_name)
        assert "actions/setup-node@v6" in job
        assert "node-version: '22'" in job


def test_fake_credential_scanner_detects_utf8_and_never_prints_the_value(tmp_path: Path) -> None:
    head = "a" * 40
    suffix = hashlib.sha256(f"pp02-r37-fake:{head}".encode()).hexdigest()
    fake = f"pp02-r37-{suffix}"
    candidate = tmp_path / "candidate.bin"
    candidate.write_bytes(b"prefix\x00" + fake.encode("utf-8") + b"\x00suffix")

    result = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts" / "scan-windows-fake-credential.js"),
            "--head",
            head,
            "--path",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    self_output = result.stdout + result.stderr
    assert result.returncode != 0
    assert fake not in self_output
    assert "R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN=FAIL" in self_output


def _write_fake_macos_signature_tools(fake_bin: Path) -> None:
    fake_bin.mkdir()
    file_tool = fake_bin / "file"
    file_tool.write_text(
        "#!/usr/bin/env bash\nprintf 'Mach-O 64-bit executable\\n'\n",
        encoding="utf-8",
        newline="\n",
    )
    codesign_tool = fake_bin / "codesign"
    codesign_tool.write_text(
        """#!/usr/bin/env bash
candidate="${@: -1}"
marker="${candidate}.removed"
case "$1" in
  -d)
    if [[ -f "${marker}" ]] || [[ "${candidate}" == *"unsigned.bin" ]]; then
      printf 'code object is not signed at all\\n' >&2
      exit 1
    fi
    printf 'Authority=adhoc\\n' >&2
    ;;
  --verify)
    if [[ "${candidate}" == *"broken.bin" ]] && [[ ! -f "${marker}" ]]; then
      printf 'broken signature\\n' >&2
      exit 1
    fi
    ;;
  --remove-signature)
    : > "${marker}"
    ;;
esac
""",
        encoding="utf-8",
        newline="\n",
    )
    file_tool.chmod(0o755)
    codesign_tool.chmod(0o755)


def test_macos_signature_audit_normalizes_invalid_signatures(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    _write_fake_macos_signature_tools(fake_bin)
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    broken = artifact / "broken.bin"
    broken.write_text("broken", encoding="utf-8")
    (artifact / "unsigned.bin").write_text("unsigned", encoding="utf-8")

    result = subprocess.run(
        [
            "bash",
            "-c",
            'PATH={fake_bin}:"$PATH"; export PATH; bash {script} normalize {artifact}'.format(
                fake_bin=shlex.quote(_bash_path(fake_bin)),
                script=shlex.quote(
                    _bash_path(REPO_ROOT / "scripts" / "macos-signature-audit.sh")
                ),
                artifact=shlex.quote(_bash_path(artifact)),
            ),
        ],
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (artifact / "broken.bin.removed").is_file()
    assert "removed=1" in result.stdout


def test_macos_signature_audit_rejects_invalid_signatures(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    _write_fake_macos_signature_tools(fake_bin)
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    broken = artifact / "broken.bin"
    broken.write_text("broken", encoding="utf-8")

    result = subprocess.run(
        [
            "bash",
            "-c",
            'PATH={fake_bin}:"$PATH"; export PATH; bash {script} check {artifact}'.format(
                fake_bin=shlex.quote(_bash_path(fake_bin)),
                script=shlex.quote(
                    _bash_path(REPO_ROOT / "scripts" / "macos-signature-audit.sh")
                ),
                artifact=shlex.quote(_bash_path(artifact)),
            ),
        ],
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not (artifact / "broken.bin.removed").exists()
    assert "invalid signature" in result.stderr
