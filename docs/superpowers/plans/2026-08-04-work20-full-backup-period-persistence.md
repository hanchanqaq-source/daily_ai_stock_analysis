# Work20 Full Backup and Period Report Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist complete period reports and provide a versioned, integrity-checked, non-secret full-data export/restore flow that survives uninstall and clean reinstall.

**Architecture:** Store canonical period reports in an additive SQLAlchemy table and expose exact stored reads. Build a strict allow-listed JSON backup service around formal PP02 rows plus the existing sanitized config export, then restore database rows in one transaction with a pre-restore recovery artifact and config compensation.

**Tech Stack:** Python 3.12, SQLAlchemy 2, SQLite, FastAPI/Pydantic, React 19, TypeScript, Vitest, pytest/unittest, GitHub Actions.

## Global Constraints

- Base is exactly `41fd6a6c76c3e3b56211ef5fb4483d869122b568` (`v3.29.2`).
- Use only synthetic data and temporary databases/config files; never modify an existing user database.
- Do not move the database directory or add/upgrade dependencies.
- Do not handle external market/news failures, MiniRacer, `stocks.index.json`, signing or unrelated fixes.
- Keep the pull request Draft. Do not Ready, merge, Tag, Release or publish `v3.29.3`.
- The fund category is `not_applicable`/zero in PP02; never import PP03 or unknown fund tables.

---

### Task 1: Add the period-report schema and prove v3.29.2 migration

**Files:**
- Modify: `src/storage.py`
- Modify: `tests/test_storage.py`
- Create: `tests/test_work20_v3292_migration.py`

**Interfaces:**
- Produces: `PeriodReportRecord`, `PERIOD_REPORT_SCHEMA_VERSION`, verified additive startup migration.
- Preserves: every pre-existing v3.29.2 row and primary key.

- [ ] **Step 1: Write the migration RED tests**

Create a raw SQLite fixture without `period_reports`, insert fixed
`analysis_history.id=4101/query_id=work20-stock-query` and
`analysis_history.id=4201/query_id=work20-market-query`, initialize
`DatabaseManager`, and assert a missing `PeriodReportRecord`/schema marker contract.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=/tmp/work20-pydeps python -m pytest tests/test_work20_v3292_migration.py tests/test_storage.py -q`

Expected: fail because the model, table and Work20 marker do not exist.

- [ ] **Step 3: Implement the additive model and verification**

Add columns and the unique identity `(period, report_kind, start_date, end_date)`, bump
`CURRENT_SCHEMA_VERSION`, create/verify through the existing startup transaction and
record the marker only after verification.

- [ ] **Step 4: Run GREEN**

Run the same command and require all tests to pass while fixed old IDs remain readable.

### Task 2: Persist and reload the exact period report

**Files:**
- Create: `src/repositories/period_report_repo.py`
- Modify: `src/services/period_report_service.py`
- Modify: `api/v1/schemas/period_report.py`
- Modify: `api/v1/endpoints/period_report.py`
- Modify: `tests/test_period_report_service.py`
- Modify: `tests/test_period_report_api.py`

**Interfaces:**
- Produces: `PeriodReportRepository.upsert_report()`, `get_report()`, `get_latest()`.
- API produces: `report_id`, `status`, `GET /latest`, `GET /{report_id}`.

- [ ] **Step 1: Write service and API RED tests**

Assert generation returns a positive ID, same-window regeneration preserves it, a new
window creates another ID, a new manager reads identical stored content, and GET routes
do not call `generate()`.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=/tmp/work20-pydeps python -m pytest tests/test_period_report_service.py tests/test_period_report_api.py -q`

Expected: fail on missing persistent repository and read routes.

- [ ] **Step 3: Implement minimal persistence and stored reads**

Serialize the complete response, derive sorted unique source history IDs, upsert by the
fixed identity, attach ID/status to the response and deserialize only from stored rows.
Retain legacy `period_outlook` lookup as fallback for old data.

- [ ] **Step 4: Run GREEN**

