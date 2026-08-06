# PP02 安全重建路线 R0–R7

## 2026-08-06 Work27 Windows Desktop AI configuration save validation repair

- Fixed Base is `main@4322e7dd…`, after PR #25 fixed Head `bae6c0ff…` passed
  Run `31037493697` and merged. Work27 uses one isolated branch and stops at a
  Draft PR plus exact-Head CI.
- The Desktop secure transaction dropped the pending secret before backend
  persistence, while the vault did not commit until that persistence succeeded.
  First-run channel saves therefore failed backend cross-field validation.
- The Web client also read `issues` from the response top level although FastAPI
  returns `detail.issues`, leaving only a generic failure message.
- Four initial expected RED failures cover fresh AIHubMix, `codex_cli` with a
  saved LiteLLM channel, historical default fields, and field-level error display;
  review added two expected RED counterexamples for notification URLs and bounded
  display. The LLM-only mask-placeholder/detail-unwrapping fix is GREEN at API `19/19` and Hook
  `5/5`. Full Web is `1081` passed / `2` skipped; lint, build, AI assets, and
  diff checks pass. Backend execution awaits exact-Head CI because the cloud
  runtime lacks locked `requests`; Draft PR, fixed-Head CI, and Windows lifecycle
  remain pending.
- No database, history, watchlist, period report, dependency, version, real
  credential, Ready, merge, Tag, or Release action is allowed.

## Historical entry | 2026-08-05 Work25 Windows frozen-backend startup timeout repair

- PR #24 fixed Head `f91576cb…` passed Run `31028088206` 8/8, then merged as
  `main@f813084…`. Main Run `31032267014` finished 7/8 and is not releaseable.
- Windows Job `92395692229` completed the frozen build and MiniRacer probe, then
  the backend exited at the inner hard-coded `3.0s` uvicorn startup deadline.
  The outer frozen verifier already polls HTTP readiness for up to 90 seconds;
  Desktop separately polls health for 60 seconds.
- Work25 uses TDD to replace only the conflicting inner gate with a bounded,
  monotonic condition wait. It must stop at one Draft PR and exact-Head CI;
  Ready, merge, Tag, Release, version/dependency changes, and real data remain
  prohibited.
- Local mutation RED reproduces the 3-second failure; delayed readiness after
  four simulated seconds is GREEN under the 30-second bounded helper. Related
  tests pass 32/32, including the real `main.start_api_server` connection, while
  complete backend and Windows artifact authority stays
  with the exact Draft PR Head CI.
- Draft PR #25 is Open Draft. Initial Head `65fddad2…` contains the exact
  reviewed implementation tree; the status-sync final Head and complete CI are
  pending.

## 2026-08-05 Work23 Windows strict-acceptance repair

- Existing Draft PR #23 remains based on locked `main@41fd6a6c…`. Work22 stays
  `FAIL`, bound to report SHA-256
  `30AC65C81E3F86E4CADBAEC9D2DBA95B432BA4DF8DBE81F12015857B9E5E39BE`.
- Head `8e08d58e…` / Run `30949323920` and Head `ca2415b8…` / Run
  `30952197181` each passed 7/8 Jobs and failed only because one official
  uninstall returned `0` without closing the live installed application.
- The new local rework packages a closed desktop/backend ownership manifest,
  derives the install root from the helper location, removes NSIS ownership
  parameters, supports the official uninstaller-directory fallback, and writes
  sanitized initial/final process-count evidence. The Windows contract must
  remove two exact owned processes and preserve an external same-name control.
- Local recovery gates pass Python packaging `26/26`, Desktop `83/83`, AI
  governance, and diff formatting. Next exact-Head full CI, one-shot installed
  lifecycle, candidate byte size/SHA-256, and unsigned identity remain pending.
  PR #23 must stay Draft; Ready, merge, Tag, Release, real signing material, and
  Work22 real data/checkpoints remain prohibited.
- Head `0eee6a7c…` / Run `30975730060` passed the new helper runtime contract,
  proving exact owned-process cleanup and external same-name preservation. NSIS
  then rejected an unused completion-label warning as fatal, while the candidate
  step masked the failed child build until lifecycle setup. Local contracts now
  require an explicit completion jump and immediate child-exit failure; next
  exact-Head CI and the installed one-shot lifecycle remain pending.
