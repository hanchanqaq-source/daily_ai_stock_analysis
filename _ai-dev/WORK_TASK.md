# WORK-023 | PR #23 Windows strict-acceptance failure repairs

## Work23 authorization and execution contract

```text
WORK_ID=WORK-023
BASE=41fd6a6c76c3e3b56211ef5fb4483d869122b568
BRANCH=agent/pp02-work20-full-backup-period-persistence
DRAFT_PR=23_OPEN_DRAFT
WORK22_EVIDENCE_REPORT_SHA256=30AC65C81E3F86E4CADBAEC9D2DBA95B432BA4DF8DBE81F12015857B9E5E39BE
WORK22_JUDGE=FAIL_LOCKED
AUTHORITATIVE_VERSION=3.29.3
REMOTE_FIXED_HEAD=PENDING_FIRST_PUSH
REMOTE_CI=PENDING_EXACT_HEAD
JUDGE=ACTIVE_DRAFT_HOLD
```

### Scope

- Make one normal official uninstall naturally close the product-owned process
  tree, without retries, orphan processes, or broad cleanup of unrelated paths.
- Normalize EXE file/product version, UI version, build information, and
  manifest to the single authoritative candidate version `3.29.3`.
- Prove the backup boundary for `fundamental_snapshot` and `stock_daily`.
  Include any non-rebuildable/user data; otherwise declare the exact cache
  contract in the manifest and verify safe restore-time clearing and rebuild.
- Assess Windows signing read-only. A credential-free policy interface and
  tests are allowed; real certificates, private keys, purchases, and CI secrets
  are prohibited and require a separate authorization gate.
- Run related regressions and complete CI on one exact PR #23 Head, then record
  the Windows candidate filename, size, and SHA-256 for the next strict retest.

### Acceptance and stop gates

1. Work22 remains `FAIL`; no lowered criterion or rewritten conclusion may be
   used to claim success.
2. The official uninstaller is executed once; installed app/backend processes
   must exit naturally, and cleanup is limited to evidence-confirmed product
   ownership.
3. `fundamental_snapshot` is included unless proven rebuildable, while an
   excluded `stock_daily` must have an exact no-user-data/rebuild manifest and
   deterministic restore behavior.
4. No Work22 real database, cold backup, complete export, or restore checkpoint
   may be read or modified.
5. PR #23 must remain Open Draft. Do not Ready, merge, write `main`, create
   another PR, tag, or release. Real signing identity acquisition is a separate
   authorization gate.

---

# Historical contract | WORK-020 / complete backup and period-report persistence

## Work20 authorization and execution contract

```text
WORK_ID=WORK-020
WORK_STATE=LOCAL_VERIFICATION_PASS_REMOTE_PENDING_DRAFT_HOLD
BASE=41fd6a6c76c3e3b56211ef5fb4483d869122b568
BRANCH=agent/pp02-work20-full-backup-period-persistence-pr
DRAFT_PR=PENDING_CONTROLLER
REMOTE_FIXED_HEAD=PENDING_CONTROLLER
REMOTE_CI=PENDING_CONTROLLER
JUDGE=DRAFT_HOLD
```

### Scope

- Add one strict, versioned, canonical complete-data backup for allow-listed
  formal PP02 state and non-sensitive configuration.
- Keep complete, configuration-only, and portfolio-event-only backup purposes
  visibly distinct.
- Require validation and a fresh preview before atomic replacement; write a
  recovery artifact first, preserve concurrent writers, roll back failures, and
  require service restart after success.
- Persist generated period reports in a canonical table, reload stored reports
  without generation, and migrate a v3.29.2 database without changing existing
  analysis-history rows.
- Document compatibility, exclusions, fund `not_applicable`, recovery, and
  uninstall/external-storage guidance.

### Acceptance and stop gates

1. Work20/related Python and affected Web suites pass, followed by the complete
   backend gate, Web lint/build, AI asset check, changed-Python compile, and
   `git diff --check`.
2. Canonical format/manifest/SHA, secret rejection, clean-install restore,
   restart persistence, recovery-before-replace, rollback, concurrent writer,
   migration, stored-report read, and user-visible distinction contracts have
   direct automated evidence.
3. Fixtures/diff contain no real credential, token, cookie, or ciphertext; only
   explicit synthetic markers are allowed. Final diff contains only Work20 and
   its named documentation/evidence files.
4. This phase may create a local evidence commit. The controller owns push,
   Draft PR creation, and exact fixed-Head Actions verification.
5. Do not Ready, merge, write `main`, tag, release, use real user data, or claim
   remote CI before controller evidence exists. Final Judge remains
   `DRAFT_HOLD`.

---

# Historical contract | WORK-016 / Windows frozen chip dependency closure

## Work16｜授权与执行合同

```text
WORK_ID=WORK-016
WORK_STATE=ACTIVE_WINDOWS_FROZEN_CHIP_CLOSURE
BASE=568e26adf0e6393a7a0da1be57369535735cd05a
BRANCH=agent/pp02-work16-windows-chip-runtime
DRAFT_PR=22
ROOT_CAUSE=EXISTING_MINI_RACER_RUNTIME_NOT_COLLECTED_OR_LOADED_BY_FROZEN_GATES
DEPENDENCY_CHANGE=FORBIDDEN
CURRENT_GATE=PASS_DRAFT_HOLD_NO_FURTHER_ACTION_WITHOUT_NEW_AUTHORIZATION
```

## 授权范围

- 先只读定位冻结候选缺少 `py_mini_racer/mini_racer.dll` 的根因，再从固定 Base 建立
  独立分支和 Draft PR。
- 测试先行增加 DLL/ICU 存在、MiniRacer 可加载求值及最终解压冻结产物筹码模块链契约。
- 只实施最小 PyInstaller 收集与验证修复；运行相关回归、完整固定 Head CI，并保持 Draft。
- 允许范围内普通 Commit、Push、Draft PR 更新及 CI 失败修复，不重复申请逐步授权。

## 已确认根因与设计

1. 固定主线 Windows CI 安装 `akshare 1.18.81`，自动解析 `mini-racer 0.14.1`；不是
   缺少依赖声明或安装失败。
2. 该 Windows wheel 已包含 `py_mini_racer/mini_racer.dll` 与 `icudtl.dat`，且其
   PyInstaller 运行时代码明确从 `_MEIPASS/py_mini_racer/` 读取二者。
3. 当前 `scripts/build-backend.ps1` 仅 `--collect-data akshare`，没有收集
   `py_mini_racer`；现有 import、fake-useragent 和 HTTP 健康探针不会实例化 V8。
4. 最小修复为收集现有 `py_mini_racer` 全部运行资产，显式检查 DLL/ICU，并让冻结
   EXE 在构建输出和最终解压 ZIP 上执行离线 MiniRacer 求值与筹码模块导入。

