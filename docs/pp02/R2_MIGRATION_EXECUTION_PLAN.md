# PP02 R2 迁移实施计划

> 后续实现必须逐切片使用测试先行，并在同一 Draft PR 上保留可审查的 Commit、
> GitHub Actions 和 Judge 证据。

**目标：** 把 R1 已确认的产品范围拆成可独立实现、测试和回滚的 R3 切片。

**架构：** 官方 v3.28.0 始终是业务基底；迁移只在现有配置、API、Web、
Desktop 和官方组合事件账本上增加 PP02 增量。禁止整仓复制旧项目、批量
cherry-pick 或新增平行事实源。

**技术栈：** Python 3.12、FastAPI、SQLAlchemy、pytest、React/TypeScript、
Electron、Node test、GitHub Actions。

## 全局约束

- 产品：`PP02｜AI 每日股票分析`。
- 官方业务基线：`v3.28.0` /
  `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c`。
- 单用户，不实现本地档案、多用户或多租户。
- 股票持仓唯一事实源是官方账户/组合事件账本。
- 手动分析默认；定时和自动推送默认关闭。
- 周期报告仅应用内手动查看。
- PP02 不包含基金。
- PR #3 保持 Draft；不转 Ready、不合并、不发布 Release。
- Windows 实机验收为 `Deferred`，在 R5 从固定 PR Head 建立全新隔离目录。
- R6 真实数据迁移和 R7 main/Release 分别需要精确授权。

## 文件责任图

| 边界 | 现有文件 | 后续职责 |
| --- | --- | --- |
| Desktop 身份与更新 | `apps/dsa-desktop/package.json`、`main.js`、`.github/workflows/desktop-release.yml` | PP02 技术 ID、产物名、Release 源和更新源 |
| 调度与通知默认值 | `.github/workflows/00-daily-analysis.yml`、`.env.example`、`src/config.py`、`src/core/config_registry.py` | 所有自动入口默认关闭和自动通知总开关 |
| 配置 API / Web | `api/v1/schemas/system_config.py`、`apps/dsa-web/src/pages/SettingsPage.tsx` | 显示并保存安全默认值 |
| 组合事实源 | `src/storage.py`、`src/repositories/portfolio_repo.py`、`src/services/portfolio_service.py` | 账户和事件账本、持仓重放 |
| 组合 API / Web | `api/v1/endpoints/portfolio.py`、`apps/dsa-web/src/api/portfolio.ts`、`PortfolioPage.tsx` | 快捷录入、预览、确认和历史 |
| 历史与周期报告 | `src/services/history_service.py`、`api/v1/endpoints/history.py` | 从正式分析历史聚合手动周期报告 |

## R3.1｜PP02 身份与更新源

**结果：** 桌面端只能从
`hanchanqaq-source/daily_ai_stock_analysis` 检查 PP02 Release，安装包和免安装包
使用 PP02 的 ASCII 技术名。

**修改文件：**

- `apps/dsa-desktop/package.json`
- `apps/dsa-desktop/package-lock.json`
- `apps/dsa-desktop/main.js`
- `apps/dsa-desktop/tests/main.test.js`
- `.github/workflows/desktop-release.yml`
- `.github/workflows/ci.yml`
- `scripts/verify-desktop-updater-artifacts.ps1`
- `scripts/build-desktop-macos.sh`
- `docs/desktop-package.md`

**验收：**

1. `GITHUB_OWNER=hanchanqaq-source`，
   `GITHUB_REPO=daily_ai_stock_analysis`。
2. `appId`、package name、product name和产物前缀均为 PP02 身份；技术 ID 只用
   ASCII。
3. 更新 URL 只接受 PP02 仓库 Release 路径。
4. Release Workflow、`latest.yml` 校验脚本和文档使用同一安装包名称。
5. `npm test`、Desktop 构建相关 CI、Web/backend 回归门全部通过。

**执行证据：**

- RED：Run `30487941321`，47 pass / 2 expected fail。
- GREEN：Desktop 49/49；实现 Head Run `30488603501` 8/8 success。
- macOS productName 路径遗漏已通过根因修复并在同一完整 Run 中转绿。
- 收口 Head Run `30489293885` 再次 8/8 success。
- 状态：`PASS`。

## R3.2｜手动默认与自动通知总开关

**结果：** 新安装在没有主动开启时既不会定时运行，也不会自动发送分析结果。

**修改文件：**

- `.github/workflows/00-daily-analysis.yml`
- `.env.example`
- `src/config.py`
- `src/core/config_registry.py`
- `api/v1/schemas/system_config.py`
- `main.py`
- `src/services/runtime_scheduler.py`
- `apps/dsa-web/src/pages/SettingsPage.tsx`
- `apps/dsa-web/src/types/systemConfig.ts`
- `tests/test_config_env_compat.py`
- `tests/test_config_registry.py`
- `tests/test_main_schedule_mode.py`
- `tests/test_system_config_api.py`
- `apps/dsa-web/src/pages/__tests__/SettingsPage.test.tsx`

