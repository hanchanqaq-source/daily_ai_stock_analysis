# Work27 Configuration Save Validation Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make first-run Windows Desktop AI-channel saves succeed without writing plaintext credentials to `.env`, and show the exact validation field and reason when a save is rejected.

**Architecture:** Keep the existing Desktop vault transaction and backend version-binding sequence. During the backend persistence step, replace only pending LLM API credentials with the existing mask token so backend cross-field validation can recognize them while `ConfigManager` continues to skip them on disk; keep the previous omission behavior for format-validated non-LLM secrets. Separately unwrap FastAPI's `detail.issues` envelope and surface a bounded `field: reason` message.

**Tech Stack:** React/TypeScript, Vitest, Electron IPC/safeStorage, FastAPI system-config API, Python `SystemConfigService`, GitHub Actions.

## Global Constraints

- Base is fixed at `main@4322e7ddf09b8262c0e7279af9e321aec4f77758`.
- Use only synthetic credential strings; never read or embed a real API key.
- Do not modify or migrate the user database, analysis history, watchlist, or period reports.
- Do not change dependency versions, backend configuration semantics, credential storage, or release version.
- Stop at one Draft PR plus exact-Head complete CI and Windows installer lifecycle evidence.
- Do not Ready, merge, write `main`, create a Tag, or create a Release.

---

### Task 1: Lock the Desktop secure-save and validation-error contracts

**Files:**
- Modify: `apps/dsa-web/src/api/__tests__/systemConfig.test.ts`
- Test: `apps/dsa-web/src/api/__tests__/systemConfig.test.ts`

**Interfaces:**
- Consumes: `systemConfigApi.update(UpdateSystemConfigRequest)` and the existing `window.dsaDesktop` write-only transaction bridge.
- Produces: regression contracts for `LLM_AIHUBMIX_API_KEY`, `GENERATION_BACKEND=codex_cli`, legacy provider fields, plaintext exclusion, and FastAPI `detail.issues` errors.

- [x] **Step 1: Write failing first-run AIHubMix and codex_cli/LiteLLM tests**

Add table-driven Desktop update cases whose bridge reports the submitted API-key field in `handledKeys`. Each expected backend PUT must retain all public fields and substitute `******` for the handled LLM credential; serialize the request and assert that the synthetic plaintext is absent.

- [x] **Step 2: Write the failing historical-default-fields test**