## 验收门

1. TDD RED 必须先证明现有脚本没有 `py_mini_racer` 收集、DLL/ICU 检查与 V8 探针。
2. GREEN 后相关合同全部通过，且 `requirements.txt` 和所有依赖版本声明保持不变。
3. Windows 固定 Head CI 必须在最终冻结输出与最终解压 ZIP 上通过筹码运行时探针。
4. 完整固定 Head CI 的全部适用 Job 成功后才可裁决；PR 始终保持 Draft。

## 非目标与停止门

- 不 Ready、不合并、不写 `main`，不创建、移动或删除 Tag/Release，不触发发布。
- 不处理新闻、签名、版本发布、真实凭据、真实用户数据或新增 Windows 真机动作。
- 不新增、移除、固定或升级依赖；如果最小打包修复无法复用现有依赖，立即停在证据与方案门。
- 不顺带修改 macOS 打包、筹码算法、数据源网络行为或其他已知残留。

---

# 历史任务合同｜WORK-015 / PR #20/#21 主线收口

## Work15｜授权与执行合同

```text
WORK_ID=WORK-015
WORK_STATE=ACTIVE_MAINLINE_CLOSURE
PR20_FIXED_HEAD=e11946f528c9cb64beeec8b626ada457c02b0034
PR20_MERGE_COMMIT=25de369f8e12438a1ec1f3511c68256c471243e4
PR20_MAIN_CI_RUN=30822458701
PR21=21
PR21_BRANCH=agent/pp02-work13-status-reconciliation
PR21_SYNC_MERGE_HEAD=25313cf0f23f0f4ab4922ea983bcd05b3577e23e
CURRENT_GATE=PR21_FIXED_HEAD_CI_THEN_READY_MERGE
```

## 授权范围

- 先将 PR #20 转为 Ready，并锁定固定 Head 合并至 `main`；核验新 main 的完整 Push CI。
- 只有新 main CI 通过后，才以普通双父 merge commit 将 main 同步到 PR #21 分支；
  禁止 rebase、force-push、丢弃或重写 Work14 证据历史。
- 只在 PR #21 原有 7 个台账/路线文件中，将 Work14 的 CI 待定状态更新为最终裁决，
  并记录 PR #20 合并及主线 CI 事实。
- PR #21 最终固定 Head CI 通过后，将其转为 Ready 并合并；最终 Run ID 只写入 PR
  元数据和 Work15 回传，不为记录 Run ID 再制造新 Head。

## 顺序门

1. PR #20 Head 必须仍为 `e11946f…`，原固定 Head CI 必须成功且范围不扩大。
2. PR #20 合并后的 main CI 必须完整成功；Auto Tag 必须保持 skipped。
3. PR #21 必须保留原 7 文件证据，使用非破坏 merge 同步新 main，不得强推。
4. PR #21 最终变更范围只允许原 7 个台账/路线文件叠加已合入 main 的 PR #20 内容。
5. PR #21 最终固定 Head CI 通过后才可 Ready 和合并。

## 非目标与停止门

- 不创建、移动或删除 Tag/Release，不触发发布工作流。
- 不处理 `mini_racer`、新闻、签名或新增 Windows 真机动作。
- 不扩大 PR #20 产品范围，不读取真实凭据、配置、数据库、日志或报告正文。

## 当前结果

- PR #20 已合并为 `main@25de369f…`；Run `30822458701` 已 8/8 success，Auto Tag
  Run `30822458692` skipped。
- 新 main 已通过双父 merge commit `25313cf0…` 非破坏同步到 PR #21；当前只待
  本 7 文件状态收口后的最终固定 Head CI。


---

# 历史任务合同｜WORK-014 / PR #20 固定 Head Windows 未发布候选验收

## Work14｜授权与验收合同

```text
WORK_ID=WORK-014
WORK_STATE=COMPLETED_DRAFT_HOLD
PRODUCT_PR=20
PRODUCT_FIXED_HEAD=e11946f528c9cb64beeec8b626ada457c02b0034
STATUS_PR=21
TARGET=UNPUBLISHED_WINDOWS_ACCEPTANCE_CANDIDATE
EVIDENCE_HEAD=da2290597e880c4c4a4c1c04e5cc548aa5542ea9
EVIDENCE_CI_RUN=30821021196
CURRENT_GATE=COMPLETED_PASS_WITH_DEGRADATIONS_DRAFT_HOLD
```

## 授权范围

- 先核对 Windows 环境及 Work12 安装、配置、数据库和日志现场。
- 从 PR #20 固定 Head 构建未发布 Windows 候选，不替换 Work12 原安装。
- 重跑 `600519` 正式历史闭环及相关 Python/Desktop、冻结健康、大盘历史和周期报告
  回归；取得真实证据后只补入现有 Draft PR #21 并运行 CI。
- 允许本 Work 所需的精确进程停启、临时候选配置副本/Junction 建立与移除，以及
  恢复 Work12 原应用；不得清理或覆盖 Work12 配置、数据库和日志。

## 验收门

1. 候选源码、build revision 与 PR #20 固定 Head 精确一致；记录版本、大小、SHA 和签名。
2. `600519` 不能只凭任务完成：必须有正式历史、history 诊断成功、运行流保存成功，
   且候选重启和 Work12 恢复后仍可重读。
3. 相关回归必须记录真实通过数；数据源/冻结依赖降级必须保留，不能升级为全量 PASS。
4. Work12 原安装恢复健康；配置、数据库、日志不被候选清理或旧副本覆盖。
5. PR #21 只改 7 个状态/路线文件并完成固定 Head CI；Work14 结束时 PR #20/#21 均保持 Draft。

## 非目标与停止门

- 不 Ready、不合并、不写 `main`，不创建或修改 Tag/Release。
- 不安装或发布 Work14 候选，不读取或输出凭据，不上传配置、数据库、日志或报告正文。
- CI 完成后停止；任何产品修复、依赖补包、签名、候选安装生命周期或新增真机动作
  都需要新的明确授权。

## 当前结果

- 真实 `600519` 历史闭环与重启持久化通过；相关测试与聚合通过。
- 当前 Judge 上限为 `PASS_WITH_DEGRADATIONS`：新闻 0 条、筹码冻结 DLL 缺失、
  安装器未签名且候选安装生命周期未执行。
- Work12 原应用已恢复 `health=ok`，数据库和日志存在；PR #21 证据 Head
  `da229059…` 的 Run `30821021196` 已 success。
- Work14 最终 Judge 为 `PASS_WITH_DEGRADATIONS — DRAFT_HOLD`；其后 Ready/合并授权
  属于 Work15，不回写改变 Work14 当时的授权边界。


---