- Head `976db882…` / Run `30977516983` passed those build gates and the helper
  isolation contract. Installed evidence then reported five CIM-owned processes
  but zero graceful/forced actions, isolating the blocker to the redundant
  `Get-Process.Path` recheck. The local repair now revalidates PID/path with the
  same exact CIM source before acting; next exact-Head installed lifecycle and
  candidate identity remain pending.
- Head `c9aca280…` / Run `30988154439` passed that repair and reached zero after
  one official uninstall. The remaining failure was evidence-only: the standard
  uninstall check performed live cleanup, then a redundant `customUnInstall`
  helper call overwrote the first evidence with `initial=0`. The local rework
  keeps one required standard uninstall entry; next exact-Head lifecycle and
  candidate identity remain pending.

## 2026-08-04 Work20 complete backup and period persistence

- Work20 starts from locked `v3.29.2` `main@41fd6a6c…`; Work18, Work19, and
  Work19-A completion history is not revised.
- Complete backup is a canonical, SHA-256-bound, closed allow-list for formal
  analysis, stock portfolio events, saved period reports, structured records,
  and non-sensitive configuration. Configuration-only and portfolio-only backup
  flows remain separate. Fund is `not_applicable`.
- Restore requires a fresh preview and explicit confirmation, writes a recovery
  artifact before replacement, preserves concurrent writers, rolls back failed
  replacement, clears derived portfolio caches, and requires restart.
- Period reports use a canonical persisted table, survive restart, and can be
  loaded without generation. The v3.29.2 migration preserves existing analysis
  history and rolls back failed schema verification.
- Local verification passed. The controller owns push, one Draft PR,
  and exact fixed-Head Actions evidence. Work20 stays `DRAFT_HOLD`; no Ready,
  merge, Tag, or Release has occurred or is authorized.

## 2026-08-03 Work16 Windows frozen chip runtime closure

- 固定 Base 为 `main@568e26adf0e6393a7a0da1be57369535735cd05a`，独立 Draft
  PR #22 只处理 Work14 已证明的冻结筹码运行时缺口。
- 根因是 `mini-racer 0.14.1` 已由 AkShare 安装且 wheel 含 DLL/ICU，但 PyInstaller
  未收集间接包资产，既有 HTTP 健康门也未实例化 V8；不是依赖声明缺失。
- 3 个新增合同先 RED，最小收集、资产检查与离线 V8/筹码模块探针实现后 5/5 GREEN；
  同一共享验证器覆盖构建输出和最终解压 ZIP。依赖声明保持不变。
- 固定 Head `016e3408…` 的 Run `30831393819` 已 7 success、1 path-skipped；Windows
  直接冻结、重建和最终解压 ZIP 共 3 次实际筹码探针成功，独立复审无重要问题。
  Work16 裁决 `PASS — DRAFT_HOLD`。Ready、合并、Tag、Release、新闻、签名、真实
  凭据/数据和新增 Windows 真机动作均不在授权范围。

## 2026-08-03 Work15 PR #20/#21 mainline closure

- PR #20 固定 Head `e11946f528c9cb64beeec8b626ada457c02b0034` 已转 Ready，并以
  merge commit `25de369f8e12438a1ec1f3511c68256c471243e4` 合入 `main`。
- 新 main 的 CI Run `30822458701` 已 8/8 success，覆盖治理、后端、Docker、Web、
  Desktop、Windows 与 macOS；Auto Tag Run `30822458692` skipped，没有创建或移动 Tag。
- PR #21 的 7 文件 Work14 证据与 PR #20 的 5 文件产品改动无路径重叠。新 main 已
  通过双父 merge commit `25313cf0f23f0f4ab4922ea983bcd05b3577e23e` 非破坏同步；
  未 rebase、force-push 或丢弃历史。
- PR #21 最终固定 Head CI Run `30825436318` success，随后已合并；最终主线为
  `main@568e26adf0e6393a7a0da1be57369535735cd05a`，Work15 裁决
  `PASS — MAINLINE_CLOSED`。其余降级由独立后续 Work 处理。


