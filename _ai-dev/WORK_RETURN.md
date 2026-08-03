# WORK-016｜Windows 冻结筹码依赖收口（执行中）

## Work16｜阶段回传

```text
BASE=568e26adf0e6393a7a0da1be57369535735cd05a
BRANCH=agent/pp02-work16-windows-chip-runtime
DRAFT_PR=PENDING
ROOT_CAUSE=CONFIRMED_EXISTING_MINI_RACER_RUNTIME_NOT_COLLECTED
DEPENDENCY_CHANGE=NONE
TDD=PENDING_RED
FULL_CI=NOT_RUN
JUDGE=IN_PROGRESS_DRAFT_ONLY
```

- 只读证据确认 Windows CI 安装 `akshare 1.18.81` 时已安装 `mini-racer 0.14.1`；
  wheel 内已有 `py_mini_racer/mini_racer.dll` 和 `icudtl.dat`。
- `scripts/build-backend.ps1` 没有收集该包，现有探针只验证导入、静态资源与 HTTP
  健康，不创建 MiniRacer/V8；这解释了冻结健康成功但 Work14 筹码链因 DLL 缺失退化。
- 已批准最小方案不改 `requirements.txt`：收集现有运行资产，检查 DLL/ICU，并在
  构建输出与最终解压 ZIP 上执行离线 V8/筹码模块探针。
- 当前未 Ready、合并、Tag、Release，未处理新闻/签名，未使用真实凭据/数据，也未
  执行新增 Windows 真机动作。

---

# 历史回传｜WORK-015 / PR #20/#21 主线收口

## Work15｜阶段回传

```text
PR20_FIXED_HEAD=e11946f528c9cb64beeec8b626ada457c02b0034
PR20_STATE=MERGED
PR20_MERGE_COMMIT=25de369f8e12438a1ec1f3511c68256c471243e4
PR20_MAIN_CI=PASS_RUN_30822458701_8_OF_8
AUTO_TAG=SKIPPED_RUN_30822458692
PR21_STATE=OPEN_DRAFT_FINAL_HEAD_CI_PENDING
PR21_SYNC_METHOD=NON_DESTRUCTIVE_TWO_PARENT_MERGE
PR21_SYNC_MERGE_HEAD=25313cf0f23f0f4ab4922ea983bcd05b3577e23e
TAG_RELEASE=NOT_CREATED_OR_CHANGED
CURRENT_GATE=PR21_FIXED_HEAD_CI_THEN_READY_MERGE
```

- PR #20 在固定 Head 未漂移、原 CI 成功且 5 文件范围未扩大的条件下转为 Ready，
  并以仓库既有 merge-commit 方式合入 `main@25de369f…`。
- 新 main 的 Push CI Run `30822458701` 全部 8 个 Job success；Windows 安装生命周期、
  macOS、Web、Desktop、后端、Docker 和治理门均通过。Auto Tag 按规则 skipped。
- PR #21 的原 7 文件证据与 PR #20 的 5 文件产品改动无路径重叠。同步采用普通双父
  merge commit `25313cf0…`；没有 rebase、force-push、历史改写或文件丢失。
- 当前状态 Commit 只收口 Work14 最终裁决与 PR #20 合并事实。下一门为 PR #21
  最终固定 Head CI；通过后按已授权顺序 Ready 并合并。
- 未创建或修改 Tag/Release，未处理 `mini_racer`、新闻、签名，也未执行新增 Windows
  真机动作。


---

# 历史回传｜WORK-014 / PR #20 固定 Head Windows 未发布候选验收

## Work14｜真实 Windows 证据回传

```text
PR20_FIXED_HEAD=e11946f528c9cb64beeec8b626ada457c02b0034
PR20_STATE=OPEN_DRAFT_UNMERGED_AT_WORK14_CLOSE
PR21_STATE=OPEN_DRAFT_UNMERGED_AT_WORK14_CLOSE
CANDIDATE_VERSION=3.29.1
INSTALLER_BYTES=217003814
INSTALLER_SHA256=DAD0CE0CCF8FC34F7318CD4E4F0CC37347C68A1A03E98D0CA7B048E393B18B33
INSTALLER_SIGNATURE=NotSigned
PYTHON_RELATED=PASS_130
DESKTOP_RELATED=PASS_82_OF_82
FROZEN_BACKEND_HEALTH=PASS_DYNAMIC_PORT
FORMAL_600519_TASK_QUERY_TRACE=1c4ae649232d40eaae7dcb6bb1b6981f
FORMAL_600519_HISTORY_ID=2
FORMAL_600519_COMPLETION=PASS_PERSISTED_AFTER_RESTART
MARKET_HISTORY=PASS_1
PERIOD_REPORT=PASS_WEEK_TO_DATE_2_SOURCES
DIAGNOSTIC=DEGRADED_NEWS_EMPTY_CHIP_DLL_MISSING
WORK12_RESTORE=PASS_HEALTH_OK_DB_AND_LOGS_PRESENT
PR21_EVIDENCE_HEAD=da2290597e880c4c4a4c1c04e5cc548aa5542ea9
PR21_EVIDENCE_CI=PASS_RUN_30821021196_4_SUCCESS_4_PATH_SKIPPED
JUDGE=PASS_WITH_DEGRADATIONS_DRAFT_HOLD
READY_MERGE_MAIN_TAG_RELEASE=NOT_AUTHORIZED
```

- 候选从 PR #20 固定 Head 构建，内置 build revision 精确一致。安装器只作为未发布
  验收产物保留证据，没有执行安装、Tag 或 Release。
- `600519` 受控任务完成为 100%，正式历史 ID `2`；task/query/trace 全部一致。
  `model_used=codex_cli`，LLM 154,358 ms，评分 59，操作建议“观望”。
- 诊断 `history=ok`，运行流 `llm_analysis=success`、
  `history_save=success`。候选后端重启及 Work12 原安装恢复后仍能重读同一历史。
- 相关回归和聚合通过：Python `130 passed`、Desktop `82/82`、大盘历史 1 条、
  周内报告来源 2 条（1 个股、1 个大盘）。
- 降级项保持显式：新闻 0 条；筹码链缺少冻结 `mini_racer.dll`；诊断总体
  `degraded`；安装器 `NotSigned`，且未执行候选安装生命周期。