# 历史任务合同｜WORK-010 / v3.29.1 发布与 Windows 真机验收

## Work10-B｜Windows 发布临时目录清理竞态

```text
WORK_ID=WORK-010
WORK_STATE=ACTIVE
BASE=91e174d30b3d0f2533b0db5df0245bf49778234f
BRANCH=agent/pp02-work10-release-cleanup
TARGET_RELEASE=v3.29.1
PRODUCT_RELEASE_COMMIT=3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65
FAILED_RELEASE_RUN=30763628302
DRAFT_PR=19
CURRENT_GATE=PR19_MERGE_AUTHORIZATION
```

## 授权范围

- 只修改现有 Desktop Release 工作流、直接回归测试和 PP02 必需台账/Changelog。
- 对已通过 runner-owned 路径校验的 Windows 最终 ZIP 临时解压目录增加有限删除重试。
- 允许正常 Commit、远端分支、Draft PR #19、完整 GitHub Actions CI 和范围内失败修复。

## 安全与失败关闭

- 保留现有 `RUNNER_TEMP` 子目录与固定目录名前缀校验；不得放宽删除目标。
- 最多尝试 15 次，每次失败等待 1 秒；成功后立即继续。
- 超过重试上限仍删除失败时必须抛错；不得使用静默忽略、无界循环或删除更大目录。
- 解压前和最终 `finally` 清理必须使用同一受限逻辑。

## 非目标与停止门

- 不修改产品代码、产品依赖、安装器、后端、Desktop 运行时或固定产品 Commit。
- 不 Ready、不合并、不写 `main`、不创建或修改 Tag/Release，不执行 Windows 真机操作。
- Draft PR #19 最终 Head 完整 CI 通过后停止并请求后续明确授权。

## 验收

1. TDD RED/GREEN 证明重试次数、等待、两处调用、安全路径先决条件和 fail-closed。
2. 相关合同、Workflow YAML、AI 资产、格式和敏感内容检查通过。
3. Draft PR #19 保持 Draft，完整 CI 绑定最终 Head 且全部适用 Job 成功。

## 固定 Head Judge

- Head `05e7a5dac1064b644cb5a01fa9300a4af109ecdb` 的 Run `30765409298` 已完成：七个
  适用 Job success，Web Gate 因未改 Web 路径正常 skipped。
- Windows 最终 ZIP、安装器合同、安装、首次启动、退出、重启、卸载、诊断上传、
  假凭据泄漏扫描和候选上传全部成功。
- 当前必须停止在 PR #19 合并授权门；Ready、合并、main、Tag、Release 和真机仍未授权。

---

## 历史任务合同｜Work10-A 云端发布入口修复

```text
WORK_ID=WORK-010
WORK_STATE=ACTIVE
BASE=3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65
BRANCH=agent/pp02-work10-release-entry
TARGET_RELEASE=v3.29.1
PRODUCT_RELEASE_COMMIT=3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65
CURRENT_GATE=READY_MERGE_TAG_RELEASE_AUTHORIZATION
DRAFT_PR=18
PR_CI_HEAD=e1a619c5867037bf569be5d741194ff792ce948b
PR_CI_RUN=30750806894
```

## 授权范围

- 在独立分支最小改造现有 `.github/workflows/desktop-release.yml`，保留 annotated Tag
  push 兼容路径，并新增可从固定产品 Commit 完成发布的手动云端入口。
- 允许契约测试、台账、Changelog、正常 Commit、远端分支、Draft PR、PR CI 与范围内
  CI 修复。
- 手动入口必须接收 SemVer Tag、完整 40 位 Commit SHA 和 annotated Tag message。
- Windows/macOS 必须 checkout 固定产品 Commit；只有 publish Job 可使用
  `contents: write`，并在同一次 Run 内完成 Tag 验证/创建与 Release。

## 安全与恢复契约

- 目标 SHA 必须直接标识 Commit object 且可从 `origin/main` 到达；工作流修复后的新
  main Head 不得替代固定产品 Commit。
- Tag 不存在时只能创建 annotated Tag；已有正确 annotated Tag 可恢复，其 Tag object
  必须直接指向目标 Commit 且内部 Tag 名匹配；lightweight、嵌套或错 Commit Tag、已有
  Release 或无法确认 Release 状态必须失败。
- 禁止 force、移动、删除或覆盖 Tag；任一构建失败时不得创建 Tag。
- Tag 创建与 Release 必须在同一次手动 Run 内闭环，不依赖默认令牌推送 Tag 后再次
  触发另一条工作流。

## 非目标与停止门

- 不修改产品业务代码，不新建平行发布系统，不增加 main push/定时自动发布，不使用
  PAT、真实 Token 或用户凭据。
- 当前不授权 Ready、Merge、main 写入、v3.29.1 Tag/Release、Windows 真机操作、
  真实数据或其他版本。
- Draft PR 固定 Head CI 全部通过后，必须停止并请求一次“Ready＋合并＋发布”授权。

## 验收

1. 四组确定性契约覆盖输入、固定 Commit、并发、Tag/Release 安全、Job 顺序与权限。
2. Workflow YAML、相关打包回归、AI 资产、格式和敏感内容检查通过。
3. Draft PR 保持 Draft，真实 CI 绑定固定 PR Head。
4. Judge 上限为 `LOCAL_GATES_PASS — DRAFT_PR_AND_CI_PENDING`，直到远端证据取得。

---

# 历史任务合同｜WORK-009 / PR #17 诊断证据链修复与 Windows 安装闭环

## 当前任务身份

```text
WORK_ID=WORK-009
WORK_STATE=ACTIVE
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=66666352e953d90becce420da7d35b649516af76
BRANCH=agent/pp02-work8-r7-installer-fix
TAKEOVER_HEAD=9cb9a70e9176711096adf12ba5674c56d6f314d2
TARGET_RELEASE=v3.29.1
DRAFT_PR=17
FAILED_RELEASE=v3.29.0
SCOPE_DRIFT=FALSE
PREVIOUS_DIAGNOSTIC_HEAD=eae4b46501c9a183dda20d2975121987e676943b
PREVIOUS_CI_RUN=30742085965
CURRENT_GATE=FULL_CI_PASS_AWAITING_PR17_MERGE_AUTHORIZATION
```

## 授权结果

- Work9 承接 Work8，不重启路线，不推翻已有证据支持的 builder/Node 22 修复，继续
  使用现有 Draft PR #17。
- 允许修改诊断、Windows 打包和后端启动相关代码，建立 RED/GREEN 测试，正常
  Commit/Push，并运行固定 Head CI。
- 必须先证明诊断位于安装清理目录之外、清理后仍存在、失败时上传仍执行且内容已
  脱敏；证据链通过前不得修改后端根因。
