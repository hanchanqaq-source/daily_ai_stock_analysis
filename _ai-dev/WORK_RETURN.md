# WORK-PP02-CLOUD-REBUILD-001 回传

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