- Work12 现场未被候选覆盖或清理。其 `.env` 在受控任务前已发生外部变更（来源未判定）；Work14 没有回写旧副本。临时副本/Junction 已精确移除，原应用恢复为
  `health=ok`，数据库和日志仍存在。
- PR #21 证据 Head `da229059…` 的 Run `30821021196` 已 success；4 个适用 Job
  成功，4 个路径无关 Job正常 skipped。Work14 最终裁决为
  `PASS_WITH_DEGRADATIONS — DRAFT_HOLD`。
- Work14 结束时 Ready、合并、`main`、Tag、Release 均未授权；后续 PR #20/#21
  主线收口属于 Work15 的独立精确授权。


---

# 历史回传｜WORK-010 / v3.29.1 发布与 Windows 真机验收

## Work10-B｜Windows 发布临时目录清理竞态

```text
MAIN_HEAD=91e174d30b3d0f2533b0db5df0245bf49778234f
FAILED_RELEASE_RUN=30763628302
FAILED_WINDOWS_JOB=91538466726
WINDOWS_INSTALLED_LIFECYCLE=PASS_IN_FAILED_RELEASE_RUN
MACOS_BUILDS=PASS_BOTH_IN_FAILED_RELEASE_RUN
FINAL_ZIP_SMOKE=PASS_BEFORE_CLEANUP_FAILURE
ROOT_CAUSE=ONE_SHOT_REMOVE_ITEM_RACED_TRANSIENT_PYD_FILE_HANDLE
MINIMAL_FIX=BOUNDED_15_ATTEMPT_1_SECOND_RETRY_AFTER_OWNED_PATH_VALIDATION
TDD=RED_THEN_GREEN
LOCAL_CONTRACTS=PASS_25_OF_25
WORKFLOW_YAML_PARSE=PASS
AI_ASSETS=PASS
DRAFT_PR=19_DRAFT
IMPLEMENTATION_HEAD=84bcbb060aaa78ebe5d5413cd8a16a7a1eac5512
FULL_CI=PASS_RUN_30765409298_HEAD_05e7a5dac1064b644cb5a01fa9300a4af109ecdb_7_SUCCESS_1_PATH_SKIPPED
WINDOWS_CANDIDATE_ARTIFACT=8839171754_SHA256_18b96a582eaf17faa405f09870ca36f6e3797663919b921842075075fb06e041
WINDOWS_DIAGNOSTIC_ARTIFACT=8839165862_SHA256_e7735f3b0df0bd061ea496f89eccbf7a1fd4b1b19258ca8f4985387822ca282c
TAG_RELEASE=NOT_CREATED
JUDGE=WORK10_B_PASS_AWAITING_PR19_MERGE_AUTHORIZATION
```

- Run `30763628302` failed only after the final Windows ZIP frozen-backend smoke passed. The
  immediate cleanup hit `Access denied` on `aiohttp/_websocket/mask.cp312-win_amd64.pyd`; the final
  publish job was skipped, so no v3.29.1 Tag or Release exists.
- The minimal workflow change preserves runner-owned path validation, retries deletion at most 15
  times with one-second waits, and still throws after exhaustion. Both pre-extraction and `finally`
  cleanup use this contract.
- No product code, installer logic, dependency, fixed product Commit, Tag or Release was changed.
  Draft PR #19 fixed Head `05e7a5da…` completed Run `30765409298` with all seven applicable Jobs
  successful and Web Gate path-skipped. The Windows Job passed final ZIP, installer contracts,
  installed lifecycle, diagnostics, credential scan and candidate upload. The Work stops at the
  explicit PR #19 merge authorization gate.

---

## 历史回传｜Work10-A 云端发布入口修复

```text
PRODUCT_RELEASE_COMMIT=3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65
BRANCH=agent/pp02-work10-release-entry
LOCAL_CONTRACTS=PASS_24_OF_24
WORKFLOW_YAML_PARSE=PASS
AI_ASSETS=PASS
DRAFT_PR=18_DRAFT
PR_CI=PASS_RUN_30750806894_HEAD_e1a619c5867037bf569be5d741194ff792ce948b_7_SUCCESS_1_PATH_SKIPPED
READY_MERGE_TAG_RELEASE=NOT_AUTHORIZED
WINDOWS_REAL_MACHINE_ACCEPTANCE=NOT_RUN
JUDGE=WORK10_A_PASS_AWAITING_READY_MERGE_TAG_RELEASE_AUTHORIZATION
```

- Work10-A preserves the existing annotated-Tag push trigger and adds a recoverable manual entry
  that accepts the Release Tag, fixed product Commit and annotated Tag message.
- Read-only preflight validates stable SemVer, exact Commit object type, `origin/main` ancestry,
  direct Tag object type/target/name, and exact Release absence. It fails closed when the Release
  state cannot be confirmed.
- Windows and macOS check out the fixed product Commit. The publish job runs only after preflight
  and every build succeeds, is the only job with write permission, and performs remote direct Tag
  object plus peeled-commit verification before `gh release create --verify-tag`.
- Local deterministic gates pass. Remote branch and Draft PR #18 are published; fixed implementation
  Head `e1a619c58670…` completed Run `30750806894` with seven applicable jobs successful and Web
  Gate correctly path-skipped. No Tag, Release, main write or Windows real-machine action has
  occurred.

---

# 历史回传｜WORK-009 / PR #17 诊断证据链修复与 Windows 安装闭环

## 2026-08-02 固定 Head 完整闭环