- 诊断链修复后必须验证最终候选 ZIP，而不是只验证 `win-unpacked`。必须核验
  `fake_useragent/data/browsers.jsonl`、managed files 清单及复制/清理链路。
- 取得有效 artifact 后，记录直接错误、组件边界、根因、开发/打包差异与最小复现；
  再以一个失败测试、一个假设和一个最小修复推进。
- PR #17 最终门包括安装包/ZIP、安装、首次启动、内置后端健康、退出、再次启动、
  卸载、诊断 artifact 和全部 CI。完成后停在合并授权门。

## 非目标与硬边界

- 不 Ready、不合并、不写 `main`、不创建 Tag/Release、不发布 `v3.29.1`。
- 不宣布 Windows 真机验收通过；需要本机操作时停止申请授权。
- 不读取、输出或上传真实 `.env`、Token、API Key、Webhook、密钥、数据库或用户数据。
- 不集中升级 Electron/npm 安全依赖，不引入 Dependabot、完整 Web/Playwright 门、
  代码签名、公证、正式图标、PP02 总控 Skill 或真实业务数据闭环。
- 若诊断仍无法保留或根因超出 PR #17，立即停止，不做猜测式补丁。

## 当前证据门结果

- Fixed diagnostic Head `b4684f0be8a818b5b29688933e2a738663e1a638`, Run
  `30744115030`: seven non-Windows jobs passed; Windows PowerShell diagnostic contract, final ZIP
  manifest/file check, final-ZIP frozen backend start, installation and registration passed.
- Head/Run-bound diagnostic artifact `8832664000` was preserved and uploaded. Both installed child
  stderr and the independent backend probe identify the same NLTK 3.10.1 bundled-`xml` CWD block.
- The only product fix changes the packaged backend working directory from the runtime/install root
  to its database parent directory so the CWD is no longer an ancestor of the PyInstaller bundle.
  A separate verifier gate now requires exit, restart readiness, second exit and uninstall order.
- Local gates pass; the current gate is a new fixed-Head full CI. Merge/Release/real-machine gates
  remain closed.

## 固定 Head Judge

- Head `db02221b92e210925044c5af5a4aacd2f08fcb4f`, Run `30745575186`: all eight CI jobs
  passed. Windows proved the final ZIP, installation, first startup/health, exit, fresh restart and
  health, second exit, uninstall and the always-uploaded diagnostic artifact.
- The current Work gate is explicit authorization to merge Draft PR #17. Ready, merge, Tag,
  Release and Windows real-machine acceptance remain unauthorized.

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 待决产品问题 | 0；用户已给出完整顺序、范围、停止门和验收标准 |
| 当前事实 | PR #17 Draft；Head `9cb9a70…`；Run `30742085965` 为 7 成功、1 Windows 失败 |
| 第一假设 | Windows PowerShell 5.1 执行诊断清单时不支持 `[IO.Path]::GetRelativePath`，导致摘要写入前再次失败 |
| 允许进入 Build | 是；必须测试先行并先修诊断证据链 |
| 发布授权 | 未授予 |

---

# 历史任务合同｜WORK-008 / R7 安装器缺陷修复与 v3.29.1 补丁发布

## 当前任务身份

```text
WORK_ID=WORK-008
WORK_STATE=COMPLETED_WITH_BLOCKER
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=66666352e953d90becce420da7d35b649516af76
BRANCH=agent/pp02-work8-r7-installer-fix
TARGET_RELEASE=v3.29.1
DRAFT_PR=17
FAILED_RELEASE=v3.29.0
SCOPE_DRIFT=FALSE
DIAGNOSTIC_HEAD=eae4b46501c9a183dda20d2975121987e676943b
LATEST_CI_RUN=30742085965
CURRENT_GATE=ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT
```

## 2026-08-02 corrective authorization result

- The required diagnostics-only fixed Head was run exactly once as Run `30742085965`.
- Seven jobs passed. Windows candidate construction passed, but the verifier contract failed before
  the installed lifecycle could run.
- The `if: always()` diagnostic upload executed and failed because no diagnostic files had been
  preserved; consequently no downloadable Windows diagnostic artifact exists.
- The installed backend root cause is not established. Further patches and CI are stopped pending
  user direction; Draft/merge/release/real-machine acceptance gates remain closed.

## 用户结果

用户已授权启动 Work8，并选择 `A｜保留安装向导`。修复必须保留选择安装目录、
当前用户安装、正常卸载、安装版自动更新和免安装 ZIP；不得通过删除安装向导来绕过
缺陷。用户随后批准设计勘误：Desktop 测试、Windows/macOS 打包和 Desktop Release
任务升级至 Node 22，独立 Web 门保持 Node 20。

## 根因与设计

- v3.29.0 正式安装器来源、大小、SHA-256 和版本信息通过；Windows 11 build 26200
  上连续 2/2 在引导阶段以 `System.dll / 0xC0000005` 崩溃。
- 根因与 electron-builder #8536 / #9564 的 24.x NSIS `System::Store()` 竞态一致。
- 批准设计见
  `docs/superpowers/specs/2026-08-01-work8-windows-installer-hotfix-design.md`。
- 构建链只精确升级 `electron-builder` 到 `26.15.7`；Electron 和业务运行依赖不顺带升级。
- `@electron/rebuild 4.x` 要求 Node `>=22.12`，因此所有 Desktop 构建路径使用 Node 22；
  既有便携测试显式声明此前由旧 builder 偶然带入的测试依赖 `archiver 5.3.2`。
- 新增可复用 Windows 验证器，并在 PR Windows 打包门和正式 Desktop Release 门中
  真实执行 install/start/uninstall。

## 范围

- 按已批准设计先写实施计划，再执行 RED→GREEN。
- 更新 Desktop manifest/lockfile、Windows installer verifier、专项测试、CI 和 Release workflow。
- 保留现有 frozen backend、portable ZIP、Head binding 与假凭据扫描。
- 更新 Desktop 打包文档、Unreleased Changelog 和四份 PP02 台账。
- 创建一个独立 Draft PR，完成固定 Head 全量 CI 和 Windows 安装候选验证。
- CI 失败只允许在当前最小范围内修复，不扩展业务功能。

## 非目标与硬边界

- 不覆盖、移动、删除或重打 `v3.29.0` Tag/Release。
- 未经单独授权，不 Ready、不合并、不写 `main`、不创建 `v3.29.1` Tag/Release。
- 不读取、导入、删除或修改真实数据库、持仓、分析历史、`.env`、API Key、
  Token、Webhook 或密码。
- 不改后端/Web 业务逻辑、数据库 Schema、分析行为、自动通知默认值或便携更新事务。
- 不把云端 Windows CI 冒充最终 Windows 正式版首次使用验收。
- 不引入 Electron 27.x 或 electron-builder 27.x 预览版。

