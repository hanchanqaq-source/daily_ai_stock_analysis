# R5 portable updater HOME collision fix

## Evidence

The A7 candidate (`a7dab6d3c745a666f34f1114726bca1e08f63ab3`) passed real Windows Basic validation: health and home returned HTTP 200, the UI was normal/nonblank, and the result was `R5_WINDOWS_BASIC_VALIDATION=PASS`.

During rollback-simulation preparation, the real packaged helper was inspected and found to assign its homepage response to `$home`. PowerShell variable names are case-insensitive, so this collides with the read-only automatic variable `$HOME` and can convert a successful readiness handshake into an exception and rollback.

## TDD record

- RED Head: `1d57f09a17654efa004548449960267c6acd29a0`
- RED CI Run: `30611152126`
- Desktop result: `60 passed, 1 failed`
- The only failure was `portable helper avoids the PowerShell HOME automatic variable`, which showed the exact `$home = Invoke-WebRequest` assignment.
- GREEN implementation Head: `170ebab8b813a63e8b071fcf20d742ee13e38837`
- Minimal production change: rename `$home` to `$homeResponse` and update the corresponding `.StatusCode` reference.

Final CI and a Head-bound final ZIP are required before R5 resumes. PR #9 remains Draft; no Ready, Merge, Tag, Release, main write, real data, or R3.7 action is authorized.
