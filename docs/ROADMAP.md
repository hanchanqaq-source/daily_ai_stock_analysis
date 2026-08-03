# PP02 滚动路线图

已完成并验收的历史不得倒改。当前 R0–R7 重建路线见
[`pp02/REBUILD_ROADMAP.md`](pp02/REBUILD_ROADMAP.md)；唯一当前状态见
[`../_ai-dev/PROJECT_STATUS.md`](../_ai-dev/PROJECT_STATUS.md)。本文件不建立第二套
当前状态真源。

## 当前路线入口

Work10 已完成 `v3.29.1` 发布；Work11 真机安装闭环裁决 `PASSED_WITH_RESIDUALS`。
Work12 的个股正式历史缺失由 Work13 PR #20 修复。Work14 已在其固定 Head 上完成
未发布 Windows 候选的 `600519` 正式历史与重启持久化验收，最终裁决为
`PASS_WITH_DEGRADATIONS — DRAFT_HOLD`；证据 Run `30821021196` 已 success。
Work15 已将 PR #20 合入 `main@25de369f…`，主线 Run `30822458701` 8/8 success；
当前只待 PR #21 非破坏同步后的最终固定 Head CI、Ready 与合并。

| 路线 | 状态 | 边界 |
| --- | --- | --- |
| R0｜云端安全重建基线 | 完成 | 官方 v3.28.0 + V1.5.6 候选、Draft PR 和两轮 CI 已通过 |
| R1｜需求与旧功能迁移确认 | 完成 | 单用户范围、保留/调整/不迁移和冲突裁决已确认 |
| R2｜迁移正式候选计划 | 完成 | R3.1–R3.7 文件边界、依赖和验收已固定 |
| R3｜功能迁移 | 完成 | R3.1–R3.7 已通过并由 PR #11 合入 `main@eb32298…` |
| R4｜数据库兼容与脱敏迁移演练 | 完成 | Work4 方案 A；PR #12 固定 Head CI 通过；Draft Hold |
| R5｜Windows 本机验收 | 完成 | Work2 / PR #9 真机启动与回滚模拟通过并进入 `main` |
| R6｜正式数据迁移 | 完成（无数据，跳过迁移） | Work6 `NO_FORMAL_DATA_FOUND`；旧项目和数据库从未建立 |
| R7｜主线与正式发布 | 完成 | `v3.29.1` annotated Tag/正式 Release；Run `30786838156` 5/5 success、7 assets |
| R7-Hotfix 验收 | Work15 主线收口中 | Work14 最终 `PASS_WITH_DEGRADATIONS — DRAFT_HOLD`；PR #20 已合并且 main CI 8/8；PR #21 最终 CI 待核验 |

## Work 1｜官方稳定版干净底座建立（历史）

| 子步骤 | 内容 | 状态 | 完成条件 |
| --- | --- | --- | --- |
| Work 1.1 | 恢复上下文、确认角色、检查目录与新旧项目边界 | 完成 | 原 WORK-001 启动会话确认为 `CHAT_ROLE=WORK`、`WORK_ID=WORK-001`，旧仓库未修改；不替代新会话独立判定 |
| Work 1.2 | 核对 Release、Tag、Commit、License、安全信息及 `main` 差异 | 完成 | 锁定 `v3.27.0 / b36c7214…`，新增提交只作候选 |
| Work 1.3 | 新仓库授权门 | 完成 | 已授权私有仓库方案 A 与首次导入/推送范围 |
| Work 1.4.1 | 从官方稳定 Tag 建立原始底座并保留历史 | 完成 | 新仓库 `main` 准确指向并可追溯到官方 Tag Commit；官方 Tag 名由上游仓库保持 |
| Work 1.4.2 | 增加项目级 `AGENTS.md` 与台账导航 | 完成 | 管理文件已发布，且未修改股票业务功能 |
| Work 1.4.3 | 与官方 Tag 比对 | 完成 | 远端仅有 8 个批准的管理/文档文件差异；业务目录零差异 |
| Work 1.4.4 | 新测试会话验证规则识别 | 完成 | 独立只读会话正确识别项目、默认角色、边界、Work、三选一、授权门与唯一台账 |
| Work 1.5 | 安装、测试、后端、Web、目录与跨项目引用验证 | 云端完成 | 云端验证全部通过；Windows 项进入实机验收 |
| Work 1.6 | 台账、CI、Judge 与总控交付总结 | 完成 | PR #2 的 CI 全部应执行门禁通过并已按授权合并；`main` 权限与文件范围复核通过，未发布 Release |