Run the same command and require every period-report test to pass.

### Task 3: Define and validate the complete backup format

**Files:**
- Create: `src/services/full_data_backup_service.py`
- Create: `api/v1/schemas/full_data_backup.py`
- Create: `tests/test_full_data_backup_service.py`

**Interfaces:**
- Produces: format `pp02.full-data.backup`, version `1`, canonical SHA-256, exact manifest and `FullDataBackupValidationError`.
- Consumes: `SystemConfigService.export_env()` only for configuration content.

- [ ] **Step 1: Write export/validation RED tests**

Seed fixed analysis/market IDs, portfolio events, a stored period report, alert/backtest/
decision rows where supported and `STOCK_LIST=600519`; assert exact categories/counts,
IDs, application/schema versions and canonical checksum. Add secret-marker assignments
and assert none appear. Assert fund status is `not_applicable` with zero rows.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=/tmp/work20-pydeps python -m pytest tests/test_full_data_backup_service.py -q`

Expected: fail because the format and service do not exist.

- [ ] **Step 3: Implement strict allow-list export and validator**

Serialize SQLAlchemy Core rows with explicit date/time handling, sort by primary key,
build category/table counts, use the sanitized config boundary, compute integrity from
canonical JSON and reject extra/missing/unknown sections or incompatible versions.

- [ ] **Step 4: Run GREEN**

Run the same command and require export, checksum, exclusion and corruption tests to pass.

### Task 4: Implement preview, recovery artifact and transactional restore

**Files:**
- Modify: `src/services/full_data_backup_service.py`
- Modify: `src/services/system_config_service.py`
- Modify: `tests/test_full_data_backup_service.py`
- Create: `tests/test_full_data_restore_integration.py`

**Interfaces:**
- Produces: `preview_restore()`, `restore_backup()`, recovery filename, fresh preview token and `restart_required`.
- Preserves: destination database/config on validation failure or injected interruption.

- [ ] **Step 1: Write restore RED tests**

Export synthetic fixed data, open a clean install database, preview and restore, then
assert original IDs/query IDs/summaries/events and report IDs. Restart and assert again.
Add checksum, missing-section, incompatible-schema, stale-preview and injected-failure
cases; compare destination digests before/after every rejection. Assert the recovery
file exists before a successful or injected restore attempt.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=/tmp/work20-pydeps python -m pytest tests/test_full_data_backup_service.py tests/test_full_data_restore_integration.py -q`

Expected: fail on missing preview/restore/recovery behavior.

- [ ] **Step 3: Implement fail-closed preview and restore**

Validate fully, build a token over incoming/current digests, atomically write the
current sanitized backup, apply only validated config with reload disabled, replace
allow-listed database rows in dependency order inside one transaction, verify counts/
digests, and compensate config on transaction failure.

- [ ] **Step 4: Run GREEN**

Run the same command and require clean-install, restart, rollback and recovery evidence to pass.

### Task 5: Expose the formal full-data API

**Files:**
- Create: `api/v1/endpoints/full_data_backup.py`
- Modify: `api/v1/endpoints/__init__.py`
- Modify: `api/v1/router.py`
- Modify: `api/v1/schemas/__init__.py`
- Create: `tests/test_full_data_backup_api.py`

**Interfaces:**
- Produces: `GET /api/v1/system/full-data-backup/export`, `POST /preview`, `POST /restore`.
- Maps: validation to 400, stale/conflict to 409 and unexpected failure to generic 500.

- [ ] **Step 1: Write API RED tests**

Assert export filename/document, preview counts/warnings/token, restore recovery metadata,
and stable errors for corruption/incompatibility without exposing payload content.

- [ ] **Step 2: Run RED**

Run: `PYTHONPATH=/tmp/work20-pydeps python -m pytest tests/test_full_data_backup_api.py -q`

Expected: fail because routes and schemas do not exist.

- [ ] **Step 3: Implement schemas, endpoints and router registration**

Keep endpoint functions thin and delegate every data/security decision to the service.