## 2026-08-03 Work14 fixed-Head Windows acceptance

- 从 Draft PR #20 固定 Head `e11946f528c9cb64beeec8b626ada457c02b0034`
  构建未发布 Windows 候选。安装器版本 `3.29.1`、大小 `217,003,814` bytes、
  SHA-256 `DAD0CE0CCF8FC34F7318CD4E4F0CC37347C68A1A03E98D0CA7B048E393B18B33`、Authenticode `NotSigned`；没有安装、Tag 或 Release。
- 相关回归通过：Python `130 passed`、Desktop `82/82`、冻结后端动态端口健康。
  `600519` task/query/trace `1c4ae649232d40eaae7dcb6bb1b6981f` 完成并保存正式历史 ID `2`；
  候选后端重启与 Work12 原安装恢复后仍可重读，运行流保存节点成功。
- 大盘历史与周内周期聚合可重读。整体为 `PASS_WITH_DEGRADATIONS`：新闻 0 条，
  筹码链因冻结 `mini_racer.dll` 缺失失败；未签名和未执行候选安装生命周期保持未验收。
- Work12 原配置、数据库和日志没有被候选覆盖或清理，原应用已恢复 `health=ok`。
  证据 Head `da2290597e880c4c4a4c1c04e5cc548aa5542ea9` 的 Run `30821021196`
  已 success；最终裁决为 `PASS_WITH_DEGRADATIONS — DRAFT_HOLD`。
- Work14 结束时 PR #20/#21 均保持 Draft；其后 Ready/合并由 Work15 独立授权，不改变
  Work14 的历史裁决。候选本身仍未安装、Tag 或 Release。

## 2026-08-03 Work10–Work13 evidence reconciliation and history contract

- PR #19 已合并为 `main@f5c7f43359ec81e27395d9bb236ec1cab0f6dcc2`；annotated
  `v3.29.1` 剥离后指向固定产品 Commit `3e1311ee…`。正式发布 Run `30786838156`
  为 `5/5` success，Release 非 Draft/非 Prerelease，共 7 个资产。
- Work11 正式 Windows 安装、内置后端健康和清洁卸载通过，仅在验收临时目录保留安装器
  副本，裁决 `PASSED_WITH_RESIDUALS`。Work12 的 Codex CLI、行情复盘正式历史和周期
  报告通过，但 `600519` 没有正式个股历史，裁决 `FAILED_STOCK_ANALYSIS_HISTORY_MISSING`。
- Work13 采用方案 A。产品 Draft PR #20 仅在明确历史落库失败时阻止 API 个股任务假
  完成；本状态 Draft PR 仅同步 Work10–Work13 台账。两者从同一 main 建立；Work13
  结束时保持 Draft，后续主线收口事实见上方 Work15 记录。

## 2026-08-02 Work10-B Windows release cleanup race（historical pre-merge snapshot）

- PR #18 is merged as `main@91e174d30b3d0f2533b0db5df0245bf49778234f`. Desktop Release
  Run `30763628302` passed both macOS builds and the full installed Windows lifecycle, then failed
  after the final ZIP smoke when one-shot cleanup raced a transient `.pyd` file handle.
- Draft PR #19 applies bounded deletion retry only after the existing runner-owned path validation.
  Product code and fixed release Commit `3e1311ee…` are unchanged; Tag/Release operations remain
  forbidden. Local related contracts pass `25/25`; fixed Head `05e7a5da…` passed Run
  `30765409298` with seven applicable Jobs success and Web path-skipped, including the complete
  Windows package and installed lifecycle. PR #19 now waits for explicit merge authorization.

## 2026-08-02 Work10-A cloud release entry

- PR #17 is merged as `main@3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65`; post-merge Run
  `30747187504` passed all eight jobs. This fixed product commit remains the v3.29.1 target.
- Work10-A adds a recoverable manual cloud release entry to the existing Desktop Release workflow.
  Fixed implementation Head `e1a619c58670…` passed Run `30750806894` (seven applicable jobs
  success, Web path-skipped), and PR #18 was later merged as `main@91e174d…`.