## 验收标准

1. RED 证明确切缺口：旧 builder line、缺失 verifier、PR/Release workflow 未执行安装器。
2. manifest 精确锁定 `electron-builder 26.15.7`，lockfile 与 Node 22/npm 一致；
   独立 Web 门继续使用 Node 20。
3. Windows verifier 对唯一安装器执行隔离 install/start/uninstall，稳定输出证据并
   仅清理自身临时目录。
4. PR Windows Job 同一 Head 的安装器、便携 ZIP、冻结后端和假凭据扫描全部通过。
5. macOS 包门与 Desktop 单测通过，完整 CI 无阻断失败。
6. Draft PR body 与 diff、根因、验证、风险和回滚一致。
7. Work8 Judge 上限为 `IMPLEMENTATION_PASS — DRAFT_HOLD`；Ready/Merge/Release
   与最终 Windows v3.29.1 实机验收分别等待授权。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 用户决定 | `A｜保留安装向导` |
| 待决产品问题 | 0；功能取舍已锁定 |
| 根因证据 | 与上游 #8536/#9564 高一致，且新 v26 模板已移除竞态路径 |
| 当前门 | `ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT`；Run `30742085965` 无诊断 artifact |
| 允许进入 Build | 否；在用户重新授权前停止追加补丁和 CI |
| 发布授权 | 未授予 |

---

# WORK-007｜R7 主线合并与正式发布任务合同

## 当前任务身份

```text
WORK_ID=WORK-007
WORK_STATE=COMPLETED
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=eb32298c8f3cbec2ff400dda37d3267a7181af40
TARGET_RELEASE=v3.29.0
SCOPE_DRIFT=FALSE
```

## 用户结果

用户正式启动 `Work7｜R7 主线合并与正式发布`，并选择方案 A：承接官方
`v3.28.0`，把本轮新增功能作为 `v3.29.0` 正式发布。选定后连续执行主线合并、
新 `main` CI、annotated Tag、GitHub Release 和正式产物验收，不再拆成逐项确认。

## 范围与执行顺序

1. 复核 PR #12/#13 的固定 Head、依赖关系、CI 与发布说明。
2. 完成最小 R7 状态、Changelog 和 PP02 Release notes 身份收口，并验证新 Head。
3. 先合并 PR #12，再把 PR #13 Base 改为 `main`；PR #13 新固定 Head CI 通过后合并。
4. 验证最终 `main` push CI，且 Tag 必须精确指向该已验证 `main` Head。
5. 创建带说明的 annotated Tag `v3.29.0` 并推送，触发正式发布工作流。
6. 验收 GitHub Release、Windows 安装/免安装更新资产、macOS x64/arm64 DMG、
   SHA-256、自动更新元数据以及 Docker/GHCR 发布结果。

## 非目标与硬边界

- 不读取、搜索、创建或迁移任何真实数据库；Work6 已裁决 `NO_FORMAL_DATA_FOUND`。
- 不读取、输出或上传真实 `.env`、Token、API Key、Webhook、密码或用户数据。
- 不强推 `main`，不创建 `v3.29.0` 以外的 Tag/Release，不扩大功能范围。
- 任一固定 Head、PR CI、`main` CI、Tag 绑定或正式产物门失败时立即停止在对应 Judge。

## 验收标准

1. PR #12/#13 均以预期固定 Head 和完整 CI 证据进入 `main`，依赖顺序无误。
2. 新 `main` push CI 全部适用 Job 成功，Tag 对象最终指向该精确 Commit。
3. `v3.29.0` 为 annotated Tag，注释非空，Release 非 Draft/非 Prerelease。
4. Windows 与 macOS 三类正式安装资产齐全；Windows 免安装 ZIP 与 SHA-256 配对、
   `latest.yml`、blockmap 和版本/文件名一致性通过发布工作流。
5. Docker/GHCR 正式发布成功；缺少可选 Docker Hub 凭据只可按工作流明确记录为 skipped。
6. 状态、路线、回传、Changelog、GitHub Release 和可验证 GitHub 事实一致。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 用户决定 | `A｜v3.29.0（推荐）` |
| 待决产品问题 | 0 个；版本和执行链已锁定 |
| 数据风险 | R6 无正式数据可迁移；R7 禁止任何真实数据操作 |
| Judge 上限 | `PASS — v3.29.0 RELEASED`，但必须逐门取得真实证据 |
| 允许进入执行 | 是；Ready/Merge/main CI/Tag/Release `v3.29.0` 已精确授权 |


## 最终执行结果

- PR #12、#13、#14 已按固定 Head 与 CI 门进入 `main`；发布提交为
  `49759dbd032f577d32e8e0f6670298f700e0f272`。
- 该发布提交的 `main` push CI 8/8 success 后创建 annotated Tag
  `v3.29.0`；Tag 精确指向发布提交且注释非空。
- GitHub Release 非 Draft、非 Prerelease；Windows 安装/免安装资产、SHA-256、
  macOS arm64/x64 DMG 与 Docker/GHCR 发布均成功。
- PR #15 在发布后补充三语言项目来源声明并修正仓库链接，合并为
  `main@b4a0ec11da19b5552ce87dde1ece716f61fd5174`；Run
  `30697946093` 8/8 success。
- Work6 `NO_FORMAL_DATA_FOUND` 边界保持不变；未读取、搜索、创建或迁移真实
  数据库，未使用真实凭据。
- 最终 Judge：`PASS — v3.29.0 RELEASED — WORK7 COMPLETED`。本合同不授权任何
  后续 Work、真实数据、其他 Tag/Release 或新的 `main` 写入。

---

# 历史任务合同｜WORK-005 / R6-A 正式数据安全只读盘点工具

## 当前任务身份

```text
WORK_ID=WORK-005
WORK_STATE=COMPLETED
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=a220e9e146e14722561bc084ec4e5306b30d36c7
BRANCH=agent/pp02-work5-r6-inventory-tool
SCOPE_DRIFT=FALSE
```

## 用户结果

用户已批准“按这个设计做”：在云端开发一个 Windows 原生运行的旧数据库安全体检
工具。工具只接受人工明确指定的一个 SQLite 文件，先做双备份，再只读统计四张正式
股票事件表；不搜索整机、不显示行值、不迁移、不覆盖、不上传。

## 范围

- 固定并执行 `docs/pp02/R6_FORMAL_DATA_INVENTORY_TOOL_DESIGN.md` 与实施计划。
- 新建独立标准库服务与薄 CLI，不导入应用数据库模型、配置、恢复或迁移模块。
- 双备份主文件及已有 WAL/SHM，校验哈希与源未变化后才检查临时副本。
- 只执行 SQLite 完整性、固定 Schema 和四张正式表的 `COUNT(*)`。
- 只输出三种裁决、四项计数和固定隐私证明；错误只含稳定代码。
- 测试仅动态创建空库与人工假数据库；完成专项、关联回归、完整本地门和固定 Head CI。
- 已授权范围内正常 Commit、Push、一个 Draft PR、CI 与范围内修复。

