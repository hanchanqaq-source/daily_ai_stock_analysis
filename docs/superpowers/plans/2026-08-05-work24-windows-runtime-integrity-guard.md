# Work24 Windows Runtime Integrity Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 阻止被替换或参数被截断的 Windows 桌面/后端程序进入业务流程，并在任何分析任务或历史写入前给出明确、可操作的失败提示。

**Architecture:** electron-builder 在 Windows `afterSign` 阶段为最终桌面 EXE 与冻结后端 EXE 生成闭合 SHA-256 身份清单；打包后的 Electron 在 `spawn` 前同步校验自己的运行路径、两个文件的大小与摘要。Python 后端在解析参数后、加载配置和数据库前验证 `DSA_DESKTOP_MODE` 的完整 `--serve-only --host <loopback> --port <1..65535>` 合同；Electron 只保留有界、脱敏的 stderr 诊断并将合同失败分类为固定中文提示。

**Tech Stack:** Node.js 22、Electron 31、electron-builder 26.15.7、Node `node:test`、Python 3.10+、pytest/unittest、GitHub Actions PowerShell。

## Global Constraints

- Base 固定为 `main@e59c9d9e475d1f1149da01cceaa0cc79101497c7`（`v3.29.3`）。
- 分支固定为 `agent/pp02-runtime-integrity-guard`，只建立 Draft PR。
- 不编码特定恶意软件名称、固定文件大小、文件名启发式或机器本地路径。
- 不读取或上传受影响电脑的 EXE、数据库、`.env`、备份、日志或证据。
- 不新增或升级依赖，不修改版本号，不 Ready、不合并、不 Tag、不 Release。
- Windows CI 是最终安装包和免安装 ZIP 的权威运行门；Linux 本地验证不得冒充 Windows 实机验收。

---

### Task 1: Windows post-sign runtime identity manifest

**Files:**
- Create: `apps/dsa-desktop/runtime-integrity/runtimeIntegrity.js`
- Create: `apps/dsa-desktop/scripts/afterSignRuntimeIntegrity.js`
- Create: `apps/dsa-desktop/tests/runtime-integrity.test.js`
- Modify: `apps/dsa-desktop/package.json`

**Interfaces:**
- Produces: `writeWindowsRuntimeIntegrityManifest({ appOutDir, platform, version }) -> { manifestPath, manifest } | { skipped: true }`。
- Produces: `PP02_RUNTIME_INTEGRITY_MANIFEST = "pp02-runtime-integrity.json"` 与闭合的 `EXPECTED_RUNTIME_ENTRIES`。
- Manifest schema: `{ schemaVersion: 1, productId, version, entries: [{ role, relativePath, size, sha256 }] }`。

- [x] **Step 1: Write the failing manifest-generator tests**

```javascript
test('afterSign records exactly the signed desktop and backend executables', async () => {
  const result = await afterSign({ appOutDir, electronPlatformName: 'win32', packager: { appInfo: { version: '3.29.3' } } });
  assert.deepEqual(result.manifest.entries.map(({ role }) => role), ['desktop', 'backend']);
  assert.equal(result.manifest.entries[0].relativePath, 'PP02 AI Daily Stock Analysis.exe');
  assert.equal(result.manifest.entries[1].relativePath, 'resources/backend/stock_analysis/stock_analysis.exe');
});

test('afterSign fails closed when a required executable is missing', async () => {
  await assert.rejects(afterSign(context), /required runtime file is missing/);
});
```

- [x] **Step 2: Run the tests and verify RED**

Run: `cd apps/dsa-desktop && node --test tests/runtime-integrity.test.js`

Expected: FAIL because the runtime-integrity module and hook do not exist.

- [x] **Step 3: Implement the minimal manifest generator and hook**

```javascript
async function afterSign(context) {
  return writeWindowsRuntimeIntegrityManifest({
    appOutDir: context.appOutDir,
    platform: context.electronPlatformName,
    version: context.packager.appInfo.version,
  });
}
```

The generator must hash files with bounded synchronous reads, require regular files inside `appOutDir`, write normalized forward-slash paths, and emit exactly two roles. Add `afterSign` and `runtime-integrity/**/*` to `package.json`.

- [x] **Step 4: Run the targeted tests and verify GREEN**

Run: `cd apps/dsa-desktop && node --test tests/runtime-integrity.test.js`

Expected: PASS.

---

