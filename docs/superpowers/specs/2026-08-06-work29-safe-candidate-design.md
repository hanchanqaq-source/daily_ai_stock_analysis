# Work29 v3.29.5 Safe Candidate Design

## Context and decision

`v3.29.4` points at `main@4322e7ddf09b8262c0e7279af9e321aec4f77758`,
but the source package metadata on the later `main@9a4a705d06370ddbebf669ab8efb0058ce9eb81a`
still reports `3.29.3`. The Desktop release workflow hides this drift by running
`npm version` only inside release runners. Ordinary CI therefore built the Work28
candidate from stale source metadata while still passing its internal consistency
checks. The Windows candidate pipeline also checks synthetic credential leakage,
but has no real antimalware scan.

The approved Work29 choice is a safe unpublished candidate. It fixes the process,
builds source version `3.29.5`, adds a fail-closed Microsoft Defender gate, and
stops at one Draft PR plus exact-Head CI. It does not merge, tag, or release.

## Considered approaches

1. **Selected: repair the version and malware gates before building.** This is
   the only option that prevents the same version regression and prevents an
   unscanned candidate from being uploaded.
2. **Temporary version-only build.** Faster, but the next release or candidate
   could repeat the same drift and it would not establish an antimalware gate.
3. **Immediate formal release.** Provides a durable download URL, but combines
   code review, merge, tagging, and publication before the new gates prove
   themselves. It is outside this Work's authorization.

## Version architecture

- Add root `VERSION` as the authoritative stable application version. Work29 sets
  it to `3.29.5`.
- Desktop and Web `package.json` plus both root lockfile entries must equal
  `VERSION`. Backup metadata that represents the application version must also
  equal it.
- A cross-platform Node verifier reads all version surfaces and the repository's
  reachable stable tags. Candidate mode fails when the source version is not
  strictly newer than the latest stable tag. Release mode fails unless the
  requested `vX.Y.Z` tag exactly equals `VERSION`.
- CI fetches tags and runs candidate mode before Desktop packaging on Linux,
  Windows, and macOS.
- Desktop Release checks source/tag equality and builds the checked-in metadata.
  It no longer mutates `package.json` or lockfiles with `npm version`.
- Auto Tag may create only the annotated tag declared by `VERSION`, and only when
  that version is the requested patch/minor/major successor of the latest stable
  tag. It never calculates and applies an independent package version.

## Windows antimalware architecture

- A Node command invokes the installed Microsoft Defender tooling on a clean
  `windows-latest` GitHub runner. The command first updates security intelligence,
  reads `Get-MpComputerStatus`, resolves the newest platform `MpCmdRun.exe`, and
  rejects disabled, non-normal, unavailable, or stale protection.
- Every target is scanned with a custom scan and `-DisableRemediation`. Microsoft
  documents that this mode scans archives and returns `2` for an unremediated
  detection, user-action requirement, or scan error. Only exit `0` is accepted.
- Before any candidate upload, the gate scans the installer EXE, its blockmap,
  updater metadata, portable ZIP and checksum, `win-unpacked`, and a fresh ZIP
  extraction. The installed lifecycle verifier also scans the actual installed
  application directory before first launch.
- Reports contain the exact Git Head, UTC timestamps, Defender engine/platform/
  signature identity, signature age, target sizes and file SHA-256 where
  applicable, per-target exit status, and one final PASS/FAIL result. Reports do
  not contain file contents, credentials, or user data.
- Defender update failure, missing scanner, unhealthy status, stale signatures,
  missing target, scan error, detection, or missing report all fail the Job.
  Security reports upload with `if: always()`, but candidate binaries upload only
  after all security and lifecycle gates pass.

## Scope and data safety

- Use only repository source and synthetic test fixtures. Do not read or embed a
  real API key, `.env`, database, analysis history, watchlist, or period report.
- Do not add or upgrade product dependencies. Node standard library and built-in
  Windows Defender tooling are sufficient.
- Do not claim that an unsigned executable is cryptographically trusted. The
  result proves the exact CI candidate passed Microsoft Defender with the recorded
  intelligence version; it cannot prove that every antivirus engine will agree.
- Stop on any gate failure. A detected artifact is not uploaded or sent to the
  user; investigation and a new fixed Head are required.

## Test and acceptance design

1. RED proves current source metadata is below `v3.29.4`, package sources lack one
   authoritative version, release builds mutate package metadata, and no Defender
   gate blocks candidate upload.
2. Unit tests exercise real version comparison and fail-closed malware-scan
   orchestration with deterministic fake process results; they cover unavailable,
   disabled, stale, update-failed, detected, missing-target, and clean paths.
3. Existing Python/Desktop/packaging contracts are updated to require `3.29.5`
   and the real workflow ordering.
4. Exact-Head CI must complete all applicable Jobs. Windows must prove version
   `3.29.5`, Defender PASS for preinstall and installed targets, fake-credential
   PASS, installer lifecycle PASS, and upload the candidate plus reports.
5. Before delivery, download the exact CI artifact, verify its SHA-256 and member
   names, cross-check the Defender report Head/version/target hashes, and provide
   only that verified candidate link.

## Rollback

The Draft branch can be closed with no effect on `main` or any released version.
No user data or database migration exists. If later merged, rollback is a normal
revert of the version verifier, workflow gates, and version-source commit; released
tags and releases remain separate, explicitly authorized operations.

## 2026-08-07 hosted-runner Defender remediation addendum

Exact-Head Run `31168780911` and its one permitted Windows rerun proved that the
candidate build is not blocked by product code or a malware detection. Both
attempts stopped before all seven target scans because the hosted Windows Server
2025 image could not complete the original `Update-MpSignature` prerequisite.
The same image also preconfigures whole-drive `C:\` and `D:\` exclusions and
disables archive scanning, so skipping the update alone would not establish a
trustworthy scan.

The approved remediation remains fail closed and is limited to the disposable
GitHub-hosted runner:

- Remove only the exact `C:\` and `D:\` path-exclusion entries when present;
  leave every other exclusion untouched.
- Force archive scanning on and verify that it remains enabled after the change.
- Resolve the newest installed `MpCmdRun.exe` and update intelligence directly
  from Microsoft MMPC with `-SignatureUpdate -MMPC`.
- Keep the existing Normal-mode, service, engine, identity, and signature-age
  checks after the update.
- Before each custom scan, run `-CheckExclusion -Path <target>`. Microsoft defines
  exit `1` as not excluded; exit `0` means excluded. Accept only exit `1` for this
  proof, then continue to the existing custom scan where only exit `0` passes.
- Record only bounded environment, exit-code, Defender-identity, digest, and
  per-target status fields. Never record child stdout/stderr or file contents.

Preparation failure, MMPC update failure, disabled archive scanning, an excluded
target, an indeterminate exclusion check, stale/unhealthy Defender, or any scan
failure still blocks installation and candidate upload. No workflow permission,
product dependency, product feature, database, user-data, Tag, or Release scope is
added by this addendum.
