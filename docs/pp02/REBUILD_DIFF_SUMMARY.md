# PP02 重建差异摘要

## 三棵树

| 树 | 身份 | 用途 |
| --- | --- | --- |
| 用户远程 main | `f2253226c0974e3d241d496a1af8ede61c599b58` | 新候选唯一父提交；不得修改 |
| 官方业务树 | `v3.28.0` / `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c` | 候选完整业务基底 |
| 本地候选树 | 最低完整性硬门后记录 | 官方业务树 + 批准控制层 |

共同历史基点为 `b36c721415560e48115ad4444d5af2125fc53f5c`。用户
`main` 相对该基点是 5 个提交、9 个控制路径；官方 v3.28.0 相对该基点是
22 个提交、141 个变化路径。

## 用户 main 的 9 个控制路径

1. `.github/workflows/ci.yml`
2. `AGENTS.md`
3. `docs/CHANGE_HISTORY.md`
4. `docs/INDEX.md`
5. `docs/OPEN_BLOCKERS.md`
6. `docs/PROJECT_CONTROL.md`
7. `docs/REQUIREMENTS.md`
8. `docs/ROADMAP.md`
9. `docs/RUNBOOK.md`

处理结果：

- `.github/workflows/ci.yml`：以官方 v3.28.0 为底，只重放
  `contents: read` 与 `pull-requests: read`。
- `AGENTS.md`：以官方文件为底，只加一个可机械剥离的 PP02 Overlay。
- 七份 PP02 控制文档：保留 Work 1 历史，迁移到 V1.5.6 职责；
  `docs/INDEX.md` 增加导航。

## 候选控制层白名单

- 上述 9 个路径。
- `_ai-dev/PROJECT_STATUS.md`、`AI_HANDOFF.md`、`WORK_TASK.md`、`WORK_RETURN.md`。
- `docs/pp02/` 下本 R0 要求的 7 份文档。

白名单以外的候选内容必须与官方 v3.28.0 的路径、Git mode 和 Blob 完全一致。
`docs/CHANGELOG.md` 使用官方 v3.28.0 内容，不承载 PP02 项目控制历史。

## 冲突、重复与范围结论

- Git 路径冲突：CI 1 项，已采用官方底稿 + 最小权限增量。
- 语义冲突：旧 `AGENTS.md`、PROJECT_CONTROL/ROADMAP 状态真源和 v3.27.0
  当前口径；已通过单一 Overlay 与 `_ai-dev/PROJECT_STATUS.md` 收敛。
- 重复能力：见 `LEGACY_FEATURE_INVENTORY.md`；官方已有能力不迁移旧实现。
- 产品迁移：R0 为零；`src/`、`api/`、`apps/`、`data_provider/`、`bot/` 等
  业务代码不得产生 PP02 控制层差异。
- 树哈希：为避免文档自引用改变树对象，最终本地/远程树哈希记录在 GitHub
  原子持久化结果和 Work 回传报告中。
