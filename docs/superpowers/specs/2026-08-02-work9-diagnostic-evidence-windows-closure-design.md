# Work9 Diagnostic Evidence and Windows Closure Design

## Status

- Project: `PP02｜AI 每日股票分析`
- Work: `WORK-009`
- Existing Draft PR: `#17`
- Branch: `agent/pp02-work8-r7-installer-fix`
- Takeover Head: `9cb9a70e9176711096adf12ba5674c56d6f314d2`
- Previous diagnostic Head / Run: `eae4b46501c9a183dda20d2975121987e676943b` / `30742085965`
- Authorization source: the user formally started Work9 on 2026-08-02 with an explicit scope,
  execution order, stop gates and final report contract.

## Problem

Work8 repaired the known electron-builder assisted-installer bootstrap defect and added a real
Windows install/start/uninstall gate. Its fixed-Head diagnostic Run built the frozen backend and
Windows candidates, but failed in the verifier contract before the installed lifecycle. The child
verifier emitted its stable failure marker, then failed while saving diagnostics; cleanup removed
the owned install root and the `if: always()` upload found no files.

The installed backend's direct error is therefore still unknown. A backend or packaging fix before
restoring the evidence chain would be a guess and is prohibited.

## Confirmed immediate failure boundary and first hypothesis

The failing workflow launches `scripts/tests/verify-windows-installer-contract.ps1` with
`powershell.exe`. That contract launches the verifier through the same host. The verifier's
installed-file collector calls `[IO.Path]::GetRelativePath`, an API available in modern .NET but
not in the .NET Framework surface used by Windows PowerShell 5.1. The call occurs before
`diagnostic-summary.txt` is created. This exactly matches the observed sequence: stable verifier
failure marker, no preserved summary, cleanup, and no artifact.

This is the first single hypothesis to test. It is not yet the installed-backend root cause.

## Selected design

### 1. Transfer the Work lock without changing product design

Close Work8 as `COMPLETED_WITH_BLOCKER`, record Work9 takeover at the exact current Head, and move
the execution lock to `HELD_BY_WORK_009`. Keep PR #17 Draft and preserve the already approved
assisted current-user installer, selectable directory, Node 22 Desktop build jobs, exact
electron-builder line, portable ZIP and updater behavior.

### 2. Make diagnostic preservation fail-safe

The verifier will create a cleanup-independent diagnostic directory under `RUNNER_TEMP`. On any
failure it will write the core summary first, before optional collectors. The summary contains the
failure stage, UTC times, exit code when known, sanitized exception and stack, executable and
working paths, file-existence state, selected port and stable command structure.

Optional collectors—desktop log, port/process state, installed-file inventory, Windows Application
events and direct backend probe—run independently. One collector failure is recorded by exception
type and cannot prevent the summary or the remaining collectors. Raw stdout/stderr are bounded,
sanitized and removed after the sanitized copy is written.

The Windows PowerShell-compatible relative-path helper will use already validated descendant paths
and normalized prefix removal instead of a .NET-Core-only method.

The contract fixture remains a real child-process test. It must prove that a failing fake installer
produces a non-zero verifier exit, a stable failure marker, a persistent diagnostic summary outside
the cleaned install root, no parent deletion and no copied fixture content. If the contract itself
fails, it will expose bounded child output and produce an explicit contract-stage report for the
workflow upload instead of leaving an empty artifact path.

### 3. Prove the final deliverable, not `win-unpacked`

The Windows package path must open the final no-install ZIP in a new temporary directory, verify its
manifest and managed-file list, and run the frozen backend from that extracted tree. The contract
must explicitly prove that `resources/backend/.../fake_useragent/data/browsers.jsonl` is present in
the final ZIP and represented by `pp02-portable-release.json.managedFiles`. Build, copy and cleanup
steps may not drop runtime data that exists in the original frozen backend.

This is a packaging integrity gate only. Missing `browsers.jsonl` becomes a confirmed root cause
only if the final artifact test or installed-backend diagnostics demonstrate that failure.

### 4. Fixed-Head evidence run

After targeted tests pass, commit and push one diagnostic enhancement Head. The PR Windows job runs
the contract and real installed lifecycle at that exact full SHA. The `if: always()` upload name
continues to bind full SHA and Run ID. The artifact must exist on either PASS or FAIL and contain no
environment dump, credentials, `.env`, database, data directory, log directory or user content.

If a usable artifact still cannot be obtained, stop immediately with
`ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT`.

### 5. Evidence-backed root-cause fix and closure

Only after a valid artifact exists, record the direct error, component boundary, confirmed root
cause, log and code evidence, packaged/development difference and smallest reproduction. Add one
failing regression test, verify the expected RED, implement one minimal fix and run targeted tests
before the full PR matrix.

The final automated closure requires final installer/ZIP structure, install, first start, backend
health, normal exit, second start, uninstall, diagnostic artifact and all PR #17 jobs. A green CI is
not Windows real-machine acceptance; real-machine work remains a separate stop gate.

## Security and privacy

- Never enumerate or print complete environment variables or raw command lines.
- Never read or upload real `.env`, credentials, databases, data, holdings, reports or user logs.
- Diagnostic text is bounded and redacted before persistence; raw probe files are deleted.
- Installed-file inventory contains relative paths and sizes only and excludes `.env`, `data/`,
  `logs/`, databases and user content.
- Cleanup is restricted to validated verifier-owned roots under `RUNNER_TEMP`.

## Out of scope

Electron/npm security consolidation, Dependabot, blocking `npm audit`, the full Web test set,
Playwright, Windows signing, macOS signing/notarization, the final icon, a PP02 control Skill and a
real-data business closure are deferred.

## Stop gates

Stop for unavailable diagnostics, scope expansion beyond PR #17, any need for real credentials or
data, a product-design change, Windows real-machine action, or after complete CI passes and merge
authorization is required. Do not Ready, merge, write `main`, tag or release in Work9.

