# Work20 Full Backup and Period Report Persistence Design

## Goal

Make the user-approved lifecycle safe without moving the database directory:
generate a durable period report, export one complete non-secret backup outside the
installation directory, uninstall, reinstall, restore through the product UI, and read
the same formal records after another restart.

## Fixed evidence and root cause

- Base is exactly `main@41fd6a6c76c3e3b56211ef5fb4483d869122b568`, the
  `v3.29.2` source commit. GitHub has no open pull requests at Work20 takeover.
- `PeriodReportService.generate()` returns historical period reports only in memory.
  The one exception is a partial `next_week` outlook snapshot stored in
  `analysis_history`; there is no canonical table, exact-report read endpoint or Web
  reload path.
- `/api/v1/system/config/export` contains only saved non-sensitive `.env` entries.
  `/api/v1/portfolio/backup/export` contains only accounts, trades, cash-ledger rows
  and corporate actions. Neither format claims or provides a complete restore.
- The watchlist is the non-sensitive `STOCK_LIST` setting, so it belongs to the
  sanitized configuration section of a complete backup.
- PP02 currently has no formal fund model or fund table. Project control assigns fund
  business to PP03. The complete-backup manifest must therefore report the fund
  category as `not_applicable` with count zero and must reject, not silently import,
  unknown fund tables.

There is no structural need to move the database directory. The approved external
backup file can cover the supported formal data through a versioned allow-list and an
atomic database transaction.

## Chosen architecture

### Period reports

Add a `period_reports` SQLAlchemy model with:

- integer `id`;
- `period`, `report_kind`, `start_date` and `end_date`;
- complete `content_json`;
- `source_record_ids_json`;
- `status` and `generated_at`;
- `updated_at` for replacement evidence.

The unique identity is `(period, report_kind, start_date, end_date)`. An explicit
regeneration for the same identity updates the same row and preserves its `id`; a
different range creates a new row. This is the product's deterministic replacement
rule and prevents uncontrolled duplicates.

`POST /api/v1/period-report/generate` persists before returning. The response exposes
`report_id` and `status`. `GET /api/v1/period-report/latest?period=...` and
`GET /api/v1/period-report/{id}` return stored content only and never regenerate.
The Web page loads the latest stored report when opened or when the selected period
changes.

The existing legacy `period_outlook` rows remain readable for prior-outlook matching.
New full period reports use `period_reports` as the canonical record; no legacy row is
deleted or rewritten.

### Additive database migration

Advance `CURRENT_SCHEMA_VERSION` to a Work20 schema identifier. Startup creates only
the missing `period_reports` table through the existing metadata transaction, verifies
its columns and unique identity, then records the new schema marker. The migration is
additive: it never updates or deletes v3.29.2 rows. Any initialization failure aborts
the transaction and leaves old tables and rows readable. Rolling back the application
therefore only makes the new table unused; no down-conversion of old data is required.

### Complete backup document

Add format `pp02.full-data.backup`, version `1`. The root contains:

- `metadata`: creation time, application version, database schema version and project;
- `manifest`: category status, row counts, exact table/config inventory and exclusions;
- `data`: supported formal database rows and sanitized configuration content;
- `integrity`: SHA-256 of canonical metadata, manifest and data JSON.

The database allow-list covers:

- `analysis_history` (both individual-stock and market-review history);
- the four authoritative portfolio event tables;
- `period_reports`;
- supported structured formal user records already owned by PP02: backtest results and
  summaries, alert rules/history, decision signals/outcomes/feedback and skill-opinion
  samples.

Derived portfolio caches, price/news/fundamental caches, scheduler/runtime state,
provider traces, logs, drafts and schema bookkeeping are excluded. Portfolio positions
are rebuilt from authoritative events. The sanitized configuration section comes from
the existing `SystemConfigService.export_env()` boundary and includes `STOCK_LIST` when
saved. Credential keys, Tokens, Cookies, vault ciphertext and unsaved Web drafts never
enter the service input.

### Restore safety

Restore is previewed before mutation. Validation is fail-closed and completes before
write work:

1. exact format and version;
2. required manifest categories and exact allow-list;
3. supported application/schema compatibility;
4. per-table column/type validation and foreign-key references;
5. canonical SHA-256 integrity;
6. sanitized config re-validation.

Immediately before restore, the current complete backup is written atomically to a
dedicated recovery directory beside the active database. The database restore deletes
and inserts only allow-listed tables inside one transaction, preserves primary IDs and
validates post-insert counts/digests before commit. Exceptions and injected interruption
roll back to the original database.

Configuration uses the existing version/conflict and sensitive-key guards with
`reload_now=False`. If the database restore fails after config application, the
pre-restore sanitized config is reapplied as compensation. The recovery artifact is
retained in all cases. A successful response reports its filename and that an
application restart is required. This is the equivalent-atomic boundary across SQLite
and the existing `.env` store.

## UI design

Settings gains a first-class card named `完整数据备份与恢复` with download, file
preview, incoming/current counts, exclusions and destructive replace confirmation.
The existing card is renamed `配置备份（仅非敏感配置）`; its copy states that it does
not contain histories or the portfolio. The Portfolio page is renamed
`股票组合账本备份（仅组合事件）`; its current narrow implementation remains intact.

No automatic backup is triggered when opening a page. The user chooses the destination
for the downloaded complete JSON file, which supports storage outside the install root.

## Error handling

- Missing section, changed checksum, unsupported version/schema, unknown table, invalid
  row, secret-like config assignment or stale preview returns a stable 4xx error.
- No validation error performs a database or config write.
- Restore interruption and insert failure roll back the database and compensate config.
- A recovery-file write failure blocks restore before mutation.
- Existing local data is never merged ambiguously: complete restore is an explicit
  replace operation with a fresh preview token.

## Testing

- Build a raw v3.29.2-compatible SQLite fixture with fixed analysis IDs/query IDs,
  market-review ID, portfolio events and no `period_reports` table. Initialize Work20
  code and prove old rows plus the new schema marker/table.
- Generate a period report, destroy service/page state, reopen the same database and
  read the same report ID and content without calling generation.
- Export fixed synthetic data, verify manifest/counts/checksum and absence of credential
  markers, then restore into a clean database and compare every required ID, query ID,
  summary and portfolio event.
- Restart the restored manager and repeat the reads.
- Mutate checksum, remove a required section, change format/schema version and inject a
  restore interruption; each must reject while the destination digest stays unchanged.
- Web tests prove latest-report loading and the three unambiguous backup labels.

## Boundaries

This Work does not move the database, modify real user data, use real credentials or
trades, change dependencies, handle external market/news failures, revisit MiniRacer,
fix `stocks.index.json`, sign packages, Ready/merge, Tag or release `v3.29.3`.