```text
WORK8_CLOSEOUT=COMPLETED_WITH_BLOCKER
WORK9_TAKEOVER=PASS
CURRENT_HEAD=db02221b92e210925044c5af5a4aacd2f08fcb4f
LATEST_CI_RUN=30745575186
DIAGNOSTIC_CONTRACT_TEST=PASS_WINDOWS_POWERSHELL_5_1
DIAGNOSTIC_ARTIFACT=PASS_FAILURE_ID_8832664000_AND_SUCCESS_ID_8833102391_REDACTED
FINAL_ZIP_VALIDATION=PASS_FINAL_EXTRACT_MANIFEST_BROWSERS_JSONL_AND_BACKEND_START
DIRECT_ERROR=NLTK_3_10_1_BLOCKED_BUNDLED_XML_FROM_INSTALL_ROOT_CWD
ROOT_CAUSE=INSTALLED_BACKEND_CWD_WAS_ANCESTOR_OF_PYINSTALLER_BUNDLE
REGRESSION_TEST=PASS_RED_THEN_GREEN_82_DESKTOP_AND_29_WINDOWS_TARGETS
MINIMAL_FIX=PASS_PACKAGED_BACKEND_CWD_MOVED_TO_DATABASE_PARENT
WINDOWS_INSTALLATION=PASS_INSTALLER_EXIT_0_AND_REGISTRATION_PASS
INSTALLED_BACKEND_STARTUP=PASS_FIRST_START_AND_HEALTH
EXIT_RESTART_UNINSTALL=PASS_EXIT_RESTART_HEALTH_SECOND_EXIT_UNINSTALL
FULL_CI=PASS_8_OF_8_RUN_30745575186
PROJECT_STATUS_SYNC=YES
PR_BODY_SYNC=YES_EXTERNAL_PR_METADATA
PR17_MERGE_STATUS=AWAITING_EXPLICIT_AUTHORIZATION
V3_29_1_RELEASE_STATUS=BLOCKED_NOT_CREATED
WINDOWS_REAL_MACHINE_ACCEPTANCE=NOT_RUN
NEXT_APPROVAL_REQUIRED=MERGE_PR17
```

- Full-CI validated Head: `db02221b92e210925044c5af5a4aacd2f08fcb4f`.
- Success diagnostic artifact `8833102391` is Head/Run-bound, has ZIP SHA-256
  `5c0f19466e01c399dc20008d5589290d210e4f8e4b612ab4ea7319e50e6b90b8`, and records all
  installed lifecycle stages as PASS without credentials, environment dump, database or user data.
- Stop gate reached. Do not Ready, merge, tag, release, or claim Windows real-machine acceptance
  without explicit authorization.

## 2026-08-02 有效诊断与最小修复

```text
WORK8_CLOSEOUT=COMPLETED_WITH_BLOCKER
WORK9_TAKEOVER=PASS
CURRENT_HEAD=b4684f0be8a818b5b29688933e2a738663e1a638
LATEST_CI_RUN=30744115030
DIAGNOSTIC_CONTRACT_TEST=PASS_ON_WINDOWS_POWERSHELL_5_1
DIAGNOSTIC_ARTIFACT=PASS_ID_8832664000_SHA256_6fa6366761d608572c04b401e69caa764483c7bab3c5bc61ecc96e958989ea65
FINAL_ZIP_VALIDATION=PASS_BROWSERS_JSONL_PRESENT_MANAGED_AND_FROZEN_BACKEND_STARTED
DIRECT_ERROR=NLTK_IMPORT_SECURITY_BLOCKED_BUNDLED_XML_FROM_INSTALL_ROOT_CWD
ROOT_CAUSE=INSTALLED_BACKEND_CWD_IS_ANCESTOR_OF_PYINSTALLER_BUNDLE
REGRESSION_TEST=PASS_RED_THEN_GREEN
MINIMAL_FIX=LOCAL_PASS_PACKAGED_CWD_MOVED_TO_DATABASE_PARENT
WINDOWS_INSTALLATION=PASS_ON_DIAGNOSTIC_HEAD
INSTALLED_BACKEND_STARTUP=FAIL_ON_DIAGNOSTIC_HEAD_ROOT_CAUSE_CONFIRMED
EXIT_RESTART_UNINSTALL=PENDING_FIXED_HEAD_CI
FULL_CI=PENDING_MINIMAL_FIX_HEAD
PR17_MERGE_STATUS=BLOCKED
V3_29_1_RELEASE_STATUS=BLOCKED
WINDOWS_REAL_MACHINE_ACCEPTANCE=NOT_RUN
```

- Artifact security check found no raw diagnostic files, token/key prefixes, credential files,
  databases, complete environment dump or user-data payload.
- Desktop `82/82` and Windows packaging/diagnostic/final-ZIP targets `29/29` pass locally.
- The next authority gate is fixed-Head full CI; PR #17 remains Draft.

## 2026-08-02 正式接管

```text
WORK8_CLOSEOUT=COMPLETED_WITH_BLOCKER
WORK9_TAKEOVER=PASS
CURRENT_HEAD=9cb9a70e9176711096adf12ba5674c56d6f314d2
LATEST_CI_RUN=30742085965
DIAGNOSTIC_CONTRACT_TEST=IN_PROGRESS
DIAGNOSTIC_ARTIFACT=PREVIOUS_RUN_MISSING
PR17_MERGE_STATUS=BLOCKED
V3_29_1_RELEASE_STATUS=BLOCKED
WINDOWS_REAL_MACHINE_ACCEPTANCE=NOT_RUN
```

- PR #17、远程分支和干净检出已重新核对；未发现晚于 `9cb9a70…` 的提交。
- Work8 锁已释放，Work9 锁已取得。Work8 的失败快照不回退，也不冒充修复成功。
- 当前仅进入诊断契约 RED/GREEN；有效 artifact 出现前不修改后端产品根因。

---

# 历史回传｜WORK-008 / Windows installer hotfix

## 2026-08-02 纠偏诊断结果

```text
DIAGNOSTIC_HEAD=eae4b46501c9a183dda20d2975121987e676943b
LATEST_CI_RUN=30742085965
WINDOWS_INSTALLATION=NOT_RUN_ON_DIAGNOSTIC_HEAD
DIAGNOSTIC_ARTIFACT=FAILED_NOT_PRESERVED
INSTALLED_BACKEND_STARTUP=NOT_RUN_ON_DIAGNOSTIC_HEAD
ROOT_CAUSE=ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT
REGRESSION_TEST=LOCAL_PASS_82_DESKTOP_AND_15_DIAGNOSTIC_CONTRACTS;WINDOWS_CONTRACT_FAIL
FULL_CI=FAIL_7_SUCCESS_1_WINDOWS_FAILURE
PROJECT_STATUS_SYNC=YES
PR_BODY_SYNC=YES_EXTERNAL_PR_METADATA
PR17_MERGE_STATUS=BLOCKED
V3_29_1_RELEASE_STATUS=BLOCKED
WINDOWS_REAL_MACHINE_ACCEPTANCE=NOT_RUN
```

