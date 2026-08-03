# Work13 Stock Analysis History Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent a manual stock-analysis task from reporting completion when its formal analysis-history write explicitly failed.

**Architecture:** Keep persistence in the existing legacy and Agent pipelines and reuse their existing run-diagnostic history evidence. Add one fail-closed API completion gate in `AnalysisService`, which is shared by synchronous and asynchronous stock-analysis callers.

**Tech Stack:** Python 3.12, pytest/unittest, existing run-diagnostics and FastAPI service/task layers.

## Global Constraints

- Base is `main@f5c7f43359ec81e27395d9bb236ec1cab0f6dcc2`.
- Do not change the database schema, installation, release workflows, model/provider configuration, prompts, notifications, market review, or period reports.
- Keep this PR Draft; do not Ready, merge, write `main`, create Tag, or create Release.
- Do not use real credentials or real user data.

---

### Task 1: Lock the failed-history completion contract

**Files:**
- Create: `tests/test_analysis_history_completion_contract.py`
- Modify: `src/services/analysis_service.py`
- Modify: `docs/CHANGELOG.md`

**Interfaces:**
- Consumes: `diagnostic_summary.components.history.status` and `.message` from the existing `AnalysisService._build_analysis_response()` result.
- Produces: `AnalysisService.analyze_stock()` returns `None` and sets `last_error` only when history status is explicitly `failed`.

- [ ] **Step 1: Write the failing regression test**

Create a focused test that runs the real service with a controlled pipeline. Emit
`record_history_run(report_saved=False, metadata_saved=False)` and assert the service returns
`None` with a persistence-specific `last_error`. Add the saved-history sibling case.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONPATH=. /tmp/pp02-work13-venv/bin/python -m pytest tests/test_analysis_history_completion_contract.py -q
```

Expected: the failed-history case fails because the current service returns a response.

- [ ] **Step 3: Implement the minimal completion gate**

Build the response once, read the existing nested history component defensively, and when its
status is `failed`, copy its non-empty message (or a fixed persistence failure fallback) to
`last_error`, log the failure without sensitive payloads, and return `None`. Otherwise return the
unchanged response.

- [ ] **Step 4: Run focused and relevant regression tests**

Run the focused test, the existing analysis-service/API contract tests, and the pipeline history
persistence tests. Confirm the RED case is GREEN and existing success behavior remains intact.

- [ ] **Step 5: Update changelog and verify repository gates**

Add one flat `[Unreleased]` fix line. Run Python compilation, `git diff --check`, AI asset check,
and the complete backend gate available in the environment. Record any environment-only gap
truthfully in the Draft PR.

- [ ] **Step 6: Commit and publish one Draft PR**

Commit only the product-scope files, push `agent/pp02-work13-analysis-history-contract`, and create
a Draft PR targeting `main`. The PR body must include Work12 symptom, root cause, TDD evidence,
checks, compatibility, risk, rollback, and the explicit no-Ready/no-merge/no-Tag/no-Release
boundary.
