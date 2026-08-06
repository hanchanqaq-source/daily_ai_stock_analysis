# Work29 v3.29.5 Safe Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an unpublished `3.29.5` Windows candidate whose source version cannot regress behind the latest release and whose installer, portable package, unpacked payload, and installed directory pass a fail-closed Microsoft Defender scan before upload.

**Architecture:** Use root `VERSION` plus a Node verifier to bind every checked-in version surface and Git tag. Use a separately tested Node Defender orchestrator to update intelligence, validate Defender health, execute non-remediating custom scans, and write exact-Head reports; wire it ahead of candidate upload and into the installed lifecycle.

**Tech Stack:** Node.js standard library and `node:test`, Python/pytest packaging contracts, PowerShell/NSIS lifecycle scripts, GitHub Actions on Ubuntu/Windows/macOS, Microsoft Defender `Get-MpComputerStatus` and `MpCmdRun.exe`.

## Global Constraints

- Base is fixed at `main@9a4a705d06370ddbebf669ab8efb0058ce9eb81a`.
- Candidate source version is exactly `3.29.5`; current formal release remains `v3.29.4`.
- Use only synthetic fixtures; never read or embed real credentials or user data.
- Do not modify or migrate databases, analysis history, watchlists, or period reports.
- Do not add or upgrade product dependencies.
- Defender unavailable, update failure, unhealthy/stale status, detection, scan error, missing target, or missing report is a blocking failure.
- Candidate upload occurs only after version, credential, Defender, runtime-integrity, and installed-lifecycle gates pass.
- Stop at one Draft PR plus exact-Head CI. Do not Ready, merge, write `main`, create a Tag, or create a Release.

---

### Task 1: Lock the version contracts at 3.29.5

**Files:**
- Create: `VERSION`
- Create: `scripts/verify-release-version.js`
- Create: `apps/dsa-desktop/tests/release-version.test.js`
- Modify: `apps/dsa-desktop/package.json`
- Modify: `apps/dsa-desktop/package-lock.json`
- Modify: `apps/dsa-web/package.json`
- Modify: `apps/dsa-web/package-lock.json`
- Modify: `src/services/full_data_backup_service.py`
- Modify: `tests/test_desktop_installer_config.py`
- Modify: `tests/test_packaging_build_scripts.py`

**Interfaces:**
- Consumes: root `VERSION`, package metadata, reachable `vX.Y.Z` tags, optional release tag or bump kind.
- Produces: `verifyRepositoryVersion({ root, mode, releaseTag, bump })` and CLI exit `0` only for a coherent candidate/release.

- [ ] **Step 1: Write failing version tests**

Add tests requiring root `VERSION=3.29.5`, all package/lock surfaces and backup
metadata to match it, candidate mode to reject equality/below `v3.29.4`, release
mode to reject a tag different from `v3.29.5`, and auto-tag mode to reject the
wrong requested successor.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py -q`

Run: `node --test apps/dsa-desktop/tests/release-version.test.js`

Expected: pytest reports stale `3.29.3`/missing `VERSION`; Node reports the missing verifier module.

- [ ] **Step 3: Implement the single source and verifier**

Use strict stable SemVer parsing, numeric comparison, and literal checks of the
four package roots plus the backup default. Candidate mode resolves reachable
stable tags with `git tag --merged HEAD` and requires `VERSION` to be newer.
Release mode requires `releaseTag === 'v' + VERSION`. Auto-tag mode additionally
requires the source version to be the requested patch/minor/major successor.

- [ ] **Step 4: Synchronize every version surface**

Set `VERSION`, Desktop/Web package roots, lockfile root entries, and
`DEFAULT_APPLICATION_VERSION` to `3.29.5`. Do not alter dependency entries.

- [ ] **Step 5: Run GREEN**

Run the two RED commands again. Expected: all selected tests pass.

### Task 2: Lock fail-closed Defender orchestration

**Files:**
- Create: `scripts/windows-defender-scan.js`
- Create: `apps/dsa-desktop/tests/windows-defender-scan.test.js`

**Interfaces:**
- Consumes: `--head <40-sha>`, `--report <json-path>`, repeated `--path <target>`; Windows PowerShell and `MpCmdRun.exe`.
- Produces: `runWindowsDefenderScan(options, dependencies)` and a sanitized JSON report bound to the exact Head and targets.

- [ ] **Step 1: Write failing orchestration tests**

Use temporary real files and deterministic fake process results. Assert fail-closed
behavior for non-Windows, signature update failure, disabled service, passive mode,
signature age over one day, missing scanner, missing target, scan exit `2`, and
missing report directory. Assert a clean run records file SHA-256 and all target
results without file contents.

- [ ] **Step 2: Run RED**

Run: `node --test apps/dsa-desktop/tests/windows-defender-scan.test.js`

Expected: FAIL because `scripts/windows-defender-scan.js` does not exist.

- [ ] **Step 3: Implement minimal scanner orchestration**

Update intelligence with `Update-MpSignature`, collect a compact JSON status from
`Get-MpComputerStatus`, choose the newest platform `MpCmdRun.exe`, validate
`AMServiceEnabled`, `AntivirusEnabled`, `AMRunningMode=Normal`, signature identity
and age, then run this for each path:

```text
MpCmdRun.exe -Scan -ScanType 3 -File <target> -DisableRemediation
```

Accept only exit `0`; write final `PASS` only after every target passes. On error,
write a bounded `FAIL` report and rethrow without exposing child output that could
contain unexpected sensitive text.

- [ ] **Step 4: Run GREEN and mutation checks**

Run the RED command again. Temporarily make scan exit `2` acceptable and confirm
the detection test fails; restore and rerun all tests.

### Task 3: Enforce version and Defender gates in candidate/release workflows

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/desktop-release.yml`
- Modify: `.github/workflows/auto-tag.yml`
- Modify: `scripts/verify-windows-installer.ps1`
- Modify: `scripts/tests/verify-windows-installer-contract.ps1`
- Modify: `tests/test_packaging_build_scripts.py`
- Modify: `tests/test_portable_final_zip_contract.py`