- The first release attempt after that merge is recorded in Work10-B; v3.29.1 Tag/Release and
  Windows real-machine acceptance remain incomplete.

## 2026-08-02 Work9 fixed-Head closure

- Draft PR #17 implementation Head `db02221b92e210925044c5af5a4aacd2f08fcb4f` passed all
  eight jobs in Run `30745575186`.
- The final Windows ZIP, managed browser-data file, installer, first startup/health, exit, restart,
  second health/exit, uninstall and redacted diagnostic artifact all passed.
- PR #17 remains Draft and unmerged. v3.29.1 Tag/Release and Windows real-machine acceptance have
  not been performed. Next gate: explicit PR #17 merge authorization.

唯一当前状态见 [`../../_ai-dev/PROJECT_STATUS.md`](../../_ai-dev/PROJECT_STATUS.md)。
当前采用 `PP02-WORK-HANDOFF-002`：一个完整大段使用一个 Work 聊天；聊天不绑定
永久角色，不改显示名称，交接依赖唯一状态和 GitHub 事实，用户无需搬运施工单。

| 阶段 | 目标 | 当前状态 | 完成证据 |
| --- | --- | --- | --- |
| R0｜云端安全重建底座 | 官方 v3.28.0 + V1.5.6 控制层候选、Draft PR 与 CI | 完成 | PR #3 两轮 7/7 CI、最终 Judge |
| R1｜需求与旧功能迁移确认 | 保留、调整、不迁移及冲突裁决 | 完成 | `R1_REQUIREMENTS_MIGRATION_CONFIRMATION.md` |
| R2｜迁移正式候选计划 | 把 R1 决定拆成独立可验收切片 | 完成 | `R2_MIGRATION_EXECUTION_PLAN.md` |
| R3｜按优先级迁移旧 PP02 功能 | 每个切片单独测试、CI 和 Judge | 完成 | R3.1–R3.7 已由 PR #11 合入 `main@eb32298…` |
| R4｜数据库兼容与脱敏迁移演练 | 空库/人工假数据验证 | 完成 | PR #12 Head `f1b433a7…` / Run `30660971800` |
| R5｜Windows 本机验收 | 安装、启动、Web/Desktop 与安全默认值 | 完成 | Work2 / PR #9 真机启动与回滚模拟通过 |
| R6｜正式数据迁移 | 迁移经确认的真实数据 | 完成（无数据，跳过迁移） | Work6 `NO_FORMAL_DATA_FOUND`；旧项目和数据库从未建立 |
| R7｜替换 main 与 Release | Ready、合并、main、Tag、Release | 完成 | `v3.29.0` 已发布；PR #15 后续文档主线 Run `30697946093` 8/8 success |
| R7-Hotfix｜Windows 安装器补丁 | 修复 v3.29.0 引导崩溃并验收历史契约 | Work16 完成 / Draft Hold | PR #22 固定 Head CI 与 Windows 双层筹码探针通过；禁止自行 Ready、合并或发布 |

## 当前 R3 顺序

1. R3.1 PP02 身份与更新源：完成。
2. R3.2 手动默认与自动通知总开关：完成。
3. R3.3 官方账本上的快捷持仓：完成。
4. R3.4 股票专用备份与恢复：完成。
5. R3.5 应用内手动周期报告＋下周参考展望：完成。
6. R3.6 Windows 便携更新：完成。
7. R3.7 Windows 安全凭据：完成。

详细文件边界、契约和验收见
[`R2_MIGRATION_EXECUTION_PLAN.md`](R2_MIGRATION_EXECUTION_PLAN.md)。

## Work9 / PR #17 diagnostic evidence and Windows closure（2026-08-02）

- Work8 以 `COMPLETED_WITH_BLOCKER` 结束；固定诊断 Head `eae4b465…` 的 Run
  `30742085965` 为 7 成功、1 Windows 失败，且没有保留诊断 artifact。
- Work9 在当前分支 Head `9cb9a70e9176711096adf12ba5674c56d6f314d2` 正式接管，继续
  Draft PR #17。顺序锁定为诊断契约、最终 ZIP、固定 Head Windows CI、证据化根因、
  最小修复和完整 CI。