**契约：**

- 删除默认 cron 触发，只保留 `workflow_dispatch`。
- `SCHEDULE_ENABLED=false` 继续作为本地默认。
- 新增 `AUTO_NOTIFICATION_ENABLED=false`；分析、市场复盘和运行时调度发送路径
  必须同时满足该总开关。
- 设置页“发送测试通知”是明确的人工动作，可独立测试已配置渠道，不得反向开启
  自动通知。

**执行中确认的下游消费者：**

- `api/v1/endpoints/analysis.py`
- `src/services/alert_worker.py`
- `apps/dsa-web/src/utils/systemConfigI18n.ts`
- `apps/dsa-web/src/locales/settingsHelp.ts`
- `tests/test_pp02_safe_defaults.py`

这些文件是同一自动发送契约的现有入口或用户可见帮助，不建立平行实现，也不改变
R3.2 产品范围。

**执行证据：**

- RED：Commit `68dab6a7d54b81f196b642b1352a0a41aa2b8eb5`，
  Run `30491953318` 为 9 个预期失败。
- GREEN：Commit `61939ec76384d5c198aecf98e8b413fe13cfdd85`，
  首轮 Run `30492811439` 暴露 2 项集成/帮助元数据回归。
- 根因修正：Commit `5316b5ea2ececd9aff0ced556e897f0738dad317`，
  Run `30493475960` 为 8/8 success；后端 `4976 passed`。
- 收口 Head Run `30494219667` 再次 8/8 success。
- 状态：`PASS`。

## R3.3｜官方账本上的快捷持仓

**结果：** 用户可输入目标数量，先查看当前数量、买卖差额和预计现金变化，再明确
确认；确认只向官方账本追加一条交易事件。现金变化由该交易事件在官方重放中计算，
不得再写一条资金流水造成重复扣款；`portfolio_positions` 仍只作为重放缓存。

**实际修改文件：**

- `.github/workflows/ci.yml`
- `api/v1/schemas/portfolio.py`
- `api/v1/endpoints/portfolio.py`
- `src/services/portfolio_service.py`
- `apps/dsa-web/src/api/portfolio.ts`
- `apps/dsa-web/src/types/portfolio.ts`
- `apps/dsa-web/src/pages/PortfolioPage.tsx`
- `tests/test_pp02_quick_positions.py`
- `apps/dsa-web/src/pages/__tests__/PortfolioPage.test.tsx`

**契约：**

- 预览只读取正式事件，不写交易、现金流水或派生持仓缓存。
- 确认在同一写事务内重新核对预览时的当前数量；账本变化后旧预览返回冲突。
- 成功确认只追加一条带唯一 `trade_uid` 的官方交易事件。
- 重复确认沿用官方去重冲突；卖出、币种、市场、日期和缓存失效继续走官方校验。
- 删除或修正仍通过正式事件历史完成，并可重新重放。
- Web 必须先预览，再由用户点击“确认写入账本”，不得调用旧直接交易接口绕过确认。

**执行证据：**

- RED：Commit `f1ebae02f21a97d97418649c23db8401a8b3fc8f` 与测试门 Commit
  `93d2a59b8eab77a2d6633898c4cbb5e93fb95d33`；Run `30513770957`
  后端 5 项按预期失败，其余 `4976 passed`；PortfolioPage 新测试因表单不存在失败，
  原有 28 项通过。
- CI 盘点发现原 `web-gate` 未运行 Vitest；R3.3 新增 PortfolioPage 专项阻断测试。
- 首次全量 Web 测试同时暴露 AlertRuleForm 日/韩市场选项的既有失败；该问题与
  R3.3 无关，未越界修改告警功能，已写入 `docs/ERRORS_AND_LESSONS.md`。
- GREEN：Commit `311664759a51f8eb8ec700417b20c2e17fa155e8`；Run
  `30514223674` 为 8/8 success，后端 `4981 passed, 4 deselected`，
  PortfolioPage `29/29 passed`。
- 异步测试稳定性修复 Head `d4615cd407ba88ed43f9da129c8c89583358a98a`；
  最终 Run `30514843576` 为 8/8 success，后端 `4981 passed, 4 deselected`，
  PortfolioPage `29/29 passed`。
- 状态：`PASS`。

## R3.4｜股票专用备份与恢复

**结果：** 导出版本化 JSON；导入先校验和预览，再由用户确认后单事务写入。

**新增文件：**

- `src/services/portfolio_backup_service.py`
- `tests/test_portfolio_backup_service.py`

**联动文件：**

