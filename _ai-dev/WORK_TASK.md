# WORK-002｜R3.6 Windows 便携更新任务合同

> 本文件只定义当前 Work。Work1 与旧
> `WORK-PP02-CLOUD-REBUILD-001` 的完成证据保留在 Git 历史、
> `WORK_RETURN.md` 和 `docs/CHANGE_HISTORY.md`，不得重新打开或改写。

## 任务身份

```text
CHAT_ROLE=WORK
TOP_LEVEL_WORK=WORK2
WORK_ID=WORK-002
CURRENT_WORK=R3.6 Windows便携更新
ROLE_LOCK=TRUE
STOP_RULE=TRUE
SCOPE_DRIFT=FALSE
SCOPE_DRIFT_BLOCKED=FALSE
```

## 边界纠正记录

- Work1 只负责官方稳定版干净底座，已完成并永久锁定。
- R0–R7 后续改造按当前有效管理口径归属 Work2；继续使用旧聊天窗口不能改变归属。
- 用户此前要求“继续同一 Work1”的记录是当时的历史事实；本任务合同只替换其
  当前身份效力，不倒改任何已完成代码、Commit、测试或 CI。
- PR #3 已合并到 `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- Work2 从该合并检查点建立 R3.6 独立分支和新的 Draft PR，不复用已合并的 PR #3。

## ACTIVE_GOAL

接收 Work1 已完成的 R3.6 现状核验和方案 A 设计，在 PP02 当前架构与安全边界内
实现 Windows 便携 ZIP 安全更新；先应用本次五项治理硬门，再继续业务施工。

本次治理补丁只强化现有 PP02 控制层，不改变官方 `v3.28.0` 业务底座，也不提前
实现 R3.6 业务代码。

## 允许做

- 只读核对真实项目文件、Git、测试和 GitHub CI。
- 在现有 `AGENTS.md` Overlay、四份 `_ai-dev` 文件、既有路线图、项目入口和
  追加式变更历史中应用治理硬门。
- 在 `agent/pp02-work2-r3-6-windows-portable-update` 上执行 R3.6 范围内的
  代码、测试、文档、普通 Commit、Push、Draft PR、CI 检查和范围内修复。
- 采用测试先行验证便携版识别、资产配对、下载校验、备份、替换、健康检查和回滚。
- 保持 NSIS 安装版现有更新方式不变。

## 禁止做

- 不创建 `00_PROJECT_STATUS.md`、`PROJECT_STATUS_v2.md` 或任何平行状态/路线/规则。
- 不建设新的复杂验证系统，不让辅助工具或测试成为新的主项目。
- 不重做 R3.1–R3.5，不提前进入 R3.7、R4–R7。
- 不转 Ready、不合并、不修改或强推 `main`、不创建 Tag 或 Release。
- 不读取或上传真实 `.env`、Token、API Key、Webhook、数据库或用户备份。
- 不执行真实数据迁移，不接入付费服务，不新增 AI 调用、定时任务、自动推送或
  后台自动更新入口。
- 不迁移基金、多用户或旧 `plugins/config` 机制，不顺手重构无关模块。
- 不把云端测试或打包结果冒充 Windows R5 实机验收。

## R3.6 已批准产品契约

- 采用方案 A：迁入并强化旧 Portable-M2 的安全更新思想，按 PP02 当前架构重写，
  不照搬不可靠实现。
- 只对可明确识别的 PP02 便携 ZIP 启用；NSIS 安装版继续使用原更新链路。
- 只在用户主动点击“安全更新”后下载匹配的 ZIP 与 `.sha256`。
- 替换前必须验证 SHA-256、目标版本、PP02 产品身份、压缩包结构、路径安全和
  便携版发布清单；校验未完成前不得停止旧后端或替换程序。
- 更新前备份 `.env`、SQLite 数据库、发布清单管理的旧程序文件和数据库恢复点。
- 只替换发布清单管理的程序文件；保留 `.env`、`data/`、`logs/` 和未知用户文件。
- PowerShell 更新助手隐藏运行，负责退出、替换、健康检查、失败恢复和重新启动。
- 后端健康检查与主页加载都通过后才确认成功；失败时恢复旧程序和更新前数据库。
- Windows 最终用户不安装或手动操作 Python、Node、Git。

