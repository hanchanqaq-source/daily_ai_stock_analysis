# Work23 Windows Strict Acceptance Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a new Draft PR #23 Windows candidate whose first official uninstall leaves zero owned processes, whose complete backup preserves historical fundamental fallbacks while explicitly rebuilding only `stock_daily`, and whose visible/package identities consistently report `3.29.3`.

**Architecture:** Keep the existing Electron/NSIS and complete-backup architecture. Add an Electron quit gate plus one exact-path Windows process helper, strengthen the existing installed lifecycle verifier so it uninstalls a live app once, drive all candidate version surfaces from `3.29.3`, and extend the closed backup schema with `fundamental_snapshot` plus a structured `stock_daily` exclusion. Authenticode remains an audit/require switch with no certificate or secret wiring.

**Tech Stack:** Electron 31, electron-builder 26.15.7, NSIS, PowerShell 5+, Node 22 test runner, React/Vite, Python 3.11/3.12, SQLAlchemy/SQLite, pytest, GitHub Actions.

## Global Constraints

- Keep PR #23 Open and Draft; do not create another PR.
- Starting evidence is Work22 `FAIL` with report SHA-256 `30AC65C81E3F86E4CADBAEC9D2DBA95B432BA4DF8DBE81F12015857B9E5E39BE`.
- Do not use or modify Work22's real database, cold backup, complete export, or restore checkpoint.
- Do not Ready, merge, write `main`, tag, release, buy a certificate, access a real certificate/private key, or read/write CI secrets.
- The sole candidate application version is `3.29.3`.
- Do not lower acceptance criteria, add an external uninstall retry, or rewrite Work22's result.
- Kill or delete only objects proven to belong to this product by exact executable path, exact isolated install root, and exact uninstall registration.
- Use synthetic data and fake credentials only.

---

### Task 1: Lock every candidate version surface to 3.29.3

**Files:**
- Modify: `tests/test_desktop_installer_config.py`
- Modify: `tests/test_packaging_build_scripts.py`
- Modify: `tests/test_portable_final_zip_contract.py`
- Modify: `apps/dsa-desktop/package.json`
- Modify: `apps/dsa-desktop/package-lock.json`
- Modify: `apps/dsa-web/package.json`
- Modify: `apps/dsa-web/package-lock.json`
- Modify: `scripts/build-backend.ps1`
- Modify: `scripts/verify-windows-installer.ps1`
- Modify: `src/services/full_data_backup_service.py`

**Interfaces:**
- Consumes: Desktop/Web package metadata, `DSA_WEB_VERSION`, Electron resource metadata, `build-info.json`, and `DEFAULT_APPLICATION_VERSION`.
- Produces: Desktop/Web/backup version `3.29.3`; Windows verifier evidence for FileVersion, ProductVersion, DisplayVersion, and packaged Web build metadata.

- [ ] **Step 1: Write the failing version contract**

```python
def test_work23_candidate_version_is_consistent() -> None:
    desktop = json.loads((DESKTOP_DIR / "package.json").read_text(encoding="utf-8"))
    desktop_lock = json.loads((DESKTOP_DIR / "package-lock.json").read_text(encoding="utf-8"))
    web = json.loads((REPO_ROOT / "apps/dsa-web/package.json").read_text(encoding="utf-8"))
    web_lock = json.loads((REPO_ROOT / "apps/dsa-web/package-lock.json").read_text(encoding="utf-8"))
    assert desktop["version"] == "3.29.3"
    assert desktop_lock["version"] == desktop["version"]
    assert desktop_lock["packages"][""]["version"] == desktop["version"]
    assert web["version"] == desktop["version"]
    assert web_lock["version"] == desktop["version"]
    assert web_lock["packages"][""]["version"] == desktop["version"]
```

