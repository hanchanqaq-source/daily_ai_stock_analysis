# WORK-PP02-CLOUD-REBUILD-001 任务合同

## 任务身份

```text
CHAT_ROLE=WORK
WORK_ID=WORK-PP02-CLOUD-REBUILD-001
ROLE_LOCK=TRUE
STOP_RULE=TRUE
SCOPE_DRIFT=FALSE
```

## 用户结果

从可核验正式来源重新生成“官方 v3.28.0 完整业务树 + P000/P001 V1.5.6
项目控制 Overlay”的完整候选；先建立可恢复的 GitHub 远程检查点，再完成完整验证、
Draft PR、真实 CI 和 Judge。

## 范围

- 核验远程 `main`、官方 Tag/Commit、框架附件和目标分支。
- 在新的隔离目录重建官方业务树与批准的控制层。
- 运行最低完整性硬门并记录候选文件清单与树哈希。
- 通过 GitHub App/Git Data 使用 `Blob → Tree → Commit → Branch` 原子持久化。
- 运行 Python、Web、Desktop、AI 治理和差异验证。
- 创建以 `main` 为目标的 Draft PR，检查并在范围内修复真实 CI。

## 非目标

- 不执行 Ready、合并、改写或强推 `main`、Release。
- 不迁移 R1–R7 的旧业务功能，不新增产品能力。
- 不读取、复制或迁移真实用户数据，不连接真实账号、行情、通知或付费服务。
- 不使用或发布旧工作树的 7 项未提交变化。
- 不访问用户本机工作区，不进行 GitHub 设备认证。

## 允许修改

- 官方 `AGENTS.md` 中唯一明确标记的 PP02 Overlay。
- `.github/workflows/ci.yml` 的既有最小只读权限块。
- `_ai-dev/` 四份项目控制文件。
- `docs/PROJECT_CONTROL.md`、`ROADMAP.md`、`OPEN_BLOCKERS.md`、
  `REQUIREMENTS.md`、`CHANGE_HISTORY.md`、`RUNBOOK.md`、`INDEX.md`。
- `docs/pp02/` 七份重建、迁移和验收文档。
- 仅为修复本候选测试/CI 且仍在上述原始范围内所必需的文件。

## 禁止修改

- 官方业务代码、`CLAUDE.md`、License、来源信息和 Copilot 规则不得因控制层重建而改变。
- 旧工作树不得 reset、clean、stash、覆盖、删除、提交或推送。
- 不复制 P001 空白模板的通用骨架、生成器、模板历史或平行规则。

## 验收标准

1. 执行前硬门全部严格匹配，目标分支不存在。
2. 五个指定完整性文件存在；官方业务文件逐路径、模式和内容一致。
3. PP02 控制层只在批准白名单；Work 1 历史和解除证据不回退。
4. 密钥、真实数据和跨项目内容检查通过；候选清单和树哈希已记录。
5. 本地树、GitHub `create_tree` 返回树和远程 Commit 树一致。
6. 完整 Python、Web、Desktop、AI 治理、格式和范围验证有本轮结果。
7. Draft PR 保持草稿；真实 Actions 通过或形成可证明的真实阻塞。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 适用性 | 已执行；当前是已批准范围的恢复性重建 |
| 问题级别 | 无待决产品问题 |
| 问答 | 0 个问题，通过 |
| 已确认假设 | 项目、仓库、官方固定 Commit、V1.5.6、手动分析优先、定时和自动推送默认关闭、Windows 优先均由任务书/总控确认 |
| 推荐方案 | 官方固定业务树 + 最小控制 Overlay；最低硬门后先持久化，再跑完整测试 |
| 明确不做 | R1–R7、基金、真实数据、Ready/合并/Release |
| Backlog | 旧功能产品取舍、脱敏迁移演练、Windows 实机、正式数据迁移和 Release |
| 剩余阻塞 | 无 |
| 证据位置 | 本文件、`docs/pp02/`、正式重建任务书和追加式台账 |
| 允许进入 Build | 是 |

## 测试要求

- 最低硬门：`git diff --check`、`python scripts/check_ai_assets.py`、业务树完整性、
  控制层白名单、台账非回退、安全扫描、文件清单与树哈希。
- 持久化后：Python 完整离线测试、Web lint/build、Desktop 支持范围内测试、
  AI 治理、格式与差异范围检查。
