# Work24 Windows Runtime Integrity Guard Design

## Status and scope

PR #23 is merged and `main` is `e59c9d9e475d1f1149da01cceaa0cc79101497c7`
(`v3.29.3`). Its portable staging and final-ZIP contracts already preserve
dependency-internal runtime data and validate the extracted candidate, so this
Work does not reopen those fixes.

Work24 addresses a different failure boundary exposed on one Windows machine:
an external executable wrapper could replace the packaged Desktop/backend
entry points, forward an incomplete launch, and leave Desktop reporting only
`backend exited with code 0`. When the backend lost `--serve-only`, it entered
the normal CLI path and produced an unintended market-review history row.

The repository change is defensive and generic. It must not encode a malware
family name, a known wrapper size, a `g*.exe` naming rule, or any machine-local
path. It must not ingest the affected machine's executable, database, `.env`,
backup, evidence, or logs. System cleanup and local Codex repair remain out of
scope.

## Options considered

### Selected: signed-stage identity manifest plus backend launch contract

Generate a Windows runtime identity manifest after electron-builder's signing
phase and before NSIS/portable artifacts are assembled. Verify the running
Desktop path and the Desktop/backend file size and SHA-256 before spawning the
backend. Independently require Desktop-mode backend processes to receive the
complete serve-only loopback contract before any configuration, scheduling, or
analysis path can run.

This is selected because it blocks both observed boundaries: file substitution
is rejected by Desktop, while argument loss is rejected again inside the real
backend. It is independent of one malware implementation and remains compatible
with future Authenticode signing because the manifest is generated after
signing. electron-builder documents `afterSign` as running after code signing
and before distributable creation.

### Rejected: improve the exit-code message only

Capturing more stderr and classifying exit code 0 would improve diagnosis, but
the substituted executable would already have run and the backend could already
have written business data. This does not meet the fail-before-side-effect
requirement.

### Rejected: wrapper-specific filename or byte-size heuristics

Checking a particular prefix, icon sidecar, or file size would be easy to evade,
could false-positive on unrelated software, and would hard-code incident data
into the product. It is not an acceptable product contract.

## Architecture

### 1. Windows post-sign runtime identity manifest

Add a focused electron-builder `afterSign` hook. On Windows only, it resolves
the staged application root from `context.appOutDir`, then records exactly two
closed entries in `resources/pp02-runtime-integrity.json`:

- role `desktop`: `PP02 AI Daily Stock Analysis.exe`;
- role `backend`: `resources/backend/stock_analysis/stock_analysis.exe`.

Each entry contains a normalized relative path, byte size, and lowercase
SHA-256. The manifest also contains schema version `1`, the PP02 product ID,
and the package version. The hook fails the build if either expected file is
missing, is not a regular file, resolves outside the staged application root,
or cannot be hashed. Non-Windows builds do not create or require this manifest.

The hook runs after signing so any signing mutation is included in the recorded
identity, and before NSIS/portable targets so the manifest is included in both
final artifacts.

### 2. Desktop pre-spawn verification

Add a small `runtime-integrity` module with no new dependency. In packaged
Windows mode, `startBackend` calls it before `child_process.spawn`.

The verifier fails closed when the manifest is missing, malformed, for another
product/version, contains duplicate or extra roles, references an unexpected
path, or when either current file's path, size, or SHA-256 differs. It also
requires `app.getPath('exe')` to resolve to the manifest's exact Desktop path;
therefore a legitimate binary launched under a renamed wrapper path is rejected
even if its bytes still match.

Development mode and packaged non-Windows mode retain their current behavior.
The public error is stable and actionable: the program files or launch contract
failed verification, the backend was not started, and no analysis task was
started. Detailed diagnostics may identify the failed role and check, but must
not include credential values or business data.

### 3. Backend Desktop launch contract

Add a pure Python validator and invoke it immediately after argument parsing,
before configuration loading and before any normal analysis branch. When
`DSA_DESKTOP_MODE` is truthy, the invocation must satisfy all of these rules:

- `--serve-only` is present;
- `--host` resolves to a loopback host accepted by the existing Desktop host
  normalization contract;
- `--port` is an integer from `1` through `65535`;
- mutually incompatible analysis modes such as `--market-review`, scheduling,
  or explicit stock execution are absent.

Violation prints one bounded diagnostic marker to stderr and exits nonzero
before creating an analyzer, scheduler, report, history row, or HTTP listener.
Ordinary CLI invocations without `DSA_DESKTOP_MODE` are unchanged.

### 4. Error classification and diagnostic tail

Desktop keeps a small bounded stderr tail for the current backend process. If
health polling observes an exited backend, it classifies the Desktop launch
contract marker separately from a generic exit and sends the stable actionable
message to the loading page. Raw unbounded backend output is never placed in a
URL or user-facing page.

Runtime-integrity rejection happens before spawn. Desktop launch-contract
rejection happens before backend business initialization. Both are recorded in
the existing installer/backend diagnostic stream using fixed reason codes.

## Data flow

1. CI freezes the backend and electron-builder stages the Windows application.
2. electron-builder completes signing (currently `NotSigned` is still a valid
   signing state), then the `afterSign` hook hashes the final staged Desktop and
   backend binaries and writes the closed manifest.
3. NSIS and the no-install ZIP consume that staged tree.
4. At runtime, packaged Windows Desktop verifies its own expected path and both
   manifest entries before spawning the backend.
5. Desktop spawns the verified backend with `DSA_DESKTOP_MODE=true` and the
   existing `--serve-only --host 127.0.0.1 --port <selected>` arguments.
6. The backend validates that contract before entering any other mode.
7. Only after both gates pass may normal health polling and UI loading begin.

## Failure behavior

- Missing/invalid manifest: do not spawn the backend; show repair/reinstall
  guidance and explicitly state that no analysis task was started.
- Desktop path/name mismatch: same fail-closed behavior, even when the binary
  hash matches.
- Desktop/backend size or digest mismatch: same fail-closed behavior.
- Desktop environment with missing or conflicting serve-only arguments: backend
  exits nonzero before business initialization; Desktop reports a launch-
  contract error instead of only the numeric exit code.
- Ordinary backend crash after a valid contract: retain the existing generic
  health failure behavior plus bounded diagnostic evidence.

No automatic deletion, quarantine, renaming, repair, security-product change,
or system scan is performed by PP02.

## Verification

Testing follows RED-GREEN-REFACTOR:

1. Node unit tests prove the manifest generator records the exact two files and
   fails on missing inputs.
2. Node unit tests prove the runtime verifier accepts a valid fixture and rejects
   missing, malformed, wrong-product/version, renamed Desktop, unexpected path,
   wrong size, and wrong digest fixtures before `spawn` is called.
3. Python unit tests prove valid Desktop serve-only arguments pass and missing or
   conflicting arguments fail before any injected business callback can run.
4. Packaging contract tests require the `afterSign` hook, manifest identity,
   and final extracted Windows ZIP checks.
5. The existing Desktop suite, relevant Python suites, AI asset checks, diff
   checks, and fixed-Head GitHub Actions must pass.

Windows CI remains the authoritative packaged-artifact gate. This cloud Linux
work does not claim a new Windows-machine acceptance result.

## Repository and release boundaries

- Base: `main@e59c9d9e475d1f1149da01cceaa0cc79101497c7`.
- Branch: `agent/pp02-runtime-integrity-guard`.
- Deliverable: one Draft PR with source, tests, documentation, and append-only
  Work24 status records.
- No merge, Ready transition, Tag, Release, version bump, signing identity,
  real Windows data, or affected-machine artifact is authorized.