Add behavioral source contracts requiring `scripts/build-backend.ps1` to default
`DSA_WEB_VERSION` from the Desktop package and the Windows verifier to inspect
both FileVersion/ProductVersion plus `static/build-info.json.version`.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py tests/test_portable_final_zip_contract.py -q`

Expected: FAIL because Desktop is `3.21.0`, Web is `0.0.0`, backup defaults to `3.29.2`, and the verifier does not yet check all version surfaces.

- [ ] **Step 3: Apply the minimal version implementation**

Set both package/lock roots to `3.29.3`, set:

```python
DEFAULT_APPLICATION_VERSION = "3.29.3"
```

Before the Web build in `scripts/build-backend.ps1`, populate only a missing
build-time value:

```powershell
if ([string]::IsNullOrWhiteSpace($env:DSA_WEB_VERSION)) {
  $env:DSA_WEB_VERSION = (
    Get-Content 'apps\dsa-desktop\package.json' -Raw | ConvertFrom-Json
  ).version
}
```

In the Windows verifier, normalize both version resources with
`^(\d+)\.(\d+)\.(\d+)`, require each to equal `$ExpectedVersion`, load the
packaged `static/build-info.json`, and require its `.version` to equal the same
value.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py tests/test_portable_final_zip_contract.py -q`

Expected: all selected tests pass.

- [ ] **Step 5: Commit the version slice**

```bash
git add tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py tests/test_portable_final_zip_contract.py apps/dsa-desktop/package.json apps/dsa-desktop/package-lock.json apps/dsa-web/package.json apps/dsa-web/package-lock.json scripts/build-backend.ps1 scripts/verify-windows-installer.ps1 src/services/full_data_backup_service.py
git commit -m "fix: align Work23 candidate version identity"
```

### Task 2: Preserve fundamental snapshots and explicitly rebuild stock_daily

**Files:**
- Modify: `tests/test_full_data_backup_service.py`
- Modify: `tests/test_full_data_restore_integration.py`
- Modify: `tests/test_work20_full_backup_acceptance.py`
- Modify: `src/services/full_data_backup_service.py`
- Modify: `apps/dsa-web/src/components/settings/FullDataBackupCard.tsx`
- Modify: `apps/dsa-web/src/components/settings/__tests__/FullDataBackupCard.test.tsx`
- Modify: `apps/dsa-web/src/i18n/uiText.ts`
- Modify: `docs/full-data-backup-and-restore.md`

**Interfaces:**
- Consumes: `Base.metadata.tables`, `get_daily_history`, the strict complete-backup document, and Settings manifest rendering.
- Produces: round-tripped `fundamental_snapshot`; `manifest.excluded_tables.stock_daily`; transactional cache clearing; visible table-level exclusion and rebuild evidence.

- [ ] **Step 1: Write failing backup and UI tests**

Add synthetic rows and literal expectations:

```python
snapshot = FundamentalSnapshot(
    query_id="work23-query",
    code="600519",
    payload='{"pe": 20.5}',
    source_chain='["synthetic"]',
    coverage='{"valuation": true}',
)
session.add(snapshot)
```

Require export and restore to preserve all fields and original `id`; require:

```python
assert backup["manifest"]["excluded_tables"] == {
    "stock_daily": {
        "classification": "rebuildable_market_data_cache",
        "contains_user_data": False,
        "restore_behavior": "cleared_then_rebuilt_on_demand",
        "rebuild_entrypoint": "get_daily_history",
    }
}
```

