# PP02 R4 Database Compatibility Rehearsal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable, fail-closed SQLite migration rehearsal that accepts only SHA-bound synthetic inputs, migrates only the official PP02 stock event ledger into a new empty database, and proves failed restore attempts leave the target unchanged.

**Architecture:** A service performs strict attestation and read-only source preflight, upgrades only an auto-cleaned temporary copy through the existing `DatabaseManager`, and reuses `PortfolioBackupService` for the stock-only export/preview/restore contract. A thin CLI writes one value-free JSON evidence report; pytest fixtures dynamically create all SQLite inputs so no database artifact enters Git.

**Tech Stack:** Python 3.12, stdlib `sqlite3`/`hashlib`/`tempfile`, SQLAlchemy through the existing storage layer, pytest, GitHub Actions.

## Global Constraints

- Base is exactly `main@eb32298c8f3cbec2ff400dda37d3267a7181af40`.
- Work branch is `agent/pp02-work4-r4-database-rehearsal`; PR remains Draft.
- Use only empty SQLite databases and manually generated fake data.
- Do not read, copy, sanitize, open, or migrate any real database, backup, account, credential, `.env`, log, or cache.
- The official portfolio account/event ledger remains the only stock-holding fact source.
- Do not migrate fund data, user profiles, multi-user state, legacy quick-position tables, derived positions/lots/snapshots, or caches.
- Do not add dependencies, database tables, runtime settings, APIs, Web UI, background tasks, or parallel state ledgers.
- Do not rename the user's chat, mark the PR Ready, merge, write `main`, tag, release, or enter R5/R6/R7.

---

### Task 1: Define the fail-closed rehearsal contract with RED tests

**Files:**
- Create: `tests/test_database_migration_rehearsal.py`
- Test: `tests/test_storage.py`
- Test: `tests/test_portfolio_backup_service.py`

**Interfaces:**
- Consumes: `DatabaseManager`, `PortfolioBackupService`, four official portfolio event tables.
- Produces: the desired `DatabaseMigrationRehearsalService.run(source_path, attestation_path, workspace_dir) -> dict` behavior used by Tasks 2 and 3.

- [ ] **Step 1: Add dynamic SQLite and attestation helpers**

Create helpers that use `tmp_path` and `sqlite3` only. The attestation must have exactly:

```python
{
    "attestation_version": 1,
    "project_id": "PP02",
    "scope": "R4_DATABASE_REHEARSAL",
    "classification": "synthetic",
    "contains_real_data": False,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
}
```

The mixed fixture creates the four current event tables with their required columns, one account,
one cash event, one trade and one corporate action. It also creates fake excluded tables/rows for
user profile, fund data, credential-like text and derived portfolio state.

- [ ] **Step 2: Add behavior tests**

Tests must assert:

```python
def test_empty_synthetic_database_rehearsal_passes_without_source_mutation(...): ...
def test_mixed_synthetic_database_migrates_only_official_event_ledger(...): ...
def test_rehearsal_rejects_missing_or_mismatched_attestation(...): ...
def test_rehearsal_rejects_real_data_declaration(...): ...
def test_rehearsal_rejects_partial_portfolio_schema_before_target_write(...): ...
def test_report_and_target_do_not_contain_excluded_fake_secret(...): ...
def test_stale_preview_rollback_probe_preserves_target_digest(...): ...
```

The mixed success report must have `real_data_used is False`,
`backup_payload_persisted is False`, matching input/output event counts, matching portfolio digests,
`source_unchanged is True`, and rollback evidence set to true. Search serialized report and target
database bytes for the unique fake excluded secret and require no match.

- [ ] **Step 3: Run RED and confirm the reason**

Run:

```bash
/tmp/pp02-r37-backend-venv/bin/python -m pytest tests/test_database_migration_rehearsal.py -q
```

Expected: FAIL because `src.services.database_migration_rehearsal_service` does not exist; existing
storage and backup tests are not involved in the failure.

- [ ] **Step 4: Commit the observed RED contract**

```bash
git add tests/test_database_migration_rehearsal.py
git commit -m "test: define R4 database rehearsal contract"
```

### Task 2: Implement the minimal rehearsal service and turn tests GREEN

**Files:**
- Create: `src/services/database_migration_rehearsal_service.py`
- Modify: `tests/test_database_migration_rehearsal.py` only if the RED test has an objective test defect; do not weaken assertions.

**Interfaces:**
- Consumes: `PortfolioBackupService.export_backup`, `preview_restore`, `restore_backup`, `DatabaseManager.reset_instance`.
- Produces:
  - `DatabaseMigrationRehearsalError(code: str)` with value-free public messages.
  - `DatabaseMigrationRehearsalService.run(*, source_path: Path, attestation_path: Path, workspace_dir: Path) -> dict`.
  - target file `workspace_dir / "pp02-r4-migrated.db"` only after preflight succeeds.

