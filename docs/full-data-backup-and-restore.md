# Complete data backup and restore

PP02 provides three different backup tools. They are intentionally separate and
are not interchangeable.

| Tool | What it contains | What it is for |
| --- | --- | --- |
| Complete data backup | Allow-listed formal analysis history, stock portfolio events, saved period reports, saved conversations, structured user records, and non-sensitive saved configuration | Moving or recovering the supported PP02 formal state |
| Configuration-only backup | Non-sensitive saved `.env` configuration only | Moving settings without histories or portfolio/report data |
| Portfolio-only backup | Stock portfolio accounts, trades, cash events, and corporate-action events only | Moving the stock portfolio event ledger without other PP02 data |

Use the complete backup when the goal is application recovery. A
configuration-only or portfolio-only file cannot restore the complete formal
state.

## Complete backup contents

The complete backup uses an explicit allow-list. Version 1 includes:

- analysis history and the fundamental snapshots referenced by analysis and
  history fallback paths;
- stock portfolio accounts (including their owner identity), trades,
  cash-ledger events, and corporate-action events;
- persisted period reports;
- persisted conversation messages and summaries, including system, user, and
  assistant messages;
- structured records for backtests, alerts, decision signals, outcomes,
  feedback, and saved skill-opinion samples; and
- non-sensitive registered configuration keys.

Fund data is not part of PP02. The manifest records the fund category as
`not_applicable` with zero rows rather than silently treating it as supported.

The following content is deliberately excluded:

- credentials, API keys, tokens, passwords, cookies, secure-vault ciphertext,
  and other credential-like material;
- unsaved Web drafts;
- database, environment-file, log, report-template, skill, and LiteLLM runtime
  paths;
- logs, provider traces (including agent-provider turns), scheduler runtime state,
  schema bookkeeping, and rebuildable price/news caches;
- the `stock_daily` market-data cache, whose manifest declaration fixes its
  classification as `rebuildable_market_data_cache`, states that it contains no
  user data, records restore behavior `cleared_then_rebuilt_on_demand`, and names
  `get_daily_history` as the controlled rebuild entry point; and
- derived portfolio positions, lots, and daily snapshots. These are rebuilt
  from the restored stock event ledger.

`fundamental_snapshot` is deliberately included rather than classified as a
cache. Although its write path is fail-open, the analysis/history fallback path
reads stored snapshots when an external provider cannot reproduce the prior
response. A snapshot can therefore contain non-reproducible historical context.
By contrast, `stock_daily` stores provider-derived OHLCV/indicator rows only.
The application can safely serve newly fetched history even if cache persistence
fails, so those rows are fully reconstructable and contain no user-authored data.

The validator rejects unknown root fields, sections, tables, columns, versions,
invalid references (including a conversation summary that covers a message in
another session), invalid domains, non-canonical numeric/date values, and
credential-like material even if a caller recomputes the checksum. Allowed
configuration values are scanned as content as well as by key: URL user-info,
tokens, cookies, passwords, and credential markers are rejected without
echoing the rejected value. Typed configuration is exported in the same
canonical representation used by settings persistence. For example, JSON
configuration is compact and key-sorted; a non-canonical representation is
rejected on import rather than changing meaning during restore.

## File format and integrity

An exported file is canonical UTF-8 JSON followed by one newline. Its filename
has the form `pp02-full-data-backup-YYYYMMDDTHHMMSSZ.json`.

The root contract is closed and contains:

- `format`: `pp02.full-data.backup`;
- `format_version`: `1`;
- `metadata`: PP02 identity, application version, database schema version, and
  UTC creation time;
- `manifest`: category status, exact included table names, per-category and
  per-table row counts, the content exclusion list, and the exact per-table
  exclusion/rebuild declaration;
- `data`: the allow-listed table rows and non-sensitive configuration; and
- `integrity`: algorithm `sha256` and the digest.

All exported database tables are read inside one explicit SQLite snapshot, so
a writer committing while an export is in progress cannot produce a document
whose tables describe different points in time. The SHA-256 value is calculated over canonical JSON with only
`integrity.value` omitted. Editing the file, changing a row, adding a field, or
changing the manifest invalidates it. Integrity is a corruption/tampering
check; it is not encryption. Store the JSON with the same care as any local
analysis archive.

## Export before uninstall or replacement

