# PP02 安全重建路线 R0–R7

唯一当前状态见 [`../../_ai-dev/PROJECT_STATUS.md`](../../_ai-dev/PROJECT_STATUS.md)。
用户已明确要求继续当前 Work1，不创建新聊天或新 Work；因此 R1 以后继续使用同一
`WORK-PP02-CLOUD-REBUILD-001`，但各阶段范围、测试和授权门仍独立记录。

| 阶段 | 目标 | 当前状态 | 完成证据 |
| --- | --- | --- | --- |
| R0｜云端安全重建底座 | 官方 v3.28.0 + V1.5.6 控制层候选、Draft PR 与 CI | 完成 | PR #3 两轮 7/7 CI、最终 Judge |
| R1｜需求与旧功能迁移确认 | 保留、调整、不迁移及冲突裁决 | 完成 | `R1_REQUIREMENTS_MIGRATION_CONFIRMATION.md` |
| R2｜迁移正式候选计划 | 把 R1 决定拆成独立可验收切片 | 完成 | `R2_MIGRATION_EXECUTION_PLAN.md` |
| R3｜按优先级迁移旧 PP02 功能 | 每个切片单独测试、CI 和 Judge | 进行中 | R3.1 实现 Head 8/8 CI通过；最终Head验证后进入R3.2 |
| R4｜数据库兼容与脱敏迁移演练 | 空库/fixture/脱敏副本验证 | 未启动 | 可重复脚本、核对与回滚 |
| R5｜Windows 本机验收 | 安装、启动、Web/Desktop 与安全默认值 | Deferred | 从固定 PR Head 新建隔离目录验收 |
| R6｜正式数据迁移 | 迁移经确认的真实数据 | 未启动 | 单独数据授权、备份与回滚 |
| R7｜替换 main 与 Release | Ready、合并、main、Tag、Release | 未启动 | 每项分别精确授权 |

## 当前 R3 顺序

1. R3.1 PP02 身份与更新源：实现 Head 已通过，最终 Head CI 待收口。
2. R3.2 手动默认与自动通知总开关。
3. R3.3 官方账本上的快捷持仓。
4. R3.4 股票专用备份与恢复。
5. R3.5 应用内手动周期报告。
6. R3.6 Windows 便携更新。
7. R3.7 Windows 安全凭据。

详细文件边界、契约和验收见
[`R2_MIGRATION_EXECUTION_PLAN.md`](R2_MIGRATION_EXECUTION_PLAN.md)。

## Mainline Scope Lock

- 所有改动继续保存在 PR #3 的 Draft 分支。
- Draft 不表示 Ready、可合并、可替换 `main` 或可发布 Release。
- R4 只能使用空库、fixture 或脱敏副本；R6 正式数据必须单独授权。
- R5 Windows 验收只从固定 PR Head 新建隔离目录，不恢复或复用已消失的旧目录。