- `api/v1/schemas/portfolio.py`
- `api/v1/endpoints/portfolio.py`
- `apps/dsa-web/src/api/portfolio.ts`
- `apps/dsa-web/src/types/portfolio.ts`
- `apps/dsa-web/src/pages/PortfolioPage.tsx`

**备份内容：** 活跃/停用账户、交易事件、现金事件和公司行动。

**明确排除：** 用户档案、基金、密钥、`.env`、日志、分析缓存、
`portfolio_positions`、lots 和快照等可重建派生数据。

**恢复契约：**

- 预览只读，必须同时显示备份与当前账本计数，不得在预览阶段写库。
- 预览令牌同时绑定规范化备份摘要和当前账本摘要；任一方变化后旧令牌失效。
- 确认恢复采用 `replace` 语义，在官方组合写锁内用一个事务完成整套替换。
- 校验、删除或写入任一步失败时事务回滚，原账本保持不变。
- 恢复后只从账户、交易、资金和公司行动重放持仓，不导入派生缓存。
- Web 必须“选择 JSON → 预览 → 危险确认”，不得选择文件后直接写入。

**执行证据：**

- RED：Commit `15e48e6000bd1a39e7db082e20897052affa558c` 与
  `b6a2cd2f02e2ebc3955bfb6276e1ffd63b3c6eac`；Run `30516073073`
  后端 6 项按预期失败、其余 `4981 passed`；PortfolioPage 新增 2 项按预期失败，
  原有 29 项通过。
- 初始 GREEN Head `85dbe71a26d175b6c2557900770b3260fea4a419` 在私有仓库
  Actions 免费分钟耗尽时出现零 Step 阻塞；公开前只读安全审计未发现密钥或真实
  数据，用户授权后仓库改为 Public，标准 Runner 恢复运行。
- 公开库重跑 Run `30516696130` 暴露 4 项确定性日期摘要失败：
  规范化后的 `date/datetime` 尚未转换为 JSON 标量。
- 日期摘要修复 Head `8355d92a81b8f951a8ee7bcb703e89585cb8de5e`；
  Run `30518936016` 后端 `4987 passed, 4 deselected`，同时暴露 1 条既有
  PortfolioPage 异步等待竞态。
- 最终实现 Head `56c887502e218efa146a20ab86c928008e9035d6`；
  Run `30519559480` 为 8/8 success，后端
  `4987 passed, 4 deselected, 50 warnings, 487 subtests passed`，
  PortfolioPage `31/31 passed`，Web Build、Docker、Desktop 单测及
  Windows/macOS 包门全部通过。
- 状态：`PASS`；收口 Head `a5b999717e57fe3c78da5c65adadcb1f05b71f95`
  的 Run `30520589917` 为 8/8 success。

## R3.5｜应用内手动周期报告

**结果：** 在 Web 中手动生成本周至今、上一周、下周展望、5周、10周、
1个月和2个月视图；没有后台定时器、模型调用或自动推送。

**新增文件：**

- `src/services/period_report_service.py`
- `api/v1/schemas/period_report.py`
- `api/v1/endpoints/period_report.py`
- `apps/dsa-web/src/api/periodReport.ts`
- `apps/dsa-web/src/types/periodReport.ts`
- `apps/dsa-web/src/pages/PeriodReportPage.tsx`
- `tests/test_period_report_service.py`
- `tests/test_period_report_api.py`
- `apps/dsa-web/src/pages/__tests__/PeriodReportPage.test.tsx`

**复用：** `HistoryService.get_history_list()`、`AnalysisHistory.report_type` 和现有
市场复盘历史；不复制报告事实表。

**周期边界：**

- 本周至今：截至日所在周的周一至截至日。
- 上一周：上一周周一至周日。
- 下周展望：下一周周一至周日。
- 5周/10周：含当前周的 5/10 个自然周，从首周周一至截至日。
- 1个月/2个月：从截至日向前移动 1/2 个日历月后的次日开始，至截至日。
- 所有边界均为闭区间；必须覆盖跨月和跨年测试。

**历史聚合契约：**

- 只通过 `HistoryService.get_history_list()` 读取现有正式历史。
- 普通股票/ETF分析排除 `market_review`、`period_outlook` 和非正式报告类型；
  市场复盘只接受 `report_type=market_review`。
- 股票与 ETF 分区返回每个标的的记录数、最新记录、方向分布和可用摘要；
  市场复盘单独返回，不与标的统计混合。
- 周期生成不得调用模型、行情、新闻、通知或调度入口。

**下周展望契约：**

- 只接受最近 14 个自然日内、具有可解释方向的 `simple`/`detailed`/`full`
  正式分析记录；每个标的以最近有效记录为主，其余记录只作历史佐证。