Export the complete backup and copy it to storage outside the application data
directory before uninstalling, deleting a portable installation, replacing a
machine, or removing a container volume. Examples include an encrypted external
drive or an access-controlled backup folder.

Do not rely on the recovery file created during restore as the only migration
copy: it is stored beside the active SQLite database and can be removed with the
installation or data volume.

## Restore procedure

1. Install and start a compatible PP02 version.
2. Open Settings and choose **Complete data backup and restore**.
3. Select the JSON file. PP02 validates the format, version, manifest, rows,
   references, compatibility metadata, and SHA-256 before issuing a short-lived
   preview.
4. Review incoming and current row counts, exclusions, warnings, and the restart
   notice. No data is replaced during preview.
5. Confirm the restore explicitly. The preview is single-use and tied to both
   the exact input digest and current destination state. If it expires, the file
   changes, the destination changes, or the result is ambiguous, create a fresh
   preview.
6. After success, record the displayed recovery filename and digests, then
   restart the service. Reload the settings, portfolio, history, and period
   report pages after restart.

Restore replaces the supported allow-listed state; it does not merge two
archives. Current credentials remain local and are not supplied by the backup.
Because agent-provider turns are excluded provider traces, restore also removes
existing destination turns before replacing formal conversations. This prevents
an old destination trace from becoming attached to an incoming message that
reuses the same identifier.

## Recovery artifact and rollback

Immediately before replacement, PP02 writes a canonical recovery backup of the
current destination into a dedicated `<database-stem>_restore_recovery`
directory beside the active SQLite database. The response exposes only the safe
filename and SHA-256/destination digests, not the local absolute path.

Database replacement and managed configuration replacement are coordinated.
Validation and stale-preview conflicts write nothing. If a pre-commit restore
step fails or is interrupted, including by process-level Python interruption,
database changes are rolled back and the prior managed configuration is
compensated before the interruption propagates. Concurrent configuration
writers are not overwritten. Derived portfolio caches and `stock_daily` are
cleared inside the restore transaction. Portfolio state is rebuilt from the
restored event ledger; `stock_daily` is repopulated only through
`get_daily_history` when requested. A failure to finalize the internal
configuration receipt after the durable database commit does not falsely report
the restore as failed: cleanup is retried safely and success is returned with a
sanitized warning if the retry path was needed.

Restore also writes a small, mode-`0600`, fsynced transaction journal before
publishing managed configuration and commits a transaction marker with the
restored SQLite rows. On the next startup, before repositories, schedulers, or
runtime configuration are exposed, PP02 reconciles an interrupted restore by
comparing the journal with the database marker. Without a marker it rolls back
only values still owned by the interrupted restore; with a marker it completes
only values still at their prior state. A concurrent third value is preserved.
The journal contains only allow-listed non-sensitive managed values and digests,
never database rows, credentials, full environment-file bytes, or absolute
paths. Corrupt or incompatible journals fail startup closed without mutating the
database, configuration, or journal.

For a manual rollback, keep the application stopped, preserve the failed state
for diagnosis, and restore the recovery artifact through the same preview and
confirm workflow. Restart again after the rollback. Do not edit the JSON or
copy individual SQLite rows by hand.

## Compatibility and limitations

- Version 1 requires the exact PP02 project identity. The backup application
  version and database schema version must each exactly equal the corresponding
  version of the running restore target. Cross-version restore, whether older
  or newer, is rejected before any replacement is attempted.
- Only file-backed SQLite restore is supported. A non-SQLite or in-memory
  destination is rejected.
- A restart is always required after successful restore so runtime singletons,
  schedules, and readers reopen the recovered state.
- Persisted period-report content is validated as the complete formal API
  response and cross-checked against its database identity, window, kind,
  status, generated time, and recursive source-history references.
- Credentials and secure-vault data must be configured separately on the target
  installation.
- Unsaved drafts, logs, the explicitly declared rebuildable caches, runtime
  paths, provider traces, and scheduler runtime state cannot be recovered from
  this file. `fundamental_snapshot` is not in that exclusion.
- Complete backup does not add fund support. The manifest must continue to show
  fund as `not_applicable`.
- The feature has deterministic local automated coverage with synthetic data.
  It does not substitute for keeping an external, access-controlled backup or
  for testing the recovery procedure for a particular deployment.
