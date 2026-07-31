# WORK-004｜R4 数据库兼容与脱敏迁移演练任务合同

## 当前任务身份

```text
WORK_ID=WORK-004
WORK_STATE=COMPLETED
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=eb32298c8f3cbec2ff400dda37d3267a7181af40
BRANCH=agent/pp02-work4-r4-database-rehearsal
SCOPE_DRIFT=FALSE
```

## 用户结果

把“一个大段一个 Work”的自动接力规则写入现有唯一框架，并在同一 Work4 内只用
空库和人工假数据完成 R4 可重复兼容检查、股票事件迁移、脱敏排除和失败回滚演练；
建立独立 Draft PR 和完整 CI 后停下。

## 范围

- 校正 Work3/R3.7 已合并事实和 R4 路线；关闭被 PR #9 替代的 PR #7/#8，保留分支。
- 更新 `AGENTS.md` 和现有状态/交接/任务/回传文件，不建立第二套状态中心。
- 冻结 R4 设计和实施计划，按 RED→GREEN 实现可重复脚本与专项测试。
- 输入只接受空 SQLite 或与 SHA-256 绑定的人工合成证明；源文件只读且保持不变。
- 复用 `DatabaseManager` 与 `PortfolioBackupService`，只迁移正式股票事件账本。
- 输出安全报告并验证失败回滚；运行本地门禁、Draft PR 完整 CI 和 Judge。

## 非目标与硬边界

- 不读取、复制、脱敏、打开或迁移真实数据库、真实备份、真实账号或真实凭据。
- 不迁移基金、用户档案、多用户隔离、旧快捷持仓表、派生持仓、缓存或日志。
- 不修改聊天显示名称，不要求用户跨聊天复制施工单或完成报告。
- 不 Ready、不合并、不写 `main`、不 Tag、不 Release、不进入 R5/R6/R7。

## 验收标准

1. 新自动接力规则只有一个活动真源，旧窗口锁明确 Superseded。
2. RED 测试在实现缺失时按预期失败；GREEN 覆盖空库、合成混合库、拒绝边界和回滚。
3. 源 SHA-256 前后一致；目标只含现有正式股票事件导出的允许内容。
4. 报告不含行值、备份正文或构造的假敏感值。
5. 本地完整后端门和 Draft PR 固定 Head 完整 CI 通过。
6. Work4 只在状态、GitHub、测试和 CI 全部一致后宣布结束。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 用户决定 | `选A`，完整启动 Work4 |
| 待决产品问题 | 0 个；技术方案复用现有事实源和恢复契约 |
| 数据风险 | 真实数据库/数据禁止；只接受空库和人工合成证明 |
| Judge 上限 | `PASS — DRAFT_HOLD` |
| 允许进入 Build | 是；先完成设计/计划检查点和 RED |

## 完成状态

- Work4 已在 Draft PR #12 完成范围内实现、测试、CI 和 Judge。
- 本合同不继续授权 R6、真实数据库/数据、Ready、合并、Tag 或 Release。
- 下一 Work 尚未启动；用户新开同项目聊天后只发送“下一步”。

---

# 历史任务合同｜WORK-PP02-CLOUD-REBUILD-001

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

### 已复审实现 Head 验收进展

- Head `b23c698b32b09749e907f1f4f7be1c056445a52e` 的 Run `30640475137` 已
  8/8 success，且同 Head Windows safeStorage/source/artifact 假凭据门通过。
- 现仅发布证据收口 Head 并完整复验，随后停止；所有授权禁止边界不变。

### 执行进展（2026-07-31）

- 独立 Draft PR `#11` 已建立；RED Head/Run 已证明新契约在实现前失败。
- 实现已通过四轮独立安全复审，所有 Critical/Important 已关闭；经复审的
  本地代码 Head 为 `0627ea85ef14cfb7d0d457937244c2a860fac345`。
- 本地门禁：Python/契约 `340/340`，Desktop `80/80`，Web `127/127`，Lint、Build、
  AI 治理、仓库根派生假密钥扫描和全差异检查通过。
- 下一动作只是把文档收口 Head 发布到同一 Draft PR 并跑完八项 CI/
  固定 Head Windows 假凭据验收；其余禁止边界不变。

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

## WORK-002｜R3.6 Windows 便携安全更新

