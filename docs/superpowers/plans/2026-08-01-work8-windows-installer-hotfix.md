# Work8 Windows Installer Hotfix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the affected electron-builder 24.x NSIS template with exactly 26.15.7 and make both PR and Release Windows jobs prove that the generated assisted installer can install, start, and uninstall.

**Architecture:** Keep PP02's existing `oneClick=false`, selectable directory, current-user install, custom NSIS include, installed updater, and portable ZIP. Add one fail-closed PowerShell verifier as the shared executable contract, plus a Windows fixture that exercises its process and cleanup boundaries before the verifier is trusted against the real package.

**Tech Stack:** Electron 31.4.x, electron-builder 26.15.7, NSIS, PowerShell 7/Windows PowerShell-compatible syntax, GitHub Actions, Python/pytest contract checks, Node 22/npm for Desktop build jobs, Node 20 for the standalone Web gate.

## Global Constraints

- Preserve `oneClick=false`, `allowToChangeInstallationDirectory=true`, `allowElevation=false`, and `installer.nsh`.
- Pin `electron-builder` to exactly `26.15.7`; do not upgrade Electron or adopt a 27.x preview.
- Use Node 22 for Desktop tests, Windows/macOS package jobs and Desktop Release jobs because
  `@electron/rebuild 4.x` requires Node `>=22.12.0`; keep the standalone Web gate on Node 20.
- The verifier may create and delete only a new `pp02-installer-verify-*` root under the Windows temporary directory.
- Do not inspect, reset, or remove an existing PP02 user directory or installation.
- Keep the frozen-backend, portable ZIP, fake-credential, macOS package, and fixed-Head gates.
- Keep PR #17 Draft. Do not Ready, merge, write `main`, tag, release, sign code, or use real data/credentials.
- CI verification is not the final Windows first-use acceptance; the final Release still requires a separate visible-wizard Windows run.

---

### Task 1: Prove the missing fixed builder and installer gates

**Files:**
- Modify: `tests/test_desktop_installer_config.py`
- Modify: `tests/test_packaging_build_scripts.py`

**Interfaces:**
- Consumes: `apps/dsa-desktop/package.json`, `apps/dsa-desktop/package-lock.json`, `.github/workflows/ci.yml`, and `.github/workflows/desktop-release.yml`.
- Produces: failing regression contracts that identify the affected builder line and both absent installer-execution gates.

- [x] **Step 1: Add the failing builder regression**

```python
def test_windows_installer_uses_fixed_electron_builder_line() -> None:
    package = json.loads((DESKTOP_DIR / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((DESKTOP_DIR / "package-lock.json").read_text(encoding="utf-8"))

    assert package["devDependencies"]["electron-builder"] == "26.15.7"
    assert lock["packages"][""]["devDependencies"]["electron-builder"] == "26.15.7"
    assert lock["packages"]["node_modules/electron-builder"]["version"] == "26.15.7"
```

- [x] **Step 2: Add failing workflow behavior contracts**

```python
def test_windows_jobs_execute_the_shared_installer_verifier() -> None:
    ci = _read_text(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    release = _read_text(REPO_ROOT / ".github" / "workflows" / "desktop-release.yml")

    verifier_call = "scripts/verify-windows-installer.ps1"
    assert verifier_call in ci
    assert ci.index(verifier_call) < ci.index("Upload verified Windows candidate")
    assert verifier_call in release
    assert release.index(verifier_call) < release.index("Prepare release artifact (Windows)")
```

Add a separate workflow-runtime contract that requires Node 22 in `desktop-test`, both Desktop
package jobs, and both Desktop Release build jobs, while requiring Node 20 in `web-gate`.

- [x] **Step 3: Run RED and confirm the expected causes**

Run:

```bash
python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py -q
```

Expected: existing tests pass; the new tests fail because the manifest still resolves 24.x,
neither workflow invokes `scripts/verify-windows-installer.ps1`, and Desktop build jobs still use
Node 20.

- [x] **Step 4: Commit the RED evidence**

```bash
git add tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py
git commit -m "test: expose Windows installer validation gap"
```

