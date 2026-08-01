# Work8 Windows Installer Hotfix Design

## Status

- Project: `PP02｜AI 每日股票分析`
- Work: `WORK-008`
- Decision: `A｜保留安装向导`
- Base: `main@66666352e953d90becce420da7d35b649516af76`
- Branch: `agent/pp02-work8-r7-installer-fix`
- Target patch release: `v3.29.1`
- Design approval source: user selected方案 A on 2026-08-01
- Implementation authorization: independent branch, normal commits, Draft PR, GitHub Actions and in-scope fixes
- Still requires separate authorization: Ready, merge, main write, tag, GitHub Release and real-data work

## Problem statement

The official `v3.29.0` Windows installer was downloaded from the expected Release asset,
matched the expected byte size and SHA-256, and exposed the expected file version. On Windows
11 Home China build `26200`, the installer crashed twice before showing an actionable wizard.
Both events reported `System.dll` and exception `0xC0000005`. No installation directory,
uninstall registration or installed process was created.

This is a real installer bootstrap failure. Startup, empty-data, safe-default and restart
acceptance remain not executed because installation never completed.

## Root cause and evidence

The desktop app currently uses:

- `electron-builder ^24.13.3` resolved by the lockfile to the 24.x line;
- `electron ^31.4.0`;
- NSIS with `oneClick=false`;
- a forced current-user installation mode;
- a custom `installer.nsh` that preserves the directory wizard and protects runtime-writable
  files from system-protected directories.

