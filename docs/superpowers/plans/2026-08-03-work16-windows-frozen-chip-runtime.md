# Work16 Windows Frozen Chip Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package and prove the existing Windows MiniRacer runtime in direct and final portable frozen artifacts.

**Architecture:** Extend the existing PyInstaller build and shared frozen verifier instead of adding a second packaging path. An opt-in early process probe loads the exact AkShare chip module and evaluates offline JavaScript, so the final extracted executable proves DLL and ICU availability without network or user data.

**Tech Stack:** Python 3.12, PyInstaller, PowerShell, `unittest`, GitHub Actions Windows runner.

## Global Constraints

- Base is exactly `568e26adf0e6393a7a0da1be57369535735cd05a`.
- Do not add, remove, pin or upgrade dependencies; `requirements.txt` remains unchanged.
- Do not perform Ready, merge, Tag, Release, signing, news, real credential/data or new Windows real-machine work.
- Keep the pull request Draft and bind final CI evidence to its full Head SHA.

---

### Task 1: Add failing packaging contracts

**Files:**
- Modify: `tests/test_desktop_packaging_assets.py`
- Test: `tests/test_desktop_packaging_assets.py`

**Interfaces:**
- Consumes: existing Windows PyInstaller and frozen-verifier text contracts.
- Produces: regression assertions for collection, asset checks, packaged runtime probe and final verifier invocation.

- [x] **Step 1: Write the failing tests**

Add `unittest` assertions requiring `--collect-all` for `py_mini_racer`, checks for
`mini_racer.dll` and `icudtl.dat`, a `DSA_PACKAGED_CHIP_PROBE` branch in `main.py`, and
use of that probe by `scripts/verify-frozen-backend.ps1`.

- [x] **Step 2: Run RED**

Run: `python -m unittest tests.test_desktop_packaging_assets -v`

Expected: the new tests fail because the fixed Base contains none of those contracts.

### Task 2: Implement the minimal runtime collection and probe

**Files:**
- Modify: `scripts/build-backend.ps1`
- Modify: `scripts/verify-frozen-backend.ps1`
- Modify: `main.py`
- Test: `tests/test_desktop_packaging_assets.py`

**Interfaces:**
- Consumes: installed `py_mini_racer.MiniRacer` and `akshare.stock_feature.stock_cyq_em`.
- Produces: `DSA_PACKAGED_CHIP_PROBE=1`, which exits zero only after the chip module imports and `MiniRacer().eval('6 * 7')` returns `42`.

- [x] **Step 1: Collect the existing runtime**

Append `--collect-all py_mini_racer` through the existing PowerShell argument array; do not modify dependency files.

- [x] **Step 2: Check packaged assets**

After PyInstaller output exists, require `_internal\py_mini_racer\mini_racer.dll` and
`_internal\py_mini_racer\icudtl.dat`, with the existing non-`_internal` fallback pattern
for compatible onedir layouts.

- [x] **Step 3: Add the offline runtime probe**

In the early `main.py` probe section, import `akshare.stock_feature.stock_cyq_em`, create
`MiniRacer` as a context manager, evaluate `6 * 7`, require `42`, print a success marker
and exit. On exception, print a bounded error and exit one.

- [x] **Step 4: Invoke the probe from the shared verifier**

Save and restore `DSA_PACKAGED_CHIP_PROBE` with the verifier's other process variables,
run the packaged executable from the temporary working directory and reject non-zero exit.

- [x] **Step 5: Run GREEN**

Run: `python -m unittest tests.test_desktop_packaging_assets -v`

Expected: all tests pass.

### Task 3: Validate, document and publish the Draft Head

**Files:**
- Modify: `docs/CHANGELOG.md`
- Modify: `_ai-dev/PROJECT_STATUS.md`
- Modify: `_ai-dev/AI_HANDOFF.md`
- Modify: `_ai-dev/WORK_TASK.md`
- Modify: `_ai-dev/WORK_RETURN.md`
- Modify only if required for accurate route status: `docs/ROADMAP.md`, `docs/OPEN_BLOCKERS.md`, `docs/pp02/REBUILD_ROADMAP.md`

**Interfaces:**
- Consumes: final local diff and GitHub Actions results.
- Produces: fixed-Head evidence and a Draft-only Work16 Judge.

- [x] **Step 1: Run related regression and static validation**

Run the packaging contract suite, `python scripts/check_ai_assets.py`, Python compile for
`main.py`, and `git diff --check`.

- [x] **Step 2: Commit and update the Draft PR**

Stage only Work16 files, commit with an English message, push the dedicated branch and
keep the PR Draft.

- [ ] **Step 3: Verify fixed-Head full CI**

Require all applicable jobs to complete successfully. In the Windows job, confirm the
direct package and final extracted ZIP both print the chip runtime success marker.

- [ ] **Step 4: Record the truthful final state**

Update the PR body and ledgers with the full Head SHA, Run ID, job counts, unverified
items, rollback and the final `DRAFT_HOLD` Judge. Do not Ready or merge.
