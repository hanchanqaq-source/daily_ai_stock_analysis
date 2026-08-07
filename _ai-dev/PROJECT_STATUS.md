<!-- WORK30_DEFENDER_RETRY: Run 31191357654 built Windows successfully, then MMPC update exited 2 before all scans; bounded retry and diagnostic-upload TDD are authorized. -->
# PP02 当前状态

> 本文件是 PP02 唯一当前状态真源。其他文档出现冲突时，以本文件和可验证证据为准。

```text
PROJECT_ID=PP02
PROJECT_NAME=AI 每日股票分析
CHAT_ROLE=AUTO_TAKEOVER
WORK_ID=WORK-030
ROLE_LOCK=SUPERSEDED_BY_PP02-WORK-HANDOFF-002
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
WORK_STATE=LOCAL_REVIEW_PASS_DRAFT_PR_PENDING
EXECUTION_LOCK=WORK30_DEFENDER_RETRY_DIAGNOSTIC_UPLOAD_DRAFT_PR_AND_EXACT_HEAD_CI_ONLY
APPLICATION_BASE_VERSION=3.29.5
CURRENT_RELEASE_VERSION=3.29.4
FRAMEWORK_TEMPLATE_VERSION=1.5.6
PROJECT_WORK_VERSION=pp02-cloud-rebuild-work.1
ACTIVE_BASE=ed44a6a3dfa366d595eed1a6999e089d65207cbc
ACTIVE_BRANCH=agent/pp02-work30-defender-retry
ACTIVE_PR=PENDING_DRAFT
CURRENT_STAGE=Work30 RED/GREEN, final local verification and independent re-review pass with no Critical or Important findings; Draft PR pending
CURRENT_WORK=WORK-030 — bounded Defender intelligence retry and diagnostic upload repair
ACTIVE_GOAL=retry only transient MMPC intelligence updates within a fixed bound and prevent pre-lifecycle missing diagnostics from adding a second failure
PRODUCT_PR=20_MERGED
PRODUCT_FIXED_HEAD=e11946f528c9cb64beeec8b626ada457c02b0034
PRODUCT_MERGE_COMMIT=25de369f8e12438a1ec1f3511c68256c471243e4
PRODUCT_MAIN_CI_RUN=30822458701
PRODUCT_MAIN_CI_RESULT=PASS_8_OF_8
STATUS_PR=21_MERGED
STATUS_SYNC_MERGE_HEAD=25313cf0f23f0f4ab4922ea983bcd05b3577e23e
UNPUBLISHED_CANDIDATE_VERSION=3.29.5_PENDING_EXACT_HEAD_CI
UNPUBLISHED_INSTALLER_BYTES=PENDING
UNPUBLISHED_INSTALLER_SHA256=PENDING
UNPUBLISHED_INSTALLER_SIGNATURE=PENDING_EXPECTED_UNSIGNED
WINDOWS_RELATED_TESTS=LOCAL_ORCHESTRATION_PASS_17_OF_17_REAL_WINDOWS_RUN_31168780911_REPRODUCED_SIGNATURE_UPDATE_FAILURE_TWICE_ALL_TARGETS_NOT_RUN
FORMAL_HISTORY_QUERY_ID=1c4ae649232d40eaae7dcb6bb1b6981f
FORMAL_HISTORY_ID=2
FORMAL_HISTORY_STATUS=PASS_PERSISTED_AFTER_CANDIDATE_RESTART_AND_WORK12_RESTORE
RUN_DIAGNOSTIC=DEGRADED_NEWS_EMPTY_AND_CHIP_DLL_MISSING
WORK12_RESTORED=PASS_HEALTH_OK_DATABASE_AND_LOGS_PRESENT
WORK14_EVIDENCE_HEAD=da2290597e880c4c4a4c1c04e5cc548aa5542ea9
WORK14_EVIDENCE_CI_RUN=30821021196
WORK14_EVIDENCE_CI_RESULT=PASS_4_SUCCESS_4_PATH_SKIPPED
WORK14_JUDGE=PASS_WITH_DEGRADATIONS_DRAFT_HOLD
WORK16_EVIDENCE_HEAD=016e3408795b4adaf1eab25210681be66b7e8ff8
WORK16_EVIDENCE_CI_RUN=30831393819
WORK16_EVIDENCE_CI_RESULT=PASS_7_SUCCESS_1_PATH_SKIPPED
WORK16_WINDOWS_JOB=91746056804_SUCCESS
WORK16_CHIP_PROBE=PASS_3_MARKERS_DIRECT_REBUILD_FINAL_ZIP
WORK16_REVIEW=PASS_NO_CRITICAL_OR_IMPORTANT
WORK16_JUDGE=PASS_DRAFT_HOLD
WORK20_LOCAL_IMPLEMENTATION_HEAD=ae310d1e7fd22fc7139d1ebb63f1bd1d3a0f416c
WORK20_EVIDENCE_COMMIT=42e8f75d435b9d90ad5764f538cb20e9e48c1e9f
WORK22_EVIDENCE_REPORT_SHA256=30AC65C81E3F86E4CADBAEC9D2DBA95B432BA4DF8DBE81F12015857B9E5E39BE
WORK22_JUDGE=FAIL_LOCKED
WORK23_AUTHORITATIVE_VERSION=3.29.3
WORK23_DRAFT_PR=23_MERGED
WORK23_REMOTE_FIXED_HEAD=190c3bd2a9cb7a1237d4e8b27b86133fddfac762
WORK23_REMOTE_CI=RUN_30990684208_PASS_8_OF_8
WORK23_WINDOWS_CANDIDATE=PASS_UNPUBLISHED
WORK23_SIGNING=READ_ONLY_AUDIT_INTERFACE_NO_REAL_IDENTITY
WORK23_JUDGE=PASS_MERGED_RELEASED_V3_29_3
WORK24_LOCAL_NODE=PASS_99_OF_99
WORK24_LOCAL_PYTHON=PASS_24_LAUNCH_CONTRACT_PLUS_10_PACKAGING
WORK24_LOCAL_AUXILIARY=PASS_PY_COMPILE_AI_ASSETS_SYNTAX_DIFF
WORK24_LOCAL_BACKEND_AGGREGATE=DEFERRED_MISSING_LOCKED_DEPS_NETWORK_POLICY_REMOTE_CI_AUTHORITATIVE
WORK24_PR=24_MERGED
WORK24_REMOTE_FIXED_HEAD=f91576cb6fa9d7d516141758593a5086a50e205a
WORK24_REMOTE_CI=RUN_31028088206_PASS_8_OF_8
WORK24_MERGE_COMMIT=f813084944f7a9c5459312ef84da7956cda1a37f
WORK24_MAIN_CI=RUN_31032267014_FAIL_7_OF_8
WORK24_WINDOWS_JOB=92395692229_FAILED_FIXED_3_SECOND_UVICORN_STARTUP_DEADLINE
WORK24_JUDGE=MERGED_MAIN_CI_FAIL_NOT_RELEASEABLE
WORK25_BASE=f813084944f7a9c5459312ef84da7956cda1a37f
WORK25_FAILURE_RUN=31032267014
WORK25_FAILURE_JOB=92395692229
WORK25_ROOT_CAUSE=INNER_FIXED_3_SECOND_STARTUP_DEADLINE_CONFLICTS_WITH_OUTER_90_SECOND_FROZEN_HEALTH_GATE
WORK25_TDD_RED=PASS_HELPER_3_SECONDS_AND_MAIN_DISCONNECT_REPRODUCE_RUNTIMEERROR
WORK25_TDD_GREEN=PASS_DELAYED_READY_AFTER_4_SECONDS
WORK25_LOCAL_RELATED=PASS_32_OF_32
WORK25_LOCAL_AUXILIARY=PASS_PY_COMPILE_AI_ASSETS_BOUNDARIES_DIFF
WORK25_LOCAL_FULL_BACKEND=DEFERRED_EXISTING_ENV_MISSING_LOCKED_DEPS_AND_FLAKE8_REMOTE_CI_AUTHORITATIVE
WORK25_DRAFT_PR=25_MERGED
WORK25_REMOTE_FIXED_HEAD=bae6c0ffa637ed443d4bb003a729fa2bba4ef042
WORK25_REMOTE_CI=RUN_31037493697_PASS
WORK25_JUDGE=PASS_MERGED_BY_SEPARATE_WORK26_AUTHORIZATION
WORK26_MAIN=4322e7ddf09b8262c0e7279af9e321aec4f77758
WORK26_ANNOTATED_TAG=V3_29_4_POINTS_TO_4322E7DDF09B8262C0E7279AF9E321AEC4F77758
WORK27_BASE=4322e7ddf09b8262c0e7279af9e321aec4f77758
WORK27_ROOT_CAUSE=DESKTOP_DROPPED_PENDING_SECRET_BEFORE_BACKEND_CROSS_FIELD_VALIDATION_AND_FRONTEND_READ_ISSUES_FROM_WRONG_LEVEL
WORK27_TDD_RED=PASS_INITIAL_4_EXPECTED_FAILURES_PLUS_REVIEW_2_EXPECTED_FAILURES
WORK27_TDD_GREEN=PASS_SYSTEM_CONFIG_API_19_OF_19_HOOK_5_OF_5
WORK27_LOCAL_FULL=PASS_WEB_1081_PASSED_2_SKIPPED_DESKTOP_100_OF_100_LINT_BUILD_AI_ASSETS_DIFF
WORK27_REVIEW=PASS_THREE_ROUNDS_NO_FINDINGS_DRAFT_PR_AND_EXACT_HEAD_CI_ALLOWED
WORK27_DRAFT_PR=26_MERGED
WORK27_INITIAL_REMOTE_HEAD=04a2259c11659ec51635a56ffde74981d55bf7dd_TREE_VERIFIED
WORK27_PRIOR_REMOTE_HEAD=9cb32d7fa663770d6cef18a9012c7518e6807ba6
WORK27_PRIOR_CI=RUN_31106977554_PASS_EXECUTED_5_OF_5_WINDOWS_AND_DESKTOP_PATH_SKIPPED_NOT_ACCEPTED
WORK27_DESKTOP_COVERAGE=PASS_FIRST_RUN_DYNAMIC_LLM_VAULT_TEST_AND_DESKTOP_100_OF_100
WORK27_REMOTE_FIXED_HEAD=849dfaef4faa9c38f91e8e833262764c40369d3d
WORK27_REMOTE_CI=RUN_31108033144_PASS_8_OF_8
WORK27_WINDOWS_LIFECYCLE=PASS_RUN_31108033144
WORK27_JUDGE=PASS_MERGED_BY_WORK28_AUTHORIZATION
WORK28_MERGE_COMMIT=9a4a705d06370ddbebf669ab8efb0058ce9eb81a
WORK28_MAIN_CI=RUN_31111163231_PASS_8_OF_8
WORK28_JUDGE=PASS_MERGED_MAIN_CI_SUCCESS
WORK29_BASE=9a4a705d06370ddbebf669ab8efb0058ce9eb81a
WORK29_SOURCE_VERSION=3.29.5
WORK29_FORMAL_RELEASE_REMAINS=3.29.4
WORK29_ROOT_CAUSE=RELEASE_TAG_BUILD_MUTATED_VERSION_ONLY_IN_RUNNER_WHILE_MAIN_SOURCES_REMAINED_3_29_3_AND_CI_LACKED_DEFENDER_GATE
WORK29_LOCAL_VERSION_TESTS=PASS_10_OF_10
WORK29_LOCAL_DEFENDER_ORCHESTRATION_TESTS=PASS_17_OF_17_WITH_HOSTED_RUNNER_EXCLUSION_ARCHIVE_MMPC_AND_CHECK_EXCLUSION_GATES
WORK29_LOCAL_DESKTOP=PASS_127_OF_127
WORK29_LOCAL_PYTHON_CONTRACTS=PASS_38_DIRECT_RUNPY_PYTEST_UNAVAILABLE
WORK29_LOCAL_AUXILIARY=PASS_AI_ASSETS_NODE_SYNTAX_YAML_PARSE_DIFF_DEPENDENCY_DATA_SECRET_BOUNDARIES
WORK29_REAL_DEFENDER=NOT_CLAIMED_LINUX_ENV_EXACT_HEAD_WINDOWS_CI_REQUIRED
WORK29_DRAFT_PR=28_OPEN_DRAFT
WORK29_INITIAL_REMOTE_HEAD=b689e51188a373262e69414fc30f0014c6647796
WORK29_REMOTE_FIXED_HEAD=3C1E73B4D9443345CD34B849DAED5F625E1130EA_RUN_31168780911_FAILED_WINDOWS_SIGNATURE_UPDATE_TWICE_SUPERSEDED_BY_DEFENDER_RUNNER_REPAIR_HEAD_PENDING
WORK29_CI_TRIGGER=PR27_PR28_OPENED_SYNCHRONIZE_REOPENED_AND_BROWSER_AUTHORED_FINAL_SYNCHRONIZE_CREATED_NO_RUN_MANUAL_SAFE_CANDIDATE_ONLY_DISPATCH_REQUIRED
WORK29_REMOTE_CI=RUN_31168780911_FAIL_SAFE_CANDIDATE_7_PASS_WINDOWS_SIGNATURE_UPDATE_EXIT_1_TWICE_SEVEN_TARGETS_NOT_RUN
WORK29_JUDGE=ACTIVE_DRAFT_HOLD
WORK30_BASE=ed44a6a3dfa366d595eed1a6999e089d65207cbc
WORK30_FAILURE_RUN=31191357654
WORK30_FAILURE_JOB=92909068724
WORK30_ROOT_CAUSE=SINGLE_ATTEMPT_EXTERNAL_MMPC_UPDATE_EXIT_2_PLUS_EXPECTED_MISSING_PRE_LIFECYCLE_DIAGNOSTIC_DIRECTORY_TREATED_AS_UPLOAD_ERROR
WORK30_LOCAL_BASELINE=PASS_DEFENDER_17_OF_17_DESKTOP_127_OF_127_AI_ASSETS_DIFF_PYTEST_UNAVAILABLE_DIRECT_RUNPY_REQUIRED
WORK30_TDD_RED=PASS_DEFENDER_16_PASS_3_EXPECTED_FAIL_WORKFLOW_1_EXPECTED_FAIL
WORK30_TDD_GREEN=PASS_DEFENDER_21_OF_21_WORKFLOW_CONTRACT_WITH_ORDER_THROW_TIMEOUT_AND_REDACTION
WORK30_LOCAL_FULL=PASS_DEFENDER_21_OF_21_DESKTOP_131_OF_131_PYTHON_ACTIONS_24_OF_24_YAML_VERSION_AI_ASSETS_DIFF_DEPENDENCY_DATA_BOUNDARIES
WORK30_REVIEW=PASS_NO_CRITICAL_OR_IMPORTANT_PRIOR_TEST_AND_STATUS_GAPS_VERIFIED_CLOSED
WORK30_DRAFT_PR=PENDING
WORK30_JUDGE=ACTIVE_DRAFT_HOLD
CURRENT_STATUS=WORK30_LOCAL_REVIEW_PASS_DRAFT_PR_PENDING
ACTIVE_BLOCKER=NONE
NEXT_WORK=NONE
NEXT_ACTION=PUSH_CREATE_DRAFT_PR_AND_WAIT_EXACT_HEAD_FULL_CI
AUTHORIZATION_REQUIRED=TRUE_FOR_READY/MERGE/TAG/RELEASE
LAST_UPDATED=2026-08-07
```

