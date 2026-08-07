# Work32 Final Usability Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to execute this plan task-by-task. Work32 is
> intentionally executed by the primary worker without subagents.

**Goal:** Produce one unpublished exact-Head Windows candidate that proves
installed API-key/AI-configuration persistence and the complete bounded Windows
lifecycle, with failure diagnostics and security evidence, before any usability
claim.

**Architecture:** Extend the shared PowerShell lifecycle verifier with bounded
owned-process execution and a real installed-configuration acceptance phase. Use
a loopback OpenAI-compatible mock and the packaged Electron `safeStorage` vault
to prove synthetic-key use after restart. Keep diagnostics pre-created,
sanitized, and always uploaded, then bind candidate artifacts and Defender reports
to one frozen Draft PR Head.

**Tech Stack:** PowerShell 7, Electron `safeStorage`, Node.js standard library and
`node:test`, FastAPI installed endpoints, LiteLLM-compatible OpenAI protocol,
pytest workflow contracts, GitHub Actions, Microsoft Defender, SHA-256.

## Global constraints

- Fixed Base: `main@295821e463674e9f82a79a75a0a13052ef1cb696`.
- Branch: `agent/pp02-work32-final-usability-closure`.
- Use only exact-Head synthetic credentials and verifier-owned `RUNNER_TEMP` data.
- Do not read real API keys, `.env` values, databases, history, watchlists,
  reports, or any user profile path.
- Do not change dependencies, schemas, product features, versions, or release
  assets outside the existing candidate flow.
- Do not retry Defender scans or security verdicts.
- Stop at one Draft PR and exact-Head evidence. Do not Ready, merge, tag, or
  release.

---

### Task 1: Lock the approved Work32 contract

**Files:**
- Create: `docs/superpowers/specs/2026-08-07-work32-final-usability-closure-design.md`
- Create: `docs/superpowers/plans/2026-08-07-work32-final-usability-closure.md`
- Modify later: `_ai-dev/PROJECT_STATUS.md`
- Modify later: `_ai-dev/AI_HANDOFF.md`
- Modify later: `_ai-dev/WORK_TASK.md`
- Modify later: `_ai-dev/WORK_RETURN.md`
- Modify later: `docs/ROADMAP.md`
- Modify later: `docs/pp02/REBUILD_ROADMAP.md`

- [ ] Record the approved hard gates, fixed Base, non-goals, and Draft Hold.
- [ ] Commit the design and plan before implementation.
- [ ] Confirm `git status`, branch, Base, and no dependency/user-data changes.

### Task 2: Bound installer and uninstaller processes with RED/GREEN contracts

**Files:**
- Modify: `scripts/verify-windows-installer.ps1`
- Modify: `scripts/tests/verify-windows-installer-contract.ps1`
- Modify: `tests/test_packaging_build_scripts.py`

**Interface:**

`Invoke-BoundedOwnedProcess -FilePath <absolute-owned-path> -ArgumentList <list>
-TimeoutSeconds <positive-int> -Stage <safe-name> -StageReportPath <owned-path>`
returns the exit code only after a clean bounded exit. Timeout terminates the
owned tree, records `TIMEOUT`, and throws without child output.

- [ ] Add a PowerShell contract fixture whose fake installer exceeds a short
  timeout; require bounded exit, a timeout stage record, stable failure marker,
  cleanup, and sanitized diagnostics.
- [ ] Add a successful short-child counterexample and invalid-timeout rejection.
- [ ] Add pytest source/workflow contracts requiring bounded install, normal
  uninstall, and cleanup uninstall paths.
- [ ] Run RED:
  `python -m pytest tests/test_packaging_build_scripts.py -q` and, on Windows,
  `pwsh -File scripts/tests/verify-windows-installer-contract.ps1`.
- [ ] Implement the smallest shared helper and replace every unbounded lifecycle
  `Start-Process -Wait` call.
- [ ] Run GREEN and mutate one uninstaller back to `-Wait` to prove the contract
  catches the regression; restore and rerun.