Seed destination `stock_daily`, restore, assert zero rows, then call
`_handle_get_daily_history` with a deterministic fake fetcher and assert the
returned market bars are usable and `save_daily_data` receives them. In the Web
test, require the preview to render `stock_daily`, its no-user-data declaration,
and its rebuild behavior before confirmation.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/test_full_data_backup_service.py tests/test_full_data_restore_integration.py tests/test_work20_full_backup_acceptance.py -q`

Run: `npm test --prefix apps/dsa-web -- --run apps/dsa-web/src/components/settings/__tests__/FullDataBackupCard.test.tsx`

Expected: Python fails because the snapshot table and structured exclusion are absent; Web fails because table-level exclusions are not rendered.

- [ ] **Step 3: Implement the closed schema extension**

Add `fundamental_snapshot` to `TABLE_GROUPS["analysis"]` and define:

```python
"fundamental_snapshot": (
    "id", "query_id", "code", "payload", "source_chain", "coverage", "created_at",
)
```

Classify `id` as integer, `created_at` as datetime, require
`id/query_id/code/payload`, and validate `payload` and `coverage` as JSON objects
and `source_chain` as a JSON array. Define one immutable `EXCLUDED_TABLES`
mapping for `stock_daily`, include it in `_manifest`, validate its exact shape,
and delete `stock_daily` at the start of `_replace_tables` inside the existing
transaction. Remove the inaccurate `price_news_fundamental_caches` text.

Render each structured exclusion as safe text in `FullDataBackupCard`; reject or
ignore inherited/malformed values just as the existing category/exclusion parser
does.

- [ ] **Step 4: Run GREEN and the controlled rebuild proof**

Run the same Python and Web commands from Step 2.

Expected: all selected tests pass; the controlled rebuild assertion proves a
network-free provider response is returned and best-effort persisted after the
restore clears `stock_daily`.

- [ ] **Step 5: Commit the backup slice**

```bash
git add tests/test_full_data_backup_service.py tests/test_full_data_restore_integration.py tests/test_work20_full_backup_acceptance.py src/services/full_data_backup_service.py apps/dsa-web/src/components/settings/FullDataBackupCard.tsx apps/dsa-web/src/components/settings/__tests__/FullDataBackupCard.test.tsx apps/dsa-web/src/i18n/uiText.ts docs/full-data-backup-and-restore.md
git commit -m "fix: preserve non-rebuildable analysis snapshots"
```

### Task 3: Make Electron wait for its backend before quitting

**Files:**
- Modify: `apps/dsa-desktop/tests/main.test.js`
- Modify: `apps/dsa-desktop/main.js`

**Interfaces:**
- Consumes: tracked `backendProcess`, `stopBackend()`, Electron `before-quit`, `window-all-closed`.
- Produces: `drainBackendBeforeAppQuit()` and a one-time quit gate that never exits Electron while the tracked backend remains live.

- [ ] **Step 1: Write the failing quit-gate test**

Capture the registered `before-quit` handler, install a fake backend, invoke the
handler, and assert:

```javascript
assert.equal(preventDefaultCalls, 1);
assert.equal(quitCalls, 0);
fakeBackend.exitCode = 0;
fakeBackend.emit('exit', 0, null);
await new Promise((resolve) => setImmediate(resolve));
assert.equal(quitCalls, 1);
assert.equal(mainModule.__getBackendProcessForTest(), null);
```

Also invoke the handler after the backend is absent and require no
`preventDefault()` call, protecting updater and already-drained quits.

- [ ] **Step 2: Run RED**

Run: `npm test --prefix apps/dsa-desktop`

Expected: the new test fails because the existing handler does not prevent quit or await the backend.

- [ ] **Step 3: Implement the one-time asynchronous quit gate**

Use module state equivalent to:

```javascript
let appQuitReady = false;
let appQuitDrainPromise = null;

