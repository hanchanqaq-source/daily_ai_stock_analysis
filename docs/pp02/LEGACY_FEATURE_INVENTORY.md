# PP02 旧功能迁移清单

本表只做 R0 分类，不实施迁移。每项必须且仅能使用一个分类：
`ALREADY_UPSTREAM`、`KEEP_AND_REIMPLEMENT`、`KEEP_AND_PORT`、`DROP` 或
`NEEDS_DECISION`。

| 功能域 | 分类 | 官方/旧证据 | 冲突与理由 | R0 动作 |
| --- | --- | --- | --- | --- |
| 股票与基金双中心旧设计 | `DROP` | 正式任务书列入旧功能域；PP02-R001/R017 固定股票专用边界 | 基金属于 PP03，双中心会重新引入跨项目耦合 | 不迁移 |
| 用户切换 | `NEEDS_DECISION` | 官方有 `src/auth.py`，但旧多用户切换的产品契约未形成可比证据 | 认证存在不等于用户切换语义相同 | R1 决策 |
| 设置页面 | `ALREADY_UPSTREAM` | `apps/dsa-web/src/pages/SettingsPage.tsx` 及其测试 | 官方已有持续维护的设置入口，旧实现会形成平行页面 | 采用官方 |
| 导入导出 | `NEEDS_DECISION` | 官方有 `portfolio_import_service.py`、`import_parser.py` 和 Web 导出工具 | 旧导入导出对象、格式和兼容范围尚未逐项确认 | R1 定义契约 |
| 手动分析 | `ALREADY_UPSTREAM` | 官方 API、Web analysis store/页面及 `main.py` 均有手动入口 | 满足“手动优先”的基础能力 | 采用官方并在后续验收 |
| 定时分析默认关闭 | `KEEP_AND_REIMPLEMENT` | 官方有 `src/scheduler.py` 和定时工作流；任务书固定默认关闭 | 能力已存在，但 PP02 的默认关闭和界面状态需在新底座明确实现/验证 | 后续独立 Work |
| 自动推送保留但默认关闭 | `KEEP_AND_REIMPLEMENT` | 官方有 `src/notification.py`；任务书固定默认关闭 | 不迁移旧配置或密钥，需在新底座建立安全默认值 | 后续独立 Work |
| 周期报告 | `NEEDS_DECISION` | 官方有报告服务和 `ReportType`，旧周期定义未形成完整对照 | 日/周/月范围和触发关系影响产品结果 | R1 决策 |
| 基金自选 | `DROP` | 正式任务书列入旧功能域；PP02-R008/R017 | 基金业务明确排除 | 不迁移 |
| 一键启动 | `KEEP_AND_REIMPLEMENT` | 官方已有 Web/API/Desktop 入口，旧一键启动脚本未审计 | 保留用户结果，但应在官方桌面结构上重做，不搬旧脚本 | 后续 Windows Work |
| GitHub Release 更新 | `ALREADY_UPSTREAM` | `.github/workflows/desktop-release.yml` 与 `scripts/verify-desktop-updater-artifacts.ps1` | 官方已有发布/更新资产；R0 不发布 Release | 采用官方，后续验收 |
| 数据库与持久化 | `ALREADY_UPSTREAM` | `src/storage.py`、`src/repositories/`、`DATABASE_PATH` 配置 | 官方已有 Schema 与迁移机制；旧数据库只能后续脱敏评估 | 采用官方架构 |
| Windows 本地使用 | `ALREADY_UPSTREAM` | `apps/dsa-desktop/`、Windows 打包工作流和 `tests/test_mimetypes_windows_init.py` | 官方 v3.28.0 已提供底座；实机仍需 R5 | 采用官方，标记未实机验证 |
| PP02 Work 1 管理与 CI 修复 | `KEEP_AND_PORT` | 用户 `main` 相对 v3.27.0 的 9 个控制路径；PR #2 历史证据 | 只保留可验证历史和 CI 最小权限，旧状态真源与旧基线文本需重构 | 在 R0 受控接入 |
| 旧仓库其他非官方提交 | `NEEDS_DECISION` | 任务书要求审计，但当前 R0 未获准把旧实现作为候选来源 | 未逐项证明需求、来源、License 和 v3.28.0 重复关系 | R1 建清单后逐项决定 |

## 分类统计

| 分类 | 数量 |
| --- | ---: |
| `ALREADY_UPSTREAM` | 5 |
| `KEEP_AND_REIMPLEMENT` | 3 |
| `KEEP_AND_PORT` | 1 |
| `DROP` | 2 |
| `NEEDS_DECISION` | 4 |
| 合计 | 15 |

本清单不授权复制旧代码，也不代表任何 R1–R7 功能已经完成。
