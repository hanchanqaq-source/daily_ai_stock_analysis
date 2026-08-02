# PP02 安全重建路线 R0–R7

## 2026-08-02 Work10-A cloud release entry

- PR #17 is merged as `main@3e1311ee94c96d2b8d0b97bc2337ee0933a2eb65`; post-merge Run
  `30747187504` passed all eight jobs. This fixed product commit remains the v3.29.1 target.
- Work10-A adds a recoverable manual cloud release entry to the existing Desktop Release workflow.
  The implementation is locally green and Draft PR #18 is open; fixed implementation Head
  `e1a619c58670…` passed Run `30750806894` (seven applicable jobs success, Web path-skipped).
- v3.29.1 Tag/Release, workflow-PR merge and Windows real-machine acceptance remain unauthorized.

## 2026-08-02 Work9 fixed-Head closure

- Draft PR #17 implementation Head `db02221b92e210925044c5af5a4aacd2f08fcb4f` passed all
  eight jobs in Run `30745575186`.
- The final Windows ZIP, managed browser-data file, installer, first startup/health, exit, restart,
  second health/exit, uninstall and redacted diagnostic artifact all passed.
- PR #17 remains Draft and unmerged. v3.29.1 Tag/Release and Windows real-machine acceptance have
  not been performed. Next gate: explicit PR #17 merge authorization.

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
| R7｜替换 main 与 Release | Ready、合并、main、Tag、Release | 完成 | `v3.29.0` 已发布；PR #15 后续文档主线 Run `30697946093` 8/8 success |
| R7-Hotfix｜Windows 安装器补丁 | 修复 v3.29.0 `System.dll / 0xC0000005` 引导崩溃 | 等待发布授权 | PR #17 已合并；Work10-A PR #18 固定实现 Head Run `30750806894` 通过 |

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

## Work9 / PR #17 diagnostic evidence and Windows closure（2026-08-02）

- Work8 以 `COMPLETED_WITH_BLOCKER` 结束；固定诊断 Head `eae4b465…` 的 Run
  `30742085965` 为 7 成功、1 Windows 失败，且没有保留诊断 artifact。
- Work9 在当前分支 Head `9cb9a70e9176711096adf12ba5674c56d6f314d2` 正式接管，继续
  Draft PR #17。顺序锁定为诊断契约、最终 ZIP、固定 Head Windows CI、证据化根因、
  最小修复和完整 CI。
- 范围内 Commit/Push/CI 已授权；Ready、Merge、main、Tag、Release、真实数据/凭据
  和 Windows 真机动作仍受停止门约束。

## Work8 / R7 Windows installer hotfix（2026-08-01）

- v3.29.0 正式安装器来源、大小与 SHA-256 正确，但在 Windows 11 build 26200 上
  连续 2/2 于安装向导前以 `System.dll / 0xC0000005` 崩溃；R7 首次使用验收为 FAIL。
- 用户已授权 Work8、选择保留安装向导，并批准 Desktop 测试与 Windows/macOS
  打包/发布任务升级至 Node 22；独立 Web 门保持 Node 20。
- Draft PR #17 精确锁定 `electron-builder 26.15.7`，保留当前用户安装和目录选择，
  并让 PR/Release 共用隔离 install/start/uninstall 验证器。
- 本地 Desktop 与专项检查通过；固定 Head Run `30742085965` 的七个非 Windows
  任务成功，但 Windows 契约在真实安装生命周期前失败，且没有诊断 artifact。
- 未授权 Ready、Merge、main、`v3.29.1` Tag/Release 或最终 Windows 实机验收。

## Work7 / R7 最终完成（2026-08-01）

- PR #12、#13、#14 已按固定 Head 与完整 CI 门合并；发布提交为
  `49759dbd032f577d32e8e0f6670298f700e0f272`。
- 该发布提交的 `main` push CI 8/8 success；annotated Tag `v3.29.0`
  精确指向该提交。
- GitHub Release 非 Draft、非 Prerelease；Windows、macOS 共 7 个正式资产以及
  Docker/GHCR 发布成功。
- PR #15 已补充三语言来源声明并合并为
  `main@b4a0ec11da19b5552ce87dde1ece716f61fd5174`；合并后 Run
  `30697946093` 8/8 success，Tag 未移动。
- Work6 `NO_FORMAL_DATA_FOUND` 结论保持不变；R7 未执行任何真实数据库搜索、
  创建或迁移。
- R0–R7 路线已全部完成。下一目标必须建立新 Work 并重新授权；不得继承 Work7
  的 Ready、合并、`main`、Tag 或 Release 权限。

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
