# Work32 Final Usability Closure Design

## Status and authority

The user approved option A on 2026-08-07 as one bounded authorization for the
P002/PP02 final usability closure. Work32 may use one isolated branch, scoped
commits, one Draft PR, and exact-Head GitHub Actions. It must not read a real API
key, modify user data, change dependencies, expand product scope, mark the PR
Ready, merge, tag, or release.

No usability claim is allowed until every hard gate in this document passes on
one frozen candidate Head. A local or partial pass is evidence only.

## Confirmed baseline

- Fixed Base: merged `main@295821e463674e9f82a79a75a0a13052ef1cb696`.
- PR #26 repaired two configuration-save defects: the Desktop transaction had
  removed a pending LLM secret before backend cross-field validation, and the Web
  client had ignored FastAPI issues nested under `detail.issues`.
- Those repairs passed their unit and prior Windows lifecycle tests, but no
  accepted installed-candidate proof binds configuration persistence, DPAPI,
  restart injection, and a real outbound inference request into one chain.
- Main CI Run `31211548666` failed only in the Windows Job. Build and verifier
  contracts passed; `Validate installed Windows lifecycle` stayed active until
  the Job ended about 48 minutes later. Diagnostic and candidate upload steps
  never ran.
- The lifecycle verifier bounds app readiness and cleanup polling, but calls the
  installer and uninstaller with `Start-Process -Wait`. A hung child therefore
  cannot enter its catch/finally diagnostic path. The workflow step has no outer
  watchdog.

## Selected design

### 1. Bounded lifecycle execution and durable diagnostics

Introduce a single PowerShell helper for installer and uninstaller execution.
It starts only the resolved owned executable, waits for a validated finite
timeout, records the bounded outcome in the pre-created stage report, terminates
the owned process tree on timeout, and throws a sanitized error. Installer,
normal uninstall, and best-effort cleanup uninstall all use this helper.

The CI and release lifecycle steps also receive a step-level timeout. This is a
last-resort watchdog, not the normal control path: the script's shorter internal
timeouts should fail first and write diagnostics. Because only the lifecycle step
times out, the following `if: always()` diagnostic upload can still execute.

The stage report exists before any external child starts. It contains only stage,
status, UTC time, bounded duration/exit metadata, and sanitized failure type. It
must not contain command output, environment values, authorization headers, file
contents, or credentials. Defender scans and verdicts are not retried.

### 2. Installed configuration acceptance with a synthetic key

The installed Windows lifecycle gets a verifier-owned application-data root under
`RUNNER_TEMP`; it does not touch a developer's or user's profile. A deterministic
fake key is derived from the exact candidate Head in memory and is never printed.

The acceptance chain uses the installed backend and the real Desktop credential
vault implementation:

1. Start the freshly installed app and discover its installed backend port from
   bounded, allow-listed startup diagnostics.
2. Validate and persist public AI settings through the installed backend using
   `GENERATION_BACKEND=codex_cli`, explicit LiteLLM fallback, AIHubMix channel,
   historical/default model fields, and the LLM mask placeholder. The public
   `.env` path must not receive plaintext.
3. Use a dedicated packaged-Electron harness with real `safeStorage`/DPAPI to
   commit the synthetic AIHubMix key against the returned configuration version
   in the same verifier-owned app-data root.
4. Stop and restart the installed app. Assert that persisted public fields return
   intact and the secret returns only the mask token.
5. Run the installed backend's explicit LiteLLM generation smoke test against a
   loopback OpenAI-compatible mock server. The server compares the Authorization
   value only in memory and emits a boolean receipt, never the key or header.
6. Export configuration and the complete backup and prove the exact synthetic key
   is absent. Run the existing exact-Head UTF-8/UTF-16 credential scanner over the
   candidate payload, installed root, verifier app-data, diagnostics, exports,
   and backup.

The loopback mock accepts only the expected request path and shape, returns the
existing exact JSON smoke response, has bounded request/body sizes and a bounded
lifetime, and writes only safe receipt metadata. All temporary state is inside an
exact verifier-owned `RUNNER_TEMP` child and is removed in cleanup.

### 3. Frozen candidate identity and security closure

One exact Draft PR Head is the only acceptance authority. Its applicable CI Jobs
must all pass without selective omission. Windows must prove candidate version and
Head identity, build/runtime contracts, install/start/configure/restart/smoke/
uninstall lifecycle, always-uploaded sanitized diagnostics, fake-credential scan,
and Microsoft Defender results for the closed candidate target set.

After CI passes, download only that Run's artifacts, bind artifact names and
reports to the frozen Head, compute SHA-256 for the artifact ZIP, installer, and
portable archive, cross-check report target hashes, and inspect member names. A
missing, expired, mismatched, warned, incomplete, or non-clean report rejects the
candidate. The result remains an unsigned unpublished candidate and does not
authorize merge or release.

## Hard gates

All of the following must pass on the same frozen Head:

1. Fresh installed AIHubMix configuration validates and saves.
2. `codex_cli` primary plus explicit LiteLLM fallback/channel saves.
3. Historical/default AI fields survive the save and restart.
4. The synthetic API key is stored by real Windows `safeStorage`/DPAPI, returns
   masked after restart, and is actually used by the installed backend request.
5. No plaintext synthetic key exists in `.env`, logs, diagnostics, exports,
   backups, candidate archives, installed files, or verifier-owned app data.
6. Installer, first start, configuration, restart, health, smoke request, process
   cleanup, and uninstaller each finish inside a declared bound.
7. A lifecycle failure or timeout still yields a sanitized diagnostic artifact;
   missing diagnostics are a hard failure.
8. Every applicable exact-Head CI Job passes; no path-skipped native gate may be
   treated as proof.
9. Candidate artifacts and security reports match the frozen Head and SHA-256;
   Microsoft Defender reports clean results for their required closed target set.

## Rejected alternatives

- **Rely only on the PR #26 unit tests.** They prove component behavior but not
  the installed DPAPI/restart/request chain that failed for the user.
- **Retry or raise GitHub Job timeouts.** A longer unbounded wait reproduces the
  same diagnostic blind spot. Retries could also hide deterministic failures.
- **Use a real API key or external model provider.** This violates the explicit
  authorization boundary and makes acceptance depend on network/provider state.
- **Publish a release to obtain an installable artifact.** Candidate validation
  must precede, not follow, merge/tag/release authority.

## Failure handling and rollback

Every failure stops the candidate gate, preserves only sanitized bounded evidence,
and keeps the PR Draft. Product dependencies, schemas, and user data are unchanged.
The branch can be closed without changing `main`; if later merged under separate
authorization, rollback is a normal source revert. Tags and releases remain
separate irreversible decisions and are outside Work32.
