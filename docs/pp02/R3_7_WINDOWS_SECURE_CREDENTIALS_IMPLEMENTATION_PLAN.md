# R3.7 Windows Secure Credentials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store Windows Desktop secrets only through Electron safeStorage/DPAPI, keep plaintext out of `.env` and exports, and prove the contract on a fixed PR Head with fake credentials.

**Architecture:** A focused Electron `CredentialVault` owns encrypted-at-rest secret values in `userData`. The existing backend remains the configuration consumer and receives decrypted values only in its child-process environment; the Web renderer gets narrow write/status IPC and never gets a plaintext read path. The backend continues to own non-sensitive `.env` settings and enforces masking/export rules.

**Tech Stack:** Electron 31 `safeStorage`, Node.js built-ins, React/TypeScript, Python/FastAPI, Node test runner, pytest, GitHub Actions Windows runner.

## Global Constraints

- Base is exactly `main@097bb5d60aa42f13737ac4d9db2f582bde50f995`.
- Branch is `agent/pp02-work3-r3-7-windows-secure-credentials`.
- Use fake credentials only; never read, copy, print, upload, or migrate a real `.env` or real secret.
- Keep the PR Draft. Do not Ready, merge, write `main`, Tag, Release, or enter a later phase.
- Windows Desktop has one persistent credential fact source: the versioned safeStorage vault.
- Exported configuration contains neither plaintext secrets nor vault ciphertext.
- Non-Windows/Desktop deployment behavior remains compatible.

---

### Task 1: Credential policy and encrypted vault

**Files:**
- Create: `apps/dsa-desktop/secure-credentials/sensitiveKeys.js`
- Create: `apps/dsa-desktop/secure-credentials/credentialVault.js`
- Create: `apps/dsa-desktop/tests/credential-vault.test.js`
- Test: `tests/test_windows_secure_credential_contract.py`

**Interfaces:**
- Produces: `isSensitiveConfigKey(key) -> boolean`.
- Produces: `CredentialVault.status()`, `prepare(items, maskToken)`, `commit(transaction)`, `rollback(transaction)`, and `buildEnvironment()`.
- Vault values are DPAPI ciphertext base64 only; no method returns plaintext to renderer-facing code.

- [ ] Write Node tests for support gates, key validation, mask no-op, set/delete, atomic write, corrupt vault, wrong product/version, decrypt failure, and no plaintext at rest.
- [ ] Run `node --test apps/dsa-desktop/tests/credential-vault.test.js` and verify RED because the modules do not exist.
- [ ] Implement the minimum policy/vault modules.
- [ ] Re-run the focused Node test and verify GREEN.
- [ ] Add the Python contract test that compares registered `is_sensitive` fields with the Desktop classifier and verifies package inclusion.
- [ ] Commit with `feat: add Windows DPAPI credential vault`.

### Task 2: Backend masking, secure-mode write gate, and safe export/import

**Files:**
- Modify: `src/core/config_manager.py`
- Modify: `src/services/system_config_service.py`
- Modify: `api/v1/schemas/system_config.py`
- Modify: `api/v1/endpoints/system_config.py`
- Modify: `tests/test_config_manager.py`
- Modify: `tests/test_system_config_service.py`
- Modify: `tests/test_system_config_api.py`

**Interfaces:**
- Produces: `ConfigManager.remove_keys(keys)` atomic removal.
- Produces: `credential_source` / secure existence metadata without plaintext.
- Secure mode is selected only by `DSA_SECURE_CREDENTIAL_MODE=windows_dpapi`.

- [ ] Add failing tests proving every sensitive field is masked, secure-mode plaintext saves/imports are rejected, and export strips sensitive assignments while retaining non-sensitive content/comments.
- [ ] Run the three focused pytest modules and verify RED at the new assertions.
- [ ] Implement atomic sensitive-key removal, secure runtime metadata, universal sensitive masking, safe export, and explicit import rejection.
- [ ] Re-run focused pytest tests and verify GREEN.
- [ ] Commit with `feat: enforce secure Desktop config boundary`.

### Task 3: Desktop IPC, backend bootstrap, and restart transaction

**Files:**
- Modify: `apps/dsa-desktop/main.js`
- Modify: `apps/dsa-desktop/preload.js`
- Modify: `apps/dsa-desktop/tests/main.test.js`
- Modify: `apps/dsa-desktop/tests/preload.test.js`
- Modify: `apps/dsa-desktop/package.json`