### Task 2: Packaged Desktop pre-spawn verification and classified error

**Files:**
- Modify: `apps/dsa-desktop/runtime-integrity/runtimeIntegrity.js`
- Modify: `apps/dsa-desktop/main.js`
- Modify: `apps/dsa-desktop/tests/runtime-integrity.test.js`
- Modify: `apps/dsa-desktop/tests/main.test.js`
- Modify: `apps/dsa-desktop/renderer/loading.html`

**Interfaces:**
- Produces: `verifyPackagedWindowsRuntime({ platform, packaged, appRoot, resourcesPath, exePath, backendPath, version })`.
- Produces: `RuntimeIntegrityError` with a fixed public message and a bounded `reasonCode`.
- Produces: `classifyBackendStartupFailure({ backendStartError, backendProcess, stderrTail }) -> string | null`.

- [x] **Step 1: Write failing verifier and spawn-order tests**

```javascript
test('verifier accepts the exact two-entry manifest', () => {
  assert.equal(verifyPackagedWindowsRuntime(validFixture).verified, true);
});

for (const mutation of ['missing manifest', 'wrong product', 'wrong version', 'renamed desktop', 'unexpected path', 'wrong size', 'wrong digest']) {
  test(`verifier rejects ${mutation}`, () => {
    assert.throws(() => verifyPackagedWindowsRuntime(mutatedFixture(mutation)), RuntimeIntegrityError);
  });
}

test('startBackend verifies packaged Windows files before spawn', () => {
  assert.throws(() => main.startBackend(runtime), /程序文件校验失败/);
  assert.equal(spawnCalls.length, 0);
});
```

- [x] **Step 2: Run the tests and verify RED**

Run: `cd apps/dsa-desktop && node --test tests/runtime-integrity.test.js tests/main.test.js`

Expected: verifier exports are absent and `startBackend` currently reaches `spawn`.

- [x] **Step 3: Implement minimal fail-closed verification**

Before credential-vault access, `.env` sanitization, or `spawn`, packaged Windows `startBackend` must verify the exact manifest, expected paths, `app.getPath('exe')`, regular-file identity, size, and SHA-256. Development and packaged non-Windows runs return `{ skipped: true }`.

Keep only a bounded sanitized stderr tail and never render raw backend output. Convert runtime-integrity rejection and the backend marker from Task 3 into the fixed Chinese message:

```text
程序文件或启动参数校验失败，后端未启动，也没有启动任何分析任务。请从官方 Release 重新安装后再试。
```

- [x] **Step 4: Run the tests and verify GREEN**

Run: `cd apps/dsa-desktop && node --test tests/runtime-integrity.test.js tests/main.test.js`

Expected: PASS with no spawn on verification failure.

---

### Task 3: Backend Desktop launch contract before configuration/database initialization

**Files:**
- Modify: `main.py`
- Create: `tests/test_desktop_launch_contract.py`

**Interfaces:**
- Produces: `validate_desktop_launch_contract(args, environ) -> None`.
- Produces: `DesktopLaunchContractError(reason_code)`.
- Produces stderr marker `PP02_DESKTOP_LAUNCH_CONTRACT_REJECTED reason=<bounded_code>` and exit code `2`.

- [x] **Step 1: Write failing pure-validator and side-effect-order tests**

```python
def test_valid_desktop_serve_only_contract_passes():
    validate_desktop_launch_contract(args(serve_only=True, host="127.0.0.1", port=8000), {"DSA_DESKTOP_MODE": "true"})

@pytest.mark.parametrize("overrides", [
    {"serve_only": False}, {"host": "0.0.0.0"}, {"port": 0},
    {"market_review": True}, {"schedule": True}, {"stocks": "600519"},
])
def test_invalid_desktop_contract_is_rejected(overrides):
    with pytest.raises(DesktopLaunchContractError):
        validate_desktop_launch_contract(args(**overrides), {"DSA_DESKTOP_MODE": "true"})

def test_main_rejects_invalid_desktop_contract_before_database_or_config():
    assert main.main() == 2
    database_get_instance.assert_not_called()
    get_config.assert_not_called()
```

- [x] **Step 2: Run the tests and verify RED**

Run: `python -m pytest tests/test_desktop_launch_contract.py -q`

Expected: FAIL because no validator exists and invalid Desktop mode currently loads configuration and may run analysis.

- [x] **Step 3: Implement the minimal validator at the top of `main()`**

