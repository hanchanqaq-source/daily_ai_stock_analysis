# PP02 决策与范围变更历史

本文件只追加，不倒改已完成和已确认历史。

| 决策编号 | 日期 | 决策 | 原因 | 影响步骤 |
| --- | --- | --- | --- | --- |
| WORK-001-DECISION-001 | 2026-07-22 | 采用方案 A：继续以官方稳定 `v3.27.0` 建立纯净底座；不整体跟随未发布 `main` | 稳定基线风险最低，同时保留后续精选补丁空间 | Work 1.2、Work 1.4；两项上游修复留作后续候选 |
| WORK-001-DECISION-002 | 2026-07-22 | 在根目录建立项目级 `AGENTS.md` 统一规则机制，并连接唯一项目台账 | 降低换聊天或换 Agent 后串错项目、越权或重复建台账的风险 | Work 1.4.2～1.4.4 |
| WORK-001-AUTH-001 | 2026-07-22 | 授权建立私有仓库 `hanchanqaq-source/daily_ai_stock_analysis`，保留官方历史并执行首次导入和推送 | 新 PP02 必须与旧混合项目隔离 | Work 1.3、Work 1.4.1；不包含合并 PR 或发布 Release |
| WORK-001-AUTH-002 | 2026-07-23 | 授权正式修复 `main` 的 CI 权限并更新 Work 1 台账；创建 Draft PR，CI 通过后等待用户确认是否合并 | 验证 PR #1 已证明缺少 `pull-requests: read` 是唯一权限根因，最小只读修复可使完整 CI 成功 | Work 1.6；允许正式分支、提交、推送和 Draft PR，不包含合并或 Release |

| WORK-001-AUTH-003 | 2026-07-23 | 授权将 PR #2 转为 Ready 并合并到 `main`；合并后复核 `main` 并更新最终进度，不发布 Release | 正式 CI 权限修复已通过完整 CI，需要完成合并与台账收口 | Work 1.6；已合并为 `a6bdfb55827080e196c2103292aaedfadc224dc7`，Release 未发布 |
| WORK-PP02-CLOUD-REBUILD-001-DECISION-001 | 2026-07-26 | Work 1 的 v3.27.0 管理底座作为历史保留；当前 R0 从官方 `v3.28.0` 固定提交重建，并叠加 P000/P001 V1.5.6 控制层 | 消除旧基线、旧状态真源和空白模板覆盖风险，同时保持官方业务树完整 | 当前 Work 只执行 R0；R1–R7 不启动 |
| WORK-PP02-CLOUD-REBUILD-001-AUTH-001 | 2026-07-26 | 授权在同一 Work 内恢复性重建，并通过已连接的 GitHub App/Git Data API 创建原子 Commit、独立分支、Draft PR、检查真实 CI 和修复范围内问题 | 已验证候选未持久化，需要先建立可恢复的远程检查点再运行完整验证 | 不含 Ready、合并、改写 `main`、Release、真实数据或重复设备认证 |
| WORK-PP02-CLOUD-REBUILD-001-AUTH-002 | 2026-07-30 | 授权对 PP02 做公开前只读安全审计，审计通过后把仓库从 Private 改为 Public 并继续 R3.4 CI | 私有仓库 2000 分钟免费 Actions 额度已耗尽；公开库标准 Runner 可继续验证 | 公开代码、分支、PR 和 Actions 历史；不包含 Ready、合并、Release、真实数据或密钥 |
| WORK-002-DECISION-001 | 2026-07-30 | Work1 永久关闭；R0–R7 后续改造按当前有效口径归属 Work2，当前任务为 R3.6 | 旧聊天窗口名被误当成顶层 Work 编号，导致 Work1 同时显示完成和进行中 | 只纠正当前与未来归属；不重做 R3.1–R3.5，不倒改历史 Commit、测试或 CI |
| WORK-002-AUTH-001 | 2026-07-30 | R3.6 从已合并 PR #3 后的 `main@0f9afe8b…` 建立独立分支、普通 Commit/Push、新 Draft PR 和范围内 CI 修复 | PR #3 已合并，不能继续把 R3.6 写入旧 PR 或旧分支 | 不含 Ready、Merge、修改 `main`、Tag、Release、真实数据、密钥或付费服务 |
| PP02-GOVERNANCE-DECISION-001 | 2026-07-30 | 在现有 PP02 Overlay 和唯一台账中增加五项治理硬门 | 防止人工中转、用户规则失效、工具异常重跑、Work 串段及平行状态真源复发 | 不改变 v3.28.0 业务底座，不创建复杂验证系统或平行状态文件 |

## 记录规则

- 新功能或范围变化先执行 Plan Challenge Gate，用户选择后再追加一行。
- 授权记录必须写清目标、范围和未包含事项。
- 技术实现细节不作为范围决策；重要故障与解除条件写入 `OPEN_BLOCKERS.md`。

## 2026-07-29｜R1 单用户裁决与 R2 迁移排序

- 用户取消本地用户切换/多档案需求，PP02 保持官方单用户模式。
- 用户档案、当前用户持久化、按用户隔离历史和用户级备份恢复全部改为不迁移。
- 官方组合事件账本固定为持仓唯一事实源。
- Windows 验收改为 Deferred，后续从固定 PR Head 新建隔离目录。
- 用户要求继续当前 Work1，不创建新聊天或新 Work；“下一步”连续完成 R2 并进入 R3.1。
- PR #3 保持 Draft，不转 Ready、不合并、不发布 Release。


## 2026-07-29｜统一执行端自动路由 v1.1 与 R3.2

- 用户发布 `PP02-AUTO-ROUTER-001 v1.1`，替代旧路由记录，但不回退已完成阶段。
- 当前 Work 在已批准范围内自动路由普通开发、测试、非默认分支 Commit、
  Draft PR 更新和 CI 修复；用户无需选择 Work、Codex 或 GitHub App。
- 用户发送“继续流程”，同一 Work1 自动进入 R3.2；业务范围仍以
  `R2_MIGRATION_EXECUTION_PLAN.md` 为准。
- Ready、合并、Release、默认分支、真实数据、本机重要文件、大型依赖、
  付费服务和范围扩大仍须单独授权。

## Change PP02-GOVERNANCE-001：五项核心治理硬门

- Request and user value：减少用户人工中转，让用户规则、异常恢复、Work 边界、
  唯一状态和长任务进度成为可核验 Judge 条件。
- Evidence state：Confirmed；用户已提供完整规则与验收要求。
- Affected current and future items：Work2 / R3.6 及后续 Work 的治理过程。
- Schedule and complexity impact：只增加现有文件内的治理检查，不增加业务施工段。
- Architecture, data, security, and operations impact：无业务架构或数据变化；强化授权、
  恢复、范围和状态一致性。
- Duplicate or conflict check：复用 `AGENTS.md` Overlay、四份 `_ai-dev` 文件和现有
  路线/变更台账；不创建第二套框架。
- Classification：Current-step substep。
- Decision and reason：批准最小增补；治理缺口会直接影响 R3.6 的可恢复性和 Judge。
- What changes：连续执行、用户规则 Judge、异常检查点、范围漂移拦截、状态优先级、
  进度显示和五项新增验收。
- What remains unchanged：官方 v3.28.0 业务底座、R3.1–R3.5 成果、R3.6 产品方案、
  R5 Windows 实机门、真实数据和 Release 授权边界。
- Revised acceptance evidence：治理一致性本地检查、AI 资产检查、新 Draft PR CI 和
  `PROJECT_STATUS` 与 Git/测试/CI 对照。
