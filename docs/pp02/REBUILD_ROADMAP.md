# PP02 安全重建路线 R0–R7

唯一当前状态见 [`../../_ai-dev/PROJECT_STATUS.md`](../../_ai-dev/PROJECT_STATUS.md)。
当前采用 `PP02-WORK-HANDOFF-002`：一个完整大段使用一个 Work 聊天；聊天不绑定
永久角色，不改显示名称，交接依赖唯一状态和 GitHub 事实，用户无需搬运施工单。

| 阶段 | 目标 | 当前状态 | 完成证据 |
| --- | --- | --- | --- |
| R0｜云端安全重建底座 | 官方 v3.28.0 + V1.5.6 控制层候选、Draft PR 与 CI | 完成 | PR #3 两轮 7/7 CI、最终 Judge |
| R1｜需求与旧功能迁移确认 | 保留、调整、不迁移及冲突裁决 | 完成 | `R1_REQUIREMENTS_MIGRATION_CONFIRMATION.md` |
| R2｜迁移正式候选计划 | 把 R1 决定拆成独立可验收切片 | 完成 | `R2_MIGRATION_EXECUTION_PLAN.md` |
| R3｜按优先级迁移旧 PP02 功能 | 每个切片单独测试、CI 和 Judge | 完成 | R3.1–R3.7 已由 PR #11 合入 `main@eb32298…` |
| R4｜数据库兼容与脱敏迁移演练 | 空库/人工假数据验证 | 完成 | PR #12 Head `f1b433a7…` / Run `30660971800` |
| R5｜Windows 本机验收 | 安装、启动、Web/Desktop 与安全默认值 | 完成 | Work2 / PR #9 真机启动与回滚模拟通过 |
| R6｜正式数据迁移 | 迁移经确认的真实数据 | 完成（无数据，跳过迁移） | Work6 `NO_FORMAL_DATA_FOUND`；旧项目和数据库从未建立 |
| R7｜替换 main 与 Release | Ready、合并、main、Tag、Release | 进行中 | 已选 A / `v3.29.0`；按固定 Head 与 CI 门连续执行 |

## 当前 R3 顺序

1. R3.1 PP02 身份与更新源：完成。
2. R3.2 手动默认与自动通知总开关：完成。
3. R3.3 官方账本上的快捷持仓：完成。
4. R3.4 股票专用备份与恢复：完成。
5. R3.5 应用内手动周期报告＋下周参考展望：完成。
6. R3.6 Windows 便携更新：完成。
7. R3.7 Windows 安全凭据：完成。

详细文件边界、契约和验收见
[`R2_MIGRATION_EXECUTION_PLAN.md`](R2_MIGRATION_EXECUTION_PLAN.md)。

## Work7 / R7 主线与发布门（2026-08-01）

- 用户已选择 A / `v3.29.0`，精确授权 PR #12/#13 Ready 与合并、最终 `main` CI、
  annotated Tag 和对应 Release。
- PR #13 叠加在 PR #12 上；顺序固定为先合并 #12，再把 #13 Base 改为 `main`，
  验证新固定 Head CI 后合并 #13。
- Tag 必须精确指向已通过 push CI 的最终 `main` Head；Release 工作流与正式资产未
  全部成功前不得宣布 R7 完成。
- Work6 已裁决 `NO_FORMAL_DATA_FOUND`，R7 不进行任何数据库搜索、创建或迁移。

## Mainline Scope Lock（历史）

- 每个新大段使用独立分支和独立 Draft PR；当前 Work4 Base 为 `main@eb32298…`。
- Draft 不表示 Ready、可合并、可替换 `main` 或可发布 Release。
- 本 Work4 的 R4 只能使用空库或人工假数据；R6 正式数据必须单独授权。
- R5 Windows 验收只从固定 PR Head 新建隔离目录，不恢复或复用已消失的旧目录。

## Work2 / R3.6 Windows 便携安全更新（2026-07-30）

Work1 已永久关闭；PR #3 已合并且 R3.1–R3.5 已进入 main。Work2 从 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 以独立分支和独立 Draft PR 接管 R3.6。实现范围与证据见 `docs/pp02/R3_6_WINDOWS_PORTABLE_UPDATE_IMPLEMENTATION.md`。R5 Windows 真机验收仍为后续授权门，本轮不进入 R3.7。

## Work3 / R3.7 Windows 安全凭据（2026-07-31）

PR #11 最终 Head `173b3d3…` 完成 8/8 CI 和固定 Head Windows 假凭据验收，
并已合入 `main@eb32298…`。Work3 已关闭。

## Work4 / R4 数据库兼容与脱敏迁移演练（2026-07-31）

用户选择方案 A。当前先校正状态并关闭已由 PR #9 替代的历史 Draft PR #7/#8，
保留分支和历史；随后通过合成证明、临时数据库副本、现有股票备份恢复契约和失败
回滚探针形成可重复演练。只用空库和人工假数据，停在独立 Draft PR 完整 CI。

最终实现 Head `f1b433a7…` 的 Run `30660971800` 全部适用 Job success；PR #12
保持 Draft，Work4 Judge 为 `PASS — WORK4 COMPLETED — DRAFT_HOLD`。下一未启动大段
是 Work5 / R6 正式数据迁移授权与计划；真实数据库和数据仍需单独授权。
