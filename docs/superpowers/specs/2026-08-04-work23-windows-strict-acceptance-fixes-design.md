# Work23 Windows Strict Acceptance Fixes Design

## Approval and locked evidence

- Design approval source: the user's Work23 authorization on 2026-08-04.
- Existing PR: `#23`, kept open and Draft on
  `agent/pp02-work20-full-backup-period-persistence`.
- Starting Head: `6dba54b9dba84f2562f6ab91d735b1c6e5744702`.
- Work22 evidence report SHA-256:
  `30AC65C81E3F86E4CADBAEC9D2DBA95B432BA4DF8DBE81F12015857B9E5E39BE`.
- Work22 remains `FAIL`; this Work does not rewrite its result or weaken its
  acceptance criteria.
- Work22's real database, cold backup, complete export, and restore checkpoint
  are immutable and out of scope.

## Root-cause evidence

### Official uninstall lifecycle

The current Windows CI stops both installed application runs with the verifier's
`Stop-StartedProcessTree` helper before invoking the uninstaller. It therefore
cannot catch Work22's live-uninstall failure. The Electron `before-quit` handler
also starts `stopBackend()` without preventing quit and waiting for the child to
exit, so normal application shutdown can leave the frozen backend after the
Electron parent exits.

electron-builder's default NSIS process check can fall back from exact executable
paths to image-name matching when PowerShell inspection is unavailable. Work23
must instead make the owned process boundary explicit: the packaged Electron
executable and the packaged `stock_analysis.exe`, both at exact paths below the
validated install root. No process may be selected only because its name matches
or because it lives in a neighboring directory.

### Version drift

The Desktop `package.json` and its lockfile still declare `3.21.0`. Those values
drive Electron's Windows FileVersion/ProductVersion, the NSIS DisplayVersion,
the installed UI's desktop runtime version, artifact names, and portable
manifest. The Work20 backup service separately defaults to `3.29.2`, while the
Web package remains the placeholder `0.0.0`. PR CI does not inject a release tag,
so these independent fallbacks can disagree in a candidate built from one Head.

### Cache classification

`stock_daily` is a best-effort market-data cache. `get_daily_history` reads it
only when fresh and otherwise obtains data through the configured fetcher, then
best-effort writes the fetched rows back. A read or write failure does not hide
freshly fetched data. It contains provider market bars and derived indicators,
not user-entered state.

`fundamental_snapshot` is not a pure cache. Its model comment still calls it
write-only, but current analysis and history APIs read it as a fallback when the
canonical context snapshot is absent. Those historical payloads are bound to a
past `query_id` and may not be reproducible after provider data changes. It must
be included in complete backup and restore.

### Windows signing

The repository has no Windows certificate identity, private key, or CI secret
wiring. electron-builder can sign when an authorized certificate is supplied,
but Work23 may not acquire or inspect one. The safe code change is therefore an
artifact audit/requirement interface: PR candidates record installer and app
Authenticode status; a future authorized release can turn on a fail-closed
`RequireAuthenticodeSignature` switch. Work23 cannot claim a trusted signature.

## Approaches considered

### A. Exact owned-process shutdown plus live-uninstall CI — selected

Gate Electron quit until the backend exits, add an installed helper that closes
only exact product executable paths, and run the official uninstaller once while
the restarted app is still live. This directly reproduces Work22 while preserving
the user's cleanup boundary.

### B. Add another uninstall retry

This would hide the symptom already observed by Work22 and would not prove the
first lifecycle completed or the orphan process disappeared. Rejected.

### C. Increase cleanup sleeps and scan the whole install directory

This is timing-dependent and could terminate unrelated executables placed below
or beside a user-selected directory. Rejected.

For data, including every cache would make a byte-for-byte database comparison
easy but would enlarge backups with provider-derived data and preserve stale
market bars. Excluding both named tables would lose historical fallback data.
The selected split is to include `fundamental_snapshot` and explicitly exclude
only `stock_daily` as a rebuildable table.

## Selected design

### 1. One-shot official uninstall

- Electron's first `before-quit` event prevents exit when a backend child is
  live. It waits for `stopBackend()` to clear the tracked child, then requests
  quit once more. A second event, or an event with no backend, proceeds normally.