Immediately after `parse_arguments()`, if `DSA_DESKTOP_MODE` is truthy, require `serve_only`, a loopback IPv4/IPv6/localhost host, integer port `1..65535`, and absence of analysis/schedule/backtest/check-only modes. On failure print only the fixed marker and return `2`; do not initialize logging, configuration, database, scheduler, reports, or history.

- [x] **Step 4: Run the tests and verify GREEN**

Run: `python -m pytest tests/test_desktop_launch_contract.py -q`

Expected: PASS.

---

### Task 4: Final ZIP contract and repository documentation/state

**Files:**
- Create: `scripts/verify-windows-runtime-integrity.js`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/desktop-release.yml`
- Modify: `tests/test_portable_final_zip_contract.py`
- Modify: `tests/test_desktop_packaging_assets.py`
- Modify: `docs/desktop-package.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`

**Interfaces:**
- Produces CLI: `node scripts/verify-windows-runtime-integrity.js <extracted-app-root> <version>`.
- CI and Release must invoke the same verifier after final ZIP extraction and before frozen-backend smoke.

- [x] **Step 1: Add failing packaging contracts**

```python
def test_windows_ci_verifies_runtime_identity_in_final_zip():
    assert "verify-windows-runtime-integrity.js $finalExtract $version" in workflow

def test_windows_release_verifies_runtime_identity_in_final_zip():
    assert "verify-windows-runtime-integrity.js $releaseFinalExtract $expectedVersion" in workflow
```

- [x] **Step 2: Run the packaging tests and verify RED**

Run: `python -m pytest tests/test_desktop_packaging_assets.py tests/test_portable_final_zip_contract.py -q`

Expected: FAIL because the final ZIP identity verifier is absent.

- [x] **Step 3: Implement the verifier calls and append-only Work24 records**

The CLI delegates to the same runtime verifier used by Electron. Update Chinese packaging documentation and the flat `[Unreleased]` changelog. Prepend Work24 as the current active Draft-Hold work while preserving all completed Work23 history unchanged.

- [x] **Step 4: Run targeted packaging/document checks**

Run: `python -m pytest tests/test_desktop_packaging_assets.py tests/test_portable_final_zip_contract.py -q`

Run: `python scripts/check_ai_assets.py`

Run: `git diff --check`

Expected: PASS.

---

### Task 5: Full verification, review, commit, push, and Draft PR

**Files:**
- Review every file changed by Tasks 1–4; do not stage unrelated files.

**Interfaces:**
- Produces one local commit on `agent/pp02-runtime-integrity-guard`.
- Produces one Draft PR targeting `main`.

- [x] **Step 1: Run affected suites**

Run: `cd apps/dsa-desktop && npm test`

Run: `python -m pytest tests/test_desktop_launch_contract.py tests/test_desktop_packaging_assets.py tests/test_portable_final_zip_contract.py -q`

Run: `python -m py_compile main.py tests/test_desktop_launch_contract.py`

- [x] **Step 2: Run repository gates**

Run: `python scripts/check_ai_assets.py`

Run: `./scripts/ci_gate.sh`

Run: `git diff --check`

Local evidence: Desktop `99/99`, scoped Python `34/34`, changed Python compile,
AI assets, syntax gate, and diff check pass. The complete backend aggregate is
deferred to exact-Head CI because the cloud worker could not fetch its missing
locked dependencies under the active network policy.

- [x] **Step 3: Perform scope/security self-review**

Confirm no malware-specific signature, machine path, credential, real data, executable, log, backup, version bump, dependency change, merge, Tag, or Release entered the diff. Confirm every production behavior was preceded by a test that failed for the expected missing behavior.

- [ ] **Step 4: Commit only the approved Work24 files**

```bash
git add <explicit Work24 paths>
git commit -m "fix: guard Windows desktop runtime integrity"
```

- [ ] **Step 5: Push and open a Draft PR**

Push the branch without force. Open a Draft PR titled `fix: guard Windows desktop runtime integrity`, targeting `main`, and describe root cause, generic defense, data-safety behavior, tests, Linux/Windows validation boundary, and prohibited release actions.

- [ ] **Step 6: Record remote identity without claiming CI prematurely**

Report branch, commit SHA, PR URL, Draft state, base/head, local validation, pending exact-Head CI, rollback (`revert` the Work24 commit), and `JUDGE=DRAFT_HOLD`.
