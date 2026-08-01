# R6 Formal Data Inventory Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed Windows-only CLI that makes two verified local backups of one explicitly selected SQLite database and reports only the four official PP02 ledger table counts.

**Architecture:** A standard-library-only service owns path validation, source fingerprinting, two-copy backup verification, temporary read-only SQLite inspection, privacy-limited reporting, and cleanup. A thin CLI owns the native-Windows, explicit-confirmation, and outside-Git gates; tests dynamically create only empty or synthetic SQLite databases in temporary directories.

**Tech Stack:** Python 3.10+, `sqlite3`, `hashlib`, `shutil`, `tempfile`, `json`, `argparse`, `pytest`.

## Global Constraints

- Cloud development and CI use only dynamically generated empty or synthetic databases.
- The production CLI runs only on native Windows and never searches for candidate databases.
- The source database and existing `-wal` / `-shm` sidecars are never opened for writing.
- A `-journal` sidecar blocks the run before any backup or inspection.
- Two backups and an unchanged-source check must pass before inspection starts.
- Reports contain no source/output paths, filenames, SQL, schema text, exception text, or row values.
- The service must not import `src.storage`, SQLAlchemy, application configuration, or migration/restore services.
- No new dependency, workflow permission, database migration, target database, Ready, merge, tag, release, or real-data action is in scope.
- Work5 Judge ceiling is `CLOUD_TOOL_IMPLEMENTATION_PASS — WINDOWS_REAL_INVENTORY_PENDING_AUTHORIZATION`.

---

### Task 1: Activate Work5 control state and establish the RED service contract

**Files:**
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Create: `tests/test_formal_data_inventory.py`

**Interfaces:**
- Consumes: approved design in `docs/pp02/R6_FORMAL_DATA_INVENTORY_TOOL_DESIGN.md` and fixed base `a220e9e146e14722561bc084ec4e5306b30d36c7`.
- Produces: active Work5 records and failing contracts for `FormalDataInventoryService.run(source_path: Path, output_dir: Path) -> dict[str, Any]`.

- [x] **Step 1: Record Work5 as the only active work**

Replace the current-state headers so they record:

```text
WORK_ID=WORK-005
WORK_STATE=ACTIVE
ACTIVE_BASE=a220e9e146e14722561bc084ec4e5306b30d36c7
ACTIVE_BRANCH=agent/pp02-work5-r6-inventory-tool
ACTIVE_PR=13
CURRENT_STAGE=R6-A / Plan-Build-Test-CI-Judge
ACTIVE_GOAL=云端实现正式数据安全只读盘点工具；仅用空库和人工假数据验证
ACTIVE_BLOCKER=NONE
AUTHORIZATION_REQUIRED=TRUE_FOR_WINDOWS_REAL_DATABASE_AND_ALL_RELEASE_ACTIONS
```

The task contract must explicitly allow normal commits, push, one Draft PR, CI, and in-scope fixes while prohibiting real databases, migration, Ready, merge, `main`, tag, release, and R7.

- [x] **Step 2: Create synthetic SQLite fixtures and service behavior tests**

The test module must define the official schema literally, without importing application models, and cover these externally observable results:

```python
OFFICIAL_TABLES = (
    "portfolio_accounts",
    "portfolio_trades",
    "portfolio_cash_ledger",
    "portfolio_corporate_actions",
)

def test_complete_empty_ledger_reports_no_formal_data_and_two_verified_backups(
    service, tmp_path: Path
) -> None:
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    source_before = sha256(source)

    report = service.run(source_path=source, output_dir=tmp_path / "inventory")

    assert report["status"] == "NO_FORMAL_DATA_FOUND"
    assert report["database"]["counts"] == {name: 0 for name in OFFICIAL_TABLES}
    assert report["backup"] == {
        "copies": 2,
        "verified": True,
        "source_unchanged": True,
        "included_sidecars": [],
    }
    assert sha256(source) == source_before
```

Add independent tests for: one synthetic row in each table; no official tables; partial official tables; a missing required column; corrupted SQLite; a `-journal` sidecar; two byte-identical backups; real WAL/SHM copying; source mutation during copy; pre-existing output; source/output collision; symlink source; reparse-point rejection through a patched file-attribute probe; atomic blocked report after verified backups; and report serialization that excludes synthetic account, symbol, amount, note, path, and exception markers.