Submit `LITELLM_MODEL`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_VISION_MODEL`, and `OPENAI_API_KEY`; require the four public legacy values to remain unchanged and the key to be represented only by `******`.

- [x] **Step 3: Write the failing structured-error test**

Reject the backend PUT with status 400 and this shape:

```ts
{
  detail: {
    error: 'validation_failed',
    message: 'System configuration validation failed',
    issues: [{
      key: 'LLM_AIHUBMIX_API_KEY',
      code: 'missing_api_key',
      message: 'AIHubMix API Key 不能为空',
      severity: 'error',
    }],
  },
}
```

Assert that `SystemConfigValidationError.issues` contains the issue and `parsedError.message` contains both the field key and reason.

- [x] **Step 4: Run the focused test and verify RED**

Run: `cd apps/dsa-web && npm test -- src/api/__tests__/systemConfig.test.ts`

Expected: the secure-save cases fail because handled keys are omitted from the backend PUT, and the error case fails because nested issues are lost.

### Task 2: Implement the minimum client fix

**Files:**
- Modify: `apps/dsa-web/src/api/systemConfig.ts`
- Test: `apps/dsa-web/src/api/__tests__/systemConfig.test.ts`

**Interfaces:**
- Consumes: `prepared.handledKeys`, `payload.maskToken`, FastAPI error response data.
- Produces: a backend-safe update item list and a `SystemConfigValidationError` with structured issues plus a user-visible detailed message.

- [x] **Step 1: Preserve handled LLM API credentials as mask-token placeholders**

Replace the filter that removes `handledKeys` with a mapping that substitutes the
mask token only when the handled key is a legacy LLM API credential or matches
`LLM_<CHANNEL>_API_KEY(S)`. Continue omitting other handled secrets such as
format-validated notification URLs.

```ts
const backendItems = payload.items.flatMap((item) => {
  if (!handledKeys.has(item.key.toUpperCase())) return [item];
  return isPendingLLMCredentialKey(item.key)
    ? [{ key: item.key, value: maskToken }]
    : [];
});
```

Send `backendItems` with `reloadNow: false`. Do not alter the prepare → backend save → vault commit → sanitize/restart/finalize order.

- [x] **Step 2: Unwrap and format validation issues**

Parse either top-level validation fields or FastAPI's nested `detail` object. Preserve the complete structured issue array and build a message of at most 600 characters from the first three issues plus a remaining-count suffix; fall back to the parsed server message only when no issue exists.

- [x] **Step 3: Add review counterexamples and backend characterization**

Prove that a vault-owned `DINGTALK_WEBHOOK_URL` is still omitted instead of
replaced with an invalid mask URL. Add a service-level fresh-install AIHubMix
contract asserting that the mask is accepted for cross-field validation, public
fields are written, the mask and API-key field are absent from `.env`, and a
fresh mask no-op has `skipped_masked_count == 0`.

- [x] **Step 4: Run the focused test and verify GREEN**

Run: `cd apps/dsa-web && npm test -- src/api/__tests__/systemConfig.test.ts`

Expected: all system-config API tests pass, the plaintext-exclusion assertions pass, and the nested error is visible by field and reason.

- [x] **Step 5: Run the hook regression suite**

Run: `cd apps/dsa-web && npm test -- src/hooks/__tests__/useSystemConfig.test.tsx`

Expected: legacy provider fields remain in save payloads and structured issues continue to bind to settings fields.

### Task 3: Synchronize Work27 evidence and verify the candidate

**Files:**
- Modify: `docs/CHANGELOG.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`
- Modify: `docs/superpowers/plans/2026-08-06-work27-config-save-validation.md`

**Interfaces:**
- Consumes: fixed base, RED/GREEN output, full local verification, final commit/PR/CI evidence.
- Produces: one auditable Work27 Draft PR with an exact Head and no release action.

- [x] **Step 1: Record the user-visible fix and active Work27 contract**

Add one flat `[Unreleased]` changelog line. Prepend Work27 current sections to the five PP02 control documents, correcting the stale Work25 current state from GitHub facts without rewriting completed history.

- [x] **Step 2: Run local verification**

Run:

```bash
cd apps/dsa-web && npm test
cd apps/dsa-web && npm run lint
cd apps/dsa-web && npm run build
python scripts/check_ai_assets.py
git diff --check
```

Also run the existing backend mask-noop contract when the locked Python dependencies are available; otherwise record the local dependency gap and require exact-Head CI to supply that evidence.

- [x] **Step 3: Review scope and secret safety**

Inspect `git diff --stat`, `git diff`, and `git status -sb`; confirm there are no dependency-lock, database, `.env`, credential, version, workflow, Tag, or Release changes.

- [ ] **Step 4: Commit, push, and create one Draft PR**

Commit message: `fix: preserve secure config validation context`

Push `agent/pp02-work27-config-save-validation`, then create a Draft PR into `main` describing root cause, minimal fix, RED/GREEN proof, security boundary, risks, rollback, and the explicit no-Ready/no-merge/no-release hold.

- [ ] **Step 5: Lock the final remote Head and wait for complete CI**

Require all applicable jobs to finish for exactly the final PR Head. In the Windows job, require final Web/Desktop packaging, candidate installer creation, install, first start/health, clean exit, restart/health, official uninstall, and zero owned-process residuals. Record artifact identity if exposed by the workflow.

- [ ] **Step 6: Stop at Draft Hold**

Report root cause, changed files, RED/GREEN and full validation results, exact PR Head/Run, and Windows candidate status. Do not mark Ready, merge, tag, or release.