function drainBackendBeforeAppQuit() {
  if (!backendProcess) {
    appQuitReady = true;
    return Promise.resolve(true);
  }
  if (!appQuitDrainPromise) {
    appQuitDrainPromise = stopBackend().then(() => {
      if (backendProcess) return false;
      appQuitReady = true;
      app.quit();
      return true;
    }).finally(() => { appQuitDrainPromise = null; });
  }
  return appQuitDrainPromise;
}
```

The `before-quit` handler returns immediately only when `appQuitReady` or no
backend is present; otherwise it calls `event.preventDefault()` synchronously and
starts the drain. Non-macOS `window-all-closed` uses the same drain. Export a
narrow test accessor/reset only if the test cannot observe the registered event.

- [ ] **Step 4: Run GREEN**

Run: `npm test --prefix apps/dsa-desktop`

Expected: 82 existing tests plus the new lifecycle tests pass.

- [ ] **Step 5: Commit the quit slice**

```bash
git add apps/dsa-desktop/tests/main.test.js apps/dsa-desktop/main.js
git commit -m "fix: wait for backend before desktop quit"
```

### Task 4: Close exact owned processes and uninstall a live app once

**Files:**
- Create: `apps/dsa-desktop/windows/close-owned-processes.ps1`
- Modify: `apps/dsa-desktop/package.json`
- Modify: `apps/dsa-desktop/installer.nsh`
- Modify: `scripts/tests/verify-windows-installer-contract.ps1`
- Modify: `scripts/verify-windows-installer.ps1`
- Modify: `tests/test_desktop_installer_config.py`
- Modify: `tests/test_packaging_build_scripts.py`
- Modify: `docs/desktop-package.md`

**Interfaces:**
- Consumes: validated install root, exact Electron executable name, exact frozen-backend relative path, NSIS `customCheckAppRunning`.
- Produces: `PP02_UNINSTALL_OWNED_PROCESS_CLEANUP=PASS`; one live uninstaller invocation; zero exact-path product processes; untouched sibling sentinel.

- [ ] **Step 1: Write failing source and Windows behavior contracts**

Require the package to install the helper as an `extraResources` file, require
`installer.nsh` to define `customCheckAppRunning`, and forbid `tasklist /IM` or a
directory-prefix `StartsWith` inside the custom helper.

Extend the Windows contract to compile two long-running fake executables with
different full paths: one at the exact product path under the owned root and one
in a sibling root. Run the helper and assert the exact product process exits,
the sibling is still alive, the helper returns zero, and its output contains the
PASS marker.

Change the lifecycle source contract to require only one
`Start-Process -FilePath $uninstaller` in the normal path and to require that the
second app remains live until that call.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py -q`

Expected: FAIL because the helper/hook is absent and the lifecycle still calls `Stop-StartedProcessTree` before uninstall.

- [ ] **Step 3: Implement exact-path close and verification**

The helper validates its root and constructs only these full paths:

```powershell
$ownedExecutablePaths = @(
  [IO.Path]::GetFullPath((Join-Path $InstallRoot $ProductExecutableName)),
  [IO.Path]::GetFullPath((Join-Path $InstallRoot $BackendRelativePath))
)
```

It compares `Win32_Process.ExecutablePath` with
`[StringComparison]::OrdinalIgnoreCase`, calls `CloseMainWindow()` only on exact
product-exe PIDs, waits up to ten seconds, force-stops only exact-path leftovers,
waits five seconds, and exits nonzero if an exact path remains. It outputs counts
and the PASS marker but not machine-wide process data.

The NSIS macro invokes the installed helper with the validated `$INSTDIR`; a
missing helper or nonzero result uses `SetErrorLevel 2` and `Quit`.

In `verify-windows-installer.ps1`, keep `$appProcess` and the backend live after
second readiness, invoke the official uninstaller once, then require the tracked
process to be exited and exact app/backend process queries to return zero before
declaring cleanup PASS. The existing `finally` cleanup remains only for failures
that occurred before the normal uninstall attempt.

- [ ] **Step 4: Run GREEN locally and on Windows CI**

Run locally: `python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py -q`

Run locally: `npm test --prefix apps/dsa-desktop`