### Task 2: Pin the repaired NSIS template line and supported Node runtime

**Files:**
- Modify: `apps/dsa-desktop/package.json`
- Modify: `apps/dsa-desktop/package-lock.json`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/desktop-release.yml`

**Interfaces:**
- Consumes: the exact version contract from Task 1.
- Produces: a deterministic desktop dependency graph with `electron-builder 26.15.7`, unchanged
  Electron 31.4.x, and an officially supported Node 22 runtime for every Desktop build path.

- [x] **Step 1: Set the exact development dependency**

```json
"devDependencies": {
  "electron": "^31.4.0",
  "electron-builder": "26.15.7"
}
```

- [x] **Step 2: Regenerate the lock with Node 22 semantics**

Run:

```bash
NPM_CONFIG_CACHE=/tmp/pp02-work8-npm-cache npx -p node@22 -c 'node --version && npm install --prefix apps/dsa-desktop --package-lock-only --ignore-scripts --save-dev --save-exact electron-builder@26.15.7'
```

Expected: Node prints `v22.x`; the root lock entry and `node_modules/electron-builder` both resolve
`26.15.7`; `@electron/rebuild` resolves to a Node-22-compatible 4.x line; `electron` remains on the
existing 31.x line.

If the clean install shows that the existing portable-update test relied on `archiver` only
through the old builder's transitive Squirrel dependency, declare the previously resolved
`archiver 5.3.2` as an exact Desktop test-only development dependency. Do not add it to runtime
dependencies or change portable-update production code.

- [x] **Step 3: Upgrade only Desktop build jobs to Node 22**

Set `node-version: '22'` in CI `desktop-test`, Windows/macOS Desktop package jobs and Desktop
Release Windows/macOS build jobs. Keep CI `web-gate` at `node-version: '20'`.

- [x] **Step 4: Verify GREEN for dependency and runtime contracts**

Run:

```bash
python -m pytest tests/test_desktop_installer_config.py::test_windows_installer_uses_fixed_electron_builder_line tests/test_packaging_build_scripts.py::test_desktop_build_jobs_use_supported_node_22_runtime -q
```

Expected: PASS.

- [x] **Step 5: Commit the dependency repair**

```bash
git add apps/dsa-desktop/package.json apps/dsa-desktop/package-lock.json .github/workflows/ci.yml .github/workflows/desktop-release.yml docs/superpowers/specs/2026-08-01-work8-windows-installer-hotfix-design.md docs/superpowers/plans/2026-08-01-work8-windows-installer-hotfix.md
git commit -m "fix: upgrade repaired NSIS builder template"
```

### Task 3: Execute a fail-closed install/start/uninstall contract

**Files:**
- Create: `scripts/verify-windows-installer.ps1`
- Create: `scripts/tests/verify-windows-installer-contract.ps1`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/desktop-release.yml`

**Interfaces:**
- Consumes: `-InstallerPath`, `-ExpectedVersion`, `-InstallRoot`, optional `-ExpectedCommitSha`, and the real NSIS artifact.
- Produces: stable `WINDOWS_INSTALLER_*` evidence, zero/non-zero exit behavior, an installed-app startup proof from `logs/desktop.log`, and safe verifier-owned cleanup.

- [x] **Step 1: Write the Windows process-boundary fixture before the verifier**

Create a PowerShell contract runner that compiles this tiny failing installer executable with `Add-Type -OutputType ConsoleApplication`:

```powershell
$fakeInstallerSource = @'
using System;
using System.IO;

public static class FakeInstaller {
  public static int Main(string[] args) {
    string installRoot = null;
    foreach (string arg in args) {
      if (arg.StartsWith("/D=", StringComparison.OrdinalIgnoreCase)) {
        installRoot = arg.Substring(3);
      }
    }
    if (String.IsNullOrWhiteSpace(installRoot)) return 91;
    Directory.CreateDirectory(installRoot);
    File.WriteAllText(Path.Combine(installRoot, "created-by-fake-installer.txt"), "owned");
    return 17;
  }
}
'@
Add-Type -TypeDefinition $fakeInstallerSource -Language CSharp `
  -OutputAssembly $fakeInstaller -OutputType ConsoleApplication