- [ ] **Step 1: Implement strict path, attestation and SQLite preflight**

Required behaviors:

```python
EXPECTED_ATTESTATION_KEYS = {
    "attestation_version", "project_id", "scope", "classification",
    "contains_real_data", "source_sha256",
}
PORTFOLIO_MODELS = (
    PortfolioAccount, PortfolioTrade, PortfolioCashLedger, PortfolioCorporateAction,
)
```

Reject symlink/non-file input, absent or extra attestation keys, any classification other than
`synthetic`, `contains_real_data` other than literal `False`, bad project/scope/version, SHA mismatch,
non-SQLite bytes, failed `PRAGMA integrity_check`, an existing target, or a partial event schema.
Zero-byte/zero-table SQLite is the supported empty database case.

- [ ] **Step 2: Implement isolated upgrade and stock-only migration**

Use a `TemporaryDirectory` under `workspace_dir`; copy the source only there. Initialize
`DatabaseManager` on the temporary copy, export through `PortfolioBackupService`, then reset the
singleton. Initialize a brand-new target, preview and restore the exported backup, re-export, and
compare counts plus a canonical SHA-256 digest of the `portfolio` object.

Never write the backup object to disk. On any target failure, dispose the manager and unlink the
new target plus SQLite `-wal`/`-shm` sidecars.

- [ ] **Step 3: Implement rollback evidence**

On the migrated target, create a preview for the valid backup, change only the backup metadata
timestamp in a deep copy, then call restore with the stale token. Require
`PortfolioBackupConflictError`, and compare the target export digest before/after. If the restore is
accepted or the digest changes, fail the entire rehearsal.

- [ ] **Step 4: Build the value-free report**

Return only:

```python
{
    "report_version": 1,
    "status": "pass",
    "source_sha256": "<hex>",
    "source_unchanged": True,
    "schema": {
        "compatible": True,
        "source_tables": ["<names only>"],
        "excluded_tables": ["<names only>"],
    },
    "migration": {
        "counts": {"accounts": 0, "trades": 0, "cash_ledger": 0, "corporate_actions": 0},
        "portfolio_digest_match": True,
        "excluded_table_data_present": False,
    },
    "rollback": {"stale_preview_rejected": True, "target_unchanged": True},
    "privacy": {"real_data_used": False, "backup_payload_persisted": False},
    "target_database": "pp02-r4-migrated.db",
}
```

- [ ] **Step 5: Run GREEN and regression tests**

Run:

```bash
/tmp/pp02-r37-backend-venv/bin/python -m pytest \
  tests/test_database_migration_rehearsal.py \
  tests/test_portfolio_backup_service.py \
  tests/test_storage.py -q
```

Expected: all collected tests pass; warnings may remain only if they match the recorded baseline.

- [ ] **Step 6: Commit the GREEN service**

```bash
git add src/services/database_migration_rehearsal_service.py tests/test_database_migration_rehearsal.py
git commit -m "feat: add synthetic database migration rehearsal"
```

### Task 3: Add the CLI and end-to-end privacy gate

**Files:**
- Create: `scripts/pp02_database_migration_rehearsal.py`
- Modify: `tests/test_database_migration_rehearsal.py`

**Interfaces:**
- Consumes: `DatabaseMigrationRehearsalService.run`.
- Produces: CLI options `--source`, `--attestation`, `--workspace`, `--report`; atomic JSON report; exit 0 on PASS and non-zero on a safe error code.

- [ ] **Step 1: Write the failing CLI test**

The test invokes the repository script with the current Python interpreter and asserts:

```python
assert completed.returncode == 0
assert "R4_DATABASE_MIGRATION_REHEARSAL=PASS" in completed.stdout
assert fake_secret not in completed.stdout + completed.stderr + report_path.read_text()
assert json.loads(report_path.read_text())["status"] == "pass"
```

Add a failure case whose attestation hash is wrong; it must return non-zero, print only a stable error
code, create no target/report, and not echo any fixture values.

- [ ] **Step 2: Run the CLI RED**

Run the two CLI tests by exact node id. Expected: FAIL because the script is absent.

- [ ] **Step 3: Implement the thin CLI**

Use `argparse`, call the service, and write report JSON through a sibling temporary file followed by
`os.replace`. Catch `DatabaseMigrationRehearsalError` and print
`R4_DATABASE_MIGRATION_REHEARSAL=FAIL code=<code>` to stderr without paths or exception details.

- [ ] **Step 4: Run CLI GREEN and syntax checks**

```bash
/tmp/pp02-r37-backend-venv/bin/python -m pytest tests/test_database_migration_rehearsal.py -q
/tmp/pp02-r37-backend-venv/bin/python -m py_compile \
  src/services/database_migration_rehearsal_service.py \
  scripts/pp02_database_migration_rehearsal.py
```

- [ ] **Step 5: Commit the CLI**