## 五项治理硬门

1. 一次指令默认完成完整可验收大段，减少用户人工中转。
2. Work 开始和 Judge 前检查中文白话、英文界面中文含义、Codex 优先操作、真实
   进度、完整交付和默认用户不是程序员；未纠正的违反项阻止完全通过。
3. `PROJECT_STATUS.md` 与 `AI_HANDOFF.md` 必须记录
   `CURRENT_WORK`、`LAST_VALID_COMMIT`、`LAST_SUCCESSFUL_TEST`、
   `ACTIVE_BLOCKER`、`NEXT_ACTION`。
4. 检测到范围漂移时设置 `SCOPE_DRIFT_BLOCKED`；Blocker 未解除不得进入下一 Work。
5. 唯一状态真源是 `_ai-dev/PROJECT_STATUS.md`，状态冲突按真实项目文件、Git、
   实际测试、GitHub CI、状态文件、聊天描述的顺序裁决。

长任务必须显示 `Plan → Build → Test → CI → Judge`、当前正在做什么、当前
Blocker 和用户是否需要操作，不得假装回复结束后仍在后台执行。

## 执行顺序

1. Plan：核对 `main`、当前分支、PR、现有更新链路、测试和治理台账。
2. Build：先完成治理硬门最小补丁；随后按批准方案 A 实现 R3.6。
3. Test：运行治理检查、Desktop 专项、Windows 便携候选、Web Build 和受影响回归。
4. CI：使用新 Draft PR 的真实 GitHub Actions；失败时从最后有效 Commit 最小修复。
5. Judge：核对 R3.6 产品验收、用户规则、恢复检查点、范围和状态一致性后停止。

除授权门、范围变化或真实 Blocker 外，不要求用户逐项回复“下一步”。

## 验收标准

### 治理补丁

- `AGENTS.md` 仍是唯一规则真源；PP02 Overlay 外官方内容未改变。
- `_ai-dev/PROJECT_STATUS.md` 是唯一当前状态文件，仓库中没有平行命名。
- Work1 锁定、Work2 接管和 PR #3 已合并的事实与 Git 一致。
- 四份 `_ai-dev` 文件及现有路线/入口不再把 R3.6 记入 Work1。
- 五项新增 Judge 条件均可从现有文件直接核对，不新增验证程序。

### R3.6 业务实现

- 便携版与 NSIS 识别稳定，ZIP 与 SHA-256 资产准确配对。
- 包身份、版本、哈希、结构和路径安全全部校验。
- 校验完成前不停止旧后端、不替换程序。
- `.env`、数据库、日志和未知用户文件得到保护，只操作发布清单文件。
- 后端和主页健康检查通过后才确认成功；失败时程序与数据库均可恢复。
- 无命令行黑框，最终用户不依赖 Python、Node 或 Git。
- R3.1–R3.5 和官方既有功能不回归，专项测试、回归和 Draft PR CI 通过。
- 云端 Judge 最高为
  `IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`，不得冒充实机通过。

## 授权门

当前已授权：

- R3.6 独立分支；
- 普通 Commit 与 Push；
- 新 Draft PR；
- 测试与范围内 CI 修复；
- 必要项目台账同步。

仍需新授权：

- Publish Changes 的范围扩大；
- PR 转 Ready；
- Merge；
- 修改 `main`；
- Tag 或 Release；
- 真实数据迁移；
- API、密钥或付费服务；
- 大型依赖或明显范围变化。

## 当前恢复检查点

```text
CURRENT_WORK=R3.6 Windows便携更新
LAST_VALID_COMMIT=6ab647a7c2c2dca90c3a0c1626f270860073b443
LAST_SUCCESSFUL_TEST=FINAL_STATUS_HEAD_D45BDFADF22CF7BEB5E1F6777490091ED5CAC438_CI_RUN_30540784009_SUCCESS
ACTIVE_BLOCKER=NONE
NEXT_ACTION=在同一分支和Draft PR4内继续R3.6方案A业务施工；不得进入R3.7
```

准确停止点：

`WORK2_R3_6_GOVERNANCE_HARD_GATES_JUDGED_R3_6_BUILD_READY`