```

The fixture creates only `$fixtureRoot/install/created-by-fake-installer.txt`, exits `17`, invokes the not-yet-present verifier in a child PowerShell process, and asserts all of these literal outcomes:

```powershell
if ($result.ExitCode -eq 0) { throw 'Verifier accepted a failing installer.' }
if (Test-Path -LiteralPath $installRoot) { throw 'Verifier did not clean its owned install root.' }
if (-not (Test-Path -LiteralPath $parentSentinel)) { throw 'Verifier removed a parent sentinel.' }
Write-Host 'WINDOWS_INSTALLER_CONTRACT_VALIDATION=PASS'
```

- [x] **Step 2: Implement the minimal shared verifier**

The script must:

```powershell
param(
  [Parameter(Mandatory=$true)][string]$InstallerPath,
  [Parameter(Mandatory=$true)][string]$ExpectedVersion,
  [Parameter(Mandatory=$true)][string]$InstallRoot,
  [string]$ExpectedCommitSha = '',
  [int]$StartupTimeoutSeconds = 120
)
```

It then performs these exact effects in order:

```powershell
$installer = [IO.Path]::GetFullPath($InstallerPath)
$ownedRoot = [IO.Path]::GetFullPath($InstallRoot)
$installProcess = Start-Process -FilePath $installer -ArgumentList "/S /D=$ownedRoot" -Wait -PassThru
if ($installProcess.ExitCode -ne 0) { throw "Installer exited with code $($installProcess.ExitCode)." }
```

After exit code 0 it requires `PP02 AI Daily Stock Analysis.exe`, `resources/app.asar`, the frozen backend, one accepted `Uninstall *.exe`, matching file version, and one HKCU uninstall entry whose `InstallLocation` equals the owned root. It temporarily sets `GITHUB_ACTIONS=false`, starts the installed app, polls the new root's `logs/desktop.log` for `Main UI loaded in`, kills only processes whose executable is inside the owned root, runs the generated uninstaller silently, and polls until app binaries plus that registry entry are gone. `finally` restores all changed environment variables and removes only the previously validated owned root.

- [x] **Step 3: Run the fixture and real artifact in the PR Windows job**

Add steps after the existing package build and before leakage scan/upload:

```powershell
./scripts/tests/verify-windows-installer-contract.ps1
$version = (Get-Content apps/dsa-desktop/package.json -Raw | ConvertFrom-Json).version
$installer = Get-Item "apps/dsa-desktop/dist/pp02-ai-daily-stock-analysis-windows-installer-v$version.exe"
$installRoot = Join-Path $env:RUNNER_TEMP "pp02-installer-verify-$env:DSA_EXPECTED_PR_HEAD_SHA"
./scripts/verify-windows-installer.ps1 -InstallerPath $installer.FullName -ExpectedVersion $version -InstallRoot $installRoot -ExpectedCommitSha $env:DSA_EXPECTED_PR_HEAD_SHA
```

Change the uploaded candidate to include the verified installer, `latest.yml`, its exact `.blockmap`, the portable ZIP, and the ZIP SHA-256.

- [x] **Step 4: Run the same verifier before Release artifact preparation**

After resolving the tag, write the checked-out commit to `DSA_RELEASE_COMMIT_SHA`. Run the fixture and real verifier after `Build desktop package (Windows)` and before `Prepare release artifact (Windows)` with this step:

```powershell
./scripts/tests/verify-windows-installer-contract.ps1
$expectedVersion = $env:RELEASE_TAG.TrimStart('v')
$installer = Get-Item "apps/dsa-desktop/dist/pp02-ai-daily-stock-analysis-windows-installer-$env:RELEASE_TAG.exe"
$installRoot = Join-Path $env:RUNNER_TEMP "pp02-installer-verify-$env:DSA_RELEASE_COMMIT_SHA"
./scripts/verify-windows-installer.ps1 -InstallerPath $installer.FullName -ExpectedVersion $expectedVersion -InstallRoot $installRoot -ExpectedCommitSha $env:DSA_RELEASE_COMMIT_SHA
```

- [x] **Step 5: Verify GREEN locally and commit**

Run:

```bash
python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py tests/test_futu_distribution_contract.py tests/test_portable_final_zip_contract.py -q
npm test --prefix apps/dsa-desktop
```

Expected: all targeted Python contracts and all Desktop tests pass. The PowerShell fixture and real installer remain explicitly `NOT_RUN_NON_WINDOWS` until the GitHub Windows job.

```bash
git add scripts/verify-windows-installer.ps1 scripts/tests/verify-windows-installer-contract.ps1 .github/workflows/ci.yml .github/workflows/desktop-release.yml tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py
git commit -m "ci: validate Windows installer lifecycle"
```

### Task 4: Document, audit, publish to the existing Draft, and judge

**Files:**
- Modify: `docs/desktop-package.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`

**Interfaces:**
- Consumes: the exact local test counts, final diff, remote Head, and GitHub Actions run evidence.
- Produces: one auditable Work8 status and an updated Draft PR #17; it does not authorize merge or release.

- [x] **Step 1: Update user and operator documentation**

Add one flat `[Unreleased]` line:

```markdown
- [修复] Windows 安装器升级到已修复 `System.dll / 0xC0000005` 竞态的 `electron-builder 26.15.7`，并在 PR 与正式发布前真实执行隔离安装、启动和卸载验证。
```

Replace the stale desktop-package statement that CI does not exercise the Release chain with the shared-verifier commands and the distinction between CI lifecycle validation and final visible-wizard acceptance.

- [x] **Step 2: Update the four ledgers and roadmap from evidence only**

Record the approved design, implementation commits, RED cause, local results, PR fixed Head, CI run/jobs, remaining final Windows acceptance, and Judge. Before remote CI, use `IMPLEMENTATION_LOCAL_PASS — CI_PENDING`; after a successful fixed-Head run, use at most `IMPLEMENTATION_PASS — DRAFT_HOLD`.

- [x] **Step 3: Run the complete pre-push verification**

Run:

```bash
python scripts/check_ai_assets.py
python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py tests/test_futu_distribution_contract.py tests/test_portable_final_zip_contract.py -q
npm test --prefix apps/dsa-desktop
git diff --check
git status --short
git diff --stat 66666352e953d90becce420da7d35b649516af76...HEAD
```

Expected: every command exits 0, only Work8 files are changed, and no generated package, cache, credential, database, or log is tracked.

- [ ] **Step 4: Commit and push the audited implementation**

```bash
git add docs/desktop-package.md docs/CHANGELOG.md docs/pp02/REBUILD_ROADMAP.md _ai-dev/PROJECT_STATUS.md _ai-dev/AI_HANDOFF.md _ai-dev/WORK_TASK.md _ai-dev/WORK_RETURN.md docs/superpowers/plans/2026-08-01-work8-windows-installer-hotfix.md
git commit -m "docs: record Work8 installer hotfix evidence"
git push origin agent/pp02-work8-r7-installer-fix
```

- [ ] **Step 5: Verify the fixed remote Head and update PR #17**

Require every applicable job to complete successfully. In particular, the Windows job must show the checked-out Head, `WINDOWS_INSTALLER_CONTRACT_VALIDATION=PASS`, `WINDOWS_INSTALLER_INSTALL_VALIDATION=PASS`, `WINDOWS_INSTALLED_APP_STARTUP_VALIDATION=PASS`, and `WINDOWS_UNINSTALL_VALIDATION=PASS` from the same Head. Update the Draft PR body with the actual diff, tests, run ID, risks, and rollback; keep it Draft.

- [ ] **Step 6: Stop at the authorization boundary**

Final Work8 implementation Judge may be:

```text
IMPLEMENTATION_PASS — DRAFT_HOLD
```

Do not mark R7 first-use acceptance PASS. Do not Ready, merge, tag, or publish `v3.29.1` without separate user authorization.
