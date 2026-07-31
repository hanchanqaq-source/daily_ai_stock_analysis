# PP02 当前状态

> 本文件是 PP02 唯一当前状态真源。其他文档出现冲突时，以本文件和可验证证据为准。

```text
PROJECT_ID=PP02
PROJECT_NAME=AI 每日股票分析
CHAT_ROLE=WORK
WORK_ID=WORK-003
ROLE_LOCK=TRUE
APPLICATION_BASE_VERSION=3.28.0
FRAMEWORK_TEMPLATE_VERSION=1.5.6
PROJECT_WORK_VERSION=pp02-cloud-rebuild-work.1
CURRENT_STAGE=R3.7 / Implementation-GREEN CI
CURRENT_WORK=Windows 安全凭据
ACTIVE_GOAL=在独立Draft PR上以safeStorage/DPAPI建立Windows Desktop安全凭据边界
CURRENT_STATUS=LOCAL_GREEN — REMOTE_IMPLEMENTATION_CI_PENDING — DRAFT_HOLD
ACTIVE_BLOCKER=NONE
NEXT_ACTION=发布实现Head并完成完整CI、独立代码审查和固定Head Windows假密钥验收
AUTHORIZATION_REQUIRED=FALSE_FOR_R3_7_BUILD_TEST_COMMIT_DRAFT_PR_CI_FAKE_CREDENTIAL_VALIDATION; READY/MERGE/MAIN/TAG/RELEASE/REAL_CREDENTIALS/NEXT_STAGE_REQUIRE_NEW_AUTHORIZATION
LAST_UPDATED=2026-07-31
```

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
- R2：迁移拆为 R3.1–R3.7；R3.1–R3.6 已完成，当前执行 R3.7
  Windows 安全凭据。
- Windows 实机验收为 `Deferred`，不把 D 盘目录缺失登记为云端阻塞。

## 当前保护边界

- PR #3 不转 Ready、不合并、不发布 Release。
- 不接触真实 `.env`、Token、API Key、Webhook 或真实数据库。
- 不迁移基金、多用户或旧平行持仓表。
- R3.7 只允许 Windows Desktop `safeStorage`/DPAPI 凭据 vault、窄 IPC、后端启动
  环境注入、敏感配置屏蔽/导入导出边界、测试和文档。
- 不读取或迁移旧明文凭据，不使用真实凭据，不扩展跨平台密钥服务或后续阶段。
- 仓库经只读安全审计和用户授权后已改为 Public；PR、分支和 Actions 历史公开，
  但真实数据、密钥和备份文件仍不得进入仓库。

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
- 实现 Head 尚未发布；完整远端 CI、独立代码审查与同一固定 Head 的 Windows 真实
  Electron `safeStorage` 假密钥验收仍待完成。PR 必须持续保持 Draft。