Windows fixed-Head CI command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/tests/verify-windows-installer-contract.ps1
```

Expected: local contracts pass; fixed-Head Windows CI proves the helper behavior
and the installed app's single live-uninstall lifecycle.

- [ ] **Step 5: Commit the uninstall slice**

```bash
git add apps/dsa-desktop/windows/close-owned-processes.ps1 apps/dsa-desktop/package.json apps/dsa-desktop/installer.nsh scripts/tests/verify-windows-installer-contract.ps1 scripts/verify-windows-installer.ps1 tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py docs/desktop-package.md
git commit -m "fix: close owned processes during official uninstall"
```

### Task 5: Add a credential-free Authenticode audit and enforcement interface

**Files:**
- Modify: `scripts/verify-windows-installer.ps1`
- Modify: `scripts/tests/verify-windows-installer-contract.ps1`
- Modify: `tests/test_packaging_build_scripts.py`
- Modify: `docs/desktop-package.md`

**Interfaces:**
- Consumes: installer and installed Electron executable paths, optional `-RequireAuthenticodeSignature` switch.
- Produces: sanitized signature status markers; fail-closed requirement mode; no certificate/secret acquisition or wiring.

- [ ] **Step 1: Write the failing audit contract**

Require the verifier to expose `-RequireAuthenticodeSignature`, call
`Get-AuthenticodeSignature` for the installer and installed Electron executable,
print only `WINDOWS_INSTALLER_SIGNATURE_STATUS=<status>` and
`WINDOWS_APP_SIGNATURE_STATUS=<status>`, and reject any status other than
`Valid` in requirement mode.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/test_packaging_build_scripts.py -q`

Expected: FAIL because the audit interface is absent.

- [ ] **Step 3: Implement sanitized audit mode**

Add:

```powershell
param(
  # existing parameters remain unchanged
  [switch]$RequireAuthenticodeSignature
)
```

For each artifact, obtain `.Status`, emit only the status name, and when the
switch is set throw unless both equal `Valid`. Do not emit `.SignerCertificate`,
subject, thumbprint, key material, environment variables, or secret names.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/test_packaging_build_scripts.py -q`

Expected: PASS. Fixed-Head Windows CI records `NotSigned` without treating it as signed; a synthetic unsigned contract invocation with the switch proves nonzero failure.

- [ ] **Step 5: Commit the audit slice**

```bash
git add scripts/verify-windows-installer.ps1 scripts/tests/verify-windows-installer-contract.ps1 tests/test_packaging_build_scripts.py docs/desktop-package.md
git commit -m "test: audit Windows Authenticode status"
```

### Task 6: Update Work23 control truth and user-facing change history

**Files:**
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`
- Modify: `docs/CHANGELOG.md`

**Interfaces:**
- Consumes: locked Work22 failure, actual local test evidence, current PR number/head, and authorization boundaries.
- Produces: append-only Work23 state with `CI_PENDING` before push and exact fixed-Head CI evidence only after completion.

- [ ] **Step 1: Write the local state update**

Record `WORK_ID=WORK-023`, the Work22 report hash, PR #23, current branch, the
four root causes, the selected cache classification, actual local commands/counts,
the unsigned authorization gate, and prohibitions. Do not enter a future Head,
run ID, job result, candidate byte size, or SHA-256 before GitHub provides it.

Add flat `[Unreleased]` lines such as:

```markdown
- [修复] Windows 官方卸载现在等待并清理精确归属的应用进程，严格生命周期会在应用运行时只调用一次卸载器。
- [修复] 完整备份纳入历史基本面快照，并在 manifest 中明确声明日线行情缓存的清空与按需重建行为。
- [修复] Windows 候选的桌面、界面、构建信息、安装登记和便携清单统一使用 3.29.3。
```

- [ ] **Step 2: Verify governance and formatting**

Run: `python scripts/check_ai_assets.py`

Run: `git diff --check`

Expected: both exit zero.

- [ ] **Step 3: Commit the state slice**

```bash
git add _ai-dev/PROJECT_STATUS.md _ai-dev/AI_HANDOFF.md _ai-dev/WORK_TASK.md _ai-dev/WORK_RETURN.md docs/ROADMAP.md docs/pp02/REBUILD_ROADMAP.md docs/CHANGELOG.md
git commit -m "docs: record Work23 local evidence"
```