```bash
git add scripts/pp02_database_migration_rehearsal.py tests/test_database_migration_rehearsal.py
git commit -m "feat: expose R4 database rehearsal CLI"
```

### Task 4: Document operations and verify a fresh synthetic rehearsal

**Files:**
- Modify: `docs/RUNBOOK.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/ERRORS_AND_LESSONS.md` only if this Work produces a new reusable incident/lesson.
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/WORK_RETURN.md`

**Interfaces:**
- Consumes: the CLI and JSON report contract.
- Produces: operator-safe instructions that explicitly forbid real database use in Work4.

- [ ] **Step 1: Add Runbook input, command, output and rollback instructions**

Document how to generate a temporary synthetic fixture and attestation in tests, how to run the CLI,
the fixed report fields, cleanup behavior, and the prohibition on real databases. State that R4 PASS
does not authorize or prove R6 real migration.

- [ ] **Step 2: Add flat Unreleased entries**

Add one `[新功能]` line for the rehearsal CLI and one `[测试]` line for synthetic/rollback/privacy
coverage. Do not add a category heading.

- [ ] **Step 3: Run a fresh end-to-end synthetic fixture rehearsal**

Use a temporary directory created by `mktemp -d`; generate data only through the test helper or a
short checked test invocation. Do not use repository `data/`, `.env`, any user path, or any existing
database. Verify PASS, inspect only report keys/counts, then remove the temporary directory.

- [ ] **Step 4: Update current state with actual evidence only**

Record exact test counts/commands and keep `CURRENT_STATUS=IMPLEMENTATION_LOCAL_PASS — CI_PENDING — DRAFT_HOLD` until remote CI finishes. Do not record a planned PR number or Run ID as fact.

- [ ] **Step 5: Commit docs and local evidence**

```bash
git add docs/RUNBOOK.md docs/CHANGELOG.md _ai-dev/PROJECT_STATUS.md _ai-dev/WORK_RETURN.md
git commit -m "docs: record R4 rehearsal operations"
```

### Task 5: Full verification, Draft PR, CI and Work4 closeout

**Files:**
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`
- Modify: `docs/CHANGE_HISTORY.md` only to append real closeout facts.

**Interfaces:**
- Consumes: all prior commits and GitHub CI evidence.
- Produces: one Draft PR, fixed-Head CI evidence, Judge result, released execution lock, and the exact next-Work handoff.

- [ ] **Step 1: Run fresh local gates**

```bash
git diff --check
/tmp/pp02-r37-backend-venv/bin/python scripts/check_ai_assets.py
/tmp/pp02-r37-backend-venv/bin/python -m pytest tests/test_database_migration_rehearsal.py -q
/tmp/pp02-r37-backend-venv/bin/python -m pytest -m "not network"
```

Also run flake8 critical checks through `./scripts/ci_gate.sh flake8` and the repository deterministic
gate. Record exact counts and any pre-existing warnings; no success claim before fresh output.

- [ ] **Step 2: Review the complete Base-to-Head diff**

Confirm only approved governance, service, CLI, tests and docs changed; no `.db`, `.env`, backup,
report, log, fixture artifact, secret-like value, dependency or workflow change is tracked. Confirm
the report schema cannot contain row values.

- [ ] **Step 3: Push and create/update one Draft PR**

Push `agent/pp02-work4-r4-database-rehearsal`, create one Draft PR targeting `main`, and include
scope, TDD evidence, data exclusions, rollback, local verification, authorization locks and rollback
plan. Keep it Draft.

- [ ] **Step 4: Close superseded PR #7 and #8**

Add a concise note that each is superseded by merged PR #9, close it, and verify the branch remains.
Do not delete branches or rewrite history.

- [ ] **Step 5: Wait for and inspect full CI**

Pin the PR Head SHA, require every expected CI job to complete successfully, and inspect failing logs
if any. Fix only in-scope root causes with a new failing regression test, rerun local gates, push, and
restart the fixed-Head check.

- [ ] **Step 6: Write final evidence without creating a self-referential CI loop**

Put final Run IDs and fixed-Head metadata in the Draft PR body/comment when that avoids changing
Head. Repository state may record the verified implementation Head and state `CI_PASS` only if a
later state commit itself receives the required full CI.

- [ ] **Step 7: Judge and release the Work lock**

Only after code, tests, report, GitHub state and ledgers agree, set Work4 to `COMPLETED — DRAFT_HOLD`,
record the next unstarted segment, and state that the user should open a new same-project Codex chat
and send only `下一步`. Do not rename the chat, Ready, merge, tag, release, or enter the next stage.

## Plan Self-Review

- Every design requirement maps to Tasks 1–5.
- All paths, public interfaces, report keys and verification commands are explicit.
- No placeholders or deferred implementation instructions remain.
- Task boundaries preserve RED→GREEN evidence, minimal production code, operational documentation,
  fixed-Head CI, and a separate Work closeout gate.
