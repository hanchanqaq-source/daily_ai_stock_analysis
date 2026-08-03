# Work13 Stock Analysis History Completion Design

## Context

Work12 accepted the released `v3.29.1` Windows application far enough to submit a manual
`600519` stock analysis, but no formal stock history record appeared. The same installation
successfully persisted market-review history and generated a period report, so this Work does not
change installation, database schema, or report generation.

The current API path is:

1. `POST /api/v1/analysis/analyze` submits an asynchronous stock task.
2. `AnalysisService.analyze_stock()` runs either the legacy or Agent pipeline.
3. Both pipeline variants call `save_analysis_history()` and record the outcome in the existing
   run-diagnostic `history_runs` collection.
4. `AnalysisService._build_analysis_response()` already exposes that evidence as
   `diagnostic_summary.components.history.status`.
5. The service currently returns the response even when that status is `failed`; the task queue
   consequently publishes `task_completed`, and the Web refresh finds no formal history row.

## Approved Approach

Add one completion gate in `AnalysisService`: build the response as today, inspect the existing
history diagnostic component, and return failure when the component explicitly reports
`status=failed`. Preserve the component message as `last_error` so synchronous API calls and
asynchronous tasks expose an actionable failure instead of a false completion.

This location is shared by the legacy and Agent analysis pipelines and by synchronous and
asynchronous API callers. It does not duplicate persistence, query the database a second time, or
change CLI-only pipeline behavior.

## Compatibility and Failure Semantics

- `history.status=ok`: unchanged successful response.
- `history.status=failed`: `AnalysisService` returns `None`, sets `last_error`, and the existing
  caller marks the request/task failed.
- Missing or legacy diagnostic component: unchanged behavior; the new gate reacts only to an
  explicit persistence failure.
- Market review and period-report flows do not use this stock-analysis service gate and remain
  unchanged.
- No schema, migration, configuration, notification, model, prompt, or report-format changes.

## Tests

The regression test drives the real `AnalysisService.analyze_stock()` contract with a controlled
pipeline result and real run-diagnostic history events:

- RED: an explicit failed history run currently still produces a non-`None` service response.
- GREEN: the same evidence returns `None`, preserves a useful `last_error`, and never reports a
  completed response.
- A sibling success test proves a saved-history event still returns the normal response.

Relevant backend tests and the repository backend gate remain the final verification boundary.

## Scope Split

This product PR contains only the completion contract, regression tests, this design/plan, and the
required changelog entry. Work10-Work13 project-state reconciliation is a separate Draft PR based
on the same `main` commit so documentation evidence and product behavior remain independently
reviewable.
