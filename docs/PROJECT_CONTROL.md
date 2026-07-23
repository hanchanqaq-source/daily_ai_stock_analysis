# PP02 项目总入口

## 项目身份

| 项目 | 当前值 |
| --- | --- |
| 项目名称 | `PP02｜AI 每日股票分析` |
| GitHub 仓库 | `hanchanqaq-source/daily_ai_stock_analysis` |
| 官方上游 | `ZhuLinsen/daily_stock_analysis` |
| 官方稳定基线 | `v3.27.0` |
| 官方基线 Commit | `b36c721415560e48115ad4444d5af2125fc53f5c` |
| License | MIT |
| 当前 Work | `WORK-001｜官方稳定版干净底座建立` |
| Work 总体状态 | `Waiting for User`（正式 CI 权限修复已进入 Draft PR 阶段；等待本次 CI 复核与合并决定） |

PP02 是新的股票专用项目。旧股票基金混合仓库只读冻结；基金业务属于 PP03，不进入本仓库。

## 文档导航

| 文档 | 唯一职责 |
| --- | --- |
| [`AGENTS.md`](../AGENTS.md) | 项目级强制开发规则与授权边界 |
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | 唯一需求总表 |
| [`ROADMAP.md`](ROADMAP.md) | 当前及后续 Work 的滚动路线图 |
| [`CHANGE_HISTORY.md`](CHANGE_HISTORY.md) | 用户决策和范围变化的追加历史 |
| [`OPEN_BLOCKERS.md`](OPEN_BLOCKERS.md) | 当前未解除阻塞 |
| [`RUNBOOK.md`](RUNBOOK.md) | 安装、启动、验证和恢复 |
| [`CHANGELOG.md`](CHANGELOG.md) | 产品版本变化；不代替项目控制台账 |

## Work 1 当前状态

| 阶段 | 状态 | 当前内容 |
| --- | --- | --- |
| Plan | 完成 | 已确认角色、边界、稳定 Tag、Commit、License 和建仓方案 |
| Build | 完成 | 远端保留官方完整历史，并在官方基线之上发布 PP02 管理层 |
| Test | 完成 | 云端依赖、后端门禁、Web lint/build、启动和健康检查均通过；Windows 另行验收 |
| CI | 复核中 | 验证运行 `29984211231` 已完整通过；正式权限修复将在本次 Draft PR 中重新执行全部门禁 |
| Judge | 等待 | 底座质量已验证；等待正式权限修复 PR 的 CI 结论及用户合并决定 |
| Windows验收 | 待验收 | 必须在 Windows 实机验证安装、启动与 Web 界面 |

正式权限修复合入并完成 Windows 实机验收前，不得进入 Work 2。

状态口径：本文件是 Work 总体状态和阶段汇总真源；`ROADMAP.md` 是子步骤状态真源。状态变化必须在同一改动中同步，冲突时不得宣称完成，先按验证证据校正。

## Work 1 云端验证证据

验证对象是官方基线 `b36c7214…` 加 PP02 管理层的准确提交树，不读取或复制旧混合项目数据。

| 检查 | 结果 |
| --- | --- |
| Python 依赖安装 | 通过；Python `3.12.13`，官方 `requirements.txt` 未修改 |
| 后端官方门禁 `./scripts/ci_gate.sh` | 通过；`4671 passed`、`4 deselected`、`416 subtests passed` |
| Web 依赖、lint、build | 通过；Node `24.14.0`、npm `11.9.0`、Vite 生产构建成功 |
| 后端与 Web 启动 | 通过；`GET /api/health` 返回 HTTP 200 和 `status=ok`，Web 根页面返回 HTTP 200 |
| 业务代码差异 | 通过；远端相对官方 Commit 仅存在 8 个批准的管理/文档文件差异，业务目录零差异 |
| License | 通过；MIT 文件与官方基线 SHA-256 一致 |
| AI 协作资产检查 | 通过；在准确提交树归档中执行 `scripts/check_ai_assets.py` 成功 |
| 新会话规则识别 | 通过；无 Work 启动标记的独立会话正确默认为 `PROJECT_CONTROL`，并识别项目、边界、流程、三选一、授权门和唯一台账 |
| 远端提交链 | 通过；首轮校正后的管理层提交为 `14be9288…`，官方 `b36c7214…` 是当前 `HEAD` 的可追溯祖先；PP02 仅增加管理层提交 |
| Work 1 CI 验证 | 通过；Draft PR #1 的运行 `29984211231` 中 Change Detection、AI governance、backend gate 和 Docker build 均成功，Web gate 因无前端改动而按有效路径判断跳过；PR 已关闭且未合并 |

未配置股票列表、AI 模型密钥和通知渠道时会产生预期告警；Work 1 未使用真实密钥、付费服务、通知或交易能力。

## 启动读取顺序

1. `AGENTS.md`
2. 本文件
3. `REQUIREMENTS.md`
4. `ROADMAP.md`
5. `CHANGE_HISTORY.md`
6. `OPEN_BLOCKERS.md`
7. 当前任务涉及的 `RUNBOOK.md`、业务文档和测试文件

## 历史保护

- 完成项只追加验收记录，不倒改成“未完成”。
- 范围改变只调整未完成步骤，并在 `CHANGE_HISTORY.md` 追加原因。
- 阻塞解除后保留原始记录和解除证据，不删除历史。