## 非目标与硬边界

- 不读取、复制、上传、迁移或修改任何 Windows 真实数据库、真实备份或真实数据。
- 不搜索 Windows 整盘或个人目录，不输出账户名、股票代码、金额、日期、备注或行值。
- 不迁移基金、用户档案、旧平行持仓、派生持仓、缓存、日志、设置或凭据。
- 不修改 R4 迁移演练器，不新增依赖，不放宽 Workflow 或仓库权限。
- 不 Ready、不合并、不写 `main`、不 Tag、不 Release、不进入 R7。

## 验收标准

1. RED 测试在实现缺失时按预期失败，GREEN 覆盖完整安全契约。
2. 两套备份逐文件哈希一致，源主文件与 sidecar 指纹前后一致。
3. 检查只针对临时副本，SQLite 为只读/query-only，四张固定表只执行计数。
4. 路径、journal、部分 Schema、损坏库、源变化和备份不一致全部 fail closed。
5. 报告和 CLI 不泄漏人工数据、路径、SQL、Schema 或异常正文。
6. 完整本地门与独立 Draft PR 固定 Head CI 通过；PR 保持 Draft。
7. 最终 Judge 上限为云端工具实现通过，Windows 真实盘点仍待精确授权。

## 本地实现与验证证据

- 服务 RED：18 项新契约因模块缺失而失败；CLI RED：7 项新契约因脚本缺失而失败。
- 独立审查后新增 5 项 RED 回归，分别证明备份中途回滚日志、清理失败、检查副本
  完整性状态、未知参数和重复源参数问题；修复后专项 `31 passed`，R6-A、R4 演练和
  组合备份联合回归 `50 passed, 4 warnings`。
- 最终代码完整 CI 等效后端门：`5070 passed, 1 skipped, 4 deselected, 48 warnings,
  499 subtests passed`；语法、严重 Flake8、确定性检查、AI 资产与格式门均通过；
  独立复核 APPROVE，无剩余 Critical、Important 或 Minor。
- 最终固定 Head `50dd04ca5a49a6e54de01e2d28ce598f690d9931` 的 CI Run
  `30691233934` 全部适用 Job success；尚未执行 Windows 真实盘点。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 用户决定 | `采用建议，云端开发盘点工具`，随后批准 `按这个设计做` |
| 待决产品问题 | 0 个；设计已固定显式路径、双备份、临时只读副本方案 |
| 数据风险 | 云端真实数据库/真实数据禁止；只用空库和人工假数据 |
| Judge 上限 | `CLOUD_TOOL_IMPLEMENTATION_PASS — WINDOWS_REAL_INVENTORY_PENDING_AUTHORIZATION` |
| 允许进入 Build | 是；按 RED→GREEN 连续执行 |

---

# 历史任务合同｜WORK-004 / R4

## 当前任务身份

```text
WORK_ID=WORK-004
WORK_STATE=COMPLETED
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=eb32298c8f3cbec2ff400dda37d3267a7181af40
BRANCH=agent/pp02-work4-r4-database-rehearsal
SCOPE_DRIFT=FALSE
```

## 用户结果

把“一个大段一个 Work”的自动接力规则写入现有唯一框架，并在同一 Work4 内只用
空库和人工假数据完成 R4 可重复兼容检查、股票事件迁移、脱敏排除和失败回滚演练；
建立独立 Draft PR 和完整 CI 后停下。

## 范围

- 校正 Work3/R3.7 已合并事实和 R4 路线；关闭被 PR #9 替代的 PR #7/#8，保留分支。
- 更新 `AGENTS.md` 和现有状态/交接/任务/回传文件，不建立第二套状态中心。
- 冻结 R4 设计和实施计划，按 RED→GREEN 实现可重复脚本与专项测试。
- 输入只接受空 SQLite 或与 SHA-256 绑定的人工合成证明；源文件只读且保持不变。
- 复用 `DatabaseManager` 与 `PortfolioBackupService`，只迁移正式股票事件账本。
- 输出安全报告并验证失败回滚；运行本地门禁、Draft PR 完整 CI 和 Judge。

## 非目标与硬边界

- 不读取、复制、脱敏、打开或迁移真实数据库、真实备份、真实账号或真实凭据。
- 不迁移基金、用户档案、多用户隔离、旧快捷持仓表、派生持仓、缓存或日志。
- 不修改聊天显示名称，不要求用户跨聊天复制施工单或完成报告。
- 不 Ready、不合并、不写 `main`、不 Tag、不 Release、不进入 R5/R6/R7。

## 验收标准

1. 新自动接力规则只有一个活动真源，旧窗口锁明确 Superseded。
2. RED 测试在实现缺失时按预期失败；GREEN 覆盖空库、合成混合库、拒绝边界和回滚。
3. 源 SHA-256 前后一致；目标只含现有正式股票事件导出的允许内容。
4. 报告不含行值、备份正文或构造的假敏感值。
5. 本地完整后端门和 Draft PR 固定 Head 完整 CI 通过。
6. Work4 只在状态、GitHub、测试和 CI 全部一致后宣布结束。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 用户决定 | `选A`，完整启动 Work4 |
| 待决产品问题 | 0 个；技术方案复用现有事实源和恢复契约 |
| 数据风险 | 真实数据库/数据禁止；只接受空库和人工合成证明 |
| Judge 上限 | `PASS — DRAFT_HOLD` |
| 允许进入 Build | 是；先完成设计/计划检查点和 RED |

## 完成状态

- Work4 已在 Draft PR #12 完成范围内实现、测试、CI 和 Judge。
- 本合同不继续授权 R6、真实数据库/数据、Ready、合并、Tag 或 Release。
- 下一 Work 尚未启动；用户新开同项目聊天后只发送“下一步”。

---

# 历史任务合同｜WORK-PP02-CLOUD-REBUILD-001

## 任务身份

```text
CHAT_ROLE=WORK
WORK_ID=WORK-PP02-CLOUD-REBUILD-001
ROLE_LOCK=TRUE
STOP_RULE=TRUE
SCOPE_DRIFT=FALSE
```

## 用户结果

从可核验正式来源重新生成“官方 v3.28.0 完整业务树 + P000/P001 V1.5.6
项目控制 Overlay”的完整候选；先建立可恢复的 GitHub 远程检查点，再完成完整验证、
Draft PR、真实 CI 和 Judge。

## 范围