- The one diagnostics-only fixed-Head Run completed without a second attempt. Windows candidate
  construction succeeded, then the verifier contract failed before installed lifecycle execution.
- The artifact upload used `if: always()` and a Head/Run-bound name, but failed because the
  diagnostic directory contained no files. No installed backend stderr or exception artifact is
  available.
- No backend or packaging-root-cause patch followed. Work8 stops at the evidence-insufficient
  verdict and PR #17 remains Draft.

## 已确认失败

```text
WINDOWS_NATIVE_ENVIRONMENT=PASS
RELEASE_PROVENANCE_VALIDATION=PASS
INSTALLER_HASH_VALIDATION=PASS
WINDOWS_INSTALLATION_VALIDATION=FAIL
FIRST_STARTUP_VALIDATION=NOT_EXECUTED_DUE_TO_INSTALLATION_FAILURE
EMPTY_DATA_VALIDATION=NOT_EXECUTED_DUE_TO_INSTALLATION_FAILURE
SAFE_DEFAULTS_VALIDATION=NOT_EXECUTED_DUE_TO_INSTALLATION_FAILURE
RESTART_VALIDATION=NOT_EXECUTED_DUE_TO_INSTALLATION_FAILURE
R7_WINDOWS_FIRST_USE_ACCEPTANCE=FAIL
```

- 验收环境：Windows 11 Home China `10.0.26200`，x64。
- v3.29.0 安装器实际大小 `209712731` 字节，SHA-256
  `a9a0b547ff9be2c9153a006d3471f350f712a5306a1267d19fd111aa0e54fbdb`，均匹配。
- Authenticode 为 `NotSigned`；本 Work 不擅自扩大到代码签名。
- 安装器两次均在显示可操作安装向导前崩溃；Windows Event 指向解包
  `System.dll`，异常 `0xC0000005`。
- 未读取或删除预先存在的用户目录；未制造空数据通过。

## Work8 当前进度