## 2026-08-06 Work29 / v3.29.5 safe unpublished Windows candidate

- Work28 merged PR #26 without Head drift as `main@9a4a705d…`; its own push Run
  `31111163231` passed 8/8 Jobs, including the full Windows install lifecycle.
  No Tag or Release was created. Work29 starts from that exact fixed Base.
- The current formal release is `v3.29.4`, but the release workflow had changed
  package versions only inside its runner. Checked-in Desktop/Web sources remained
  `3.29.3`, and ordinary main CI therefore produced a misleading `3.29.3`
  candidate. Existing CI also had no real antimalware gate.
- Work29 makes root `VERSION=3.29.5` authoritative and binds both packages,
  lockfile roots, and backup metadata to it. Candidate builds must be newer than
  every fetched canonical stable Tag; release builds must exactly match the checked-in
  version; Auto Tag may only create that annotated source Tag.
- A fail-closed Windows orchestrator updates Defender intelligence, requires an
  enabled Normal-mode engine with current identity metadata, and runs non-remediating
  custom scans over the installer, metadata, portable ZIP, unpacked/fresh-extracted
  payloads, final release assets, and the actual installed directory. Any detection,
  scan error, stale/unavailable engine, missing input, or missing report blocks
  artifact upload.
- Local Desktop passes 122/122, including 10/10 version and 12/12 Defender tests;
  all 34 related Python contracts pass through direct `runpy`. Accepting
  `MpCmdRun` exit `2` was mutation-tested and correctly failed. Selected Python
  workflow contracts, YAML parsing, AI governance, Node syntax and diff checks
  pass. This Linux environment has neither
  pytest nor Windows Defender, so it cannot claim the authoritative real scan.