- 范围内 Commit/Push/CI 已授权；Ready、Merge、main、Tag、Release、真实数据/凭据
  和 Windows 真机动作仍受停止门约束。

## Work8 / R7 Windows installer hotfix（2026-08-01）

- v3.29.0 正式安装器来源、大小与 SHA-256 正确，但在 Windows 11 build 26200 上
  连续 2/2 于安装向导前以 `System.dll / 0xC0000005` 崩溃；R7 首次使用验收为 FAIL。
- 用户已授权 Work8、选择保留安装向导，并批准 Desktop 测试与 Windows/macOS
  打包/发布任务升级至 Node 22；独立 Web 门保持 Node 20。
- Draft PR #17 精确锁定 `electron-builder 26.15.7`，保留当前用户安装和目录选择，
  并让 PR/Release 共用隔离 install/start/uninstall 验证器。
- 本地 Desktop 与专项检查通过；固定 Head Run `30742085965` 的七个非 Windows
  任务成功，但 Windows 契约在真实安装生命周期前失败，且没有诊断 artifact。
- 未授权 Ready、Merge、main、`v3.29.1` Tag/Release 或最终 Windows 实机验收。

## Work7 / R7 最终完成（2026-08-01）

- PR #12、#13、#14 已按固定 Head 与完整 CI 门合并；发布提交为
  `49759dbd032f577d32e8e0f6670298f700e0f272`。
- 该发布提交的 `main` push CI 8/8 success；annotated Tag `v3.29.0`
  精确指向该提交。
- GitHub Release 非 Draft、非 Prerelease；Windows、macOS 共 7 个正式资产以及
  Docker/GHCR 发布成功。
- PR #15 已补充三语言来源声明并合并为
  `main@b4a0ec11da19b5552ce87dde1ece716f61fd5174`；合并后 Run
  `30697946093` 8/8 success，Tag 未移动。
- Work6 `NO_FORMAL_DATA_FOUND` 结论保持不变；R7 未执行任何真实数据库搜索、
  创建或迁移。
- R0–R7 路线已全部完成。下一目标必须建立新 Work 并重新授权；不得继承 Work7
  的 Ready、合并、`main`、Tag 或 Release 权限。

## Mainline Scope Lock（历史）

- 每个新大段使用独立分支和独立 Draft PR；当前 Work4 Base 为 `main@eb32298…`。
- Draft 不表示 Ready、可合并、可替换 `main` 或可发布 Release。
- 本 Work4 的 R4 只能使用空库或人工假数据；R6 正式数据必须单独授权。
- R5 Windows 验收只从固定 PR Head 新建隔离目录，不恢复或复用已消失的旧目录。

## Work2 / R3.6 Windows 便携安全更新（2026-07-30）

Work1 已永久关闭；PR #3 已合并且 R3.1–R3.5 已进入 main。Work2 从 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 以独立分支和独立 Draft PR 接管 R3.6。实现范围与证据见 `docs/pp02/R3_6_WINDOWS_PORTABLE_UPDATE_IMPLEMENTATION.md`。R5 Windows 真机验收仍为后续授权门，本轮不进入 R3.7。

## Work3 / R3.7 Windows 安全凭据（2026-07-31）

PR #11 最终 Head `173b3d3…` 完成 8/8 CI 和固定 Head Windows 假凭据验收，
并已合入 `main@eb32298…`。Work3 已关闭。

## Work4 / R4 数据库兼容与脱敏迁移演练（2026-07-31）

用户选择方案 A。当前先校正状态并关闭已由 PR #9 替代的历史 Draft PR #7/#8，
保留分支和历史；随后通过合成证明、临时数据库副本、现有股票备份恢复契约和失败
回滚探针形成可重复演练。只用空库和人工假数据，停在独立 Draft PR 完整 CI。

最终实现 Head `f1b433a7…` 的 Run `30660971800` 全部适用 Job success；PR #12
保持 Draft，Work4 Judge 为 `PASS — WORK4 COMPLETED — DRAFT_HOLD`。下一未启动大段
是 Work5 / R6 正式数据迁移授权与计划；真实数据库和数据仍需单独授权。
