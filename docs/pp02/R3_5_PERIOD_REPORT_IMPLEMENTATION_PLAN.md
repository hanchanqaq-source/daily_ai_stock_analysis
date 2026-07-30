# R3.5 Period Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:test-driven-development` to implement every production behavior.
> This Work is executed inline on the existing Draft PR branch; do not dispatch
> subagents or open a second route.

**Goal:** Build an application-only manual period report with seven correct date
windows, separated stock/ETF and market-review aggregation, and a traceable
next-week outlook derived only from existing qualified history.

**Architecture:** `PeriodReportService` owns deterministic date windows,
history aggregation, conditional outlook derivation, and snapshot lookup/save.
It reads report facts only through `HistoryService.get_history_list()` and
stores outlook snapshots in the existing `AnalysisHistory` table with
`report_type=period_outlook`. One FastAPI endpoint exposes explicit manual
generation, and one React page renders the seven entrances without making an
initial request.

**Tech Stack:** Python 3.10+, SQLAlchemy, FastAPI/Pydantic v2, pytest, React 19,
TypeScript, Axios, Vitest, Testing Library, Vite.

## Global Constraints

- Continue Draft PR #3 from
  `a5b999717e57fe3c78da5c65adadcb1f05b71f95`.
- Do not create a second history fact table or add database columns.
- Do not call AI, market data, news, notification, scheduler, or GitHub Actions
  scheduling code.
- Do not add funds, user profiles, multi-user isolation, R3.6, or R3.7.
- Only `next_week` writes a snapshot, and only after an explicit API POST.
- Keep PR Draft. Do not merge, update `main`, publish a Release, or use real
  credentials/data.

---

### Task 1: Deterministic period windows and separated history aggregation

**Files:**

- Create: `src/services/period_report_service.py`
- Create: `tests/test_period_report_service.py`

**Interfaces:**

- Produces:
  `PeriodReportService.resolve_window(period: str, as_of: date) -> PeriodWindow`
- Produces:
  `PeriodReportService.generate(period: str, as_of: date | None = None) -> dict`
- Consumes:
  `HistoryService.get_history_list(start_date, end_date, page, limit)`

- [ ] Write table-driven RED tests for all seven windows, including
  `2026-01-01`, a month end, and a year-crossing previous week.
- [ ] Run
  `python -m pytest tests/test_period_report_service.py -q`; verify failures
  are missing service/import behavior.
- [ ] Implement immutable `PeriodWindow(period, start_date, end_date)` and
  calendar-month subtraction without adding a dependency.
- [ ] Write RED fixtures containing stock, ETF, market-review, and
  `period_outlook` rows; assert stock/ETF and market reviews remain separate
  and outlook rows are excluded.
- [ ] Implement paginated history reads through `HistoryService` only, with
  formal report types limited to `simple`, `detailed`, and `full`.
- [ ] Re-run the service tests and keep them GREEN.

### Task 2: Conditional next-week outlook and traceable snapshot

**Files:**

- Modify: `src/services/period_report_service.py`
- Modify: `src/storage.py`
- Modify: `tests/test_period_report_service.py`

**Interfaces:**

- Produces:
  `DatabaseManager.save_period_outlook_snapshot(*, query_id: str,
  snapshot: dict, created_at: datetime) -> int`
- Produces outlook items with:
  `stock_code`, `stock_name`, `asset_type`, `tendency`, `confidence`,
  `historical_signals`, `risks`, `invalidation_conditions`,
  `data_as_of`, `source_record_count`, `source_record_ids`.

- [ ] Write RED tests proving records older than 14 calendar days and records
  without an interpretable direction cannot create an outlook.
- [ ] Write RED tests for bullish, neutral, and bearish mappings; confidence;
  source IDs; risks; support/resistance-based invalidation; and the exact
  insufficient-data message.
- [ ] Implement strict signal extraction from persisted list/detail fields.
  Never synthesize a target price or deterministic wording.
- [ ] Write a RED persistence test proving `next_week` creates one
  `AnalysisHistory(report_type="period_outlook", code="PERIOD")` row whose
  snapshot contains the target week and all source IDs.
- [ ] Implement the dedicated storage write using the existing transaction
  helper and table; do not add schema.