- Draft PR [#28](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/pull/28)
  is Open Draft and mergeable at initial Head `b689e511…`. PR #27 was closed
  without CI after GitHub created no Check Suite for its normal events. The
  reviewed recovery keeps the main CI topology, embeds both Defender scans in
  the existing lifecycle verifier, directly gates the Windows Job on version,
  and produced browser-authored Head `25739486…`; GitHub still created no Check
  Suite. The bounded fallback reuses CI through Desktop Release's existing manual
  input surface only when the release message starts `[SAFE_CANDIDATE_ONLY]`.
  In that mode normal release preflight/build/publish Jobs are skipped, so no Tag
  or Release path can execute; exact-Head CI is the only called workflow. The
  first safe dispatch, Run `31127507235` at Head `3c227d12…`, failed at workflow
  startup before any Job because the caller had not delegated CI's read-only
  `pull-requests` permission. A RED/GREEN contract now requires the caller to
  grant only `contents: read` and `pull-requests: read`; an exact-Head retry is pending.
- Scope remains one Draft PR and exact-Head CI. No database/user data, real
  credential, dependency, Ready, merge, main write, Tag, or Release is authorized.
- Safe-candidate Run `31127543822` at Head `33ec1eb…` ran the full topology: six
  candidate Jobs passed; backend failed only because an older test still required
  every non-publish Job to have exactly `contents: read`; Windows completed the
  frozen backend, portable candidate and verifier contract, then stopped before
  any Defender target scan because signature update and status query shared one
  opaque PowerShell process. The diagnostic artifact is exact-Head bound and all
  seven targets are `NOT_RUN`; it is not a malware verdict or deliverable.
- The approved minimum correction keeps both Defender operations blocking but
  runs them separately, records only bounded stage/exit/signal/error-code metadata,
  and never records child stdout/stderr. The permission contract now grants only
  the reusable caller's required `contents: read` plus `pull-requests: read` while
  preserving every other Job's prior permission. RED/GREEN evidence is Desktop
  `123/123` and related Python/Actions contracts `38/38`; a new exact-Head CI is
  still required before any candidate can be accepted.
- Run `31168780911` at Head `3c1e73b4…` then passed every candidate Job except
  Windows. The original Windows attempt and the one permitted rerun both failed
  at signature update with exit `1`; all seven targets remained `NOT_RUN`, and
  install/start/restart/uninstall plus candidate upload did not execute. The
  GitHub-hosted Windows Server 2025 image preconfigures exact `C:\` and `D:\`
  whole-drive exclusions and disables archive scanning, so bypassing the update
  would not establish a valid malware verdict.
- The approved runner repair removes only those exact whole-drive exclusions when
  present, enables and rechecks archive scanning, updates through the official
  `MpCmdRun -SignatureUpdate -MMPC` path, and requires each target's
  `-CheckExclusion` result to be exactly exit `1` before the existing custom scan.
  Focused TDD produced 15 expected RED failures and `17/17` GREEN. The exclusion
  mutation was detected; Desktop `127/127`, Python/Actions `38/38`, AI assets,
  syntax, diff and scope boundaries pass. A new exact-Head Windows CI remains
  pending; no malware PASS is claimed from Linux.

## Historical current entry | 2026-08-06 Work27 / Windows Desktop AI configuration save validation repair

- GitHub and fetched refs confirm Work25 is no longer active: PR #25 merged as
  `main@4322e7dd…`; annotated `v3.29.4` peels to that exact commit. Work27 starts
  from that fixed Base in `agent/pp02-work27-config-save-validation`.
- Root cause 1: Desktop validates the full draft, then removed every vault-owned
  secret before the backend save. A new key is not committed to DPAPI until that
  save succeeds, so backend cross-field validation saw `missing_api_key`.
- Root cause 2: FastAPI returns validation metadata under `detail.issues`, while
  the Web client read top-level `issues`; the field errors became an empty array
  and the UI showed only `System configuration validation failed`.
- Initial TDD RED is four expected failures: first-run AIHubMix, `codex_cli` plus
  a saved LiteLLM channel, historical default provider fields, and nested field
  issues. Review added two more RED counterexamples for a notification URL and
  bounded error display. The minimal client repair sends the existing mask token
  only for pending LLM API credentials, keeps prior omission semantics for other
  vault-owned secrets, and unwraps field issues into structured UI state plus a
  bounded `field: reason` alert. Focused GREEN is API `19/19` and Hook `5/5`.
- Full Web is `1081` passed / `2` skipped; lint, production build, AI-asset check,
  and diff check pass. The cloud Python runtime lacks locked `requests`, so the
  new backend characterization is deferred to exact-Head CI and is not claimed
  locally. Independent re-review reports no Critical, Important, or Minor
  findings and permits Draft PR plus exact-Head CI. No database, user data,
  dependency, version, workflow, Tag, Release, or real credential was changed.
  Draft PR identity, exact Head CI, and the
  Windows installer lifecycle remain pending.
- Draft PR [#26](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/pull/26)
  is Open Draft from initial remote Head `04a2259c…`. Its tree
  `bd912914…` was compared against the local candidate tree and matches exactly.
  Head `9cb32d7f…` completed Run `31106977554`: all five executed Jobs passed,
  including backend offline tests, but Desktop/Windows/macOS were path-skipped.
  A native rerun kept the same skip condition, so that Head is not accepted.
- A related Desktop regression now proves first-run dynamic LLM credentials are
  prepared without pre-commit disk writes, stored without plaintext, and restored
  only in memory. Desktop full is `100/100`; third-round review has no findings.
  This Desktop coverage commit is the new frozen CI Head and must run the Windows
  install/start/restart/uninstall lifecycle before Work27 can pass.

## Historical current entry | 2026-08-05 Work25 / Windows frozen-backend startup timeout repair

- PR #24 fixed Head `f91576cb…` passed Run `31028088206` 8/8 and was merged as
  `main@f813084…`. The merge tree matches the PR tree, but main Run
  `31032267014` finished 7/8 and therefore remains non-releaseable.
- The only failed Job was Windows `92395692229`. Its frozen backend completed
  packaging and the MiniRacer probe, then exited because `start_api_server`
  allowed only `3.0s` for `uvicorn_server.started`. The outer frozen verifier
  already waits for real HTTP readiness for up to 90 seconds; Desktop waits for
  health for 60 seconds. The inner fixed deadline is the conflicting gate.
- The `cp1252` `UnicodeEncodeError` lines occurred while rendering diagnostics
  after startup had already failed. They are secondary noise, not this Work's
  root cause or scope.
- Work25 is limited to a tested, bounded condition-based startup wait and the
  existing project-control/changelog evidence. No dependency, API, port,
  version, signing, product-data, Ready, merge, Tag, or Release change is allowed.
- TDD mutation evidence reproduces the exact old failure when the new helper's
  default is temporarily set back to `3.0s`, then passes with a delayed 4-second
  readiness under the restored 30-second bound. Disconnecting `main.py` from
  the helper also reproduces the exact 3-second failure. Related local tests
  pass 32/32;
  Python compile, AI governance, explicit error/dead-thread/timeout boundaries,
  and diff checks pass. The existing cloud environment lacks locked backend
  dependencies and flake8, so exact-Head CI remains authoritative for those gates.
- Draft PR #25 was created from the exact nine-file tree with initial remote
  implementation Head `65fddad2…`. One status-only synchronization commit is
  required so the final Head records the PR identity before authoritative CI.

## Historical current entry | Work24 / Windows runtime integrity guard

- Work23 已以 Head `190c3bd2…`、CI Run `30990684208` 8/8 成功后合并，`main`、
  `v3.29.3` 与本 Work 固定 Base 均为 `e59c9d9…`。旧台账的 Open Draft 与待重测
  状态已按 GitHub 事实纠正；Work23 历史证据不回退。
- Windows `afterSign` 阶段为最终桌面端和冻结后端生成闭合两项 SHA-256 身份清单。
  打包版 Electron 在任何后端 `spawn`、安全凭据迁移或 `.env` 清理前，校验自身路径、
  两项固定路径、普通文件类型、大小与摘要；失败时不执行后端或分析任务。
- Python 后端在参数解析后、日志/配置/数据库初始化前验证 Desktop 模式只能是完整的
  本机回环 `serve-only` 合同。缺参或混入大盘复盘、定时、个股、回测等模式时只输出
  一个有界原因码并以 `2` 退出；打包版 Desktop 固定监听 `127.0.0.1`。
- Desktop 只保留有界、脱敏的 stderr 尾部用于合同分类；加载页改为中文。最终 Windows
  ZIP 在 CI 和正式 Release 流程中复用同一身份校验后，才运行冻结后端探针。
- 当前本地专项证据：Desktop Node `99/99`；Python 启动合同 `24/24`；打包与最终
  ZIP 合同 `10/10`；Python 编译、AI 治理、语法门与 diff 检查通过。云端工作器因
  网络策略无法补齐完整后端聚合所缺的锁定依赖，因此未把局部环境冒充完整后端门；
  Draft PR 固定 Head CI 是权威结果。
- 未读取或上传受影响 Windows 电脑的 EXE、数据库、`.env`、备份、日志或安全证据；
  未编码特定病毒名称、固定代理大小或机器路径。未 Ready、合并、Tag、Release 或改版本。

## 2026-08-04 Work23 / PR #23 Windows strict-acceptance failure repairs

- Work22 remains `FAIL`, bound to evidence-report SHA-256
  `30AC65C81E3F86E4CADBAEC9D2DBA95B432BA4DF8DBE81F12015857B9E5E39BE`.
  Work23 does not lower its gates or revise that decision.
- The official uninstaller now drains the Electron-owned backend before final
  quit and invokes a bundled exact-path process helper. Windows verification
  runs the official uninstaller once and requires the installed app/backend
  process tree to reach zero without a retry or broad name-based termination.
- Candidate identity is normalized to `3.29.3` across Desktop/Web package
  metadata, backend defaults, build information, installer manifest, and the
  Windows file/product-version checks.
- Evidence shows `fundamental_snapshot` contains formal non-rebuildable
  snapshot data, so it is included in the complete backup. `stock_daily` is a
  rebuildable market-data cache with no user data; it remains excluded under an
  exact manifest contract, is cleared on restore, and rebuilds on demand via
  `get_daily_history`.
- Authenticode handling is read-only. The verifier records installer/app status
  and supports a credential-free `RequireValidSignature` policy gate, but no
  certificate, private key, signing purchase, or CI secret was accessed. A real
  signing identity remains a separate authorization gate.
- Related backend suites, Desktop `83/83`, Windows packaging contracts `26/26`,
  and Web `1076 passed / 2 skipped` plus lint/build pass locally. The offline
  backend aggregate passed `5327` tests plus `499` subtests when the sandbox-
  blocked crash-recovery process-kill file was omitted; exact remote CI remains
  authoritative for the complete gate.
- PR #23 remains Open Draft. Remote fixed Head, complete Actions evidence, and
  the Windows candidate name/size/SHA-256 are pending the next authorized push.
  No Work22 real database, cold backup, export, or restore checkpoint was used.
- The first published Work23 Head `d0e1bdf2…` / Run `30948969458` exposed one
  deterministic Web test wait race; the test-only wait fix passed on the next
  Head. Head `8e08d58e…` / Run `30949323920` and Head `ca2415b8…` / Run
  `30952197181` each finished 7/8 Jobs, with Windows alone failing after the
  official uninstaller returned `0` but left the running application alive.
- The new local rework removes all NSIS command-line ownership parameters. A
  packaged closed manifest declares the exact desktop/backend relative paths;
  the helper derives the install root from its own resource location, while
  NSIS can fall back from `$INSTDIR` to the official uninstaller directory.
  Sanitized JSON evidence records helper execution, initial owned count, and
  final zero count. A Windows runtime contract starts two exact owned copies
  plus an external same-name control process and requires only the owned pair
  to exit.
- Fresh recovery verification passed Python packaging contracts `26/26`,
  Desktop `83/83`, AI governance, and diff formatting. Run `30975730060` now
  supplies the Windows runtime-helper PASS; the one-shot installed lifecycle
  remains pending the next exact-Head Actions run. No failed remote Head is a
  candidate PASS.
- Head `0eee6a7c…` / Run `30975730060` proved the Windows runtime helper
  contract: two exact owned process paths exited and the external same-name
  control survived. The Windows candidate build itself failed because NSIS
  treats warning 6012 as fatal and the required-uninstall macro left its final
  label without an explicit jump. The candidate step also masked the child
  `build-all.ps1` exit code until the lifecycle could not find the installer.
  Local RED/GREEN contracts now require the explicit label jump and immediate
  `$LASTEXITCODE` failure; a next exact-Head CI is required.
- Head `976db882…` / Run `30977516983` passed that NSIS/fail-fast boundary,
  rebuilt the candidate, and again passed the synthetic helper contract. The
  installed lifecycle passed install/start/exit/restart, then one official
  uninstaller returned `0`; helper evidence was `FAIL` with initial owned count
  `5`, graceful/forced counts `0`, and final count `-1`. This proves the initial
  CIM exact-path lookup succeeded while the later `Get-Process.Path` recheck
  prevented every action on real Electron/backend processes. Diagnostic artifact
  `8919511035` is Head/Run-bound with SHA-256
  `1DE5397EBCD6B07314685E2C0C709FA7BFC75A84BC190701ABD2CBE9270CA1DC`.
  Local RED/GREEN now requires one CIM PID/path identity source before both
  graceful and forced actions; the next exact-Head installed lifecycle remains
  authoritative.
- Head `c9aca280…` / Run `30988154439` passed the full candidate build, the
  synthetic exact-path helper contract, install/start/exit/restart, and one
  official uninstall returned `0`. The diagnostic then proved the install root
  was removed, app/backend processes were gone, and the final helper evidence
  was `PASS` with zero remaining processes. CI still failed because the helper
  ran twice: electron-builder's standard `un.checkAppRunning` performed the
  live cleanup, then the extra `customUnInstall` call overwrote evidence with a
  no-op `initial=0` run. Diagnostic artifact `8923770478` is Head/Run-bound with
  SHA-256 `686692F0EB7B4D96084DE30143C11A29C6E6E7406A105B07A7C639732FDC73F4`.
  Local RED/GREEN now keeps one standard uninstall entry, required for uninstall
  builds and optional for install/upgrade builds; next exact-Head CI remains
  authoritative.

## 2026-08-04 Work20 / complete backup and persisted period reports

- Work20 is based on the locked `v3.29.2` main commit
  `41fd6a6c76c3e3b56211ef5fb4483d869122b568`. Work18, Work19, and Work19-A
  history remains locked and is not revised by this append-only checkpoint.
- The implementation adds a strict complete-data backup format, explicit
  preview/confirm restore, a pre-replacement recovery artifact, coordinated
  SQLite/config rollback, and persisted/reloadable period reports.
- Complete backup is distinct from the existing configuration-only and
  portfolio-event-only tools. Credentials, cookies, tokens, vault ciphertext,
  drafts, logs, caches, and runtime paths remain excluded. Fund is recorded as
  `not_applicable`.
- Local verification is complete at evidence commit
  `42e8f75d435b9d90ad5764f538cb20e9e48c1e9f`. The Draft PR, remote fixed
  Head, Actions Run, and job results are pending the controller and must not be
  invented or backfilled from a different Head.
- Judge remains `DRAFT_HOLD`. Work20 has not been pushed, made Ready, merged,
  tagged, or released by this local phase.

## 2026-08-03 Work16 / Windows 冻结筹码依赖收口

- 用户授权以 `main@568e26adf0e6393a7a0da1be57369535735cd05a` 为固定 Base，先只读
  定位冻结候选缺少 `py_mini_racer/mini_racer.dll` 的根因，再建立独立 Draft PR。
- 根因证据已确认：Windows 固定主线 CI 安装 `akshare 1.18.81` 时已解析并安装
  `mini-racer 0.14.1`，其 wheel 已包含 `py_mini_racer/mini_racer.dll` 与
  `icudtl.dat`；现有 PyInstaller 命令没有收集该包的二进制/数据，现有 import 与
  HTTP 健康探针也没有实例化 V8，因此冻结健康通过但真实筹码链仍会缺 DLL。
- 最小设计只收集已安装的 `py_mini_racer` 运行资产，构建后检查 DLL/ICU 存在，
  通过离线 JavaScript 求值证明可加载，并在最终解压便携 ZIP 上重复同一探针。
  `requirements.txt` 不变，不新增或升级任何依赖。
- 独立 Draft PR [#22](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/pull/22)
  已从固定 Base 建立并保持 Draft。新增 3 个合同测试先以预期缺口 RED，再由最小实现
  推进至 `tests.test_desktop_packaging_assets` 5/5 GREEN；Python 编译、AI 资产检查和
  diff 格式检查均通过。
- 固定证据 Head `016e3408795b4adaf1eab25210681be66b7e8ff8` 的 CI Run
  [`30831393819`](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/actions/runs/30831393819)
  已 success：7 个 Job 成功、Web 路径无关 skipped。Windows Job `91746056804`
  先后两次确认 MiniRacer 可用与 DLL/ICU 已打包，并在直接构建、`build-all` 重建和
  最终解压 ZIP 共输出 3 次筹码运行时探针成功标记；对应 HTTP smoke 也 3 次通过。
- 独立只读复审无 Critical/Important。Work16 最终裁决为 `PASS — DRAFT_HOLD`；
  PR #22 保持 Draft，后续 Ready、合并或发布均须新的单独授权。
- Work15 已在本 Work 启动前完成：PR #21 最终固定 Head CI Run `30825436318`
  成功并已合并，当前 `main` 为 `568e26ad…`。本 Work 不回退其历史。
- 当前只允许独立分支、正常 Commit、Draft PR、相关回归与固定 Head 完整 CI；禁止
  Ready、合并、Tag、Release、新闻、签名、真实凭据/数据及新增 Windows 真机动作。

## 2026-08-03 Work15 / PR #20/#21 主线收口

- PR #20 固定 Head `e11946f528c9cb64beeec8b626ada457c02b0034` 已按授权转为
  Ready，并通过 merge commit `25de369f8e12438a1ec1f3511c68256c471243e4` 合入 `main`。
- 新 `main` 的 CI Run
  [`30822458701`](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/actions/runs/30822458701)
  已 `8/8` success：治理、后端、Docker、Web、Desktop、Windows 与 macOS 均通过；
  Auto Tag Run `30822458692` 按规则 skipped，没有创建或移动 Tag。
- PR #21 的 Work14 7 文件证据与 PR #20 的 5 文件产品改动没有路径重叠。新 `main`
  已通过双父 merge commit `25313cf0f23f0f4ab4922ea983bcd05b3577e23e` 非破坏同步到
  `agent/pp02-work13-status-reconciliation`；没有 rebase、force-push 或历史丢失。
- 本次只把 Work14 最终裁决、证据 CI 与 PR #20 合并事实写回原 7 个台账/路线文件。
  PR #21 最终 Head 的 Run ID 只写入 PR 元数据，避免为记录 CI 再制造新 Head。
- Work15 已授权 PR #21 在最终固定 Head CI 通过后转 Ready 并合并。Tag、Release、
  `mini_racer`、新闻、签名和新增 Windows 真机动作仍明确禁止。
- PR #21 后续最终固定 Head CI Run `30825436318` 成功，并已合并为
  `main@568e26adf0e6393a7a0da1be57369535735cd05a`；Work15 最终裁决为
  `PASS — MAINLINE_CLOSED`。其余已知降级项由后续独立 Work 处理。

## 2026-08-03 Work14 / PR #20 固定 Head Windows 未发布候选验收

- 验收源码当时精确固定为 Draft PR #20 Head
  `e11946f528c9cb64beeec8b626ada457c02b0034`，Base 为
  `main@f5c7f43359ec81e27395d9bb236ec1cab0f6dcc2`。构建信息内 revision 与该 Head
  一致；候选仅用于本机验收，没有安装、Tag 或 Release。
- Windows 未发布安装器版本 `3.29.1`，大小 `217,003,814` bytes，SHA-256
  `DAD0CE0CCF8FC34F7318CD4E4F0CC37347C68A1A03E98D0CA7B048E393B18B33`，Authenticode 为 `NotSigned`。冻结后端动态端口健康探针通过；
  相关 Python 回归 `130 passed`，Desktop Node 22 回归 `82/82`。
- 受控 API 单独提交 `600519`，task/query/trace 均为 `1c4ae649232d40eaae7dcb6bb1b6981f`。
  任务 `completed/100`，正式历史 ID `2`，`model_used=codex_cli`，评分 `59`，
  操作建议“观望”。诊断 `history=ok`，运行流 `llm_analysis=success` 与
  `history_save=success`。
- 候选后端停机重启后，任务状态从数据库恢复，history ID/query ID 和运行流仍可读；
  恢复 Work12 原安装后，其端口 8000 健康接口也能读取同一条历史。同期大盘历史
  1 条；`week_to_date` 周期聚合读取 2 条来源（1 个股、1 个大盘）。
- 裁决为 `PASS_WITH_DEGRADATIONS`，不是全量 PASS：新闻搜索为 0 条，筹码数据因冻结
  产物缺少 `py_mini_racer/mini_racer.dll` 而失败，整体诊断为 `degraded`；
  安装器未签名，本 Work 也未执行候选安装生命周期。
- Work12 配置、数据库和日志均未被清理或用候选覆盖。现场 `.env` 在受控单股重跑前
  已发生外部变更，元数据变为 50,268 bytes（来源未判定）；Work14 保留该现场版本，没有用 50,288
  bytes 的旧临时副本回写。临时副本和两个精确 Junction 已删除，Work12 原应用已恢复
  且 `health=ok`。
- Work14 证据 Head `da2290597e880c4c4a4c1c04e5cc548aa5542ea9` 的 CI Run
  [`30821021196`](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/actions/runs/30821021196)
  已 success：4 个适用 Job 成功，4 个路径无关 Job正常 skipped。最终裁决为
  `PASS_WITH_DEGRADATIONS — DRAFT_HOLD`。
- Work14 结束时 Ready、合并、`main`、Tag 与 Release 均未授权；该历史边界已由
  Work15 的精确收口授权替代。PR #20 后续合并事实见上方 Work15 记录。


## 2026-08-03 Work13 / 方案 A 双 Draft PR 修复

- 用户授权 Work13 采用方案 A：先只读核验证据，再从同一
  `main@f5c7f43359ec81e27395d9bb236ec1cab0f6dcc2` 建立两个相互独立的 Draft PR。
- 产品 Draft PR [#20](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/pull/20)
  修复个股分析完成契约。两个流水线原本都记录正式历史落库结果，但共享的
  `AnalysisService` 即使看到 `history.status=failed` 仍返回成功响应，使异步任务发布
  完成而历史列表无记录。
- 最小修复只在共享服务返回边界拦截明确的历史失败，保留诊断消息为 `last_error`；
  历史成功、缺少旧诊断、CLI-only 流程、行情复盘和周期报告不变。TDD 先复现
  `1 failed, 1 passed`，修复后专项 `2/2`、Python compile、flake8 fatal selectors、
  AI asset check 与 `git diff --check` 通过。
- 本状态 Draft PR 只校正 Work10–Work13 台账与路线事实，不含产品代码。Work13 当时
  要求两份 PR 保持 Draft；该历史边界后由 Work15 的精确 Ready/合并授权替代。

## 2026-08-03 Work10–Work12 / 发布与真机证据收口

- PR #19 已合并为 `main@f5c7f43359ec81e27395d9bb236ec1cab0f6dcc2`。手动 Desktop
  Release Run [`30786838156`](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/actions/runs/30786838156)
  的 preflight、Windows、两项 macOS 和 publish-release 共 `5/5` 成功。
- Annotated Tag `v3.29.1` 的 Tag object 为 `cf6e34b6…`，剥离后仍精确指向固定产品
  Commit `3e1311ee…`。正式 Release 非 Draft、非 Prerelease，共 7 个资产。
- Work11 从正式 Release 下载 Windows 安装器，大小 `218,044,195` bytes、SHA-256
  `4efc4bb2b7e3f54c6c649617eac2b301d5bb481ae8e20a77540e3746e6c56060` 与 Release
  元数据一致；签名状态为 `NotSigned`。安装版本 `3.29.1.0`、内置后端健康和清洁卸载
  通过；仅验收临时目录保留安装器证据副本，裁决 `PASSED_WITH_RESIDUALS`。
- Work12 的安装、后端健康、Codex CLI 配置及重启后持久化、行情复盘正式历史和周期
  报告通过；手动 `600519` 个股分析虽提交任务，却没有形成正式个股历史。因此总体
  裁决为 `FAILED_STOCK_ANALYSIS_HISTORY_MISSING`，直接进入 Work13 修复而不回退已通过项。

## 2026-08-02 Work10-B / Windows release artifact cleanup race（historical pre-merge snapshot）

> 本节保留 PR #19 合并前快照；其后合并、发布与真机结果以本文件顶部 Work10–Work13
> 收口记录为准。

- PR #18 is merged as `main@91e174d30b3d0f2533b0db5df0245bf49778234f`. Manual Desktop
  Release Run `30763628302` used fixed product Commit
  `3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65` and passed preflight, both macOS builds, the
  Windows package build and the complete installed Windows lifecycle.
- The Windows final portable ZIP smoke also passed. Its immediate one-shot cleanup then failed on
  the briefly loaded `aiohttp/_websocket/mask.cp312-win_amd64.pyd` with `Access denied`; Windows
  Job `91538466726` failed and `publish-release` was skipped. No v3.29.1 Tag or Release was created.
- The user authorized a minimal Draft PR #19 fix restricted to the Desktop Release workflow,
  regression tests and required ledgers. Product code, Tag and Release operations are forbidden.
- TDD RED proved the old workflow had no bounded retry contract. GREEN adds the existing repository
  pattern of at most 15 delete attempts with one-second waits after the existing runner-owned path
  validation; exhaustion still fails closed. Local related contracts pass `25/25`.
- Draft PR #19 is open on `agent/pp02-work10-release-cleanup`; implementation Head
  `84bcbb060aaa78ebe5d5413cd8a16a7a1eac5512` changes only the release workflow and two tests.
  Final validated Head `05e7a5dac1064b644cb5a01fa9300a4af109ecdb` completed Run `30765409298`
  with all seven applicable Jobs successful and Web Gate correctly path-skipped. Windows final ZIP,
  installer contracts, installed lifecycle, diagnostics, credential scan and candidate upload all
  passed. PR #19 remains Draft and stops at explicit merge authorization.

## 2026-08-02 Work10-A / cloud release entry（historical）

- PR #17 has been merged as `main@3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65`; post-merge
  Run `30747187504` completed all eight jobs successfully. This merge commit is the fixed product
  commit for v3.29.1 even though the release-workflow repair will later move `main`.
- v3.29.1 Tag and Release do not exist. v3.29.0 remains immutable at its original annotated Tag,
  commit and Release.
- Work10-A modifies only the existing Desktop Release workflow, deterministic contracts and
  ledgers. Manual dispatch now accepts a SemVer tag, full 40-character product commit and annotated
  tag message; a read-only preflight validates exact Commit object type, main ancestry, direct Tag
  object type/target/name and Release absence.
- Windows and macOS build the preflight's fixed product commit. Only the final publish job has
  `contents: write`; after every build succeeds it creates or safely reuses the same annotated Tag,
  verifies both the remote Tag object's direct target and peeled commit, and creates the Release in
  the same Workflow Run.
- Local contracts passed and Draft PR #18 fixed implementation Head `e1a619c58670…` completed Run
  `30750806894`: all seven applicable jobs succeeded and Web Gate was correctly path-skipped. PR
  #18 was later merged as `main@91e174d…`; the subsequent release result is recorded in Work10-B.

## 2026-08-02 Work9 / formal takeover

- User formally authorized `WORK-009｜PR #17 诊断证据链修复与 Windows 安装闭环` to
  continue the existing Draft PR #17 without restarting the route or changing the approved
  assisted current-user installer design.
- GitHub and a clean branch checkout were rechecked at takeover. PR #17 remains Open/Draft on
  `agent/pp02-work8-r7-installer-fix`; the current full Head is
  `9cb9a70e9176711096adf12ba5674c56d6f314d2`. No newer branch commit was found.
- Work8 is closed as `COMPLETED_WITH_BLOCKER`. Its last evidence remains diagnostic Head
  `eae4b46501c9a183dda20d2975121987e676943b` and Run `30742085965`: seven jobs passed,
  the Windows verifier contract failed, and no Windows diagnostic artifact was retained.
- The Work8 execution lock is released and transferred to `HELD_BY_WORK_009`. Work9 is authorized
  for in-scope tests, commits, pushes and fixed-Head CI on the existing Draft PR. Ready, merge,
  `main`, Tag, Release, real data/credentials and Windows real-machine actions remain hard gates.
- Required order is evidence-chain RED/GREEN first, final ZIP verification second, one fixed-Head
  diagnostic run third, and only then an evidence-backed backend root-cause fix. If the artifact is
  still unavailable, stop at `ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT` without guessing.

## 2026-08-02 Work9 / diagnostic evidence and minimal root-cause fix

- The cleanup-independent diagnostic change was pushed at fixed Head
  `b4684f0be8a818b5b29688933e2a738663e1a638`. Run `30744115030` finished with seven
  successful non-Windows jobs and one failed Windows lifecycle job. The Windows PowerShell 5.1
  diagnostic contract passed before the installed lifecycle ran.
- Final candidate verification passed before installation: the final ZIP was extracted, its
  `pp02-portable-release.json.managedFiles` contained exactly one
  `resources/backend/stock_analysis/_internal/fake_useragent/data/browsers.jsonl`, the file was
  present, and the frozen backend started from the final extracted ZIP.
- The installer returned exit code 0 and its install/registration checks passed. The installed
  desktop launched the bundled backend but never opened port 8000. The Head/Run-bound
  `if: always()` upload succeeded as artifact `8832664000` (52,836 bytes, SHA-256
  `6fa6366761d608572c04b401e69caa764483c7bab3c5bc61ecc96e958989ea65`).
- The artifact contains stage/process timing, exit status, sanitized desktop/backend stderr,
  executable and working-directory evidence, port/process state, Windows event status, installed
  package inventory and collector status. It contains no raw stderr, credential/token prefix,
  complete environment dump, database, or user-data file.
- Direct error, reproduced by both the Electron child and an independent backend probe:
  NLTK 3.10.1 `pyi_rth_nltk.py` imports `nltk.internals`, whose `xml` import is rejected with
  `ImportError: Blocked import of xml from current working directory for security reasons`.
- Confirmed boundary/root cause: installed Electron starts the packaged backend with the install
  root as CWD while the PyInstaller bundle is inside that root under `resources/backend/...`.
  NLTK's import-security finder therefore classifies bundled stdlib `xml` as CWD content. The
  build/final-ZIP smoke uses an unrelated temporary CWD and does not reproduce this topology.
- TDD RED reproduced the installed ancestry in the Desktop launcher test. The single product fix
  changes packaged-backend CWD to the database parent directory (created before spawn), keeping it
  outside bundle ancestry while retaining `PYTHONSAFEPATH=1`; no NLTK guard, dependency or
  packaging file was disabled or upgraded. The verifier also has a RED/GREEN gate for first exit,
  fresh restart readiness, second exit and uninstall ordering.
- Local GREEN: Desktop `82/82`; Windows packaging/diagnostic/final-ZIP targets `29/29`; workflow
  YAML, AI assets and `git diff --check` pass. Fixed-Head full CI remains required before any merge
  request.

## 2026-08-02 Work9 / fixed-Head Windows closure

- Final implementation Head `db02221b92e210925044c5af5a4aacd2f08fcb4f` completed Run
  `30745575186` with all eight jobs successful: Change Detection, AI governance, Web, Backend,
  Desktop tests, Docker, macOS package and Windows package/lifecycle.
- Windows logs prove the ordered lifecycle on that exact Head: installer exit 0; install and
  registration pass; first installed startup pass; first process-tree exit pass; fresh restart
  readiness pass; second exit pass; uninstaller exit 0; uninstall cleanup pass.
- The final ZIP gate again passed before installation, including exact managed-file membership and
  existence for `fake_useragent/data/browsers.jsonl` plus frozen-backend startup from the extracted
  final ZIP.
- Success-path diagnostics were uploaded with `if: always()` as artifact `8833102391`, bound to the
  full Head and Run ID. Its ZIP SHA-256 is
  `5c0f19466e01c399dc20008d5589290d210e4f8e4b612ab4ea7319e50e6b90b8`; its summary is
  `WINDOWS_INSTALLER_DIAGNOSTIC=NOT_REQUIRED_VALIDATION_PASS`, and its stage report records every
  lifecycle stage through uninstall cleanup as PASS. Security review found no credential file,
  token prefix, unredacted sensitive assignment, complete environment dump, database or user data.
- PR #17 remains Open/Draft and unmerged. No Tag or Release exists for v3.29.1, and Windows real
  machine acceptance has not been run. Work9 is stopped at the explicit merge-authorization gate.

## 2026-08-02 Work8 / corrective diagnostic run blocked on evidence preservation

- The corrective audit rechecked GitHub before making changes: Draft PR #17 was at
  `eec9a44ce707daf149b3f571761fc27385772e85`, and Run `30717606318` had seven
  successful jobs plus one failed Windows lifecycle job. The installer completed, but the
  installed application never opened backend port `127.0.0.1:8000`; no diagnostic artifact was
  retained.
- A diagnostics-only commit produced fixed Head
  `eae4b46501c9a183dda20d2975121987e676943b`. It added redacted backend lifecycle capture,
  process/port state, relevant Windows events, an installed-file manifest, cleanup-independent
  evidence storage and an `if: always()` artifact upload whose name binds the full Head and Run ID.
  It did not change backend logic, dependencies or packaging structure.
- Local diagnostic checks passed: Desktop tests `82/82`, packaging diagnostic contracts `15/15`,
  both workflow YAML files, AI asset checks and `git diff --check`.
- The one fixed-Head diagnostic Run `30742085965` ended with seven successful jobs and one failed
  Windows job. Windows backend freezing and installer/portable candidate construction passed.
  The verifier contract then failed with `Verifier did not preserve diagnostic evidence before
  cleanup`; the installed lifecycle step was skipped. The `if: always()` upload step did execute,
  but failed because the bound diagnostic directory contained no files. The Run contains no
  Windows diagnostic artifact.
- Therefore the installed backend's direct error, component boundary and root cause remain
  unproven. Mandatory verdict: `ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT`. No backend fix, further
  diagnostic patch or additional CI run is authorized from this evidence.
- PR #17 remains Draft. `PR17_MERGE_STATUS=BLOCKED`, `V3_29_1_RELEASE_STATUS=BLOCKED`, and
  `WINDOWS_REAL_MACHINE_ACCEPTANCE=NOT_RUN` for the patch candidate.
- Deferred follow-up remains out of this PR: concentrated Electron/npm security upgrades,
  Dependabot/blocking `npm audit`, all 101 Web test files, blocking Playwright E2E, Windows signing,
  macOS signing/notarization and the final desktop icon.

## 2026-08-01 Work8 / v3.29.0 Windows installer failure and A-design

- Windows native acceptance verified the official installer filename, byte size and SHA-256, then
  reproduced an installer bootstrap crash twice before installation completed. Both Windows Event
  records identified `System.dll` and `0xC0000005`; no install registration, install directory or
  PP02 process remained.
- Final acceptance Judge is `R7_WINDOWS_FIRST_USE_ACCEPTANCE=FAIL`. Startup, empty-data,
  safe-default and restart checks were not executed because installation failed.
- User authorized `Work8｜R7 安装器缺陷修复与 v3.29.1 补丁发布` and selected
  `A｜保留安装向导`.
- Root cause matches upstream electron-builder issue #8536 and merged fix #9564: the 24.x NSIS
  current-user assisted-installer template can race in `System::Store()` on Windows 11.
- Approved design is committed at
  `docs/superpowers/specs/2026-08-01-work8-windows-installer-hotfix-design.md`.
  It pins `electron-builder 26.15.7`, keeps the install-directory wizard and current-user mode,
  and adds real Windows install/start/uninstall gates to PR and Release workflows.
- User approved the design correction that Desktop test, Windows/macOS packaging and Desktop
  Release jobs use Node 22 because `@electron/rebuild 4.x` requires Node `>=22.12`; the standalone
  Web gate remains on Node 20.
- Implementation commits pin the repaired builder, explicitly declare the existing test-only
  `archiver 5.3.2` dependency, and add the shared fail-closed Windows verifier plus fixture.
- Local evidence: Desktop Node 22 tests `81/81`; installer and packaging contracts `23/23`;
  workflow YAML parsing and `git diff --check` pass. Windows lifecycle and macOS packaging remain
  pending the PR fixed-Head Actions run.
- Current authorization covers this branch, normal commits, a Draft PR, CI and in-scope fixes.
  Ready, merge, main write, `v3.29.1` tag/Release and real data remain separate authorization
  gates. `v3.29.0` is immutable and must not be moved or rebuilt.


## 2026-08-01 Work7 / R7 最终发布与台账收口

- PR #14 已合并为发布提交
  `49759dbd032f577d32e8e0f6670298f700e0f272`；该提交的 `main` push CI
  全部 8 个适用 Job 成功。
- annotated Tag `v3.29.0` 精确指向上述已验证发布提交；GitHub Release
  非 Draft、非 Prerelease，Desktop 与 Docker 正式发布工作流成功。
- 正式 Release 含 Windows 安装版、Windows 免安装 ZIP 与 SHA-256、macOS
  arm64/x64 DMG 等 7 个资产；未使用真实数据或真实凭据。
- PR #15 已补充三语言项目来源声明并修正当前仓库链接，明确本项目基于
  `ZhuLinsen/daily_stock_analysis@v3.28.0` 复制后进行二次开发、非上游官方版本；
  原 MIT License 保持不变，Release 正文也已加入同款声明。
- PR #15 已合并为
  `main@b4a0ec11da19b5552ce87dde1ece716f61fd5174`；合并后 Run
  `30697946093` 的 8 个 Job 全部 success。Tag 仍保持在发布提交
  `49759dbd…`，没有因发布后文档合并而移动。
- Judge：`PASS — v3.29.0 RELEASED — WORK7 COMPLETED`。Work7 施工权已释放，
  当前无 Active Work；任何新功能、真实数据、Tag、Release、Ready、合并或
  `main` 写入都必须由后续新 Work 单独授权。


## 2026-08-01 Work7 / R7 主线合并与 CI 阻塞

- PR #12 已以固定 Head `a220e9e146e14722561bc084ec4e5306b30d36c7` 合并，合并
  Commit `ad5588fb5aa12f3424596ada2a411261e8b74916`。
- PR #13 改以 `main` 为 Base 后，最终 Head
  `263578266ab4cd604a1dcde701621139e66ea193` 的 Run `30693442671` 通过；已合并
  为 `main@6650f9c30f394a1ba6b7e7fd99de67d5c11488ab`。
- 该 `main` 的 push CI Run `30693665810` 未过：`web-gate` 暴露两个账户
  选项未渲染就交互的测试竞态；macOS 冻结后端因 NLTK 导入安全检查将
  位于当前可执行目录下的自带 `xml` 误判为 CWD 注入而失败。
- 修复分支 `agent/pp02-r7-main-web-ci-stabilization` 只增强目标测试就绪等待，
  并把冻结后端的 CI/正式 Desktop 工作目录切到独立运行数据目录，同时
  设置 `PYTHONSAFEPATH=1`；不禁用 NLTK 安全检查。
- Draft PR #14 已创建；必须以本状态收口后的最终固定 Head 验证 CI。
- `v3.29.0` Tag/Release 尚未创建，必须等修复 PR 与新 `main` push CI
  全部通过。

## 2026-08-01 Work7 / R7 接管与版本裁决

- 用户正式启动 `Work7｜R7 主线合并与正式发布`，并选择方案 A：目标正式版本
  `v3.29.0`；该授权覆盖 PR #12/#13 的 Ready、固定 Head 合并、新 `main` CI、
  annotated Tag `v3.29.0`、对应 GitHub Release 与正式产物验收。
- 当前远程 `main` 为 `eb32298c8f3cbec2ff400dda37d3267a7181af40`；PR #12
  固定 Head `a220e9e146e14722561bc084ec4e5306b30d36c7`，PR #13 叠加在
  PR #12 上，固定 Head `50dd04ca5a49a6e54de01e2d28ce598f690d9931`。
- PR #12 Run `30661990072` success；PR #13 Run `30691233934` success。
  R7 发布收口会产生一个新的 PR #13 Head，必须重新通过完整 CI 才能合并。
- 合并顺序固定为：先 PR #12 → 把 PR #13 Base 改为 `main` → 验证 PR #13 新
  固定 Head CI → 合并 PR #13 → 验证新 `main` push CI → 创建 annotated Tag
  `v3.29.0` → 验收 Release 工作流与产物。
- 正式数据、真实凭据、其他版本 Tag/Release、范围外功能和强推仍未授权。

## 2026-08-01 Work6 / R6 最终裁决

- Windows 本机确认旧项目目录与指定数据库从未建立，最终裁决为
  `NO_FORMAL_DATA_FOUND`；这不是数据丢失。
- 未搜索 D 盘其他位置，未创建数据库、备份或隔离检出，未读取或迁移真实数据。
- R6 正式数据迁移因此按“无正式数据可迁移”跳过；R6-A 安全盘点工具作为未来显式
  单文件检查能力保留，不得据此声称已盘点某个真实数据库。

## 2026-08-01 Work5 / R6-A 最终收口

- Draft PR #13 固定 Head `50dd04ca5a49a6e54de01e2d28ce598f690d9931` 的
  CI Run `30691233934` 全部适用 Job success；Work5 Judge 为
  `CLOUD_TOOL_IMPLEMENTATION_PASS — WINDOWS_REAL_INVENTORY_NOT_RUN`。
- Work5 已释放施工权；其旧授权边界不覆盖 Work7，但 Work7 的新精确授权已单独记录。

## 2026-08-01 Work5 / R6-A 接管

- 用户选择 A 后确认“采用建议，云端开发盘点工具”，并最终批准“按这个设计做”。
- Work5 从 Work4 Draft PR #12 固定 Head
  `a220e9e146e14722561bc084ec4e5306b30d36c7` 建立独立分支
  `agent/pp02-work5-r6-inventory-tool`；初始只含已批准设计。
- 本 Work 只在云端开发、用空库和人工假 SQLite 测试；不接触 Windows 真实数据库。
- 允许范围内正常 Commit、Push、一个 Draft PR、CI 和范围内修复；Draft PR 初始以
  Work4 分支为 Base，只显示 Work5 增量。
- Windows 真实盘点、正式迁移、Ready、合并、`main`、Tag、Release 和 R7 均需后续
  精确授权；云端 CI 不得冒充 Windows 真实盘点。

## 2026-08-01 Work5 / R6-A 云端实现与本地验证证据

- TDD 服务 RED：18 项新契约因实现模块不存在而失败；CLI RED：7 项新契约因脚本
  不存在而失败，既有通过项未被改写。
- 已新增标准库安全核心 `src/services/formal_data_inventory_service.py` 与 Windows 薄
  CLI `scripts/pp02_formal_data_inventory.py`；只接受人工指定文件，不含扫描或迁移入口。
- 独立审查发现并已修复 3 项 Important：备份期间回滚日志竞态、CLI 无效参数路径
  回显、未验证输出清理失败被吞掉；同时修正检查副本失败时的完整性状态。
- 审查修复后 R6-A 专项 `31 passed`；R6-A、R4 迁移演练和组合备份联合回归
  `50 passed, 4 warnings`。
- 最终代码完整 CI 等效后端门：`5070 passed, 1 skipped, 4 deselected,
  48 warnings, 499 subtests passed`；语法、严重 Flake8、确定性检查、AI 资产和
  差异格式全部通过；独立复核结论为 APPROVE，无剩余发现。
- 第一轮临时测试环境缺少 AkShare、拼音、Jinja2、飞书 SDK、OpenAI 和 Uvicorn 等
  正式依赖，补齐后原失败文件 `511` 项仅剩两项明确缺包，再补齐后归零；未修改无关
  业务代码掩盖环境问题。
- Windows 真实数据库未读取、未备份、未盘点；当前只完成云端工具实现和人工假库
  验证。Draft PR #13 已创建并保持 Draft，正在等待最终固定 Head CI；这不是正式
  数据操作授权。

## 已验证基线

- 官方底座：`v3.28.0` /
  `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c`。
- Draft PR：`#3`，分支 `agent/pp02-v3.28.0-cloud-rebuild`，保持 Draft。
- R0 最终 Head `1327e402ac9d88e711ca4ef8de174118f427ad0e` 的 GitHub Actions
  Run `30221540882` 为 7/7 success。
- 远程 `main` 未因 R1/R2 改动。

## R1/R2 当前裁决

- R1：需求、保留/调整/不迁移分类和冲突处理已确认。
- PP02 保持单用户；旧用户档案、切换、隔离和用户级备份全部不迁移。
- 官方账户/组合事件账本是持仓唯一事实源。
- R2：迁移拆为 R3.1–R3.7；R3 已全部完成并通过 PR #11 合入 `main`。
- R4：方案 A 已完成；只用空库和人工假数据完成兼容、迁移、排除和回滚演练。
- R5：Work2 已通过 PR #9 完成 Windows 真机验收并进入 `main`。

## 当前保护边界

- Work7 / R7 已完成并释放施工权；当前不存在 Active Work、活动分支或活动 PR。
- `v3.29.0` Tag 固定在已发布提交 `49759dbd…`；发布后文档主线为
  `b4a0ec11…`，不得移动或重打该 Tag。
- 后续目标必须新建 Work，并重新确认范围、Base、分支、PR 与授权。
- 不接触真实 `.env`、Token、API Key、Webhook、账号或真实数据库；Work6
  `NO_FORMAL_DATA_FOUND` 的历史裁决继续有效。
- PP02 只包含股票业务；基金、多用户和旧平行持仓表不得迁入。
- 仓库为 Public；代码、PR、分支和 Actions 历史公开，但真实数据、密钥、备份、
  一次性验收材料和临时日志仍不得进入仓库。

## 2026-07-31 Work3 / R3.7 最终收口

- PR #11 最终 Head `173b3d3bd358b281c4dd86057b5162605bd277b0` 的 Run
  `30643230898` 为 8/8 success；Windows Job `91198401578` 与固定 Head 一致。
- PR #11 已合并；当前远程 `main` Head 为
  `eb32298c8f3cbec2ff400dda37d3267a7181af40`。R3 全部完成，Work3 已关闭。
- 该完成事实不授权 R4 之后的真实数据、Ready、合并、Tag 或 Release。

## 2026-07-31 Work4 / R4 接管

- 当前唯一 Active Work：`WORK-004`；Base `main@eb32298…`；分支
  `agent/pp02-work4-r4-database-rehearsal`。
- 用户选择方案 A，并批准自动接力规则。旧窗口角色锁已由
  `PP02-WORK-HANDOFF-002` 替代；聊天显示名称保持原样。
- PR #7/#8 是已被 PR #9 替代的历史 Draft，获准关闭但保留分支和全部历史。
- R4 只使用动态生成的空库和人工假数据；Judge 上限为 `DRAFT_HOLD`。

## 2026-07-31 Work4 / R4 本地实现证据

- 历史 Draft PR #7/#8 已添加 superseded 说明并关闭；远程分支和全部历史保留。
- 当前 Draft PR：`#12`；分支 `agent/pp02-work4-r4-database-rehearsal`；保持 Draft。
- RED：新增 8 项服务契约后全部因实现模块缺失而失败；未混入既有回归失败。
- GREEN：R4 专项 `13 passed`；服务、CLI、意外异常脱敏和原子报告语法检查通过；
  存储/备份/R4 联合回归 `43 passed, 17 warnings`，警告与记录基线一致。
- 全新系统临时目录端到端演练返回 `R4_DATABASE_MIGRATION_REHEARSAL=PASS`；四类事件
  各迁移 1 条，源 SHA 不变、组合摘要一致、过期预览被拒绝且目标不变；真实数据和
  备份正文均未使用或落盘。
- CI 等效 UTC 环境完整离线后端门：`5040 passed, 4 deselected, 47 warnings,
  499 subtests passed`；Flake8 严重错误为 0，AI 资产、语法、确定性检查和差异格式均通过。
- Base-to-Head 自审只包含批准的规则、状态、设计、服务、CLI、测试和文档；未跟踪
  `.db`、`.env`、备份、报告、日志、依赖或 Workflow 变化，报告结构不含行值。
- 最终实现候选 Head `f1b433a7a97ed43a7048aeb4239b76357003083b`，Tree
  `cdc54b1d1488358a13c40223a6354c901b8a5001`；CI Run `30660971800` 的
  AI 治理、变更检测、Docker 和后端门全部 success，未改路径的 Desktop/Web/打包
  Job 按规则 skipped。PR #12 保持 Draft。
- Judge：`PASS — WORK4 COMPLETED — DRAFT_HOLD`。施工权已释放；R6 未启动且需要
  新授权，不得读取真实数据库或数据。

## R3.1 实现与验证证据

- 测试先行 RED：Commit `c762825102f22b1352949244c12148b821b80b87`，
  CI Run `30487941321` 的 `desktop-test` 按预期失败；47项旧测试通过，
  2项新 PP02 身份测试因仍指向官方仓库/名称失败。
- 首次 GREEN：Commit `c7e483928a92ed1ed589c68647acb554e3b5ee41`；
  Desktop 49/49 通过，但 macOS 包门暴露旧固定 App 路径。
- 根因修复：Commit `639d2bc8fc605fbe553fb9c16df7137042bb2079`，
  将 macOS 未签名 App 与 DMG 验收路径同步为 PP02 productName。
- 实现 Head CI：Run `30488603501`，8/8 success。
- 收口 Head `1740fa3655b5eed55c7e4ebda81523ca8095e176` 的 Run `30489293885` 为 8/8 success；R3.1 Judge 已完成。
- PR #3 仍为 Draft；Windows 实机、Ready、合并、Release 和真实数据均未执行。


## R3.2 实现与验证证据

- 行为测试 RED：Commit `68dab6a7d54b81f196b642b1352a0a41aa2b8eb5`，
  Run `30491953318` 为 9 个预期失败，覆盖配置、Workflow、CLI、运行时调度、
  Alert Worker、Web/API 分析和市场复盘。
- GREEN 实现：Commit `61939ec76384d5c198aecf98e8b413fe13cfdd85`；
  删除默认 cron，新增 `AUTO_NOTIFICATION_ENABLED=false` 并贯穿全部自动发送入口。
- 集成回归根因修正：Commit `5316b5ea2ececd9aff0ced556e897f0738dad317`；
  将旧的默认发送断言改为默认关闭，并补齐设置页中英文帮助元数据。
- 实现 Head CI：Run `30493475960`，8/8 success；后端
  `4976 passed, 4 deselected`，Web、Docker、Desktop 单测及 Windows/macOS 包门均通过。
- 手动“测试通知”保持独立；关闭总开关时分析、报告持久化和告警记录继续执行，
  仅抑制外部自动发送。
- 收口 Head `e879f0692d2bd330b166df561cd8a90d4542a5ce` 的 Run
  `30494219667` 为 8/8 success；R3.2 Judge 已完成。
- Windows 实机仍为 Deferred；未使用真实通知渠道、凭据、付费服务或真实数据。

## R3.3 实现与验证证据

- RED：Commit `f1ebae02f21a97d97418649c23db8401a8b3fc8f`；补充 Web
  专项测试门的 Commit `93d2a59b8eab77a2d6633898c4cbb5e93fb95d33`。
- RED Run `30513770957`：后端 5 项预期失败、其余 `4976 passed`；
  PortfolioPage 新测试按预期失败，原有 28 项通过。
- GREEN：Commit `311664759a51f8eb8ec700417b20c2e17fa155e8`。
- 实现 Head Run `30514223674`：8/8 success；后端
  `4981 passed, 4 deselected`，PortfolioPage `29/29 passed`。
- 预览只读；确认在原子事务内做过期检查和去重，只追加官方交易事件；
  现金变化由官方重放计算，不直接写 `portfolio_positions`。
- Windows 实机仍为 Deferred；未使用真实持仓、券商账户或真实数据库。
- 收口 Head `d4615cd407ba88ed43f9da129c8c89583358a98a` 的 Run
  `30514843576` 为 8/8 success；R3.3 Judge 已完成。

## R3.4 实现与验证证据

- RED：Commit `15e48e6000bd1a39e7db082e20897052affa558c` 与
  `b6a2cd2f02e2ebc3955bfb6276e1ffd63b3c6eac`；Run `30516073073`
  后端 6 项预期失败、其余 `4981 passed`；PortfolioPage 新增 2 项预期失败，
  原有 29 项通过。
- GREEN 初始 Head `85dbe71a26d175b6c2557900770b3260fea4a419`。
- 私有仓库 Actions 分钟耗尽导致 Run `30516696130` 零 Step 阻塞；公开前审计
  未发现密钥或真实数据，用户授权改为 Public 后标准 Runner 恢复。
- 日期摘要根因修复：Commit `8355d92a81b8f951a8ee7bcb703e89585cb8de5e`；
  明确把 `date/datetime` 规范化为 ISO 标量，未知对象仍拒绝序列化。
- Web 异步测试稳定性修复：
  Commit `56c887502e218efa146a20ab86c928008e9035d6`。
- 实现 Head Run `30519559480`：8/8 success；后端
  `4987 passed, 4 deselected, 50 warnings, 487 subtests passed`；
  PortfolioPage `31/31 passed`。
- 备份只包含账户、交易、资金和公司行动；预览只读，确认在单事务内整套替换，
  失败回滚，恢复后由官方账本重放派生持仓。
- Windows 实机仍为 Deferred；未导出、读取或恢复真实备份。

## R3.4 最终收口

- 最终 Head `a5b999717e57fe3c78da5c65adadcb1f05b71f95` 的 Run
  `30520589917` 为 8/8 success；后端 `4987 passed, 4 deselected`，
  PortfolioPage `31/31 passed`，Web Build 与双平台打包门全部通过。
- R3.4 Judge：`PASS`；PR #3 保持 Draft，`main` 未改变。

## R3.5 已确认产品契约

- 七个手动入口：本周至今、上一周、下周展望、5周、10周、1个月、2个月。
- 周期事实只来自 `HistoryService.get_history_list()` 和现有
  `AnalysisHistory`；股票/ETF 与市场复盘分区展示。
- 下周展望只使用最近 14 个自然日内的合格历史，不调用 AI；数据不足时固定显示
  “近期有效数据不足，暂不能形成下周展望。”
- 展望使用 `report_type=period_outlook` 写回现有分析历史，保存目标周、生成时间、
  来源记录 ID、方向、置信度、依据、风险与失效条件。
- 进入下一周后，上一周周期汇总可读取日期完全匹配的旧展望快照并列复盘。
- 页面免责声明固定为：
  “下周展望基于已有历史分析形成，仅供参考，不代表确定结果。”

## R3.5 实现与验证证据

- 计划 Commit `e7a71a806c8b5ac852348b58cd3c0d742410a17a`；服务、
  API、历史隔离和 Web 施工合并为后续四个逻辑 Commit。
- 实现 Head `4b563bc63e9638731f2a17ed25129de095046ef4` 的 Run
  `30525590779` 为 8/8 success。
- 后端 `5005 passed, 4 deselected, 51 warnings, 494 subtests passed`；
  Web 阻断套件 `55/55 passed`，Web Production Build 成功。
- 七个周期边界、跨月/跨年、14 日有效期、股票/ETF/市场复盘分区、数据不足、
  来源追溯和上周展望并列复盘均有专项测试。
- 生成人工入口只有 `POST /api/v1/period-report/generate`；页面初次打开不请求，
  周期生成不调用模型、行情、新闻、通知或调度入口。
- 展望快照继续使用 `AnalysisHistory(report_type=period_outlook)`，未增加表或列；
  普通股票历史与回测显式排除该报告类型。
- 额外全量 Web 基线为 `1044 passed, 2 skipped, 1 failed`；唯一失败是既有
  `AlertRuleForm` JP/KR 选项测试与相邻既有“不显示 JP/KR”测试契约矛盾，
  不在 R3.5 正式 Web 阻断门内，未修改产品或旧测试掩盖该基线债。
- PR #3 保持 Draft；Windows 实机仍为 Deferred；未使用真实历史、真实数据库、
  模型、通知渠道或自动入口。

`R3_5_IMPLEMENTATION_CI_PASSED_FINAL_HEAD_CI_PENDING`

## 2026-07-30 Work2 / R3.6 接管

`WORK_ID=WORK-002`；`CURRENT_STAGE=R3.6 / Build-Test-Publish-CI`；`ACTIVE_GOAL=Windows 便携安全更新`。Work1 已永久关闭，PR #3 已合并，R3.1–R3.5 已进入 `main`。本轮基线 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`，独立分支 `agent/pp02-work2-r3-6-windows-portable-update`，只创建独立 Draft PR。Windows R5 真机验收、Ready、合并、Tag、Release 和真实数据继续禁止。

## 2026-07-30 Work2 / R3.6 Review 修复（历史，已由 PR #6 取代）

- 当时 Draft PR：`#5`；实际分支：`codex`。该 PR 现已关闭并标记为 superseded。
- 上一 Head：`e5cdb70`；CI Run `30543513470` 为 8/8 success，但 Work2 Judge 发现更新事务与真实运行行为阻断，不能据此判定通过。
- 先前 `PUBLISH_BLOCKED` 仅保留为历史说明，当前不再是 Active Blocker。
- 历史动作：收敛助手资源、下载重定向/超时、停止后备份、完整回滚、动态端口握手、严格便携身份和真实行为测试；成果后由 PR #6 接管。

## 2026-07-30 Work2 / R3.6 最终收口

- 活动 Draft PR：`#6`；分支：`codex-xbl3c5`；Base：`main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- 已验证 Head：`71404954407a9a3a6362a398465fc822b1351c72`；CI Run `30547333980` 为 8/8 success。
- PR #5 已关闭并由 PR #6 取代，只保留为 superseded 历史。
- 当前 Judge：`IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`；`DRAFT_HOLD`。
- 本轮只为 Windows CI 增加已验证便携候选 artifact，不修改便携更新业务行为、不升版本、不创建 Tag 或 Release。


## 2026-07-30 PR #7｜R5 Windows 基础启动失败与返工

- 活动 Draft PR：`#7`；验收失败 Head `d489a795b6089575a1fd61a27c9b28e2f3cb1b03`；CI Run `30564032072` 为 8/8 success。
- 失败 Artifact SHA-256：`203e41a35e2cd081a20640f514c9de417bd507cbd9b8a2f097a4d0bed36cda1a`；不得继续用于回滚模拟。
- Windows 11 隔离目录中 Electron loading shell 可启动，但冻结后端因缺少 `fake_useragent.data` / 浏览器数据立即崩溃，健康端点持续 `ECONNREFUSED`。
- 根因：依赖无上限、PyInstaller 未收集 `fake_useragent` 全部数据/子模块、冻结探针未实际加载 UserAgent 数据或 efinance 链、候选上传前未真实启动冻结后端。
- 修复范围：`fake-useragent>=1.4.0,<3.0.0`（当前 CI 同代环境实测 2.2.0）、Windows/macOS `--collect-all fake_useragent`、真实运行时探针，以及 Windows 动态端口健康/主页/进程树启动门。
- 当前结论：`R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`。新 Head 完整 CI 和 Head-bound Artifact 通过前不得重进 R5。


## 2026-07-30 PR #8｜CI 失败根因与下一修复

- 当前唯一活动项为 Draft PR `#8`；CI Run `30576678660` 失败。
- 根因：冻结启动门继承 Actions Runner 的 `GITHUB_ACTIONS=true`，触发 `main.py` 既有保护条件，冻结进程可存活但 `--serve-only` 服务不会启动，动态端口健康与主页检查因此失败。
- `main.py` 的 `GITHUB_ACTIONS` 保护条件保持不变；正确修复位于启动门边界。
- 启动冻结 EXE 前保存并临时设置 `GITHUB_ACTIONS=false`、`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`；finally 恢复全部环境变量并可靠停止进程树。
- 当前继续 `R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`；新 Head 完整 CI 与新 Head-bound Artifact 前不得进入 R5。


## 2026-07-31 PR #9｜R5 Windows 最终真机验收

- 当前活动项：Draft PR `#9`；分支 `codex-2ka919`；Base `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- Windows 验收实现 Head：`958b64de78c50bd2ebb2f9b10a15409ee7040eea`；CI Run `30615265618` 为 8/8 success。
- 验收 Artifact：`8787591352`；外层 SHA-256 `ef4025618b3de9ba8cc45c487518e54340088a69b6eca388d4da5aaa25e30971`；内层便携候选 ZIP SHA-256 `8cc00e59414d418362418ba817271adfef81bbdadf4dfb92549db34555652e45`。
- Windows 隔离目录基础启动复验通过：PP02 主界面完整打开，`/api/health` 与主页均返回 HTTP 200，人工确认后正常关闭窗口；`R5_WINDOWS_BASIC_VALIDATION=PASS`。
- 隔离回滚模拟通过：故障注入确认部分替换会失败，正式候选 `portable-update-helper.ps1` 随后恢复首个被替换程序文件；`.env`、DB、WAL、SHM 与旧 manifest 哈希保持不变；隔离旧入口探针成功重启；`R5_WINDOWS_ROLLBACK_SIMULATION=PASS`。
- 模拟未访问正式安装目录、正式数据库、真实凭据或网络 Release；一次性验收截图不进入仓库。
- Judge：`PASS — R5 WINDOWS VALIDATION COMPLETED — DRAFT_HOLD`。
- PR 继续保持 Draft；未执行 Ready、Merge、main 直写、Tag、Release、真实数据或 R3.7。

## 2026-07-31 Work3 / R3.7 接管

- Work2 已由 PR #9 完成 R5 Windows 验收并进入 `main`；PR #10 仅补齐 `main`
  Push 完整 CI，当前固定基线为 `main@097bb5d60aa42f13737ac4d9db2f582bde50f995`。
- Work3 独立分支：`agent/pp02-work3-r3-7-windows-secure-credentials`；只允许创建并
  更新独立 Draft PR。
- 采用 Electron `safeStorage` / Windows DPAPI；Windows Desktop 敏感配置只有
  `userData` 下版本化 vault 一个持久化事实源，renderer 没有明文读取 IPC。
- 本轮先冻结威胁模型，再提交 RED 测试，随后最小实现、完整 CI 和固定 PR Head 的
  Windows 假密钥验收。
- 只使用构造的假凭据；禁止读取、复制、迁移、打印或上传真实 `.env`、Token、Key、
  Password、Webhook、数据库或账号资料。
- Judge 上限为 `DRAFT_HOLD`；不得 Ready、Merge、直写 `main`、Tag、Release 或进入
  R3.8/后续阶段。

## 2026-07-31 Work3 / R3.7 RED 与本地 GREEN

- 独立 Draft PR：`#11`；Base：
  `main@097bb5d60aa42f13737ac4d9db2f582bde50f995`；分支：
  `agent/pp02-work3-r3-7-windows-secure-credentials`。
- 威胁模型与实施计划已先冻结；远端 RED Head
  `096ffa4725d552fcc2ca9008409572deb5d9652d` 的 Run `30634867504` 已观察到
  `backend-gate` 与 `desktop-test` 按新契约预期失败。
- 本地 GREEN 已覆盖版本化密文 vault、原子写入/回滚/事务失效、窄 IPC、主 frame
  校验、继承环境敏感值清除、后端内存注入、全量敏感项遮罩和无凭据导出。
- 本地证据：Desktop `73/73`、后端相关模块 `265/265`、跨运行时/CI 契约
  `4/4`、Web 阻断套件 `124/124`，Web Lint 与 Production Build 均通过。
- 初始实现远端 Head `368566e6125d4ff348be817e638c2e195b474c65` 已由独立安全
  审查和完整 CI 判定作废；不得作为最终固定 Head 证据。PR 必须持续保持 Draft。

## 2026-07-31 Work3 / R3.7 独立审查返工

- 独立只读审查确认四项阻断：PR workflow 默认使用临时 merge SHA、畸形 dotenv
  敏感行可绕过导出、Backend 原始异常可能进入日志，以及 vault 先于 `.env` 提交会
  形成“新凭据/旧 endpoint”崩溃窗口。
- 同时修复单 vault 并发事务、replace 后权限失败、finalize 验证顺序、可信 origin/
  主 frame 导航约束，以及源码/日志/最终 ZIP 与解包目录假密钥扫描缺口。
- 采用 `.env` 精确版本绑定：先持久化非敏感配置，再由 main 校验磁盘版本并提交
  vault；任一崩溃/外部改写导致版本不一致时，启动必须 fail closed，不注入凭据。
- 作废 Head Run `30637145300` 的 `backend-gate` 另发现
  `CUSTOM_WEBHOOK_URLS` 已标记敏感但仍使用 textarea；已改为 password 控件。该 Run
  即使其余 Job 成功也不计最终 Judge。
- 审查修复本地证据：Desktop `80/80`；Backend 配置相关 `325/325`；跨运行时、
  打包和泄漏扫描契约 `14/14`；Web 阻断套件 `127/127`；Lint、Production Build、
  AI 治理、全差异 whitespace 检查和派生假密钥源码扫描均通过。
- 审查修复 Head 尚未发布；必须先独立复审，再以新 Head 完整跑八个 CI Job，并从
  Windows Job 日志证明 checkout Head、safeStorage PASS 与 artifact scan Head 三者一致。

## 2026-07-31 Work3 / R3.7 第二次独立复审返工

- 第二次独立复审确认原有四项 Critical 和五项 Important 全部关闭，无新增
  Critical。
- 剩余两项 Important 已以回归测试先行修复：Windows secure mode 在
  dotenv 解析前识别并拒绝畸形敏感 assignment；Windows 假密钥源码扫描扩大为
  整个仓库根目录。
- 两项新回归在修复前均按预期失败，修复后 `2/2` 通过；测试值均为构造的
  假密钥，拒绝信息不包含假密钥。
- 修复仍只存在本地分支；第三次独立复审通过前不发布，Draft PR `#11`
  继续保持 Draft。

## 2026-07-31 Work3 / R3.7 第三次独立复审返工

- 第三次独立复审确认仓库根 source scanner 和此前安全边界均已闭环，无
  Critical；发现一项 Important：`python-dotenv` 支持单引号键，而初版原始扫描
  只识别裸键，畸形 value 可使该行被解析器丢弃。
- 回归矩阵扩大到裸键、单引号键、双引号键及两种引号键的 `export`
  形式；修复前单引号两种形式均可复现失败，修复后五种形式全部通过。
- 本地修复仍未发布；必须第四次独立复审无 Critical/Important 后才能更新
  Draft PR `#11`。

## 2026-07-31 Work3 / R3.7 第四次独立复审通过

- 第四次独立只读复审在固定本地 Head
  `0627ea85ef14cfb7d0d457937244c2a860fac345` 未发现 Critical 或 Important，
  结论为 `PUBLISH_TO_EXISTING_DRAFT_PR`。
- 复审实测裸键、单/双引号键、可选 `export`、BOM、空白/Tab、大小写混合和
  不完整引号 value 组合均在 dotenv 丢弃前识别敏感键；拒绝信息无假值，
  `.env` 原始字节不变。
- 完整 base→Head 的 vault 原子性、版本绑定、单活事务、finalize 预检、
  IPC origin/navigation、日志抑制、导出过滤和 Windows Head-bound scanner 未发现
  新的 Critical/Important。
- 发布前最终本地门禁：Python/契约 `340/340`，Desktop `80/80`，Web `127/127`，
  Lint、Production Build、AI 治理、仓库根假密钥扫描与全差异 whitespace 检查通过。
- 下一步只允许发布到现有 Draft PR `#11` 并执行完整 CI/假密钥验收；
  Ready、合并、main 写入、Tag、Release、真实凭据/数据和后续阶段仍禁止。

## 2026-07-31 Work3 / R3.7 已复审实现 Head 完整 CI

- 远端 Head `b23c698b32b09749e907f1f4f7be1c056445a52e` 的树
  `9b21a84a6b55e1e3dc967d96ceed72bea7b33ae4` 与本地已复审树精确一致。
- CI Run `30640475137` 为 8/8 success：Change Detection、AI Governance、Docker、
  Backend、Desktop Test、Web、macOS 和 Windows 全部成功。
- Backend 精确结果：`5027 passed, 4 deselected, 51 warnings, 499 subtests passed`。
- Windows Job `91189042298` 日志证明 checkout/ref/环境期望 Head 均为
  `b23c698b32b09749e907f1f4f7be1c056445a52e`；`safeStorage` 验收 PASS 恰好一次且
  validation Head 相同。
- 同一 Windows Job 的仓库根 source scan PASS，并对最终 ZIP、解包目录和
  `win-unpacked` 做联合 artifact scan PASS；两个 scan Head 均与验收 Head 一致，
  完整 Job 日志不含派生假凭据明文。
- 临时 CI artifact `8798100943` 与 Head 同名绑定，不是 Tag 或 Release，本轮不下载、
  不分发。
- 本节作为证据收口会生成新 Head；为避免自指 Head/Run 无限漂移，新 Head 的
  最终 Run ID 与同 Head Windows 标记只写入 Draft PR `#11` 元数据和总控回传，
  不再修改代码树。
