# PP02 安全重建路线 R0–R7

唯一当前状态见 [`../../_ai-dev/PROJECT_STATUS.md`](../../_ai-dev/PROJECT_STATUS.md)。
旧“继续当前 Work1”的记录保留为历史。当前有效口径为：Work1 已完成并锁定，
R0–R7 后续改造归属 Work2，当前任务是 R3.6；各阶段范围、测试和授权门继续独立
记录。

| 阶段 | 目标 | 当前状态 | 完成证据 |
| --- | --- | --- | --- |
| R0｜云端安全重建底座 | 官方 v3.28.0 + V1.5.6 控制层候选、Draft PR 与 CI | 完成 | PR #3 已通过并合并到 `main@0f9afe8b…` |
| R1｜需求与旧功能迁移确认 | 保留、调整、不迁移及冲突裁决 | 完成 | `R1_REQUIREMENTS_MIGRATION_CONFIRMATION.md` |
| R2｜迁移正式候选计划 | 把 R1 决定拆成独立可验收切片 | 完成 | `R2_MIGRATION_EXECUTION_PLAN.md` |
| R3｜按优先级迁移旧 PP02 功能 | 每个切片单独测试、CI 和 Judge | 进行中 | R3.1–R3.5 已完成；Work2 当前执行 R3.6 |
| R4｜数据库兼容与脱敏迁移演练 | 空库/fixture/脱敏副本验证 | 未启动 | 可重复脚本、核对与回滚 |
| R5｜Windows 本机验收 | 安装、启动、Web/Desktop 与安全默认值 | Deferred | 从固定 PR Head 新建隔离目录验收 |
| R6｜正式数据迁移 | 迁移经确认的真实数据 | 未启动 | 单独数据授权、备份与回滚 |
| R7｜替换 main 与 Release | Ready、合并、main、Tag、Release | 未启动 | 每项分别精确授权 |

## 当前 R3 顺序

1. R3.1 PP02 身份与更新源：完成。
2. R3.2 手动默认与自动通知总开关：完成。
3. R3.3 官方账本上的快捷持仓：完成。
4. R3.4 股票专用备份与恢复：完成。
5. R3.5 应用内手动周期报告＋下周参考展望：完成。
6. R3.6 Windows 便携更新：进行中。
7. R3.7 Windows 安全凭据。

详细文件边界、契约和验收见
[`R2_MIGRATION_EXECUTION_PLAN.md`](R2_MIGRATION_EXECUTION_PLAN.md)。

## Mainline Scope Lock

- PR #3 已合并，不再接收改动。
- R3.6 从 `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 建立独立 Draft；
  当前唯一活动项为 PR `#7` / `codex-4z7ady`，治理来源 PR #4 只用于提交归并。
- Draft 不表示 Ready、可合并、可替换 `main` 或可发布 Release。
- R4 只能使用空库、fixture 或脱敏副本；R6 正式数据必须单独授权。
- R5 Windows 验收只从固定 PR Head 新建隔离目录，不恢复或复用已消失的旧目录。

## Work2 / R3.6 Windows 便携安全更新（2026-07-30）

Work1 已永久关闭；PR #3 已合并且 R3.1–R3.5 已进入 main。Work2 从 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 以独立分支和独立 Draft PR 接管 R3.6。实现范围与证据见 `docs/pp02/R3_6_WINDOWS_PORTABLE_UPDATE_IMPLEMENTATION.md`。R5 Windows 真机验收仍为后续授权门，本轮不进入 R3.7。