## Work 2 及以后

以下是 Work 1 当时的历史约束。后续阶段现统一受
[`pp02/REBUILD_ROADMAP.md`](pp02/REBUILD_ROADMAP.md) 和独立 Work 授权控制，
当前 R1/R2 已在用户追加授权下于同一 Work1 完成；R3 按已确认切片推进。

已登记但未排期的上游候选补丁：

- Windows `mimetypes` 启动卡死修复
- 美股、港股英文新闻相关性修复

## Work2 / R3.6 Windows 便携安全更新（2026-07-30）

Work1 已永久关闭；PR #3 已合并且 R3.1–R3.5 已进入 main。Work2 从 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 以独立分支和独立 Draft PR 接管 R3.6。实现范围与证据见 `docs/pp02/R3_6_WINDOWS_PORTABLE_UPDATE_IMPLEMENTATION.md`。R5 Windows 真机验收仍为后续授权门，本轮不进入 R3.7。

## Work3 / R3.7 Windows 安全凭据（2026-07-31）

Work2/R5 已完成并进入 `main`。Work3 从固定基线
`097bb5d60aa42f13737ac4d9db2f582bde50f995` 建立独立 Draft PR `#11`，完成
`safeStorage` / DPAPI 版本化 vault、窄 IPC、backend 内存注入、导入导出边界和
固定 Head 假凭据验收门。威胁模型与四次独立安全复审已无 Critical/Important；
最终 Head `173b3d3` 的 Run `30643230898` 已 8/8 success，Windows Job
`91198401578` 已同 Head 完成 safeStorage 和最终产物扫描。PR #11 已合并，
Work3 已关闭；该历史合并不自动授权 R4 或后续阶段。

## Work4 / R4 数据库兼容与脱敏迁移演练（2026-07-31）

Work3 已完成并由 PR #11 合入 `main@eb32298…`。Work4 使用独立分支
`agent/pp02-work4-r4-database-rehearsal`，先把自动接力规则写入现有唯一框架，
再只用空库和人工假数据完成可重复兼容、迁移、排除与回滚演练。真实数据库、
Ready、合并、Tag、Release 和后续阶段均未授权。

Work4 最终实现 Head `f1b433a7…` 的 CI Run `30660971800` 全部适用 Job success，
Judge 为 `PASS — WORK4 COMPLETED — DRAFT_HOLD`。下一未启动大段是 Work5 / R6
正式数据迁移授权与计划；必须在新聊天接管后先取得单独授权。

## Work5–Work7 / R6–R7（2026-08-01）

Work5 已在 Draft PR #13 完成 Windows 原生安全只读盘点工具，固定 Head
`50dd04ca…` 的 Run `30691233934` 全部适用 Job success。Work6 在 Windows 本机确认
旧项目和指定数据库从未建立，裁决 `NO_FORMAL_DATA_FOUND`，因此不执行真实数据迁移。

Work7 已选择方案 A / `v3.29.0`。PR #12 与叠加其上的 PR #13 将按固定 Head 顺序
进入 `main`；最终 `main` push CI 通过后才创建 annotated Tag，并以 GitHub Release、
Windows/macOS 正式资产和 Docker/GHCR 结果作为 R7 完成证据。