Work1 已永久关闭；Work2 从已合并 PR #3 的 main 基线 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 接管 R3.6，继承而不重做 R3.1–R3.5。批准方案为复用旧 Portable-M2 安全思想并按 PP02 当前边界重建。允许独立分支 Commit、Draft PR 和 CI 修复；禁止 Ready、合并、Tag、Release、真实数据和进入 R3.7。Plan Challenge：0 个问题，通过。

### R3.6 最终收口授权

只更新现有 Draft PR `#6` / `codex-xbl3c5`。已验证 Head `71404954407a9a3a6362a398465fc822b1351c72` 的 Run `30547333980` 为 8/8 success；PR #5 已关闭并由 PR #6 取代。本轮只允许更新五份唯一台账，并在 Windows CI 上传经同一 Job 验证的 ZIP/SHA 临时候选 artifact（14 天保留）；不得修改业务行为、升版本、创建新 PR、Ready、Merge、Tag、Release、main 直写或进入 R3.7。完成后保持 `IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED` / `DRAFT_HOLD`。


### PR #7 R5 基础启动返工授权

只修复现有 Draft PR #7。范围限于约束 `fake-useragent` 兼容上限、Windows/macOS PyInstaller 完整收集、能实际加载浏览器数据并触发 `data_provider.efinance_fetcher` 的冻结探针、Windows 候选上传前以隔离 `.env`/数据库和动态端口真实启动冻结 EXE并验证健康与主页，以及六份台账。失败 Head `d489a795b6089575a1fd61a27c9b28e2f3cb1b03` 和 Artifact `203e41a3…` 作废。禁止新 PR、Ready、Merge、Tag、Release、main 直写、真实数据/密钥及 R3.7。


### PR #8 CI 环境修复授权

只更新现有 Draft PR #8。不得删除 `main.py` 的 `GITHUB_ACTIONS` 保护条件；只允许在 `scripts/verify-frozen-backend.ps1` 启动冻结 EXE 前保存并临时覆盖 `GITHUB_ACTIONS=false`、`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`，继续验证动态端口健康和主页 HTTP 200，并在 finally 恢复环境与清理进程树。记录 Run `30576678660` 失败并等待新 Head CI/Artifact。禁止新 PR、Ready、Merge、Tag、Release、main 直写和 R3.7。


## WORK-003｜R3.7 Windows 安全凭据

总控已授权启动独立 Work3。固定基线为
`main@097bb5d60aa42f13737ac4d9db2f582bde50f995`，独立分支为
`agent/pp02-work3-r3-7-windows-secure-credentials`，目标是建立 Electron
`safeStorage` / Windows DPAPI 安全凭据边界，并完成威胁模型、测试先行实现、
完整 CI 和固定 PR Head 的 Windows 假密钥验收。

### 范围与验收

1. Windows Desktop 敏感值只持久化为 `userData` 下的 DPAPI 密文；不得继续写入
   `.env`，不得通过读取接口或配置导出返回明文。
2. renderer 只能写入、删除和查询存在状态；不得新增任何明文读取 IPC。
3. backend 只在启动/安全重启时通过 child environment 获得内存中的解密值；
   Windows secure mode 必须拒绝明文敏感配置写入和导入。
4. 先提交可证明失败的契约测试，再做最小实现；完整 CI 必须绑定最终 PR Head。
5. Windows 验收只使用由测试构造的假凭据，证明真实 Electron `safeStorage` 可加密/
   解密、vault 和导出无明文、日志与 artifact 不泄漏，并记录 Head/Run/Job。

### 授权与禁止边界

- 已授权：威胁模型、实施计划、独立分支、普通 Commit、独立 Draft PR、范围内 CI
  修复、固定 Head Windows 假密钥验收和事实台账更新。
- 禁止：真实 `.env`、真实 Key/Token/Password/Webhook、真实账号或数据库；PR Ready、
  Merge、`main` 直写/强推、Tag、Release，以及自行进入 R3.8 或任何后续阶段。
- 最终 Judge 必须保持 `DRAFT_HOLD`，即使实现、CI 和 Windows 验收全部通过。

### Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 问题级别 | 无待决产品问题 |
| 问答 | 0 个问题，通过 |
| 已确认方案 | Electron `safeStorage` / Windows DPAPI |
| 唯一事实源 | Windows Desktop 版本化凭据 vault |
| 测试策略 | RED Commit → 最小实现 → 完整 CI → 固定 Head Windows 假密钥验收 |
| 明确不做 | 旧 P001 密钥迁移、真实密钥、跨平台密钥服务、Ready/Merge/Tag/Release、后续阶段 |
| 允许进入 Build | 是 |