- 方向只允许“看多/中性/看空”，置信度只允许“低/中/高”。
- 返回主要历史信号、主要风险、判断失效条件、数据截至时间、来源记录数量和
  来源记录 ID；不得使用“必涨/必跌/准确预测”或伪精确目标价。
- 全部数据不足时固定返回：
  “近期有效数据不足，暂不能形成下周展望。”
- 页面固定提示：
  “下周展望基于已有历史分析形成，仅供参考，不代表确定结果。”

**持久化与复盘：**

- 使用 `AnalysisHistory` 的 `report_type=period_outlook` 保存整个下周展望快照；
  `context_snapshot` 保存目标周、生成时间、股票/ETF分区、来源记录 ID 和版本。
- 不增加数据库列或新表；快照记录不参与普通周期历史统计。
- 生成上一周汇总时，查找目标日期与上一周完全一致的最新展望快照，并与实际
  周期汇总并列返回；没有旧快照时正常返回实际汇总。

**API 与 Web：**

- `POST /api/v1/period-report/generate` 是唯一生成人工入口。
- Web 初次打开不自动生成；用户选择周期并点击后才请求。
- `next_week` 生成并保存展望快照；其他周期只读聚合。
- 页面沿用现有官方卡片、徽标、错误态和空态，不显示内部编号或控制规则。

**阻断测试：**

- 服务专项覆盖七个日期边界、跨月/跨年、历史分区、14 日过期、方向/置信/
  风险/失效条件、快照来源和旧展望并列复盘。
- API 专项证明 Schema、人工 POST、无模型调用和数据不足契约。
- Web 专项证明七个入口、初始不请求、点击生成、分区展示、免责声明与错误态。
- Web CI 必须运行 PeriodReportPage 专项测试后再执行 Build。

**实现证据：**

- 计划/服务/API/隔离/Web 五个逻辑 Commit 已连续落在 Draft PR #3；实现 Head
  为 `4b563bc63e9638731f2a17ed25129de095046ef4`。
- Run `30525590779` 为 8/8 success；Backend
  `5005 passed, 4 deselected, 51 warnings, 494 subtests passed`；
  Web 阻断套件 `55/55 passed` 且 Production Build 成功。
- 专项测试覆盖七个日期边界、跨月/跨年、14 日过期、数据不足、来源追溯、
  股票/ETF/市场复盘分区与旧展望并列复盘。
- 普通股票历史和回测显式排除 `period_outlook`，避免持久化快照进入正式分析
  事实统计。
- 状态：`PASS — FINAL_HEAD_CI_PENDING`。

## R3.6｜Windows 便携更新

- NSIS 安装版继续作为第一发布形态。
- 免安装 ZIP 保留“检查更新并打开 Release 页”的现有行为。
- 便携版自动替换、SHA-256、恢复点和回退作为独立切片，不阻塞 R3.1–R3.5。
- 必须在 R5 Windows 实机验证后才能判定完成。

## R3.7｜Windows 安全凭据

- 在最终设置契约稳定后实现 Electron `safeStorage` / Windows DPAPI。
- 只允许一个密钥事实源；导出配置不得包含解密后的密钥。
- 旧版部分实现只作参考，不迁移旧密钥或真实 `.env`。
- 该切片需要独立威胁模型、Desktop IPC 测试和 Windows 实机验收。

## 阶段与授权门

| 阶段 | 自动可继续范围 | 必须单独授权 |
| --- | --- | --- |
| R3 | 逐个完成上述已确认切片、测试、Draft PR CI 和范围内修复 | Ready、合并、Release |
| R4 | 只用空库、fixture 或脱敏副本做兼容演练 | 接触真实数据库 |
| R5 | 从固定 PR Head 建立全新 Windows 隔离验收目录 | 覆盖现有本机目录 |
| R6 | 无 | 正式数据备份、迁移和回滚 |
| R7 | 无 | Ready、合并 main、Tag 和 Release 分别授权 |

## R2 Judge

`PASS`

- 每个迁移能力都有唯一事实源、依赖、文件边界和验收出口。
- 单用户决定已贯穿所有切片。
- R3.1–R3.4 已完成。
- R3.5 已有实现 Head 完整 CI 证据，当前只待 Judge 文档收口后的最终 Head CI。
- R3.5 收口后停止并回传总控；不得自行启动 R3.6。

## Work2 / R3.6 Windows 便携安全更新（2026-07-30）

Work1 已永久关闭；PR #3 已合并且 R3.1–R3.5 已进入 main。Work2 从 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 以独立分支和独立 Draft PR 接管 R3.6。实现范围与证据见 `docs/pp02/R3_6_WINDOWS_PORTABLE_UPDATE_IMPLEMENTATION.md`。R5 Windows 真机验收仍为后续授权门，本轮不进入 R3.7。