- 用户已授权 Work8 并选择 `A｜保留安装向导`。
- 固定 Base：`main@66666352e953d90becce420da7d35b649516af76`。
- 分支：`agent/pp02-work8-r7-installer-fix`。
- Draft PR：[#17](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/pull/17)。
- 已提交设计：
  `docs/superpowers/specs/2026-08-01-work8-windows-installer-hotfix-design.md`。
- 设计锁定 `electron-builder 26.15.7`、保留 assisted/current-user 安装，并新增
  PR 与 Release 共用的 Windows install/start/uninstall verifier。
- 用户已批准设计勘误：Desktop 测试、Windows/macOS 打包和 Desktop Release 使用
  Node 22，独立 Web 门继续使用 Node 20。
- 已精确锁定 builder、显式补齐既有测试使用的 `archiver 5.3.2` 开发依赖，并新增
  fail-closed verifier、失败进程 fixture、PR 与 Release 生命周期门。
- TDD RED 分别证明旧 builder、缺失 verifier/工作流门、旧 Node 20 和未声明
  `archiver` 会失败；GREEN 后 Desktop Node 22 测试 `81/81`、安装器与打包专项
  `23/23` 通过，workflow YAML 与差异格式检查通过。
- 当前 Judge：`ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT`。
- Run `30742085965`：macOS 与其余六个非 Windows Job 成功；Windows 在 verifier
  contract 失败，安装/启动/卸载生命周期被跳过，诊断 artifact 上传失败。
- 未授权 Ready、Merge、main、`v3.29.1` Tag/Release 或真实数据。

---

# WORK-007｜R7 主线合并与正式发布最终回传

> 当前 Work 已完成。以下只记录已取得的 GitHub、CI、Tag、Release 和产物证据。

## 实际完成

- PR #12 合并 Commit：`ad5588fb5aa12f3424596ada2a411261e8b74916`。
- PR #13 最终 Head `263578266ab4cd604a1dcde701621139e66ea193` 的 Run
  `30693442671` 成功后合并为 `6650f9c30f394a1ba6b7e7fd99de67d5c11488ab`。
- 首轮 `main` CI 暴露 Web 账户选项竞态和 macOS 冻结后端 NLTK CWD 安全阻断；
  PR #14 采用最小修复并合并为发布提交
  `49759dbd032f577d32e8e0f6670298f700e0f272`，新 `main` 的 8 个适用 Job
  全部 success。
- annotated Tag `v3.29.0` 精确指向发布提交；GitHub Release 非 Draft、非
  Prerelease。Windows 安装版、Windows 免安装 ZIP 与 SHA-256、macOS arm64/x64
  DMG 等 7 个正式资产已上传，Desktop 与 Docker/GHCR 发布成功。
- Release 正文和三语言 README 已明确声明：本项目基于
  `ZhuLinsen/daily_stock_analysis@v3.28.0` 复制后进行二次开发，不是上游官方
  版本；原 MIT License 未修改。
- 来源声明 PR #15 已合并为
  `main@b4a0ec11da19b5552ce87dde1ece716f61fd5174`；合并后 CI Run
  `30697946093` 8/8 success。Tag 仍保持在发布提交 `49759dbd…`。
- Work6 结论继续为 `NO_FORMAL_DATA_FOUND`；本 Work 未读取、创建、迁移或上传
  真实数据库、真实数据、真实账号或真实凭据。

## 未验证项、风险与回滚

- 未验证项：无 R7 阻断项；真实数据不适用，因为旧项目和数据库从未建立。
- 风险：`v3.29.0` 是发布提交，发布后 `main` 另含来源声明文档；不得为追平
  `main` 而移动或重打已发布 Tag。
- 回滚：文档可通过后续独立 PR 修正；已发布 Tag/Release 的删除、移动或重建属于
  破坏性发布操作，未经精确授权不得执行。

## 最终 Judge

`PASS — v3.29.0 RELEASED — WORK7 COMPLETED`

Work7 施工权已释放，当前无 Active Work。任何新功能、真实数据、Ready、合并、
`main` 写入、Tag 或 Release 都必须由新的 Work 单独授权。

---

# 历史回传｜WORK-005 / R6-A 正式数据安全只读盘点工具

> 当前 Work 已结束。只有本 Work 的新鲜证据可以更新当前结果；旧 Work 内容在下方
> 作为追加历史保留。

## 当前进度

- 用户已批准 R6-A 书面设计与实施；Work5 为唯一 Active Work。
- 固定 Base：Work4 Draft PR #12 Head
  `a220e9e146e14722561bc084ec4e5306b30d36c7`。
- 独立分支：`agent/pp02-work5-r6-inventory-tool`；Draft PR `#13` 已创建并保持 Draft。
- 已完成标准库安全核心、Windows 薄 CLI、31 项专项测试、精确 Windows 用法和隐私边界文档。
- TDD RED 已分别证明服务模块和 CLI 缺失时的新契约失败；GREEN 后专项
  `26 passed`。独立审查发现 3 项 Important 和 1 项 Minor，已用 5 项新 RED 回归复现
  并修复；当前专项 `31 passed`，R6-A/R4/备份联合 `50 passed, 4 warnings`。
- 最终代码完整 CI 等效后端门为 `5070 passed, 1 skipped, 4 deselected,
  48 warnings, 499 subtests passed`；语法、严重 Flake8、确定性检查、AI 资产和
  格式检查通过；独立复核 APPROVE，无剩余发现。
- 最终固定 Head `50dd04ca5a49a6e54de01e2d28ce598f690d9931` 的 CI Run
  `30691233934` 全部适用 Job success。
- 云端只用动态空库和人工假数据；Windows 真实数据库未读取、未备份、未盘点。

## 当前 Judge

`CLOUD_TOOL_IMPLEMENTATION_PASS — WINDOWS_REAL_INVENTORY_NOT_RUN`

工具云端实现、本地验证与 Draft PR #13 固定 Head CI 已完成。Work5 已收口；Windows
真实盘点仍未运行。其历史授权不包含 Ready、合并、`main`、Tag、Release 或 R7，
这些动作仅由后续 Work7 的新精确授权覆盖。

---

# 历史回传｜WORK-004 / R4

> 当前 Work 已结束。只有本 Work 的新鲜证据可以更新当前结果；旧 Work 内容在下方
> 作为追加历史保留。

## 当前进度

- 已核对 `main@eb32298…`、PR #11 合并、PR #7/#8 仍 Open/Draft，以及旧台账漂移。
- 已建立隔离分支 `agent/pp02-work4-r4-database-rehearsal`。
- 已选择并记录 `PP02-WORK-HANDOFF-002`；聊天显示名称保持不变。
- 已冻结 R4 设计；仅允许空库和人工假数据。
- 已关闭被 PR #9 替代的历史 Draft PR #7/#8，分支和历史保留；已建立 Draft PR #12。
- 基线专项：`tests/test_storage.py` + `tests/test_portfolio_backup_service.py` 为
  `30 passed`；`scripts/check_ai_assets.py` 通过。
- TDD RED：8 项服务契约均因实现模块缺失而失败；意外异常脱敏回归也先证明原始
  异常会泄漏，再完成修正；GREEN 后 R4 专项为 `13 passed`。
- R4、备份与存储联合回归：`43 passed, 17 warnings`；警告与既有基线一致。
- 临时目录全新混合假数据演练：PASS；四类正式事件各 1 条，源 SHA 不变、摘要一致、
  过期预览被拒绝且目标不变；报告和目标未包含构造的排除值。
- CI 等效 UTC 环境完整离线后端门：`5040 passed, 4 deselected, 47 warnings,
  499 subtests passed`；Flake8 严重错误 0，AI 资产、语法、确定性检查和差异格式通过。
- Base-to-Head 安全自审通过；未跟踪数据库、环境文件、备份、报告、日志、依赖或
  Workflow 变化，报告不包含行值或备份正文。
- 固定实现 Head `f1b433a7a97ed43a7048aeb4239b76357003083b`；Tree
  `cdc54b1d1488358a13c40223a6354c901b8a5001`；CI Run `30660971800` 中 AI 治理、
  变更检测、Docker 和后端门全部 success，未改路径 Job 按规则 skipped。
- PR #12 保持 Draft；未 Ready、未合并、未写 `main`、未 Tag、未 Release，且未使用
  真实数据库、数据、备份、账号或凭据。

## 当前 Judge

`PASS — WORK4 COMPLETED — DRAFT_HOLD`

施工权已释放。下一段为未启动的 `WORK-005 / R6 正式数据迁移授权与计划`；新聊天
只能先做接管核对和白话授权决策，不得自动接触真实数据。

---

# 历史回传｜WORK-PP02-CLOUD-REBUILD-001

> 运行中记录；只有本 Work 的新鲜证据可以更新本文件。

## 实际完成

- 已核验远程 `main`、官方 v3.28.0 Commit、目标分支不存在和框架附件。
- 已在新的隔离目录从官方固定 Commit 建立完整业务树。
- 已接入批准的 P000/P001 V1.5.6 控制 Overlay，并通过最低完整性硬门。
- 已通过 GitHub App/Git Data 原子创建初始候选 Commit 和独立分支；远程 Commit
  与本地候选树一致。
- 已完成 Python、Web、Desktop、AI 治理、格式、白名单和安全范围的本轮本地验证。

## 修改范围

- `.github/workflows/ci.yml`：重放 Work 1 已接受的最小只读权限。
- `AGENTS.md`：官方规则不变，新增单一有标记的 PP02 控制 Overlay。
- `_ai-dev/`、既有 PP02 控制台账、`docs/INDEX.md` 和 `docs/pp02/`。
- 官方业务代码：相对官方 v3.28.0 零差异。

## 测试与 CI

| 项目 | 当前结果 |
| --- | --- |
| 最低完整性硬门 | 通过：格式、AI 治理、官方业务树、20 路径白名单、历史非回退、安全扫描、文件清单和树对象已核验 |
| 候选持久化 | 通过：初始 Commit `9a2588004ba3436faa2b61d489fc8eab564ccef4`；分支 `agent/pp02-v3.28.0-cloud-rebuild`；本地/远程树 `c157f143640d056892ba5b1345e65a63eb86babd` |
| Python 完整离线测试 | 通过：官方 `./scripts/ci_gate.sh`；`4966 passed`、`4 deselected`、`45 warnings`、`487 subtests passed` |
| Web lint / build | 通过：ESLint 成功，TypeScript + Vite 生产构建成功；本地 Node `24.14.0` / npm `11.9.0`，CI Node 20 尚待验证 |
| Desktop | 通过：`47 passed`；Windows/macOS 打包由 Draft PR CI 验证，Windows 实机仍为 `NOT_VERIFIED_IN_CLOUD` |
| AI 治理 | 通过：`python scripts/check_ai_assets.py` |
| 差异与安全 | 通过：格式、20 路径控制白名单、官方业务零差异、台账非回退、差异层密钥签名/真实数据/跨项目内容均无命中 |
| Draft PR | `#3`，目标 `main`，保持 Draft，未转 Ready、未合并 |
| Draft PR CI | 首轮 Run `30220968264` 通过：7 个 Job 全部 success；收口证据 Commit 只有在同一 PR 最终 Head CI 也通过后才可完成外部回传 |

## 未验证项、阻塞与风险

- 未验证：Windows 实机、真实数据。
- 当前阻塞：无。
- 风险：Windows CI 验证冻结后端，不等于 Windows 实机安装验收；旧 Work 1 CI
  不得复用。

## Backlog 与清理

- Backlog：R1–R7；见 `docs/pp02/REBUILD_ROADMAP.md`。
- 清理：旧工作树保持原样；新的重建目录必须保留到发布链路和回传完成。临时缓存
  仅在验证完成后清理。

## Judge

`PASS`——候选恢复、远程持久化、本地完整验证和本次 Draft PR 真实 CI 均通过；
PR 必须保持 Draft，不构成 Ready 或合并授权。外部最终回传只在本收口证据 Commit
的 Head CI 同样通过后发出。

下一 Work：未授权，当前 Work 完成后停止并等待总控。

## 2026-07-29 R1/R2 连续阶段回传

- R1 产品范围已确认：PP02 保持单用户，用户档案/切换/隔离/用户级备份不迁移。
- 官方账户/组合事件账本固定为持仓唯一事实源。
- R2 已将迁移拆成 R3.1–R3.7，并固定依赖、文件边界和验收出口。
- Windows 实机验收为 Deferred；D 盘目录缺失不属于云端阻塞。
- 当前进入 R3.1：PP02 身份与更新源。
- R1/R2 未修改业务代码、未处理真实数据、未改变 PR #3 Draft 状态。

## 2026-07-29 R3.1｜PP02 身份与更新源

### 实际改动

- Desktop package name：`pp02-ai-daily-stock-analysis-desktop`。
- `appId`：`com.hanchanqaq.pp02.aidailystockanalysis`。
- `productName`：`PP02 AI Daily Stock Analysis`。
- 更新与 Release 仓库：`hanchanqaq-source/daily_ai_stock_analysis`。
- Windows installer、noinstall ZIP 与 macOS DMG 使用
  `pp02-ai-daily-stock-analysis-*` ASCII 产物前缀。
- CI 新增阻断型 `desktop-test` Job。

### 测试与 CI

- RED Run `30487941321`：47 pass、2 expected fail，证明新测试能识别官方旧身份。
- GREEN Desktop：49/49 pass。
- 首次 GREEN Run `30488079539`：macOS 发现 productName 下游固定路径遗漏。
- 根因修复后 Run `30488603501`：8/8 success。
- Windows 实机：Deferred；未以 CI 冻结门冒充实机验收。

### Judge

`PASS`

功能实现 Head Run `30488603501` 与文档收口 Head Run `30489293885` 均为
8/8 success；R3.1 已完成。


## 2026-07-29 R3.2｜手动默认与自动通知总开关

### 实际改动

- GitHub 每日分析 Workflow 移除默认 cron，只保留人工 `workflow_dispatch`。
- 新增产品级 `AUTO_NOTIFICATION_ENABLED=false`，并纳入配置 Registry 与 Web 设置帮助。
- CLI 主流程、市场复盘、运行时调度、Alert Worker、Web/API 分析及市场复盘均使用
  同一自动通知安全门；单次 `no-notify` 仍可进一步关闭。
- 总开关关闭时继续执行分析、保存报告和记录告警，只禁止外部自动发送。
- 用户明确点击“测试通知”仍可诊断已配置渠道，且不会反向开启自动通知。

### 测试与 CI

- RED Run `30491953318`：9 个预期失败，证明旧入口仍会自动发送或保留 cron。
- 首次 GREEN Run `30492811439`：产品行为已满足新契约；发现 1 条旧集成断言和
  1 处设置帮助元数据遗漏。
- 根因修正 Head `5316b5ea2ececd9aff0ced556e897f0738dad317`，
  Run `30493475960`：8/8 success。
- 后端：`4976 passed, 4 deselected`；Web、Docker、Desktop 单测及
  Windows/macOS 冻结/包门全部通过。

### Judge

`PASS`

R3.2 功能实现和实现 Head 完整 CI 已通过；收口 Head
`e879f0692d2bd330b166df561cd8a90d4542a5ce` 的 Run `30494219667`
再次 8/8 success。PR #3 保持 Draft，Windows 实机为 Deferred；Ready、合并、
Release、真实数据与真实通知渠道均未执行。


## 2026-07-30 R3.3｜官方账本上的快捷持仓

### 实际改动

- 新增目标持仓预览与确认 API；预览不写库，确认才写入。
- 确认在官方组合写事务中重新计算当前数量，拒绝过期预览和重复确认。
- 成功确认只追加一条官方交易事件；现金余额、持仓、成本和缓存失效继续由官方
  事件重放完成，未直接写 `portfolio_positions`。
- Web 新增“快捷持仓调整”，必须先预览差额，再人工确认写入。
- `web-gate` 新增 PortfolioPage 专项 Vitest 阻断步骤。

### 测试与 CI

- RED Run `30513770957`：后端 5 项预期失败、`4976 passed`；
  PortfolioPage 新测试预期失败、28 项旧测试通过。
- GREEN Head `311664759a51f8eb8ec700417b20c2e17fa155e8`，
  Run `30514223674`：8/8 success。
- 后端：`4981 passed, 4 deselected`；PortfolioPage：`29/29 passed`。
- Windows/macOS 冻结与 unsigned 包门通过；Windows 实机仍为 Deferred。

### Judge

`PASS`

R3.3 功能、事实源边界和实现 Head 完整 CI 已通过；收口 Head
`d4615cd407ba88ed43f9da129c8c89583358a98a` 的 Run `30514843576`
再次 8/8 success。PR #3 保持 Draft，未执行 Ready、合并、Release 或真实数据。


## 2026-07-30 R3.4｜股票专用备份与恢复

### 实际改动

- 导出带格式版本、PP02 身份、应用基线和数据库 Schema 元数据的 JSON。
- 只导出活跃/停用账户、交易、资金和公司行动；排除用户档案、基金、密钥、
  `.env`、日志和可重建派生数据。
- 导入先做严格字段、引用、ID、交易去重、日期和数值校验，再生成只读替换预览。
- 预览令牌绑定备份与当前账本摘要；任一方变化后拒绝旧令牌。
- 确认在官方写锁内用单事务整套替换；失败回滚，成功后由官方事件重放持仓。
- Web 必须选择 JSON、查看预览，再点击危险确认；导出只在用户明确点击后发生。

### 测试与 CI

- RED Run `30516073073`：后端 6 项预期失败、`4981 passed`；
  PortfolioPage 新增 2 项预期失败、29 项旧测试通过。
- 私有仓库免费 Actions 分钟耗尽导致 Run `30516696130` 零 Step 阻塞；
  公开前安全审计通过并获用户授权改为 Public 后，标准 Runner 恢复。
- 公开库重跑暴露 4 项 `date/datetime` 摘要序列化失败；Commit
  `8355d92a81b8f951a8ee7bcb703e89585cb8de5e` 从摘要源头做 ISO 规范化。
- 同轮 Web 暴露 1 条既有异步等待竞态；Commit
  `56c887502e218efa146a20ab86c928008e9035d6` 只修正测试等待，不改业务逻辑。
- 最终实现 Run `30519559480`：8/8 success。
- 后端：`4987 passed, 4 deselected, 50 warnings, 487 subtests passed`；
  PortfolioPage：`31/31 passed`；Web Build、Docker、Desktop 单测及
  Windows/macOS 冻结/包门全部通过。
- Windows 实机仍为 Deferred；未使用真实数据库、真实账户或真实备份。

### Judge

`PASS`

R3.4 功能、事务边界、排除范围和实现 Head 完整 CI 已通过；收口 Head
`a5b999717e57fe3c78da5c65adadcb1f05b71f95` 的 Run `30520589917`
再次 8/8 success。PR #3 保持 Draft，未执行 Ready、合并、Release、真实数据
导出或恢复。

## 2026-07-30 R3.5｜应用内手动周期报告与下周展望

### 实际改动

- 新增本周至今、上一周、下周展望、5周、10周、1个月和2个月七个手动入口。
- 通过正式历史服务聚合股票、ETF 与市场复盘，三个分区不混合统计。
- 下周展望复用 14 日内趋势、策略、置信、支撑/压力和风险字段；数据不足时不
  生成方向，并显示固定不足提示和免责声明。
- `period_outlook` 快照保存目标周、生成时间、来源记录 ID 和展望字段；进入下周
  后可与实际上一周汇总并列。
- Web 初次打开不发请求；只有用户选择周期并点击后才调用人工 POST。
- 未新增事实表、数据库列、模型调用、后台任务、cron 或自动通知。

### 测试与 CI

- 本地服务/API 专项：`18 passed`；旧历史/回测兼容：`3 passed`。
- 本地 Web 正式阻断套件：`55 passed`；Lint 和 Production Build 成功。
- 额外全量 Web 基线：`1044 passed, 2 skipped, 1 failed`；唯一失败为既有
  `AlertRuleForm` JP/KR 选项测试与相邻测试契约矛盾，未纳入 R3.5 改动。
- 实现 Head `4b563bc63e9638731f2a17ed25129de095046ef4` 的 Run
  `30525590779`：8/8 success。
- Backend：`5005 passed, 4 deselected, 51 warnings, 494 subtests passed`；
  Web：`55/55 passed`；Build、Docker、Desktop、Windows/macOS 包门全绿。
- Windows 实机仍为 Deferred；未使用真实历史、真实数据库、密钥或模型服务。

### Judge

`PASS — FINAL_HEAD_CI_PENDING`

R3.5 功能、事实源、手动边界、快照追溯和实现 Head 完整 CI 已通过；最终外部
回传仍要求本次文档收口 Head 自身 8/8。PR #3 保持 Draft，未执行 Ready、合并、
Release、`main`、真实数据、AI 调用、定时器或自动推送。

## WORK-002 / R3.6 执行回传（待最终 CI）

- 身份：Work2；Work1 CLOSED；PR #3 MERGED_AND_CLOSED。
- 起点：`0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- 发布分支：`agent/pp02-work2-r3-6-windows-portable-update`；新 Draft PR 编号和最终 CI 待发布后回填。
- 范围：便携身份、Release 资产、下载、ZIP/清单校验、事务计划、隐藏 PowerShell 助手、Desktop/Web 状态、Windows 候选与正式资产流程。
- Judge 上限：`IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`；`DRAFT_HOLD`。

### 发布结果

`PUBLISH_BLOCKED`（历史状态，现已解除）：本地 Commit `df3cee8` 已完成，且已通过 `make_pr` 准备 Draft PR 标题和完整正文；但容器没有 GitHub App 写入工具，本地 HTTPS push 又被网络代理以 `CONNECT tunnel failed, response 403` 拒绝，因此没有实际远程分支、PR 编号或 CI Run。不得把该状态表述为已发布或 CI 已通过。


## PR #5 Judge 阻断修复（历史，已关闭并由 PR #6 取代）

- 实际分支：`codex`；上一 Head `e5cdb70`；CI Run `30543513470` 为 8/8 success。
- CI 成功不覆盖 Judge 阻断；该 PR 当时用于修复助手资源、受控重定向、事务顺序、完整回滚、动态端口握手、严格身份和行为测试。
- PR #5 已关闭并标记为 superseded；当前唯一活动项为下方 PR #6。

## PR #6 最终收口

- 唯一活动 Draft PR：`#6`；分支 `codex-xbl3c5`；Base `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- 已验证 Head `71404954407a9a3a6362a398465fc822b1351c72`；CI Run `30547333980` 为 8/8 success。
- PR #5 已关闭，状态为 superseded，仅保留历史。
- 本轮仅增加 Windows CI 已验证便携 ZIP/SHA 候选 artifact，保留 14 天；它不是 GitHub Release。
- Judge：`IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`；`DRAFT_HOLD`。


## PR #7 R5 Windows 基础启动失败

- 候选：Head `d489a795b6089575a1fd61a27c9b28e2f3cb1b03`；Run `30564032072` 8/8 success；Artifact SHA-256 `203e41a35e2cd081a20640f514c9de417bd507cbd9b8a2f097a4d0bed36cda1a`。
- 实机结果：Electron loading shell 启动，冻结后端因 `ModuleNotFoundError: fake_useragent.data` / 浏览器数据解析失败退出，`/api/health` 为 `ECONNREFUSED`。
- 根因：PyInstaller 收集缺口、依赖上限缺失、探针只做静态导入、Artifact 上传前没有真实服务启动门。
- 旧候选已作废；新 Head 完整 CI 和新 Head-bound Artifact 前不得用于回滚模拟或重进 R5。
- Judge：`R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`。


## PR #8 CI 失败与最小修复

- CI Run：`30576678660`，失败。
- 根因：Windows 冻结 smoke 继承 `GITHUB_ACTIONS=true`，`main.py` 按既有安全条件不启动 serve-only 服务；仅观察进程存活不足以证明服务已启动。
- 修复：保留 `main.py` 保护条件；启动门保存/覆盖/恢复 `GITHUB_ACTIONS`、`PYTHONUTF8`、`PYTHONIOENCODING`，继续强制动态端口健康与主页均为 HTTP 200，并在 finally 清理进程树。
- 状态：`R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`；待新 Head 完整 CI 与新 Artifact。


## 2026-07-31 PR #9｜R5 Windows 最终真机验收

- 当前活动项：Draft PR `#9`；分支 `codex-2ka919`；Base `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- Windows 验收实现 Head：`958b64de78c50bd2ebb2f9b10a15409ee7040eea`；CI Run `30615265618` 为 8/8 success。
- 验收 Artifact：`8787591352`；外层 SHA-256 `ef4025618b3de9ba8cc45c487518e54340088a69b6eca388d4da5aaa25e30971`；内层便携候选 ZIP SHA-256 `8cc00e59414d418362418ba817271adfef81bbdadf4dfb92549db34555652e45`。
- Windows 隔离目录基础启动复验通过：PP02 主界面完整打开，`/api/health` 与主页均返回 HTTP 200，人工确认后正常关闭窗口；`R5_WINDOWS_BASIC_VALIDATION=PASS`。
- 隔离回滚模拟通过：故障注入确认部分替换会失败，正式候选 `portable-update-helper.ps1` 随后恢复首个被替换程序文件；`.env`、DB、WAL、SHM 与旧 manifest 哈希保持不变；隔离旧入口探针成功重启；`R5_WINDOWS_ROLLBACK_SIMULATION=PASS`。
- 模拟未访问正式安装目录、正式数据库、真实凭据或网络 Release；一次性验收截图不进入仓库。
- Judge：`PASS — R5 WINDOWS VALIDATION COMPLETED — DRAFT_HOLD`。
- PR 继续保持 Draft；未执行 Ready、Merge、main 直写、Tag、Release、真实数据或 R3.7。

## 2026-07-31 WORK-003 / R3.7 实现回传（证据提交最终 CI 待收口）

- 固定 Base：`main@097bb5d60aa42f13737ac4d9db2f582bde50f995`；活动项是
  独立 Draft PR `#11` / `agent/pp02-work3-r3-7-windows-secure-credentials`。
- 已完成版本化 DPAPI 密文 vault、`.env` 精确版本绑定、单活事务、窄 IPC、
  origin/navigation 校验、backend child environment 注入、敏感项全遮罩和无凭据导出。
- Windows secure mode 在 dotenv 解析前识别裸键、单/双引号键与可选
  `export`，畸形敏感导入明确拒绝且不显示值。
- Windows CI 改为 checkout 精确 PR Head，从 Head 派生一次性假凭据，并扫描仓库根、
  日志、最终 ZIP 和解包目录；未使用真实凭据。
- 四次独立安全复审最终未发现 Critical/Important。本地证据：Python/契约
  `340/340`，Desktop `80/80`，Web `127/127`，Lint/Build/治理/根目录扫描通过。
- 首轮固定远端 Head `b23c698b32b09749e907f1f4f7be1c056445a52e` 的 CI Run
  `30640475137` 已 8/8 success。Windows Job `91189042298` 明确 checkout 同一
  Head；`R3_7_WINDOWS_FAKE_CREDENTIAL_VALIDATION=PASS` 与最终
  `R3_7_WINDOWS_FAKE_CREDENTIAL_SCAN=PASS` 也都回报同一 Head。
- 同一 Job 上传 Head-bound Artifact `8798100943`；Actions 外层上传摘要为
  `64f01f7a4dc62fd6aac9d393da19dc07ea92fca8a395f862d3b0c5af3e62e254`。
- 当前只剩本证据提交自身的八项最终 CI；Judge 继续 `DRAFT_HOLD`，不得 Ready、
  合并、Tag、Release、使用真实凭据或进入后续阶段。

### 已复审实现 Head 远程证据

- Head `b23c698b32b09749e907f1f4f7be1c056445a52e` / Run `30640475137`：
  8/8 success；Backend `5027 passed, 4 deselected, 499 subtests passed`。
- Windows Job `91189042298`：精确 checkout 同 Head，`safeStorage` validation PASS 恰好一次，
  source 与 artifact 扫描均 PASS 且 Head 一致，日志不含派生假凭据明文。
- 本证据记录将生成最终证据 Head；该 Head 的完整 CI/Windows 复验结果将只更新
  Draft PR `#11` 元数据，避免再次改变 Head。
