# PP02 当前状态

> 本文件是 PP02 唯一当前状态真源。其他文档出现冲突时，以本文件和可验证证据为准。

```text
PROJECT_ID=PP02
PROJECT_NAME=AI 每日股票分析
CHAT_ROLE=AUTO_TAKEOVER
WORK_ID=WORK-008
ROLE_LOCK=SUPERSEDED_BY_PP02-WORK-HANDOFF-002
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
WORK_STATE=ACTIVE
EXECUTION_LOCK=HELD_BY_WORK_008
APPLICATION_BASE_VERSION=3.29.0
TARGET_RELEASE_VERSION=3.29.1
FRAMEWORK_TEMPLATE_VERSION=1.5.6
PROJECT_WORK_VERSION=pp02-cloud-rebuild-work.1
ACTIVE_BASE=66666352e953d90becce420da7d35b649516af76
ACTIVE_BRANCH=agent/pp02-work8-r7-installer-fix
ACTIVE_PR=17
CURRENT_STAGE=R7 Hotfix / Diagnostic Evidence Blocked
CURRENT_WORK=WORK-008 — Windows installer defect repair and v3.29.1 patch
ACTIVE_GOAL=repair assisted per-user NSIS installer without removing directory selection
LAST_DIAGNOSTIC_HEAD=eae4b46501c9a183dda20d2975121987e676943b
LATEST_CI_RUN=30742085965
CURRENT_STATUS=ROOT_CAUSE_BLOCKED_EVIDENCE_INSUFFICIENT
ACTIVE_BLOCKER=WINDOWS_DIAGNOSTIC_ARTIFACT_NOT_PRESERVED_OR_UPLOADED
FAILED_RELEASE_TAG=v3.29.0
FAILURE_CLASS=INSTALLER_BOOTSTRAP_CRASH
FAILURE_REPRODUCIBILITY=2/2
FAILURE_EXCEPTION=0xC0000005 / System.dll
NEXT_WORK=NONE_WHILE_WORK_008_ACTIVE
NEXT_ACTION=WAIT_FOR_USER_DIRECTION;NO_FURTHER_PATCH_OR_CI_UNDER_CURRENT_EVIDENCE
AUTHORIZATION_REQUIRED=TRUE_FOR_ANY_FURTHER_PATCH_OR_CI/READY/MERGE/MAIN_WRITE/TAG/RELEASE/REAL_DATA
LAST_UPDATED=2026-08-02
```

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