- [x] **Step 3: Run the service tests and verify RED**

Run:

```bash
python -m pytest tests/test_formal_data_inventory.py -q
```

Expected: FAIL because `src.services.formal_data_inventory_service` does not exist; the failure must be the missing production contract, not a fixture syntax error.

- [x] **Step 4: Commit the RED checkpoint**

```bash
git add _ai-dev/PROJECT_STATUS.md _ai-dev/AI_HANDOFF.md _ai-dev/WORK_TASK.md \
  _ai-dev/WORK_RETURN.md tests/test_formal_data_inventory.py \
  docs/superpowers/plans/2026-08-01-r6-formal-data-inventory-tool.md
git commit -m "test: define R6 formal data inventory contracts"
```

### Task 2: Implement verified backup and read-only inventory service

**Files:**
- Create: `src/services/formal_data_inventory_service.py`
- Test: `tests/test_formal_data_inventory.py`

**Interfaces:**
- Consumes: one explicit regular SQLite file and one non-existing output directory.
- Produces: `FormalDataInventoryService`, `FormalDataInventoryError`, `INVENTORY_REPORT_NAME`, `OFFICIAL_TABLE_COLUMNS`, and a privacy-limited report.

- [x] **Step 1: Implement stable types and fixed schema contract**

Define only standard-library imports and these public contracts:

```python
INVENTORY_REPORT_NAME = "pp02-formal-data-inventory-report.json"

OFFICIAL_TABLE_COLUMNS = {
    "portfolio_accounts": frozenset({
        "id", "owner_id", "name", "broker", "market", "base_currency",
        "is_active", "created_at", "updated_at",
    }),
    "portfolio_trades": frozenset({
        "id", "account_id", "trade_uid", "symbol", "market", "currency",
        "trade_date", "side", "quantity", "price", "fee", "tax", "note",
        "dedup_hash", "created_at",
    }),
    "portfolio_cash_ledger": frozenset({
        "id", "account_id", "event_date", "direction", "amount", "currency",
        "note", "created_at",
    }),
    "portfolio_corporate_actions": frozenset({
        "id", "account_id", "symbol", "market", "currency", "effective_date",
        "action_type", "cash_dividend_per_share", "split_ratio", "note", "created_at",
    }),
}

class FormalDataInventoryError(RuntimeError):
    def __init__(self, code: str, *, backups_verified: bool = False):
        self.code = code
        self.backups_verified = backups_verified
        super().__init__(code)

class FormalDataInventoryService:
    def run(self, *, source_path: Path, output_dir: Path) -> dict[str, Any]:
        raise FormalDataInventoryError("inventory_not_started")
```

- [x] **Step 2: Implement fail-closed source and output validation**

Validation must reject non-files, symlinks/reparse points, existing output paths, a source under the output path, and a present rollback journal. It must walk existing path components without following unsafe link/reparse components. Every rejection raises one stable code such as `source_path_invalid`, `output_path_invalid`, `path_overlap`, or `rollback_journal_present` and does not create output.

- [x] **Step 3: Implement source snapshots and two verified copies**

Use a private immutable fingerprint containing size, `st_mtime_ns`, and SHA-256. Snapshot exactly the main file plus existing `-wal` and `-shm`; copy the same set into `backup-a/` and `backup-b/`, verify every destination SHA-256, then snapshot the source set again and require exact equality.

```python
source_snapshot = self._snapshot_source(source)
self._copy_snapshot(source_snapshot, backup_a)
self._copy_snapshot(source_snapshot, backup_b)
self._verify_backup(source_snapshot, backup_a)
self._verify_backup(source_snapshot, backup_b)
if self._snapshot_source(source) != source_snapshot:
    raise FormalDataInventoryError("source_changed_during_backup")
backups_verified = True
```

Any failure before `backups_verified = True` removes only the newly created output directory and never touches the source.

- [x] **Step 4: Inspect a temporary copy in SQLite read-only/query-only mode**

Copy `backup-a` into a `TemporaryDirectory` under the output directory, preserving the main basename and sidecar names. Open only the temporary main copy through a URI with `mode=ro`, immediately execute `PRAGMA query_only = ON`, then run:

```sql
PRAGMA integrity_check;
SELECT name FROM sqlite_master WHERE type='table';
PRAGMA table_info("portfolio_accounts");
SELECT COUNT(*) FROM "portfolio_accounts";
```

The table identifiers come only from `OFFICIAL_TABLE_COLUMNS`; no user-controlled identifier enters SQL. All four absent means `NO_FORMAL_DATA_FOUND`; all four present with compatible columns means zero/non-zero classification; a partial set or missing column is `INVENTORY_BLOCKED`.

- [x] **Step 5: Implement privacy-limited atomic reports and cleanup**

Successful reports match the approved output contract. After backups are verified, inventory failures atomically write this fixed-shape report and preserve both backups:

```python
{
    "report_version": 1,
    "project_id": "PP02",
    "status": "INVENTORY_BLOCKED",
    "error_code": error.code,
    "backup": {
        "copies": 2,
        "verified": True,
        "source_unchanged": True,
        "included_sidecars": included_sidecars,
    },
    "database": {
        "integrity_ok": False,
        "schema_compatible": False,
        "counts": None,
    },
    "privacy": {
        "row_values_selected": False,
        "row_values_reported": False,
        "real_data_uploaded": False,
        "migration_performed": False,
    },
}
```

Do not serialize caught exception text. Re-raise `FormalDataInventoryError` with `backups_verified=True` so the CLI exits non-zero while the local blocked report remains available.

- [x] **Step 6: Run service tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_formal_data_inventory.py -q
python -m py_compile src/services/formal_data_inventory_service.py
```

Expected: all service tests PASS; compile exits 0.

- [x] **Step 7: Commit the service checkpoint**

```bash
git add src/services/formal_data_inventory_service.py tests/test_formal_data_inventory.py
git commit -m "feat: add verified formal data inventory service"
```

### Task 3: Add the native-Windows CLI through a second RED/GREEN cycle

**Files:**
- Create: `scripts/pp02_formal_data_inventory.py`
- Modify: `tests/test_formal_data_inventory.py`

**Interfaces:**
- Consumes: `--source`, `--output-dir`, and `--confirm-apps-closed`.
- Produces: stdout verdict only on success; stderr stable code only on failure; exit `0` on inventory result and `2` on blocked/rejected runs.

- [x] **Step 1: Add CLI tests before creating the script**

Add behavior tests for the real `main(argv)` entry point:

```python
def test_cli_rejects_non_windows_before_creating_output(cli_module, tmp_path, capsys):
    source = create_official_database(tmp_path / "source.db", with_rows=False)
    output = tmp_path / "inventory"

    result = cli_module.main([
        "--source", str(source),
        "--output-dir", str(output),
        "--confirm-apps-closed",
    ])

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "wrong_environment\n"
    assert not output.exists()
```

Also test: missing close confirmation; output inside a synthetic Git repository; patched native-Windows success with no-data and formal-data verdicts; blocked inventory stderr; and absence of synthetic path/data markers from stdout/stderr/report.

- [x] **Step 2: Run CLI tests and verify RED**

Run:

```bash
python -m pytest tests/test_formal_data_inventory.py -q
```

Expected: only new CLI tests FAIL because `scripts/pp02_formal_data_inventory.py` is missing; service tests remain green.

- [x] **Step 3: Implement the thin CLI**

The CLI must check in this order: native Windows (reject Linux/WSL), `--confirm-apps-closed`, output outside every `.git` ancestor, then service execution. It must not print paths or exception text.

```python
def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not _is_native_windows():
        print("wrong_environment", file=sys.stderr)
        return 2
    if not args.confirm_apps_closed:
        print("apps_not_confirmed_closed", file=sys.stderr)
        return 2
    if _is_inside_git_repository(args.output_dir):
        print("output_inside_git_repository", file=sys.stderr)
        return 2
    try:
        report = FormalDataInventoryService().run(
            source_path=args.source,
            output_dir=args.output_dir,
        )
    except FormalDataInventoryError as exc:
        print(exc.code, file=sys.stderr)
        return 2
    print(report["status"])
    return 0
```

- [x] **Step 4: Run CLI/service tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_formal_data_inventory.py -q
python -m py_compile scripts/pp02_formal_data_inventory.py
```

Expected: all tests PASS; compile exits 0.