- [ ] **Step 4: Run GREEN**

Run the same command and require all API tests to pass.

### Task 6: Reload stored reports and distinguish all three UI entrances

**Files:**
- Modify: `apps/dsa-web/src/types/periodReport.ts`
- Modify: `apps/dsa-web/src/api/periodReport.ts`
- Modify: `apps/dsa-web/src/pages/PeriodReportPage.tsx`
- Modify: `apps/dsa-web/src/pages/__tests__/PeriodReportPage.test.tsx`
- Create: `apps/dsa-web/src/types/fullDataBackup.ts`
- Create: `apps/dsa-web/src/api/fullDataBackup.ts`
- Create: `apps/dsa-web/src/components/settings/FullDataBackupCard.tsx`
- Create: `apps/dsa-web/src/components/settings/__tests__/FullDataBackupCard.test.tsx`
- Modify: `apps/dsa-web/src/pages/SettingsPage.tsx`
- Modify: `apps/dsa-web/src/pages/__tests__/SettingsPage.test.tsx`
- Modify: `apps/dsa-web/src/pages/PortfolioPage.tsx`
- Modify: `apps/dsa-web/src/pages/__tests__/PortfolioPage.test.tsx`
- Modify: `apps/dsa-web/src/i18n/uiText.ts`

**Interfaces:**
- Consumes: stored-report GET and full-backup export/preview/restore endpoints.
- Produces: exact Chinese/English labels for complete data, config-only and portfolio-ledger-only backup.

- [ ] **Step 1: Write UI RED tests**

Assert page mount loads latest stored ID without generation, selection changes load that
period, complete export downloads JSON, restore requires preview/confirmation, and all
three limited/full labels and exclusion copy are visible.

- [ ] **Step 2: Run RED**

Run: `npm run test -- --run src/pages/__tests__/PeriodReportPage.test.tsx src/components/settings/__tests__/FullDataBackupCard.test.tsx src/pages/__tests__/SettingsPage.test.tsx src/pages/__tests__/PortfolioPage.test.tsx`

Expected: fail because latest loading, the complete card and unambiguous labels are absent.

- [ ] **Step 3: Implement minimal UI and API adapters**

Use browser file download/upload only; do not retain file contents outside component
state, log backup data, auto-run generation or auto-confirm replacement.

- [ ] **Step 4: Run GREEN**

Run the same command and require all affected Web tests to pass.

### Task 7: Document, verify and publish the Draft Head

**Files:**
- Modify: `docs/CHANGELOG.md`
- Create: `docs/full-data-backup-and-restore.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/OPEN_BLOCKERS.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`

**Interfaces:**
- Produces: user-visible backup distinctions, migration/rollback guidance, fixed-Head Draft PR evidence and honest Judge.

- [ ] **Step 1: Run complete local verification**

Run Work20 backend tests, existing related regressions, `./scripts/ci_gate.sh`, Web
`npm run lint`, Web `npm run build`, affected Vitest suites, `python scripts/check_ai_assets.py`,
Python compile for changed Python files and `git diff --check`.

- [ ] **Step 2: Perform requirement and security review**

Map every Work20 acceptance item to a test/evidence row, scan the backup fixture for
credential/token/cookie/ciphertext markers and review the final diff for unrelated files.

- [ ] **Step 3: Commit, push and create one Draft PR**

Stage only Work20 files, use English commit messages without release directives, push
`agent/pp02-work20-full-backup-period-persistence` and create a Draft PR targeting `main`.

- [ ] **Step 4: Verify fixed-Head GitHub Actions**

Require all applicable blocking jobs to complete successfully for the exact final Head.
Do not rerun unrelated external network smoke or trigger a release workflow.

- [ ] **Step 5: Record the truthful Work20 Judge**

Record Draft PR, full Head, CI Run/jobs, coverage manifest, migration proof, exact report
restart proof, clean-install restore comparison, rollback evidence, limitations and
`DRAFT_HOLD`. Do not Ready or merge.