### Task 3: Guarantee diagnostic continuation after lifecycle failure

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/desktop-release.yml`
- Modify: `tests/test_packaging_build_scripts.py`
- Modify: `tests/test_desktop_release_workflow.py`

- [ ] Add failing workflow contracts requiring a finite lifecycle
  `timeout-minutes`, a shorter internal process timeout, diagnostic upload
  immediately after lifecycle with `if: always()`, and strict missing-file
  behavior for ordinary CI.
- [ ] Run RED:
  `python -m pytest tests/test_packaging_build_scripts.py tests/test_desktop_release_workflow.py -q`.
- [ ] Add the same bounded lifecycle parameters to CI and release. Put the outer
  watchdog on the lifecycle step only, never on the entire Job.
- [ ] Ensure the pre-created stage report path matches the always-uploaded
  artifact path before invoking the verifier.
- [ ] Run GREEN and YAML parsing. Confirm candidate/security uploads remain after
  the lifecycle and cannot run on failure.

### Task 4: Add the synthetic loopback smoke server and real DPAPI vault harness

**Files:**
- Create: `apps/dsa-desktop/tests/installed-config-smoke-server.js`
- Create: `apps/dsa-desktop/tests/windows-installed-config-vault-harness.js`
- Create: `apps/dsa-desktop/tests/installed-config-acceptance.test.js`
- Modify: `apps/dsa-desktop/package.json` only if a test script entry is needed;
  do not change dependencies.

**Interfaces:**

- Mock server input: loopback port, expected exact-Head key hash, receipt path,
  bounded lifetime. Output: OpenAI chat-completion JSON and a receipt containing
  only `authorizationMatched`, request count, route, and model.
- Vault harness input: verifier-owned app-data root, config version, credential
  key name, synthetic secret through inherited process environment. Output:
  stable PASS/FAIL marker only; no secret, ciphertext, or environment dump.

- [ ] Write Node RED tests requiring localhost-only binding, request/body/time
  bounds, exact `/v1/chat/completions` acceptance, wrong/missing Authorization
  rejection, valid response shape, safe receipt, and zero key leakage to stdout,
  stderr, or receipt.
- [ ] Write RED tests for the harness contract: real `safeStorage`, product-name
  binding, dynamic AIHubMix key, exact config-version binding, verifier-owned root,
  and no secret logging.
- [ ] Run RED:
  `node --test apps/dsa-desktop/tests/installed-config-acceptance.test.js`.
- [ ] Implement with Node/Electron standard facilities and existing
  `CredentialVault`; do not add packages.
- [ ] Run GREEN plus wrong-key, wrong-version, oversized-body, and timeout
  counterexamples.

### Task 5: Prove installed save, restart, actual key use, and non-leakage

**Files:**
- Modify: `scripts/verify-windows-installer.ps1`
- Modify: `scripts/tests/verify-windows-installer-contract.ps1`
- Modify: `scripts/scan-windows-fake-credential.js` only if an additional closed
  path type needs support; do not weaken existing detection.
- Modify: `tests/test_packaging_build_scripts.py`

**Installed acceptance sequence:**

1. Set `APPDATA` and `LOCALAPPDATA` to exact verifier-owned children of
   `RUNNER_TEMP` before first installed start.
2. Start the installed app and resolve its backend port from allow-listed startup
   evidence.
3. Call `/api/v1/system/config/validate` with fresh AIHubMix,
   `GENERATION_BACKEND=codex_cli`, explicit LiteLLM fallback, protocol/base URL,
   and historical/default model fields.
4. PUT `/api/v1/system/config` with public fields and the mask placeholder;
   capture the returned configuration version without dumping response bodies.
5. Stop the app, run the Electron vault harness with the synthetic secret, and
   restart the app.
6. GET configuration and require public persistence plus masked secret.
7. POST `/api/v1/system/config/generation-backends/smoke-test` for `litellm` in
   JSON mode; require service success and the mock's safe authorization receipt.
8. GET configuration export and complete-backup export to verifier-owned files.
9. Scan the exact synthetic key across public config, exports, backup, candidate
   archives, installed root, verifier app data, mock artifacts, and diagnostics.

- [ ] Add source and fixture RED contracts for every step and ordering above.
- [ ] Require every HTTP/process wait to have a declared finite timeout and all
  error summaries to use bounded allow-listed fields.
- [ ] Run RED focused pytest and Node contracts.
- [ ] Implement the minimal PowerShell orchestration and cleanup.
- [ ] Run GREEN; then remove the smoke receipt check and prove its dedicated test
  fails before restoring it.
- [ ] On Windows, run the complete verifier contract with only synthetic data.

### Task 6: Run local hard gates and synchronize the truth files

**Files:**
- Modify: `docs/CHANGELOG.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`

- [ ] Run focused Node, Desktop, Web, Python/Actions, PowerShell-available,
  AI-asset, YAML, syntax, and `git diff --check` gates.
- [ ] Run full Desktop and Web suites and the repository's complete Python suite
  where the locked environment supports them; distinguish environment skips from
  passes.
- [ ] Inspect the complete Base-to-Head diff for dependencies, real credentials,
  user data, schema/version changes, scope drift, security weakening, and unsafe
  diagnostic text.
- [ ] Update truth files with observed RED/GREEN counts only. Keep candidate,
  remote CI, hashes, and Defender verdict `PENDING`; keep Judge `DRAFT_HOLD`.
- [ ] Commit the reviewed implementation and evidence synchronization.

### Task 7: Open one Draft PR and verify the frozen candidate

**Files:**
- Modify only Work32 truth files if remote evidence requires a final append-only
  synchronization commit.

- [ ] Push the scoped branch and create exactly one Draft PR into `main` with
  root cause, security model, tests, rollback, hard gates, and explicit Draft
  Hold.
- [ ] Require one final exact-Head CI where all applicable Jobs pass. Native Jobs
  that are path-skipped do not satisfy this gate.
- [ ] Require Windows evidence for install/start/save/DPAPI/restart/actual mock
  request/exports/non-leakage/uninstall, strict diagnostics upload, Defender, and
  candidate upload.
- [ ] Download only the final Run's artifacts. Verify artifact-to-Head binding,
  member names, candidate version, and SHA-256 for artifact ZIP, installer, and
  portable archive; cross-check Defender target hashes and clean status.
- [ ] If any hard gate fails, diagnose and fix only within this approved scope,
  create a new Head, and rerun the entire required gate set. Never relabel a
  partial or stale Run as final evidence.
- [ ] Return a factual closure report. Only after every hard gate passes may the
  candidate be described as usable; it remains unsigned, unpublished, and Draft.
  Do not Ready, merge, tag, or release.