- [x] **Step 5: Commit the CLI checkpoint**

```bash
git add scripts/pp02_formal_data_inventory.py tests/test_formal_data_inventory.py
git commit -m "feat: add Windows formal data inventory CLI"
```

### Task 4: Document use, close local verification, and prepare the Draft PR

**Files:**
- Modify: `docs/pp02/R6_FORMAL_DATA_INVENTORY_TOOL_DESIGN.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`

**Interfaces:**
- Consumes: verified implementation and actual command outputs.
- Produces: exact Windows command, safety explanation, current Head/PR/CI evidence, deferred real-inventory gate, and Judge.

- [x] **Step 1: Add exact Windows usage and result handling**

Document this shape without a real path or database:

```powershell
$sourcePath = Read-Host "旧数据库的完整路径"
$outputDirectory = Read-Host "全新本地输出目录的完整路径"
python scripts/pp02_formal_data_inventory.py `
  --source $sourcePath `
  --output-dir $outputDirectory `
  --confirm-apps-closed
```

Explain the three status values, fixed report filename, two backup folders, no-Git/no-upload rule, and that a successful cloud CI does not authorize or prove a Windows real-data run.

- [x] **Step 2: Add flat Unreleased changelog entries**

Append exactly one feature entry and one test entry under `[Unreleased]` with the repository's flat `- [类型]` format.

- [x] **Step 3: Run focused and associated regressions**

Run:

```bash
python -m pytest tests/test_formal_data_inventory.py tests/test_database_migration_rehearsal.py \
  tests/test_portfolio_backup_service.py -q
python -m py_compile src/services/formal_data_inventory_service.py \
  scripts/pp02_formal_data_inventory.py
python scripts/check_ai_assets.py
git diff --check
```

Expected: all tests PASS and all checks exit 0.

- [x] **Step 4: Run the complete local CI-equivalent backend gate**

Run:

```bash
./scripts/ci_gate.sh
```

Expected: syntax, critical flake8, deterministic checks, and offline tests all exit 0. Record exact pass/skip/warning counts from this fresh run.

- [x] **Step 5: Perform the base-to-Head safety review**

Run:

```bash
git diff --stat a220e9e146e14722561bc084ec4e5306b30d36c7...HEAD
git diff --name-status a220e9e146e14722561bc084ec4e5306b30d36c7...HEAD
git ls-files | rg '(\.db(-wal|-shm)?$|backup-a|backup-b|formal-data-inventory-report|\.env$|\.log$)'
git diff --check a220e9e146e14722561bc084ec4e5306b30d36c7...HEAD
```

Expected: only approved code/tests/docs/control files differ; no database, sidecar, backup, report, `.env`, log, credential, dependency, or workflow file is newly tracked.

- [x] **Step 6: Record verified local results and commit**

Update the four `_ai-dev` files with exact evidence and `LOCAL_PASS — DRAFT_CI_PENDING`, then run `git diff --check` and commit:

```bash
git add docs/pp02/R6_FORMAL_DATA_INVENTORY_TOOL_DESIGN.md docs/CHANGELOG.md \
  _ai-dev/PROJECT_STATUS.md _ai-dev/AI_HANDOFF.md _ai-dev/WORK_TASK.md _ai-dev/WORK_RETURN.md
git commit -m "docs: record R6 inventory verification"
```

- [x] **Step 7: Push and create/update one Draft PR**

Push `agent/pp02-work5-r6-inventory-tool`, create one Draft PR whose base is `agent/pp02-work4-r4-database-rehearsal`, and include scope, tests, privacy boundary, risk, rollback, and `Windows real inventory not run` in the body. Do not mark Ready.

- [ ] **Step 8: Verify fixed-Head GitHub CI and finalize Judge**

Require the Draft PR Head SHA to match the tested/recorded Head and all applicable blocking GitHub Actions jobs to pass. CI failures may be fixed only within this plan's scope. Final project records must distinguish:

```text
CLOUD_TOOL_IMPLEMENTATION_PASS
WINDOWS_REAL_INVENTORY=NOT_RUN
REAL_DATA_MIGRATION=NOT_AUTHORIZED
DRAFT_HOLD
```

Do not change Head solely to embed its own final CI Run ID; put self-referential final evidence in Draft PR metadata and the user handoff.