- 核验远程 `main`、官方 Tag/Commit、框架附件和目标分支。
- 在新的隔离目录重建官方业务树与批准的控制层。
- 运行最低完整性硬门并记录候选文件清单与树哈希。
- 通过 GitHub App/Git Data 使用 `Blob → Tree → Commit → Branch` 原子持久化。
- 运行 Python、Web、Desktop、AI 治理和差异验证。
- 创建以 `main` 为目标的 Draft PR，检查并在范围内修复真实 CI。

## 非目标

- 不执行 Ready、合并、改写或强推 `main`、Release。
- 不迁移 R1–R7 的旧业务功能，不新增产品能力。
- 不读取、复制或迁移真实用户数据，不连接真实账号、行情、通知或付费服务。
- 不使用或发布旧工作树的 7 项未提交变化。
- 不访问用户本机工作区，不进行 GitHub 设备认证。

## 允许修改

- 官方 `AGENTS.md` 中唯一明确标记的 PP02 Overlay。
- `.github/workflows/ci.yml` 的既有最小只读权限块。
- `_ai-dev/` 四份项目控制文件。
- `docs/PROJECT_CONTROL.md`、`ROADMAP.md`、`OPEN_BLOCKERS.md`、
  `REQUIREMENTS.md`、`CHANGE_HISTORY.md`、`RUNBOOK.md`、`INDEX.md`。
- `docs/pp02/` 七份重建、迁移和验收文档。
- 仅为修复本候选测试/CI 且仍在上述原始范围内所必需的文件。

## 禁止修改

- 官方业务代码、`CLAUDE.md`、License、来源信息和 Copilot 规则不得因控制层重建而改变。
- 旧工作树不得 reset、clean、stash、覆盖、删除、提交或推送。
- 不复制 P001 空白模板的通用骨架、生成器、模板历史或平行规则。

## 验收标准

1. 执行前硬门全部严格匹配，目标分支不存在。
2. 五个指定完整性文件存在；官方业务文件逐路径、模式和内容一致。
3. PP02 控制层只在批准白名单；Work 1 历史和解除证据不回退。
4. 密钥、真实数据和跨项目内容检查通过；候选清单和树哈希已记录。
5. 本地树、GitHub `create_tree` 返回树和远程 Commit 树一致。
6. 完整 Python、Web、Desktop、AI 治理、格式和范围验证有本轮结果。
7. Draft PR 保持草稿；真实 Actions 通过或形成可证明的真实阻塞。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 适用性 | 已执行；当前是已批准范围的恢复性重建 |
| 问题级别 | 无待决产品问题 |
| 问答 | 0 个问题，通过 |
| 已确认假设 | 项目、仓库、官方固定 Commit、V1.5.6、手动分析优先、定时和自动推送默认关闭、Windows 优先均由任务书/总控确认 |
| 推荐方案 | 官方固定业务树 + 最小控制 Overlay；最低硬门后先持久化，再跑完整测试 |
| 明确不做 | R1–R7、基金、真实数据、Ready/合并/Release |
| Backlog | 旧功能产品取舍、脱敏迁移演练、Windows 实机、正式数据迁移和 Release |
| 剩余阻塞 | 无 |
| 证据位置 | 本文件、`docs/pp02/`、正式重建任务书和追加式台账 |
| 允许进入 Build | 是 |

### 已复审实现 Head 验收进展

- Head `b23c698b32b09749e907f1f4f7be1c056445a52e` 的 Run `30640475137` 已
  8/8 success，且同 Head Windows safeStorage/source/artifact 假凭据门通过。
- 现仅发布证据收口 Head 并完整复验，随后停止；所有授权禁止边界不变。

### 执行进展（2026-07-31）

- 独立 Draft PR `#11` 已建立；RED Head/Run 已证明新契约在实现前失败。
- 实现已通过四轮独立安全复审，所有 Critical/Important 已关闭；经复审的
  本地代码 Head 为 `0627ea85ef14cfb7d0d457937244c2a860fac345`。
- 本地门禁：Python/契约 `340/340`，Desktop `80/80`，Web `127/127`，Lint、Build、
  AI 治理、仓库根派生假密钥扫描和全差异检查通过。
- 下一动作只是把文档收口 Head 发布到同一 Draft PR 并跑完八项 CI/
  固定 Head Windows 假凭据验收；其余禁止边界不变。

## 测试要求

- 最低硬门：`git diff --check`、`python scripts/check_ai_assets.py`、业务树完整性、
  控制层白名单、台账非回退、安全扫描、文件清单与树哈希。
- 持久化后：Python 完整离线测试、Web lint/build、Desktop 支持范围内测试、
  AI 治理、格式与差异范围检查。
- 远程：Draft PR 的真实 GitHub Actions；失败时先诊断，再做范围内最小修复。

## 授权门与回传

本 Work 已获独立分支、Commit、Draft PR、CI 和范围内修复授权；Ready、合并、
`main`、Release、真实数据和下一 Work 仍需总控另行授权。最终回传必须包含远程
基线、重建来源、旧树保护、硬门、初始/最终 Commit、树哈希、PR、测试、Actions、
Judge、阻塞、`SCOPE_DRIFT`、超授权检查和下一决定。

## 2026-07-29 用户追加授权｜同一 Work1 连续推进

- 用户明确要求继续当前 Work1，不创建新聊天或新 Work。
- R1 已授权并完成需求与旧功能迁移确认；单用户裁决覆盖此前本地档案建议。
- “下一步”授权本轮连续完成 R2 迁移计划，并进入首个 R3.1 小版本。
- R3.1 只允许 PP02 Desktop 身份、Release/更新源、ASCII 技术 ID、产物名、
  对应测试和文档；不修改股票分析、数据库、持仓、调度或通知行为。
- Windows 实机验收标记为 Deferred；不恢复、不新建或操作旧 D 盘验收目录。
- Ready、合并、main、Release、真实数据和密钥操作继续禁止。


## 2026-07-29 用户追加授权｜自动路由 v1.1 与 R3.2

- `PP02-AUTO-ROUTER-001 v1.1` 覆盖旧路由：当前 Work 在已批准范围内自动完成
  普通开发、测试、独立分支 Commit、Draft PR 更新和范围内 CI 修复，不反复询问。
- 用户发送“继续流程”，授权同一 Work1 进入 R3.2；主要执行端为云端 Codex，
  GitHub App 负责保存 Commit、更新同一 Draft PR 并验证 CI。
- R3.2 仅覆盖手动默认、默认 cron 移除、自动通知总开关、全部自动发送入口、
  设置帮助、测试和文档。
- Ready、合并、`main`、Release、Windows 本机、真实数据、真实通知渠道、
  大型依赖与付费服务继续禁止，必须单独授权。

## 2026-07-30 用户追加授权｜R3.5 应用内手动周期报告