Upstream issue
[`electron-builder#8536`](https://github.com/electron-userland/electron-builder/issues/8536)
reports the same builder line, assisted current-user installation, `System.dll`, and
`0xC0000005`. Upstream fix
[`electron-builder#9564`](https://github.com/electron-userland/electron-builder/pull/9564)
identifies a race in the Windows 7 compatibility path around `System::Store()` and avoids that
path on Windows 8 and later. The published `app-builder-lib 26.15.7` NSIS template no longer
contains the affected `System::Store` sequence.

The working hypothesis is therefore specific: the official PP02 `v3.29.0` installer inherited
the affected 24.x NSIS template, and Windows 11 triggered its known bootstrap race. The patch will
change only the builder/template line and the missing installer validation path; it will not
rewrite PP02's application runtime.

## Selected design

### 1. Keep the assisted installer

Retain:

- `oneClick=false`;
- `allowToChangeInstallationDirectory=true`;
- current-user installation without elevation;
- the existing protected-directory validation;
- the existing quoted old-uninstaller retry;
- installed-mode automatic update metadata;
- the no-install ZIP as a separate fallback asset.

The user can continue choosing a normal writable directory. The product will not be changed to a
fixed-path one-click installer and will not become portable-only.

### 2. Upgrade only the affected build chain

Change the desktop development dependency from the 24.x builder line to exactly
`electron-builder 26.15.7`, and regenerate the desktop lockfile with Node 20/npm. Keep the
current Electron runtime and application dependencies unchanged unless the lockfile operation
proves an unavoidable peer incompatibility. Any such incompatibility is a design blocker and
must be reported before widening scope.

Use an exact version instead of a caret range so a future Release cannot silently adopt a new
installer template.

### 3. Add a reusable Windows installer verifier

Add `scripts/verify-windows-installer.ps1` as the single verification entrypoint. It will accept:

- an explicit installer path;
- an explicit expected semantic version;
- an explicit isolated install root;
- an optional expected commit SHA for evidence binding.

The verifier will:

1. reject non-Windows execution and a missing or ambiguous installer;
2. create a unique test root below the GitHub runner temporary directory;
3. launch the NSIS installer silently in current-user mode with the explicit custom directory;
4. require exit code 0 and verify the installed executable, resources, uninstaller and file version;
5. start the installed application and prove it remains alive long enough to pass the existing
   packaged-runtime startup contract;
6. stop only the process tree started by the verifier;
7. run the generated uninstaller silently while preserving user data semantics;
8. require exit code 0 and verify program binaries and uninstall registration are removed;
9. clean only the verifier-owned temporary root;
10. emit stable PASS/FAIL evidence without printing credentials, environment contents or user data.

Cleanup belongs in `finally`. A failed install or uninstall must leave enough paths and exit-code
evidence in the Actions log to diagnose the failure, while still attempting safe process cleanup.
The script must never inspect or remove an existing PP02 user directory.

### 4. Make CI test the artifact it intends to ship

In `.github/workflows/ci.yml`, the Windows packaging job will build the installer, resolve the
single expected `pp02-ai-daily-stock-analysis-windows-installer-v<version>.exe`, and invoke the
verifier before uploading candidates. The existing frozen-backend, portable ZIP, fake-credential
scan and Head binding remain in place.

The Windows candidate artifact will include:

- the verified installer;
- the verified no-install ZIP;
- its SHA-256 file;
- update metadata needed for later Release validation.

This closes the current gap where CI proves that an installer file exists but never executes it.

In `.github/workflows/desktop-release.yml`, run the same verifier immediately after the Windows
Release build and before `Prepare release artifact (Windows)`. A tag workflow cannot publish an
installer that failed install/start/uninstall verification.

### 5. Preserve release and data boundaries

The patch does not modify `v3.29.0`, move its tag, replace its assets or erase the failed
acceptance evidence. `v3.29.1` may be created only after:

- the Draft PR fixed Head passes every applicable CI job;
- the Windows installer verifier passes on that same Head;
- the PR is separately authorized Ready and merged;
- the resulting main push CI passes;
- tag and Release receive separate authorization;
- the final `v3.29.1` Release asset is revalidated on a Windows machine.

No real API key, token, webhook, database, holding or historical analysis data enters build or test.

## Test strategy

### RED

Before changing the dependency or workflow, add tests that fail because:

- the desktop manifest does not pin the fixed builder version;
- no installer verification script exists;
- Windows CI does not execute the verifier against the generated installer;
- the Release workflow does not execute the verifier before publishing.

For the PowerShell verifier, use a controlled fake installer/uninstaller harness for fast contract
tests of argument validation, exit-code propagation, unique-root ownership and cleanup behavior.
Do not mock the process boundary that the test claims to verify.

### GREEN

Implement the smallest changes that make those tests pass, regenerate the lockfile, then run:

- desktop Node tests;
- PowerShell verifier contract tests on Windows;
- desktop package build;
- real silent install/start/uninstall against the generated installer;
- existing portable candidate verification;
- existing fake-credential scan;
- macOS package gate to catch builder-upgrade regressions;
- the full repository CI matrix.

### Release acceptance

A CI pass is necessary but not the final user acceptance. After an authorized `v3.29.1` Release,
Windows native acceptance must download the exact Release installer, verify size and SHA-256,
install through the visible wizard, confirm an empty isolated first start and safe defaults, close
and restart once, and report a final Judge.

## Error handling and Judge rules

- Hash or artifact ambiguity: stop with `BLOCKED_ARTIFACT_IDENTITY`.
- Installer non-zero exit or crash: `WINDOWS_INSTALLER_VALIDATION=FAIL`.
- Installed app exits before readiness: `INSTALLED_APP_STARTUP_VALIDATION=FAIL`.
- Uninstaller non-zero exit or residue in the verifier-owned program root:
  `WINDOWS_UNINSTALL_VALIDATION=FAIL`.
- Missing Windows runner or external Actions outage: `BLOCKED_ENVIRONMENT`.
- A failed CI or Windows verifier cannot be downgraded to skipped or treated as a documentation
  warning.
- Work8 can reach `IMPLEMENTATION_PASS — DRAFT_HOLD` without merge/release authorization.
- Final `R7_WINDOWS_FIRST_USE_ACCEPTANCE=PASS` requires the separately authorized
  `v3.29.1` Release acceptance.

## Files expected to change

- `apps/dsa-desktop/package.json`
- `apps/dsa-desktop/package-lock.json`
- `scripts/verify-windows-installer.ps1` (new)
- verifier contract tests under the existing desktop or scripts test structure
- `.github/workflows/ci.yml`
- `.github/workflows/desktop-release.yml`
- `docs/desktop-package.md`
- `docs/CHANGELOG.md`
- PP02 state, task, handoff and return ledgers

No backend, Web business logic, database schema, analysis behavior or notification behavior is in
scope.

## Rollback

Before release, close the Draft PR or revert its commits. After an authorized `v3.29.1` release,
do not move or overwrite tags. A later corrective version may revert the builder/workflow changes,
while `v3.29.0` and its failed acceptance evidence remain immutable.
