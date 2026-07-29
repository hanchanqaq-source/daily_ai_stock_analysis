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

- 状态：R1、R2、R3.1 已完成；R3.2 实现 Head 已通过完整 CI，正在收口最终 Head。
- 已完成：远程 `main`、官方 Tag/Commit、目标分支不存在和框架附件均已只读核验；
  已从官方固定 Commit 建立新的隔离候选；业务树、控制白名单、历史非回退、格式、
  AI 治理、安全和候选清单检查均通过；初始候选已持久化到独立分支，完整
  Python/Web/Desktop 本地验证已通过；Draft PR `#3` 的首轮 CI Run
  `30220968264` 已 7/7 success。
- 未完成：Windows 实机、真实数据以及任何 Ready/合并/Release；这些均不在当前
  Work 授权内。
- 当前阻塞：无。
- 下一动作：验证 R3.2 文档收口后的最终 Head；保持 PR 为 Draft，随后进入 R3.3。

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
- 初始持久化：分支 `agent/pp02-v3.28.0-cloud-rebuild`，Commit
  `9a2588004ba3436faa2b61d489fc8eab564ccef4`，本地/远程树
  `c157f143640d056892ba5b1345e65a63eb86babd`。
- Draft PR：`#3` /
  `https://github.com/hanchanqaq-source/daily_ai_stock_analysis/pull/3`，保持草稿。
- CI 状态：本候选 Run `30220968264` 的 Change Detection、AI governance、
  backend、Docker、Web、Windows Futu 冻结和 macOS Desktop 包共 7 个 Job 全部
  success；收口证据 Commit 的最终 Head CI 结果由外部回传报告记录。
- 最后更新：2026-07-26。

若本文件与 `PROJECT_STATUS.md` 冲突，立即报告差异并以可验证证据修正，不得自行扩大范围。

## 2026-07-29 R1/R2 追加交接

- 用户要求继续同一 Work1，不创建新聊天或新 Work。
- R1 已完成；最终裁决是官方单用户模式，旧用户档案、切换、隔离和用户级备份全部不迁移。
- R2 已完成；实施顺序见
  `docs/pp02/R2_MIGRATION_EXECUTION_PLAN.md`。
- 当前 Active Goal 是 R3.1 PP02 Desktop 身份与更新源。
- Windows 实机为 Deferred；PR #3 继续保持 Draft。

## 2026-07-29 R3.1 追加交接

- R3.1 PP02 身份与更新源已实现。
- 实现 Head `639d2bc8fc605fbe553fb9c16df7137042bb2079` 的 CI Run
  `30488603501` 为 8/8 success。
- CI 已新增 `desktop-test`，Desktop 测试为 49/49。
- macOS productName 固定路径遗漏已修复并记录到
  `docs/ERRORS_AND_LESSONS.md`。
- 当前只待 Judge 文档收口后的最终 Head CI；PR #3 保持 Draft。
- 下一迁移切片：R3.2 手动默认与自动通知总开关。


## 2026-07-29 R3.2 追加交接

- R3.1 收口 Head `1740fa3655b5eed55c7e4ebda81523ca8095e176` 的
  Run `30489293885` 已 8/8 success，旧“最终 CI 待通过”状态已关闭。
- R3.2 已删除每日 Workflow 默认 cron，并建立
  `AUTO_NOTIFICATION_ENABLED=false` 产品级总开关。
- CLI、市场复盘、运行时调度、Alert Worker 及 Web/API 自动发送入口均受同一总开关约束；
  手动测试通知保持独立。
- R3.2 实现 Head `5316b5ea2ececd9aff0ced556e897f0738dad317` 的
  Run `30493475960` 为 8/8 success；后端 `4976 passed`。
- 当前只待 Judge 文档收口后的最终 Head CI；PR #3 保持 Draft。
- 下一迁移切片：R3.3 官方账本上的快捷持仓。
