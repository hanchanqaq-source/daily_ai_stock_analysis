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
- 状态：`PASS — FINAL_HEAD_CI_PENDING`。

## R3.3｜官方账本上的快捷持仓

**结果：** 用户可快捷新增或调整持仓，但每次确认都会生成官方交易/现金事件；
`portfolio_positions` 仍只作为重放缓存。

**修改文件：**

- `api/v1/schemas/portfolio.py`
- `api/v1/endpoints/portfolio.py`
- `src/services/portfolio_service.py`
- `src/repositories/portfolio_repo.py`
- `apps/dsa-web/src/api/portfolio.ts`
- `apps/dsa-web/src/types/portfolio.ts`
- `apps/dsa-web/src/pages/PortfolioPage.tsx`
- `tests/test_portfolio_service.py`
- `tests/test_portfolio_api.py`
- `apps/dsa-web/src/pages/__tests__/PortfolioPage.test.tsx`

**契约：**

- 快捷调整先返回事件预览，用户确认后写入。
- 禁止直接写 `portfolio_positions`。
- 超卖、币种、市场、日期和重复事件沿用官方校验。
- 删除或修正通过正式事件历史完成，并可重新重放。

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

## R3.5｜应用内手动周期报告

**结果：** 在 Web 中手动生成本周至今、上一周、下一周参考区间、5周、10周、
1个月和2个月视图；没有后台定时器和自动推送。

**新增文件：**

- `src/services/period_report_service.py`
- `api/v1/schemas/period_report.py`
- `api/v1/endpoints/period_report.py`
- `apps/dsa-web/src/api/periodReport.ts`
- `apps/dsa-web/src/types/periodReport.ts`
- `apps/dsa-web/src/pages/PeriodReportPage.tsx`
- `tests/test_period_report_service.py`
- `tests/test_period_report_api.py`

**复用：** `HistoryService.get_history_list()`、`AnalysisHistory.report_type` 和现有
市场复盘历史；不复制报告事实表。

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
- 当前无 R3.1 产品决策阻塞。
- 下一执行切片固定为 R3.1。
