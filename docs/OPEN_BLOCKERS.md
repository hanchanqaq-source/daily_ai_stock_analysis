# PP02 当前阻塞

当前状态和当前 Active Blocker 以
[`../_ai-dev/PROJECT_STATUS.md`](../_ai-dev/PROJECT_STATUS.md) 为唯一真源。下列
`WORK-001` 项目均为追加式历史记录；其解除证据完整保留，不因本次
`WORK-PP02-CLOUD-REBUILD-001` 启动而回退。当前 R0 已完成候选远程持久化和
本地完整验证，没有新增已确认阻塞；“Draft PR/CI 尚未触发”是执行顺序中的预期
状态，不登记为阻塞。

## WORK-001-BLOCKER-001｜远端完整历史尚未导入

| 项目 | 当前事实 |
| --- | --- |
| 发现日期 | 2026-07-22 |
| 影响步骤 | Work 1.4.1，继而阻塞 CI 和 Judge |
| 本地状态 | 已从官方 Tag 取得完整可追溯仓库；Tag 解引用 Commit 为 `b36c721415560e48115ad4444d5af2125fc53f5c` |
| 远端状态 | 新私有仓库已完成 ChatGPT/Codex 授权且具有管理员/推送权限，但尚未含官方历史；仅有一次性导入尝试产生的临时引导提交 |
| 原因 | 当前云端没有 `gh`，本地 Git 没有私有仓库推送凭据；GitHub 连接器不能跨仓库复制 899 个提交；连接器提交未触发一次性 Actions 引导任务 |
| 风险 | 若直接用连接器复制文件，只能得到快照，会违反“保留官方提交历史”的已选方案 |
| 解除条件 | 通过 GitHub 官方 Import code 或已认证 Git 执行历史导入；随后确认目标 `main` 可追溯到 `b36c7214…`，并清除临时引导内容 |

阻塞解除后，在本节下追加解除日期、采用方法和验证证据，不删除本记录。

## 已完成但不解除本阻塞的验证

- 本地官方 Tag 与完整 899 条上游提交历史已核验。
- PP02 管理层已在官方基线之上形成独立本地提交。
- 云端依赖安装、后端官方门禁、Web lint/build、API 健康检查和 Web 页面启动均通过。
- 这些结果证明代码底座可运行，但不能代替远端完整历史导入。

## WORK-001-BLOCKER-001 解除记录

| 项目 | 解除证据 |
| --- | --- |
| 解除日期 | 2026-07-23 |
| 采用方法 | 一次性 Actions 导入已把官方 Git 对象传入目标仓库；随后使用已授权的 GitHub 管理权限将远端 `main` 精确移动到官方 Commit |
| 远端结果 | `main = b36c721415560e48115ad4444d5af2125fc53f5c`，最新提交序列与官方历史一致，临时引导工作流不在正式代码树中 |
| 结论 | 完整历史导入阻塞已解除；不得删除本历史记录 |

## WORK-001-BLOCKER-002｜目标仓库尚未建立基线 Tag

| 项目 | 当前事实 |
| --- | --- |
| 发现日期 | 2026-07-23 |
| 影响步骤 | Work 1.4.1、Work 1.6 |
| 已完成 | 目标仓库 `main` 已准确指向官方 `b36c7214…`，完整历史与 MIT License 可读 |
| 未完成 | 目标仓库内尚无 `v3.27.0` Tag；按该 ref 读取返回 404 |
| 风险 | Commit 基线真实且可追溯，但目标仓库不能通过 Tag 名直接复核，Runbook 的 Tag 校验命令暂不能在新远端成立 |
| 解除条件 | 在目标仓库建立指向 `b36c721415560e48115ad4444d5af2125fc53f5c` 的 `v3.27.0` Tag，并重新核验 Tag 解引用结果 |

## WORK-001-BLOCKER-002 解除记录

| 项目 | 解除证据 |
| --- | --- |
| 解除日期 | 2026-07-23 |
| 复核结果 | Work 1 原验收要求是“从官方稳定 Tag 建立底座并可追溯到 Tag Commit”，不要求在目标仓库复制同名 Tag |
| 真源边界 | `v3.27.0` Tag 继续以上游 `ZhuLinsen/daily_stock_analysis` 为真源；PP02 以固定 Commit 和祖先关系验收 |
| 文档修正 | Runbook 改为从 `upstream` 核对 Tag，再验证该 Commit 是 PP02 `HEAD` 的祖先 |
| 结论 | 不降低原验收标准；目标仓库缺少重复 Tag 不再阻塞 Work 1 |

## WORK-001-BLOCKER-003｜GitHub 阻断 CI 需要 Pull Request

| 项目 | 当前事实 |
| --- | --- |
| 发现日期 | 2026-07-23 |
| 影响步骤 | Work 1.6、Judge |
| 工作流事实 | `.github/workflows/ci.yml` 只监听目标为 `main` 的 `pull_request`，直接更新 `main` 不触发该阻断 CI |
| 已完成 | 本地执行等价后端门禁、Web lint/build、AI 治理和启动健康检查均通过 |
| 当前授权 | `WORK-001-AUTH-001` 覆盖首次导入和推送，不覆盖为 CI 新建分支及 Draft PR |
| 解除条件 | 用户授权为 Work 1 CI 建立最小验证分支和 Draft PR；CI 通过后关闭 PR，不合并业务改动，并完成 Judge |


## WORK-001-BLOCKER-003 进展与正式修复

| 项目 | 当前证据 |
| --- | --- |
| 验证日期 | 2026-07-23 |
| 根因 | `dorny/paths-filter@v3` 在 Pull Request 事件中需要读取 PR 文件列表，但工作流未声明 `pull-requests: read`，导致 `Resource not accessible by integration` |
| 已验证修复 | 在已关闭、未合并的 Draft PR #1 中增加顶层只读权限 `contents: read` 与 `pull-requests: read`；运行 `29984211231` 完整成功 |
| 正式处理 | 用户已授权从最新 `main` 创建正式修复分支，永久加入同一最小权限并同步 Work 1 台账 |
| 当前状态 | 已解除；正式 PR #2 的 CI 运行 `29986024984` 成功，并已按用户授权合并到 `main` |
| 解除证据 | PR #2 已合并为 `a6bdfb55827080e196c2103292aaedfadc224dc7`；`main` 已包含 `contents: read` 与 `pull-requests: read`；仅剩 Windows 实机验收 |