- 远程：Draft PR 的真实 GitHub Actions；失败时先诊断，再做范围内最小修复。

## 授权门与回传

本 Work 已获独立分支、Commit、Draft PR、CI 和范围内修复授权；Ready、合并、
`main`、Release、真实数据和下一 Work 仍需总控另行授权。最终回传必须包含远程
基线、重建来源、旧树保护、硬门、初始/最终 Commit、树哈希、PR、测试、Actions、
Judge、阻塞、`SCOPE_DRIFT`、超授权检查和下一决定。

## 2026-07-29 用户追加授权｜同一 Work1 连续推进

- 用户明确要求继续当前 Work1，不创建新聊天或新 Work。
- R1 已授权并完成需求与旧功能迁移确认；单用户裁决覆盖此前本地档案建议。
- “下一步”授权本轮连续完成 R2 迁移计划，并进入首个 R3.1 小版本。
- R3.1 只允许 PP02 Desktop 身份、Release/更新源、ASCII 技术 ID、产物名、
  对应测试和文档；不修改股票分析、数据库、持仓、调度或通知行为。
- Windows 实机验收标记为 Deferred；不恢复、不新建或操作旧 D 盘验收目录。
- Ready、合并、main、Release、真实数据和密钥操作继续禁止。


## 2026-07-29 用户追加授权｜自动路由 v1.1 与 R3.2

- `PP02-AUTO-ROUTER-001 v1.1` 覆盖旧路由：当前 Work 在已批准范围内自动完成
  普通开发、测试、独立分支 Commit、Draft PR 更新和范围内 CI 修复，不反复询问。
- 用户发送“继续流程”，授权同一 Work1 进入 R3.2；主要执行端为云端 Codex，
  GitHub App 负责保存 Commit、更新同一 Draft PR 并验证 CI。
- R3.2 仅覆盖手动默认、默认 cron 移除、自动通知总开关、全部自动发送入口、
  设置帮助、测试和文档。
- Ready、合并、`main`、Release、Windows 本机、真实数据、真实通知渠道、
  大型依赖与付费服务继续禁止，必须单独授权。

## 2026-07-30 用户追加授权｜R3.5 应用内手动周期报告

- 继续当前 Work1 和 Draft PR #3，不重开路线、不重做 R3.1–R3.4。
- 采用“方案 A＋下周参考展望”，一次性完成 Plan、Build、Test、CI 和 Judge。
- 周期报告只聚合正式分析历史和市场复盘历史，覆盖本周至今、上一周、下周展望、
  5周、10周、1个月和2个月。
- 下周展望只使用最近 14 个自然日内的合格记录；不得重新调用 AI，不访问第二套
  报告事实表，不编造方向、目标价或确定性结论。
- 展望快照及来源记录标识必须使用现有 `AnalysisHistory` 和可识别
  `report_type` 持久化；不得创建平行历史真源。
- 只允许用户在应用内手动生成；不新增后台定时器、GitHub Actions 周五定时、
  自动模型调用、通知或报告推送。
- 允许当前分支普通 Commit、Draft PR 更新、测试先行施工、范围内 CI 修复与
  项目台账同步。
- PR 转 Ready、合并、Release、`main`、真实密钥/数据库、定时器和自动推送继续
  禁止。

### R3.5 Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 问题级别 | 无待决产品问题 |
| 问答 | 0 个问题，通过 |
| 已确认方案 | 方案 A＋条件化下周参考展望 |
| 唯一事实源 | `HistoryService.get_history_list()` / `AnalysisHistory` |
| 快照边界 | `report_type=period_outlook`，保留来源记录 ID |
| 自动化边界 | 仅应用内手动触发；无定时、模型调用或推送 |
| 允许进入 Build | 是 |

### R3.5 执行结果

- 实现 Head `4b563bc63e9638731f2a17ed25129de095046ef4` 的 Run
  `30525590779` 已 8/8 success。
- Backend：`5005 passed, 4 deselected, 51 warnings, 494 subtests passed`。
- Web 阻断套件：`55/55 passed`；Lint 与 Production Build 成功。
- 未新增 AI 调用、定时器、自动通知、事实表、基金或多用户功能。
- 当前只待本次 Judge 文档收口 Head 的完整 CI；成功后 R3.5 一次性回传总控。
