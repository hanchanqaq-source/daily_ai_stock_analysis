# PP02 新聊天交接

## 身份与基线

| 项目 | 当前值 |
| --- | --- |
| 仓库 | `hanchanqaq-source/daily_ai_stock_analysis` |
| 远程 main 最近核验 | `f2253226c0974e3d241d496a1af8ede61c599b58` |
| 官方来源 | `ZhuLinsen/daily_stock_analysis` |
| 官方 Tag / Commit | `v3.28.0` / `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c` |
| 框架 | P000/P001 V1.5.6；总包 SHA-256 `06B8B4F196097C50B5E1A232B55BB7D14F41E1133C6D44945F0146693A79C7C4` |
| Work | `WORK-PP02-CLOUD-REBUILD-001`，`ROLE_LOCK=TRUE` |

## 当前候选

- 状态：最低完整性硬门已通过，等待 GitHub App 原子持久化。
- 已完成：远程 `main`、官方 Tag/Commit、目标分支不存在和框架附件均已只读核验；
  已从官方固定 Commit 建立新的隔离候选；业务树、控制白名单、历史非回退、格式、
  AI 治理、安全和候选清单检查均通过。
- 未完成：原子持久化、完整 Python/Web/Desktop 验证、Draft PR 和真实 GitHub Actions。
- 当前阻塞：无。
- 下一动作：再次核验远程硬门并立即建立候选远程持久化检查点。

## 必读文件

1. [`PROJECT_STATUS.md`](PROJECT_STATUS.md)——唯一当前状态真源。
2. [`WORK_TASK.md`](WORK_TASK.md)——当前授权、范围和验收。
3. [`../AGENTS.md`](../AGENTS.md)——官方规则与 PP02 Overlay。
4. [`../docs/pp02/UPSTREAM_BASELINE.md`](../docs/pp02/UPSTREAM_BASELINE.md)。
5. [`../docs/pp02/REBUILD_DIFF_SUMMARY.md`](../docs/pp02/REBUILD_DIFF_SUMMARY.md)。
6. [`WORK_RETURN.md`](WORK_RETURN.md)——只读取本 Work 的新鲜结果。

## 验收与授权边界

- 验收：官方业务树完整、控制层白名单、台账不回退、安全扫描、树一致性、完整测试、
  Draft PR 真实 CI 和 Judge 均有证据。
- 已授权：GitHub App/Git Data 原子 Commit、独立分支
  `agent/pp02-v3.28.0-cloud-rebuild`、Draft PR、CI 检查和范围内修复。
- 禁止：Ready、合并、修改或强推 `main`、Release、真实数据、下一业务 Work、设备认证。
- CI 状态：未触发；不得把旧 `main` 或 Work 1 的 CI 当作本候选 CI。
- 最后更新：2026-07-26。

若本文件与 `PROJECT_STATUS.md` 冲突，立即报告差异并以可验证证据修正，不得自行扩大范围。