- The packaged uninstall helper resolves exactly two executable paths below the
  supplied install root: the Electron product executable and the frozen backend.
  It first requests a normal main-window close, waits for Electron's own shutdown
  gate, then force-stops only exact-path leftovers and verifies that both exact
  paths have zero live processes.
- The NSIS `customCheckAppRunning` hook invokes that helper and fails closed if
  the helper is missing or cannot prove zero owned processes.
- The Windows lifecycle verifier does not call its external process-tree killer
  after the second readiness marker. It starts the official uninstaller exactly
  once, waits for exit code zero, and then proves the tracked Electron process,
  exact app/backend paths, installed files, and the exact HKCU uninstall record
  are all gone. A sibling sentinel remains untouched in the helper contract.

### 2. Authoritative `3.29.3` identity

- Desktop `package.json` and lockfile are `3.29.3`.
- Web `package.json` and lockfile are `3.29.3`; packaged builds also default
  `DSA_WEB_VERSION` from the Desktop package before building static assets.
- Complete backup metadata defaults to `3.29.3`. Tests that explicitly rehearse
  a v3.29.2 source remain fixed fixtures rather than new candidate identity.
- Windows validation requires both FileVersion and ProductVersion to begin with
  exactly `3.29.3`, the HKCU DisplayVersion to equal it, packaged Web
  `build-info.json.version` to equal it, and the portable manifest/tag to equal
  `3.29.3` / `v3.29.3`.

### 3. Backup/restore classification

- Add `fundamental_snapshot` to the analysis backup group with its full safe
  column set and JSON/timestamp validation. Export, preview counts, restore,
  recovery artifacts, digests, and restart verification all cover it.
- Replace the vague fundamental-cache exclusion with a structured
  `manifest.excluded_tables.stock_daily` declaration containing its cache class,
  `contains_user_data: false`, restore behavior, and rebuild entrypoint.
- Restore clears destination `stock_daily` inside the same SQLite transaction so
  stale destination cache cannot survive a formal restore.
- A deterministic test starts with an empty post-restore cache, drives
  `get_daily_history` through a fake provider, verifies a usable result, and
  verifies best-effort repopulation. No external network or real user data is
  used.

### 4. Signing audit boundary

- Windows validation records installer and installed Electron Authenticode
  status without printing certificate material.
- `RequireAuthenticodeSignature` rejects anything except `Valid`; it is not
  enabled in Work23 CI because no authorized identity exists.
- No certificate, private key, password, real secret, or CI secret reference is
  added or read. Activating real signing remains a separate authorization gate.

## Error handling and security

- Uninstall fails closed if exact ownership cannot be resolved or owned processes
  remain. It never broadens to directory-prefix, image-name, registry-name, or
  machine-wide process deletion.
- Backup validation remains a closed schema with SHA-256 integrity. Adding
  `fundamental_snapshot` subjects its JSON text to the existing secret-key and
  credential-like-value rejection.
- Restore clears the declared cache only after full validation and within the
  existing `BEGIN IMMEDIATE` transaction. Rollback restores the destination on
  any pre-commit failure.
- Diagnostic output contains statuses and counts, not real data, paths outside
  the isolated owned root, environment dumps, certificate bodies, or secrets.

## Verification

1. TDD RED/GREEN for Electron quit gating and exact-path uninstall helper.
2. Windows contract proves owned live processes are removed and a sibling
   sentinel survives.
3. Windows installed lifecycle invokes the uninstaller once while the app is
   live and proves zero remaining owned processes.
4. Version contract covers Desktop/Web packages and locks, backup metadata,
   FileVersion/ProductVersion, DisplayVersion, Web build-info, and portable
   manifest.
5. Backup tests prove `fundamental_snapshot` round-trips and `stock_daily` is
   explicitly declared, cleared, and deterministically rebuilt.
6. Authenticode audit records unsigned status; the require switch fails closed
   in its Windows contract without using a real certificate.
7. Run affected Python, Web, Desktop, governance, syntax, and packaging contract
   checks locally, then the complete PR #23 fixed-Head CI.

The resulting artifact is a new unsigned Windows candidate for strict retest.
Unsigned is reported, not converted into a PASS; obtaining a trusted signing
identity requires separate authorization.
