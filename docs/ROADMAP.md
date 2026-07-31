# PP02 滚动路线图

已完成并验收的历史不得倒改。当前 R0–R7 重建路线见
[`pp02/REBUILD_ROADMAP.md`](pp02/REBUILD_ROADMAP.md)；唯一当前状态见
[`../_ai-dev/PROJECT_STATUS.md`](../_ai-dev/PROJECT_STATUS.md)。本文件不建立第二套
当前状态真源。

## 当前路线入口

| 路线 | 状态 | 边界 |
| --- | --- | --- |
| R0｜云端安全重建基线 | 完成 | 官方 v3.28.0 + V1.5.6 候选、Draft PR 和两轮 CI 已通过 |
| R1｜需求与旧功能迁移确认 | 完成 | 单用户范围、保留/调整/不迁移和冲突裁决已确认 |
| R2｜迁移正式候选计划 | 完成 | R3.1–R3.7 文件边界、依赖和验收已固定 |
| R3｜功能迁移 | 进行中 | R3.1–R3.6 已完成；R3.7 安全复审已通过，等待最终 Head CI/Windows 假密钥收口 |
| R4–R7 | 未启动 | 脱敏演练、Windows验收、真实数据和发布分别受授权门控制 |

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
固定 Head 假凭据验收门。威胁模型与四次独立安全复审已无
Critical/Important；当前只等待最终 Head 完整 CI 与 Windows Job 证据。
Judge 上限仍为 `DRAFT_HOLD`，不进入后续阶段。