**Interfaces:**
- Consumes: exact PR/release Head, `VERSION`, built Windows assets, installed root, Defender scanner.
- Produces: candidate and release workflow ordering that cannot upload or publish before all version/security gates pass.

- [ ] **Step 1: Write failing workflow/lifecycle contracts**

Require full tag checkout, candidate verifier execution on all Desktop package
platforms, removal of every `npm version` release mutation, exact source/tag
verification, preinstall Defender scan before lifecycle, installed-root scan before
first application launch, always-uploaded Defender reports, and candidate upload
strictly after every scan.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/test_packaging_build_scripts.py tests/test_portable_final_zip_contract.py -q`

Expected: missing version and Defender gates plus remaining release-time mutation.

- [ ] **Step 3: Wire candidate gates**

Add `VERSION` and both security scripts to path detection. Fetch tags, run candidate
version verification before Desktop tests/builds, preserve final ZIP extraction for
the scan, scan the closed upload set plus unpacked/extracted directories, pass the
real scanner into installed lifecycle, upload reports with `if: always()`, then run
credential scan, lifecycle, and candidate upload.

- [ ] **Step 4: Wire release and Auto Tag gates**

Replace release-time `npm version` with `node scripts/verify-release-version.js release --tag "$RELEASE_TAG"`.
Make Auto Tag validate the checked-in version and create only its exact annotated
tag after the requested bump check.

- [ ] **Step 5: Extend installed lifecycle**

Require a scanner path and Defender report path, invoke the scanner on `$ownedRoot`
after installed identity/registration validation and before first launch, record a
stage PASS, and keep failure cleanup/uninstall behavior unchanged. Contract tests
use a deterministic fake scanner executable but cannot omit the scan.

- [ ] **Step 6: Run GREEN**

Run the RED command again plus Desktop full tests. Expected: all pass.

### Task 4: Synchronize Work29 evidence and verify locally

**Files:**
- Modify: `docs/CHANGELOG.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify: `docs/pp02/REBUILD_ROADMAP.md`

**Interfaces:**
- Consumes: RED/GREEN output, root cause, fixed base, review and CI evidence.
- Produces: auditable Work29 current state without rewriting completed Work27/28 history.

- [ ] **Step 1: Record Work28 closure and Work29 authorization**

Set current Work29 Base/branch/goal, mark PR/CI/candidate pending, preserve Work27
history, and record that Ready/merge/Tag/Release are forbidden.

- [ ] **Step 2: Run local verification**

Run:

```bash
node --test apps/dsa-desktop/tests/release-version.test.js
node --test apps/dsa-desktop/tests/windows-defender-scan.test.js
npm ci --prefix apps/dsa-desktop
npm test --prefix apps/dsa-desktop
python -m pytest tests/test_desktop_installer_config.py tests/test_packaging_build_scripts.py tests/test_portable_final_zip_contract.py -q
python scripts/check_ai_assets.py
git diff --check
```

Do not claim a real Defender PASS locally because this cloud environment is Linux;
the exact-Head Windows Job is authoritative.

- [ ] **Step 3: Scope and secret review**

Inspect status and the complete diff. Confirm no real credentials/data, dependency
changes, database changes, Ready/merge/Tag/Release operations, or unrelated product
features.

- [ ] **Step 4: Independent review and fixes**

Review the fixed Base-to-Head diff against this plan. Resolve every Critical or
Important issue, rerun affected tests, and record any accepted residual risk.

### Task 5: Publish one Draft PR and verify the exact candidate

**Files:**
- Modify: Work29 control files only for final remote evidence.

**Interfaces:**
- Consumes: reviewed local Head.
- Produces: one Draft PR, exact-Head CI, security reports, candidate identity, and a verified download link.

- [ ] **Step 1: Commit and push the reviewed branch**

Use scoped commits, push `agent/pp02-work29-safe-candidate`, and create one Draft PR
into `main`. The PR body records root cause, tests, Defender limitations, rollback,
and Draft Hold.

- [ ] **Step 2: Wait for exact-Head complete CI**

Require all applicable Jobs. Windows must show source/installer/Web/manifest
`3.29.5`, preinstall Defender PASS, installed-root Defender PASS, fake-credential
PASS, runtime integrity PASS, install/start/restart/health/uninstall PASS, and
candidate/report artifacts.

- [ ] **Step 3: Download and cross-check artifacts**

Verify the artifact belongs to the frozen Head, compute its ZIP SHA-256, inspect
member names, compute installer/portable SHA-256, and match those hashes plus Head
and Defender identity to the security report. Reject expired, missing, mismatched,
or warned artifacts.

- [ ] **Step 4: Return the safe candidate link**

Provide the exact candidate download link, version, Head, CI Run, hashes, Defender
engine/signature identity, and scan scope. Explicitly state that it is an unsigned
unpublished candidate and keep the PR Draft. Do not merge, tag, or release.
