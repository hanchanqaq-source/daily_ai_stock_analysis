# PP02 项目总入口

## 当前项目控制

当前状态唯一真源为 [`../_ai-dev/PROJECT_STATUS.md`](../_ai-dev/PROJECT_STATUS.md)；
新聊天交接入口为 [`../_ai-dev/AI_HANDOFF.md`](../_ai-dev/AI_HANDOFF.md)。本文件只保留
项目入口、版本关系和历史索引，不再作为当前状态真源。

| 项目 | 当前值 |
| --- | --- |
| 项目名称 | `PP02｜AI 每日股票分析` |
| GitHub 仓库 | `hanchanqaq-source/daily_ai_stock_analysis` |
| 官方上游 | `ZhuLinsen/daily_stock_analysis` |
| 当前官方基线 | `v3.28.0` / `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c` |
| 项目控制框架 | `P000/P001 V1.5.6` |
| 当前 Work | `WORK-PP02-CLOUD-REBUILD-001` |
| 当前阶段 | R1/R2/R3.1 完成；R3.2 实现 Head 8/8 CI 通过，等待最终 Head 收口 |
| 后续路线 | [`pp02/REBUILD_ROADMAP.md`](pp02/REBUILD_ROADMAP.md)；Windows 验收 Deferred |

## Work 1 历史身份

| 项目 | 当前值 |
| --- | --- |
| 项目名称 | `PP02｜AI 每日股票分析` |
| GitHub 仓库 | `hanchanqaq-source/daily_ai_stock_analysis` |
| 官方上游 | `ZhuLinsen/daily_stock_analysis` |
| 官方稳定基线 | `v3.27.0` |
| 官方基线 Commit | `b36c721415560e48115ad4444d5af2125fc53f5c` |
| License | MIT |
| 当前 Work | `WORK-001｜官方稳定版干净底座建立` |
| Work 总体状态 | `Waiting for User`（当时的云端 Plan、Build、Test、CI、Judge 已完成；等待 Windows 实机验收） |

PP02 是新的股票专用项目。旧股票基金混合仓库只读冻结；基金业务属于 PP03，不进入本仓库。

## 文档导航

| 文档 | 唯一职责 |
| --- | --- |
| [`AGENTS.md`](../AGENTS.md) | 项目级强制开发规则与授权边界 |
| [`../_ai-dev/PROJECT_STATUS.md`](../_ai-dev/PROJECT_STATUS.md) | 唯一当前状态真源 |
| [`../_ai-dev/AI_HANDOFF.md`](../_ai-dev/AI_HANDOFF.md) | 新聊天交接入口 |
| [`pp02/REBUILD_ROADMAP.md`](pp02/REBUILD_ROADMAP.md) | R0–R7 重建路线 |
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | 唯一需求总表 |
| [`ROADMAP.md`](ROADMAP.md) | 已接受历史与重建路线导航 |
| [`CHANGE_HISTORY.md`](CHANGE_HISTORY.md) | 用户决策和范围变化的追加历史 |
| [`OPEN_BLOCKERS.md`](OPEN_BLOCKERS.md) | 阻塞及解除记录 |
| [`RUNBOOK.md`](RUNBOOK.md) | 安装、启动、验证和恢复 |
| [`CHANGELOG.md`](CHANGELOG.md) | 产品版本变化；不代替项目控制台账 |

## Work 1 历史状态

| 阶段 | 状态 | 当前内容 |
| --- | --- | --- |
| Plan | 完成 | 已确认角色、边界、稳定 Tag、Commit、License 和建仓方案 |
| Build | 完成 | 远端保留官方完整历史，并在官方基线之上发布 PP02 管理层 |
| Test | 完成 | 云端依赖、后端门禁、Web lint/build、启动和健康检查均通过；Windows 另行验收 |
| CI | 完成 | 正式 PR #2 的运行 `29986024984` 全部应执行门禁通过；Web gate 因无前端改动而正确跳过 |
| Judge | 通过 | PR #2 已按授权合并到 `main`，合并提交 `a6bdfb55827080e196c2103292aaedfadc224dc7`；业务代码零修改 |
| Windows验收 | 待验收 | 必须在 Windows 实机验证安装、启动与 Web 界面 |

Windows 实机验收完成前，不得进入 Work 2。

历史口径：本节记录 Work 1 当时的完成事实，不因本次 R0 重建而回退。当前状态以
`_ai-dev/PROJECT_STATUS.md` 为唯一真源；摘要冲突时先按可验证证据校正。

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

## WORK-003 / R3.7 当前控制摘要

| 阶段 | 状态 | 证据/边界 |
| --- | --- | --- |
| Plan | 完成 | 固定 `main@097bb5d60aa42f13737ac4d9db2f582bde50f995`，先冻结威胁模型与 TDD 计划 |
| Build | 完成 | `safeStorage`/DPAPI vault、版本绑定、窄 IPC、backend 环境注入、导入导出与泄漏扫描 |
| Test | 本地通过 | Python/契约 `340/340`，Desktop `80/80`，Web 阻断 `127/127`，Lint/Build/治理/根目录假密钥扫描通过 |
| Review | 通过 | 四次独立安全复审后未发现 Critical/Important；批准发布到现有 Draft PR `#11` |
| CI | 待验证 | 下一发布 Head 必须八项完整通过；Windows Job 必须同 Head 执行假凭据 safeStorage 与 artifact 扫描 |
| Judge | `DRAFT_HOLD` | 不得 Ready、合并、main 直写、Tag、Release、真实凭据/数据或后续阶段 |