### Task 7: Full local verification, review, push, fixed-Head CI, and candidate identity

**Files:**
- Modify after CI only: `_ai-dev/PROJECT_STATUS.md`
- Modify after CI only: `_ai-dev/WORK_RETURN.md`
- Modify after CI only: `docs/pp02/REBUILD_ROADMAP.md`
- Remote metadata: existing Draft PR #23 body

**Interfaces:**
- Consumes: all Work23 commits, full repository validation, GitHub Actions results/artifacts.
- Produces: one fixed new Head, complete CI evidence, downloadable Windows candidate byte size/SHA-256, signing status, and a strict Work23 Judge without Ready/merge/release.

- [ ] **Step 1: Run complete local affected verification**

```bash
python -m pytest tests/test_full_data_backup_service.py tests/test_full_data_restore_integration.py tests/test_work20_full_backup_acceptance.py tests/test_data_tools_daily_history_cache.py tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py tests/test_portable_final_zip_contract.py -q
npm test --prefix apps/dsa-desktop
npm ci --prefix apps/dsa-web
npm run lint --prefix apps/dsa-web
npm test --prefix apps/dsa-web -- --run
npm run build --prefix apps/dsa-web
python scripts/check_ai_assets.py
git diff --check
```

Expected: every command exits zero with no failing test, lint, build, governance, or diff check.

- [ ] **Step 2: Inspect exact scope and security boundaries**

Run: `git status --short --branch`

Run: `git diff 6dba54b9dba84f2562f6ab91d735b1c6e5744702...HEAD --stat`

Run: `git diff 6dba54b9dba84f2562f6ab91d735b1c6e5744702...HEAD -- . ':!docs/superpowers/specs/*' ':!docs/superpowers/plans/*'`

Confirm no real data, backups, exports, checkpoints, certificates, private keys,
CI secrets, dependency upgrades, Ready/merge/tag/release actions, or unrelated
changes are present.

- [ ] **Step 3: Push only the existing PR branch**

```bash
git push origin agent/pp02-work20-full-backup-period-persistence
```

Resolve the exact pushed Head with `git rev-parse HEAD`, verify PR #23 remains
Open Draft with that Head, and update its body with Work23 root causes, changes,
local verification, Work22 immutable FAIL, and current CI pending state.

- [ ] **Step 4: Wait for the complete fixed-Head CI**

Use the GitHub app to fetch workflow runs for the exact Head, inspect every job,
and fetch failed logs if any. A failure returns to the relevant TDD task; never
rerun to hide a deterministic defect.

Expected: all applicable jobs, including the Windows live uninstall lifecycle,
Web, Desktop, backend, Docker, macOS, governance, and change detection, are
successful or explicitly path-skipped by the workflow's established rules.

- [ ] **Step 5: Download and verify the fixed-Head Windows candidate**

Download the exact fixed-Head Windows candidate artifact, identify the installer
file unambiguously, calculate byte size and SHA-256, read FileVersion and
ProductVersion evidence from the Windows job, read Authenticode status evidence,
and verify the artifact/manifest identity says `3.29.3`.

- [ ] **Step 6: Record final evidence without creating an evidence-only new Head**

Update the PR body with fixed Head, run/jobs, installer name, size, SHA-256,
version surfaces, signing status, and remaining real-machine retest. Keep repo
truth at the tested Head; do not make a post-CI evidence commit that invalidates
the fixed-Head result.

- [ ] **Step 7: Return the strict Work23 Judge**

Use `IMPLEMENTATION_PASS — DRAFT_HOLD — SIGNING_IDENTITY_GATE` only if all code,
local, and CI requirements pass while the artifact remains unsigned. Do not call
the Windows strict acceptance PASS: the next Windows real-machine retest and a
separately authorized signing identity remain distinct gates.