**Interfaces:**
- Preload exposes only `getSecureCredentialStatus`, `prepareSecureCredentialUpdate`, `commitSecureCredentialUpdate`, `rollbackSecureCredentialUpdate`, and `finalizeSecureCredentialUpdate`.
- Main validates sender/main frame and owns all transaction state.
- Backend env receives `DSA_SECURE_CREDENTIAL_MODE`, `DSA_SECURE_CREDENTIAL_KEYS`, and decrypted key/value pairs.

- [ ] Add failing IPC/preload/main tests for sender rejection, absence of read API, environment injection, transaction rollback, `.env` cleanup, and backend restart.
- [ ] Run Desktop tests and verify RED.
- [ ] Wire the vault into main/preload, package files, backend launch context, and safe restart.
- [ ] Re-run Desktop tests and verify GREEN.
- [ ] Commit with `feat: connect Desktop secure credential IPC`.

### Task 4: Web settings integration and user-facing contract

**Files:**
- Modify: `apps/dsa-web/src/api/systemConfig.ts`
- Modify: `apps/dsa-web/src/types/systemConfig.ts`
- Modify: `apps/dsa-web/src/hooks/useSystemConfig.ts`
- Modify: `apps/dsa-web/src/pages/SettingsPage.tsx`
- Modify: `apps/dsa-web/src/i18n/uiText.ts`
- Modify: `apps/dsa-web/src/api/__tests__/systemConfig.test.ts`
- Modify: `apps/dsa-web/src/hooks/__tests__/useSystemConfig.test.tsx`
- Modify: `apps/dsa-web/src/pages/__tests__/SettingsPage.test.tsx`

**Interfaces:**
- `systemConfigApi.update()` keeps the public caller contract and coordinates secure Desktop transactions internally.
- Desktop config export remains `.env` text but explicitly excludes credentials.

- [ ] Add failing Web tests for Desktop secure save, rollback on backend failure, masked refresh, and credential-free export copy.
- [ ] Run the focused Vitest suite and verify RED.
- [ ] Implement the secure transaction coordinator and update explanatory copy.
- [ ] Re-run focused Vitest and build; verify GREEN.
- [ ] Commit with `feat: route Windows secrets through safeStorage`.

### Task 5: Windows fake-key harness and CI gate

**Files:**
- Create: `apps/dsa-desktop/tests/windows-secure-credential-harness.js`
- Create: `scripts/verify-windows-secure-credentials.ps1`
- Modify: `.github/workflows/ci.yml`
- Modify: `tests/test_packaging_build_scripts.py`

**Interfaces:**
- PowerShell verifier exits non-zero unless real Electron safeStorage encrypt/decrypt succeeds on Windows and all leak scans pass.
- The Windows CI job prints only pass/fail metadata and Head SHA, never the fake secret value.

- [ ] Add failing packaging/CI contract tests for the missing harness step.
- [ ] Run the focused contract test and verify RED.
- [ ] Implement the Electron harness and invoke it in `desktop-futu-package-windows` before candidate upload.
- [ ] Re-run local contract tests and verify GREEN.
- [ ] Commit with `test: gate Windows safeStorage with fake credentials`.

### Task 6: Documentation, ledgers, and full verification

**Files:**
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `docs/ERRORS_AND_LESSONS.md`
- Modify: `docs/desktop-package.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/PROJECT_CONTROL.md`
- Modify: `docs/OPEN_BLOCKERS.md`

**Interfaces:**
- Ledgers record facts only: base/head, tests, CI, Windows acceptance, Judge, blockers, and authorization locks.

- [ ] Update product docs and append-only lessons without adding real values, screenshots, artifacts, or transient logs.
- [ ] Run `git diff --check`, `python scripts/check_ai_assets.py`, focused Node/Python/Web tests, full Desktop tests, full offline backend gate, Web blocking tests/build, and secret-pattern scans.
- [ ] Review the complete diff against the threat model and fix Critical/Important findings.
- [ ] Commit with `docs: record R3.7 secure credential contract`.

### Task 7: Draft PR, full CI, and fixed-Head Windows acceptance

**Files:**
- Update only evidence fields in the Task 6 ledgers and Draft PR body after remote results exist.

**Interfaces:**
- Draft PR targets `main`; CI and Windows evidence must bind to the exact final Head SHA.

- [ ] Push the independent branch and create a Draft PR.
- [ ] Verify PR state is Draft, base is `main`, and no Tag/Release/main write occurred.
- [ ] Wait for all eight blocking CI jobs; diagnose and fix only R3.7-scope failures.
- [ ] Confirm the Windows fake-key harness ran in the Windows job on the same final Head.
- [ ] Re-run final-Head CI if evidence-only commits change the Head.
- [ ] Record final Head, Run, job results, fake-key acceptance, unresolved review threads, and `DRAFT_HOLD` Judge.

