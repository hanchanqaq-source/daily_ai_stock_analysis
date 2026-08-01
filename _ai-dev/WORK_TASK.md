# WORK-007｜R7 主线合并与正式发布任务合同

## 当前任务身份

```text
WORK_ID=WORK-007
WORK_STATE=COMPLETED
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=eb32298c8f3cbec2ff400dda37d3267a7181af40
TARGET_RELEASE=v3.29.0
SCOPE_DRIFT=FALSE
```

## 用户结果

用户正式启动 `Work7｜R7 主线合并与正式发布`，并选择方案 A：承接官方
`v3.28.0`，把本轮新增功能作为 `v3.29.0` 正式发布。选定后连续执行主线合并、
新 `main` CI、annotated Tag、GitHub Release 和正式产物验收，不再拆成逐项确认。

## 范围与执行顺序

1. 复核 PR #12/#13 的固定 Head、依赖关系、CI 与发布说明。
2. 完成最小 R7 状态、Changelog 和 PP02 Release notes 身份收口，并验证新 Head。
3. 先合并 PR #12，再把 PR #13 Base 改为 `main`；PR #13 新固定 Head CI 通过后合并。
4. 验证最终 `main` push CI，且 Tag 必须精确指向该已验证 `main` Head。
5. 创建带说明的 annotated Tag `v3.29.0` 并推送，触发正式发布工作流。
6. 验收 GitHub Release、Windows 安装/免安装更新资产、macOS x64/arm64 DMG、
   SHA-256、自动更新元数据以及 Docker/GHCR 发布结果。

## 非目标与硬边界

- 不读取、搜索、创建或迁移任何真实数据库；Work6 已裁决 `NO_FORMAL_DATA_FOUND`。
- 不读取、输出或上传真实 `.env`、Token、API Key、Webhook、密码或用户数据。
- 不强推 `main`，不创建 `v3.29.0` 以外的 Tag/Release，不扩大功能范围。
- 任一固定 Head、PR CI、`main` CI、Tag 绑定或正式产物门失败时立即停止在对应 Judge。

## 验收标准

1. PR #12/#13 均以预期固定 Head 和完整 CI 证据进入 `main`，依赖顺序无误。
2. 新 `main` push CI 全部适用 Job 成功，Tag 对象最终指向该精确 Commit。
3. `v3.29.0` 为 annotated Tag，注释非空，Release 非 Draft/非 Prerelease。
4. Windows 与 macOS 三类正式安装资产齐全；Windows 免安装 ZIP 与 SHA-256 配对、
   `latest.yml`、blockmap 和版本/文件名一致性通过发布工作流。
5. Docker/GHCR 正式发布成功；缺少可选 Docker Hub 凭据只可按工作流明确记录为 skipped。
6. 状态、路线、回传、Changelog、GitHub Release 和可验证 GitHub 事实一致。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 用户决定 | `A｜v3.29.0（推荐）` |
| 待决产品问题 | 0 个；版本和执行链已锁定 |
| 数据风险 | R6 无正式数据可迁移；R7 禁止任何真实数据操作 |
| Judge 上限 | `PASS — v3.29.0 RELEASED`，但必须逐门取得真实证据 |
| 允许进入执行 | 是；Ready/Merge/main CI/Tag/Release `v3.29.0` 已精确授权 |


## 最终执行结果

- PR #12、#13、#14 已按固定 Head 与 CI 门进入 `main`；发布提交为
  `49759dbd032f577d32e8e0f6670298f700e0f272`。
- 该发布提交的 `main` push CI 8/8 success 后创建 annotated Tag
  `v3.29.0`；Tag 精确指向发布提交且注释非空。
- GitHub Release 非 Draft、非 Prerelease；Windows 安装/免安装资产、SHA-256、
  macOS arm64/x64 DMG 与 Docker/GHCR 发布均成功。
- PR #15 在发布后补充三语言项目来源声明并修正仓库链接，合并为
  `main@b4a0ec11da19b5552ce87dde1ece716f61fd5174`；Run
  `30697946093` 8/8 success。
- Work6 `NO_FORMAL_DATA_FOUND` 边界保持不变；未读取、搜索、创建或迁移真实
  数据库，未使用真实凭据。
- 最终 Judge：`PASS — v3.29.0 RELEASED — WORK7 COMPLETED`。本合同不授权任何
  后续 Work、真实数据、其他 Tag/Release 或新的 `main` 写入。

---

