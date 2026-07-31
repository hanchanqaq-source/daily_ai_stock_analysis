# PR #9 / R5 Windows Basic Evidence — superseded for final judgment

- Head: `a7dab6d3c745a666f34f1114726bca1e08f63ab3`
- CI Run: `30607541335` — success after targeted Web retry
- Artifact ID: `8784669686`
- Artifact SHA-256: `0982e1b898f50bff191c349f8314dfd947496f032a09b8af0b6d6ff2f2c2095a`
- Inner portable ZIP SHA-256: `26e960ea87985f4ca2cbff73a81225a19b9392c1ec322072be4af627e69aa95c`
- Final-ZIP `fake_useragent/data/browsers.jsonl`: present, digest verified, listed in `managedFiles`
- Real Windows 11 Basic validation: PASS
  - `/api/health`: HTTP 200
  - `/`: HTTP 200
  - UI: normal, no error popup, nonblank
  - result: `R5_WINDOWS_BASIC_VALIDATION=PASS`

## Superseding blocker

During preparation of the isolated rollback simulation, the real packaged updater helper was found to assign the homepage response to `$home`. PowerShell variable names are case-insensitive, so `$home` collides with the read-only automatic variable `$HOME`. This can turn the real updater success handshake into an exception and unintended rollback.

Therefore the A7 Basic PASS remains valid launch evidence, but A7 is superseded as the final R5 update candidate. Final R5 judgment must bind to a new Head after the helper variable is renamed and the full CI/final ZIP/R5 checks are repeated.

Current state: `R5_HELPER_SUCCESS_HANDSHAKE_REWORK_REQUIRED — DRAFT_HOLD`.
