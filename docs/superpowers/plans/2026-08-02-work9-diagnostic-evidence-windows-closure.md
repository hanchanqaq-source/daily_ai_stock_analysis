# Work9 Diagnostic Evidence and Windows Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore a cleanup-independent, redacted Windows installer diagnostic artifact, prove the
final ZIP contents, then use fixed-Head evidence to make and verify only the confirmed backend fix.

**Architecture:** Keep the existing PR #17 installer design. Make the verifier write a core stage
report before optional diagnostic collectors, isolate every collector failure, use a Windows
PowerShell-compatible path helper, and strengthen the real final-ZIP contract. Run one fixed-Head
diagnostic CI before any product fix.

**Tech Stack:** Windows PowerShell 5.1, PowerShell 7, NSIS/electron-builder 26.15.7, Electron 31.x,
Node 22 Desktop jobs, Node 20 standalone Web gate, Python/pytest contracts, GitHub Actions.

## Global Constraints

- Continue existing Draft PR #17 on `agent/pp02-work8-r7-installer-fix`.
- Preserve the assisted current-user installer, selectable directory, updater and portable ZIP.
- Do not change backend product behavior until a valid fixed-Head diagnostic artifact exists.
- Do not dump environments, raw commands, credentials, `.env`, databases, data, logs or user files.
- Keep diagnostics outside the verifier-owned install root and cleanup only validated owned roots.
- Do not Ready, merge, write `main`, tag, release or perform Windows real-machine actions.

---

### Task 1: Transfer the execution lock and freeze the Work9 contract

**Files:**
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`
- Create: `docs/superpowers/specs/2026-08-02-work9-diagnostic-evidence-windows-closure-design.md`

**Interfaces:**
- Consumes: PR #17 Head `9cb9a70e9176711096adf12ba5674c56d6f314d2` and Run `30742085965`.
- Produces: one active `HELD_BY_WORK_009` status and historical Work8
  `COMPLETED_WITH_BLOCKER` record.

- [x] Recheck GitHub PR, branch Head, CI and unique status truth.
- [x] Update the execution lock and Work9 scope without creating a parallel state file.
- [x] Run AI asset and diff checks, then commit the takeover records.

### Task 2: Reproduce and repair diagnostic preservation

**Files:**
- Modify: `scripts/tests/verify-windows-installer-contract.ps1`
- Modify: `scripts/verify-windows-installer.ps1`
- Modify: `tests/test_packaging_build_scripts.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/desktop-release.yml`

**Interfaces:**
- Consumes: failing Windows contract from Run `30742085965`.
- Produces: persistent `diagnostic-summary.txt`, stage report, sanitized bounded evidence and an
  uploadable directory for every contract/lifecycle failure.

- [ ] Record the existing Windows contract failure as RED and add a contract-stage persistence
  assertion before production changes.
- [ ] Run targeted Linux-readable contracts and confirm the new assertion fails for the expected
  missing behavior; retain Run `30742085965` as the real Windows RED.
- [ ] Add a normalized descendant-relative-path helper compatible with Windows PowerShell 5.1.
- [ ] Write the core diagnostic summary before optional collectors and guard each collector
  independently.
- [ ] Make contract failure output bounded and create an explicit uploadable stage report when the
  contract itself fails.
- [ ] Run targeted Python/Desktop checks and parse both workflow YAML files.

### Task 3: Prove the final ZIP runtime data

**Files:**
- Modify: `tests/test_portable_final_zip_contract.py`
- Modify only if RED proves a defect: `scripts/build-desktop.ps1`, `scripts/build-all.ps1`, or the
  existing portable manifest builder used by those scripts.

**Interfaces:**
- Consumes: final no-install ZIP and `pp02-portable-release.json.managedFiles`.
- Produces: a final-extract proof for `fake_useragent/data/browsers.jsonl` and a backend startup
  smoke from the final ZIP tree.

- [ ] Add a final-artifact assertion that identifies the browser data file by literal suffix and
  verifies it is a managed file.
- [ ] Run the final-ZIP contract and confirm RED only if the final artifact path actually drops the
  file; do not force a packaging change when the contract is already satisfied.
- [ ] If RED, implement the smallest copy/manifest correction and verify GREEN.
- [ ] Run related frozen-backend and portable-update regressions.

### Task 4: Publish one fixed-Head diagnostic run

**Files:**
- Modify as needed: Work9 task/return/status records and PR #17 body.

**Interfaces:**
- Consumes: locally verified diagnostic and final-ZIP contracts.
- Produces: one full commit SHA, one PR CI Run ID and a downloadable SHA/Run-bound diagnostic
  artifact on Windows PASS or FAIL.

- [ ] Commit and push the diagnostic enhancement to the existing PR branch.
- [ ] Confirm PR #17 remains Draft and its Head exactly matches the pushed full SHA.
- [ ] Inspect every job and the Windows job logs for that fixed Head.
- [ ] Fetch the diagnostic artifact, verify expected files and scan for prohibited content.
- [ ] If no valid artifact exists, stop at `ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT`.

### Task 5: Confirm and fix the installed-backend root cause

**Files:**
- Modify only the files directly identified by the artifact and code trace.
- Add the nearest real regression test for that component boundary.

**Interfaces:**
- Consumes: direct installed-backend error and artifact from Task 4.
- Produces: one confirmed root cause, one RED regression and one minimal GREEN fix.

- [ ] Record direct error, failing component, root cause, code/log evidence, packaged/development
  difference and minimal reproduction.
- [ ] Add one failing regression and run it to verify the expected RED.
- [ ] Implement one minimal fix without dependency consolidation or unrelated refactoring.
- [ ] Run targeted tests and verify GREEN plus related regressions.

### Task 6: Complete CI and stop at the merge gate

**Files:**
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`
- Modify: PR #17 body through the GitHub app.

**Interfaces:**
- Consumes: final implementation Head and complete CI.
- Produces: truthful Judge and the exact next authorization requirement.

- [ ] Run complete relevant local verification and fixed-Head PR CI.
- [ ] Verify installer/ZIP, install, first start, backend health, exit, restart, uninstall and
  diagnostic artifact results from the Windows job.
- [ ] Synchronize unique status truth, handoff, return, roadmap and PR body to the actual Head/Run.
- [ ] Keep PR #17 Draft and stop before Ready/merge with `NEXT_APPROVAL_REQUIRED=MERGE_PR_17` only
  if every required CI result is successful.