- [ ] Write a RED test proving a later `previous_week` report returns the
  latest stored snapshot whose target dates exactly match that week.
- [ ] Implement readback and comparison without including snapshot rows in
  actual-period aggregation.
- [ ] Re-run service tests and keep them GREEN.

### Task 3: Manual FastAPI contract

**Files:**

- Create: `api/v1/schemas/period_report.py`
- Create: `api/v1/endpoints/period_report.py`
- Modify: `api/v1/endpoints/__init__.py`
- Modify: `api/v1/router.py`
- Create: `tests/test_period_report_api.py`

**Interfaces:**

- Consumes: `PeriodReportService.generate(period)`
- Produces: `POST /api/v1/period-report/generate`
- Request: `{ "period": "week_to_date" | "previous_week" | "next_week" |
  "weeks_5" | "weeks_10" | "month_1" | "months_2" }`

- [ ] Write RED API tests for the seven accepted values, invalid values,
  dependency injection, separated response sections, and the insufficient
  outlook message.
- [ ] Add strict Pydantic response models for period metadata, asset summaries,
  market reviews, outlook items, snapshot metadata, and matched prior outlook.
- [ ] Implement one POST route. It must not import or call analyzer, LLM,
  notifier, scheduler, or market data modules.
- [ ] Run
  `python -m pytest tests/test_period_report_api.py tests/test_period_report_service.py -q`
  and keep it GREEN.

### Task 4: Formal Web page with explicit generation

**Files:**

- Create: `apps/dsa-web/src/types/periodReport.ts`
- Create: `apps/dsa-web/src/api/periodReport.ts`
- Create: `apps/dsa-web/src/pages/PeriodReportPage.tsx`
- Create: `apps/dsa-web/src/pages/__tests__/PeriodReportPage.test.tsx`
- Modify: `apps/dsa-web/src/App.tsx`
- Modify: `apps/dsa-web/src/App.test.tsx`
- Modify: `apps/dsa-web/src/components/layout/SidebarNav.tsx`
- Modify: `apps/dsa-web/src/i18n/uiText.ts`
- Modify: `apps/dsa-web/src/locales/featureText.ts`

**Interfaces:**

- Consumes: `POST /api/v1/period-report/generate`
- Route: `/period-report`
- Navigation label: `周期报告` / `Period report`

- [ ] Write RED page tests proving all seven entrances render, initial mount
  performs zero API calls, and clicking the action sends exactly one request.
- [ ] Write RED render tests for stock/ETF separation, market-review separation,
  insufficient data, prior-outlook comparison, disclaimer, loading, and API
  failure.
- [ ] Implement typed API conversion through the existing Axios client and
  `toCamelCase`.
- [ ] Implement the page with existing `Card`, `Badge`, `EmptyState`,
  `ApiErrorAlert`, and button styles. Do not expose internal rule IDs.
- [ ] Add lazy route, sidebar item, and bilingual UI text.
- [ ] Run
  `npm test -- --run src/pages/__tests__/PeriodReportPage.test.tsx src/App.test.tsx`.
- [ ] Run `npm run lint` and `npm run build`.

### Task 5: Blocking gates, documentation, and Draft PR evidence

**Files:**

- Modify: `.github/workflows/ci.yml` only if the current Web gate does not run
  the new page test.
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/RUNBOOK.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/pp02/R2_MIGRATION_EXECUTION_PLAN.md`

- [ ] Confirm the Web CI test step includes
  `PeriodReportPage.test.tsx`; write a workflow change only when required.
- [ ] Run Python compile checks for all changed Python files.
- [ ] Run service/API专项 tests, Web page tests, Web lint/build, AI governance,
  `git diff --check`, and `./scripts/ci_gate.sh`.
- [ ] Review the full diff for no scheduler, model, notifier, fund, profile,
  or second-table changes.
- [ ] Commit intended files with English messages and push the existing branch.
- [ ] Verify the new PR Head and all blocking GitHub Actions jobs.
- [ ] If CI fails, use `superpowers:systematic-debugging`, reproduce the root
  cause, add a RED regression test, and make the smallest in-scope fix.
- [ ] Record exact test counts, final Commit/Head, CI run, Draft state, no-AI
  and no-automation evidence, then run the final Head CI before Judge `PASS`.