- 继续当前 Work1 和 Draft PR #3，不重开路线、不重做 R3.1–R3.4。
- 采用“方案 A＋下周参考展望”，一次性完成 Plan、Build、Test、CI 和 Judge。
- 周期报告只聚合正式分析历史和市场复盘历史，覆盖本周至今、上一周、下周展望、
  5周、10周、1个月和2个月。
- 下周展望只使用最近 14 个自然日内的合格记录；不得重新调用 AI，不访问第二套
  报告事实表，不编造方向、目标价或确定性结论。
- 展望快照及来源记录标识必须使用现有 `AnalysisHistory` 和可识别
  `report_type` 持久化；不得创建平行历史真源。
- 只允许用户在应用内手动生成；不新增后台定时器、GitHub Actions 周五定时、
  自动模型调用、通知或报告推送。
- 允许当前分支普通 Commit、Draft PR 更新、测试先行施工、范围内 CI 修复与
  项目台账同步。
- PR 转 Ready、合并、Release、`main`、真实密钥/数据库、定时器和自动推送继续
  禁止。

### R3.5 Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 问题级别 | 无待决产品问题 |
| 问答 | 0 个问题，通过 |
| 已确认方案 | 方案 A＋条件化下周参考展望 |
| 唯一事实源 | `HistoryService.get_history_list()` / `AnalysisHistory` |
| 快照边界 | `report_type=period_outlook`，保留来源记录 ID |
| 自动化边界 | 仅应用内手动触发；无定时、模型调用或推送 |
| 允许进入 Build | 是 |

### R3.5 执行结果

- 实现 Head `4b563bc63e9638731f2a17ed25129de095046ef4` 的 Run
  `30525590779` 已 8/8 success。
- Backend：`5005 passed, 4 deselected, 51 warnings, 494 subtests passed`。
- Web 阻断套件：`55/55 passed`；Lint 与 Production Build 成功。
- 未新增 AI 调用、定时器、自动通知、事实表、基金或多用户功能。
- 当前只待本次 Judge 文档收口 Head 的完整 CI；成功后 R3.5 一次性回传总控。

## WORK-002｜R3.6 Windows 便携安全更新

Work1 已永久关闭；Work2 从已合并 PR #3 的 main 基线 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 接管 R3.6，继承而不重做 R3.1–R3.5。批准方案为复用旧 Portable-M2 安全思想并按 PP02 当前边界重建。允许独立分支 Commit、Draft PR 和 CI 修复；禁止 Ready、合并、Tag、Release、真实数据和进入 R3.7。Plan Challenge：0 个问题，通过。

### R3.6 最终收口授权

只更新现有 Draft PR `#6` / `codex-xbl3c5`。已验证 Head `71404954407a9a3a6362a398465fc822b1351c72` 的 Run `30547333980` 为 8/8 success；PR #5 已关闭并由 PR #6 取代。本轮只允许更新五份唯一台账，并在 Windows CI 上传经同一 Job 验证的 ZIP/SHA 临时候选 artifact（14 天保留）；不得修改业务行为、升版本、创建新 PR、Ready、Merge、Tag、Release、main 直写或进入 R3.7。完成后保持 `IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED` / `DRAFT_HOLD`。


### PR #7 R5 基础启动返工授权

只修复现有 Draft PR #7。范围限于约束 `fake-useragent` 兼容上限、Windows/macOS PyInstaller 完整收集、能实际加载浏览器数据并触发 `data_provider.efinance_fetcher` 的冻结探针、Windows 候选上传前以隔离 `.env`/数据库和动态端口真实启动冻结 EXE并验证健康与主页，以及六份台账。失败 Head `d489a795b6089575a1fd61a27c9b28e2f3cb1b03` 和 Artifact `203e41a3…` 作废。禁止新 PR、Ready、Merge、Tag、Release、main 直写、真实数据/密钥及 R3.7。


### PR #8 CI 环境修复授权

只更新现有 Draft PR #8。不得删除 `main.py` 的 `GITHUB_ACTIONS` 保护条件；只允许在 `scripts/verify-frozen-backend.ps1` 启动冻结 EXE 前保存并临时覆盖 `GITHUB_ACTIONS=false`、`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`，继续验证动态端口健康和主页 HTTP 200，并在 finally 恢复环境与清理进程树。记录 Run `30576678660` 失败并等待新 Head CI/Artifact。禁止新 PR、Ready、Merge、Tag、Release、main 直写和 R3.7。


## WORK-003｜R3.7 Windows 安全凭据

总控已授权启动独立 Work3。固定基线为
`main@097bb5d60aa42f13737ac4d9db2f582bde50f995`，独立分支为
`agent/pp02-work3-r3-7-windows-secure-credentials`，目标是建立 Electron
`safeStorage` / Windows DPAPI 安全凭据边界，并完成威胁模型、测试先行实现、
完整 CI 和固定 PR Head 的 Windows 假密钥验收。

### 范围与验收

1. Windows Desktop 敏感值只持久化为 `userData` 下的 DPAPI 密文；不得继续写入
   `.env`，不得通过读取接口或配置导出返回明文。
2. renderer 只能写入、删除和查询存在状态；不得新增任何明文读取 IPC。
3. backend 只在启动/安全重启时通过 child environment 获得内存中的解密值；
   Windows secure mode 必须拒绝明文敏感配置写入和导入。
4. 先提交可证明失败的契约测试，再做最小实现；完整 CI 必须绑定最终 PR Head。
5. Windows 验收只使用由测试构造的假凭据，证明真实 Electron `safeStorage` 可加密/
   解密、vault 和导出无明文、日志与 artifact 不泄漏，并记录 Head/Run/Job。

### 授权与禁止边界

- 已授权：威胁模型、实施计划、独立分支、普通 Commit、独立 Draft PR、范围内 CI
  修复、固定 Head Windows 假密钥验收和事实台账更新。
- 禁止：真实 `.env`、真实 Key/Token/Password/Webhook、真实账号或数据库；PR Ready、
  Merge、`main` 直写/强推、Tag、Release，以及自行进入 R3.8 或任何后续阶段。
- 最终 Judge 必须保持 `DRAFT_HOLD`，即使实现、CI 和 Windows 验收全部通过。

### Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 问题级别 | 无待决产品问题 |
| 问答 | 0 个问题，通过 |
| 已确认方案 | Electron `safeStorage` / Windows DPAPI |
| 唯一事实源 | Windows Desktop 版本化凭据 vault |
| 测试策略 | RED Commit → 最小实现 → 完整 CI → 固定 Head Windows 假密钥验收 |
| 明确不做 | 旧 P001 密钥迁移、真实密钥、跨平台密钥服务、Ready/Merge/Tag/Release、后续阶段 |
| 允许进入 Build | 是 |