# 历史任务合同｜WORK-005 / R6-A 正式数据安全只读盘点工具

## 当前任务身份

```text
WORK_ID=WORK-005
WORK_STATE=COMPLETED
WORKFLOW=ONE_MAJOR_SEGMENT_PER_WORK
BASE=a220e9e146e14722561bc084ec4e5306b30d36c7
BRANCH=agent/pp02-work5-r6-inventory-tool
SCOPE_DRIFT=FALSE
```

## 用户结果

用户已批准“按这个设计做”：在云端开发一个 Windows 原生运行的旧数据库安全体检
工具。工具只接受人工明确指定的一个 SQLite 文件，先做双备份，再只读统计四张正式
股票事件表；不搜索整机、不显示行值、不迁移、不覆盖、不上传。

## 范围

- 固定并执行 `docs/pp02/R6_FORMAL_DATA_INVENTORY_TOOL_DESIGN.md` 与实施计划。
- 新建独立标准库服务与薄 CLI，不导入应用数据库模型、配置、恢复或迁移模块。
- 双备份主文件及已有 WAL/SHM，校验哈希与源未变化后才检查临时副本。
- 只执行 SQLite 完整性、固定 Schema 和四张正式表的 `COUNT(*)`。
- 只输出三种裁决、四项计数和固定隐私证明；错误只含稳定代码。
- 测试仅动态创建空库与人工假数据库；完成专项、关联回归、完整本地门和固定 Head CI。
- 已授权范围内正常 Commit、Push、一个 Draft PR、CI 与范围内修复。

## 非目标与硬边界

- 不读取、复制、上传、迁移或修改任何 Windows 真实数据库、真实备份或真实数据。
- 不搜索 Windows 整盘或个人目录，不输出账户名、股票代码、金额、日期、备注或行值。
- 不迁移基金、用户档案、旧平行持仓、派生持仓、缓存、日志、设置或凭据。
- 不修改 R4 迁移演练器，不新增依赖，不放宽 Workflow 或仓库权限。
- 不 Ready、不合并、不写 `main`、不 Tag、不 Release、不进入 R7。

## 验收标准

1. RED 测试在实现缺失时按预期失败，GREEN 覆盖完整安全契约。
2. 两套备份逐文件哈希一致，源主文件与 sidecar 指纹前后一致。
3. 检查只针对临时副本，SQLite 为只读/query-only，四张固定表只执行计数。
4. 路径、journal、部分 Schema、损坏库、源变化和备份不一致全部 fail closed。
5. 报告和 CLI 不泄漏人工数据、路径、SQL、Schema 或异常正文。
6. 完整本地门与独立 Draft PR 固定 Head CI 通过；PR 保持 Draft。
7. 最终 Judge 上限为云端工具实现通过，Windows 真实盘点仍待精确授权。

## 本地实现与验证证据

- 服务 RED：18 项新契约因模块缺失而失败；CLI RED：7 项新契约因脚本缺失而失败。
- 独立审查后新增 5 项 RED 回归，分别证明备份中途回滚日志、清理失败、检查副本
  完整性状态、未知参数和重复源参数问题；修复后专项 `31 passed`，R6-A、R4 演练和
  组合备份联合回归 `50 passed, 4 warnings`。
- 最终代码完整 CI 等效后端门：`5070 passed, 1 skipped, 4 deselected, 48 warnings,
  499 subtests passed`；语法、严重 Flake8、确定性检查、AI 资产与格式门均通过；
  独立复核 APPROVE，无剩余 Critical、Important 或 Minor。
- 最终固定 Head `50dd04ca5a49a6e54de01e2d28ce598f690d9931` 的 CI Run
  `30691233934` 全部适用 Job success；尚未执行 Windows 真实盘点。

## Plan Challenge Result

| 项目 | 结果 |
| --- | --- |
| 用户决定 | `采用建议，云端开发盘点工具`，随后批准 `按这个设计做` |
| 待决产品问题 | 0 个；设计已固定显式路径、双备份、临时只读副本方案 |
| 数据风险 | 云端真实数据库/真实数据禁止；只用空库和人工假数据 |
| Judge 上限 | `CLOUD_TOOL_IMPLEMENTATION_PASS — WINDOWS_REAL_INVENTORY_PENDING_AUTHORIZATION` |
| 允许进入 Build | 是；按 RED→GREEN 连续执行 |

---

# 历史任务合同｜WORK-004 / R4

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
