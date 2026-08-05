# PP02 handoff

## Current takeover entry | WORK-025

| Item | Current fact |
| --- | --- |
| State | `WORK25_LOCAL_RELATED_VERIFICATION_PASS_DRAFT_PR_PENDING` |
| Base | `main@f813084944f7a9c5459312ef84da7956cda1a37f` |
| Branch | `agent/pp02-work25-windows-frozen-startup-timeout` |
| Goal | Replace the conflicting fixed 3-second uvicorn startup deadline with one bounded condition-based wait |
| Draft PR | Pending publication |
| Failure evidence | Main Run `31032267014` 7/8; Windows Job `92395692229` failed after `3.0s` FastAPI startup deadline |
| Root cause | Inner 3-second deadline terminated the backend before the outer 90-second frozen HTTP readiness gate could complete |
| Local evidence | Helper/main-disconnect RED; delayed-ready GREEN; related `32/32`; compile/governance/boundaries/diff pass |
| Remote CI | Pending exact Draft PR Head |
| Judge | `ACTIVE — DRAFT_HOLD` |
| Prohibited | Ready, merge, `main`, Tag, Release, version/dependency/config expansion, signing identity, real Windows data |

Continue with final diff review, one commit/push, one Draft PR, and exact-Head
Actions verification. The cloud environment lacks locked backend dependencies
and flake8, so it did not claim the full local backend gate; remote CI is the
authority for backend, Windows/macOS packaging, final ZIP, and lifecycle checks.

Work24 fixed Head `f91576cb…` passed PR Run `31028088206` 8/8 and merged as
`f813084…`; main Run `31032267014` failed only the Windows package Job, so it
must not be described as releaseable. Work25 does not reopen or broaden Work24.

---

## Historical takeover entry | WORK-024

- PR #24: merged; fixed Head `f91576cb6fa9d7d516141758593a5086a50e205a`.
- PR CI: Run `31028088206`, 8/8 success.
- Merge commit: `f813084944f7a9c5459312ef84da7956cda1a37f`.
- Main CI: Run `31032267014`, 7/8; Windows Job `92395692229` failed at the
  frozen FastAPI fixed 3-second startup deadline.
- No Tag or Release was created from the failed main.

---

## Historical takeover entry | WORK-023

---

## Historical takeover entry | WORK-016 / Windows frozen chip dependency closure

| 项目 | 当前值 |
| --- | --- |
| 当前状态 | `WORK16_PASS_DRAFT_HOLD` |
| 当前 Work | `WORK-016｜Windows 冻结筹码依赖收口` |
| 固定 Base | `main@568e26adf0e6393a7a0da1be57369535735cd05a` |
| Work15 结果 | PR #20/#21 均已合并；最终裁决 `PASS — MAINLINE_CLOSED` |
| 当前分支 | `agent/pp02-work16-windows-chip-runtime` |
| 当前 PR | [Draft PR #22](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/pull/22) |
| 未发布候选 | `3.29.1` / `217,003,814` bytes / SHA-256 `DAD0CE0CCF8FC34F7318CD4E4F0CC37347C68A1A03E98D0CA7B048E393B18B33` / `NotSigned` |
| 正式历史闭环 | `600519` history ID `2`；task/query/trace `1c4ae649232d40eaae7dcb6bb1b6981f` |
| Work16 证据 | Head `016e3408…` / Run `30831393819`：7 success、1 path-skipped；Windows 双层冻结筹码门通过 |
| Work14 最终裁决 | `PASS_WITH_DEGRADATIONS — DRAFT_HOLD`；证据 Run `30821021196` success |
| Work12 现场 | 原安装已恢复，端口 8000 `health=ok`；数据库和日志仍在 |
| 根因 | `mini-racer 0.14.1` 已安装且 wheel 含 DLL/ICU，但 PyInstaller 未收集、健康探针未加载 V8 |
| 下一动作 | 无；保持 PR #22 Draft，等待新的单独授权 |
| 授权边界 | 禁止 Ready/合并/Tag/Release、依赖变更、新闻、签名及新增 Windows 真机动作 |

Work14 只从 PR #20 固定 Head 构建未发布验收候选，没有安装、Tag 或发布该候选。
正式 `600519` API 任务完成并生成可重读历史；候选后端停机重启、再由 Work12 原安装
重读后，history ID、query ID、LLM 与运行流保存状态仍一致。同期大盘历史和周内周期
聚合也可重读。证据 Head `da229059…` 的 Run `30821021196` 已通过，Work14 正式以
`PASS_WITH_DEGRADATIONS — DRAFT_HOLD` 结束。

候选整体不是无条件 PASS：诊断状态为 `degraded`，新闻搜索无结果，筹码链因冻结产物
缺少 `py_mini_racer/mini_racer.dll` 失败；安装器未签名且本 Work 未执行候选安装生命周期。
Work12 的 `.env` 在受控单股重跑前已发生外部变更，元数据变为 50,268 bytes（来源未判定）；
Work14 未用旧副本覆盖它，临时副本与目录联接均已精确删除。最后更新：2026-08-03。

Work15 已将 PR #20 与 PR #21 依序合入主线；PR #21 最终固定 Head CI Run
`30825436318` 成功，最终 `main` 为 `568e26ad…`，裁决 `PASS — MAINLINE_CLOSED`。

Work16 只处理 Work14 已证实的 Windows 冻结筹码运行时缺口。Windows CI 已证明
`akshare 1.18.81` 自动安装 `mini-racer 0.14.1`；因此本 Work 不改依赖，只让
PyInstaller 收集其现有 `py_mini_racer` DLL/ICU，并在构建目录与最终解压便携 ZIP
中执行无网络 V8/筹码模块探针。新闻、签名、版本发布和真机验收均不在范围内。
Draft PR #22 已建立并保持 Draft；3 个新合同先 RED，最小实现后包装合同 5/5 GREEN，
Python 编译、AI 资产与 diff 格式检查通过。依赖声明未改。固定证据 Head
`016e3408…` 的 Run `30831393819` 已 7 success、1 路径跳过；Windows Job 在直接构建、
重建和最终解压 ZIP 共记录 3 次真实 MiniRacer/V8 探针成功，独立复审无重要问题。
Work16 裁决 `PASS — DRAFT_HOLD`，不得据此自行 Ready、合并、Tag 或 Release。

以下内容是旧 Work 的追加历史；与本节冲突时，以 `PROJECT_STATUS.md`、本节和
GitHub 可验证事实为准。

## 历史身份与基线

| 项目 | 当前值 |
| --- | --- |
| 仓库 | `hanchanqaq-source/daily_ai_stock_analysis` |
| 远程 main 最近核验 | `f2253226c0974e3d241d496a1af8ede61c599b58` |
| 官方来源 | `ZhuLinsen/daily_stock_analysis` |
| 官方 Tag / Commit | `v3.28.0` / `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c` |
| 框架 | P000/P001 V1.5.6；总包 SHA-256 `06B8B4F196097C50B5E1A232B55BB7D14F41E1133C6D44945F0146693A79C7C4` |
| Work | `WORK-PP02-CLOUD-REBUILD-001`，`ROLE_LOCK=TRUE` |

## 当前候选

- 状态：R1、R2、R3.1–R3.4 已完成；R3.5 实现 Head 已通过完整 CI，正在收口最终 Head。
- 已完成：远程 `main`、官方 Tag/Commit、目标分支不存在和框架附件均已只读核验；
  已从官方固定 Commit 建立新的隔离候选；业务树、控制白名单、历史非回退、格式、
  AI 治理、安全和候选清单检查均通过；初始候选已持久化到独立分支，完整
  Python/Web/Desktop 本地验证已通过；Draft PR `#3` 的首轮 CI Run
  `30220968264` 已 7/7 success。
- 未完成：Windows 实机、真实数据以及任何 Ready/合并/Release；这些均不在当前
  Work 授权内。
- 当前阻塞：无。
- 下一动作：验证 R3.5 文档收口后的最终 Head；保持 PR 为 Draft，成功后停止并
  一次性回传总控，不自行启动 R3.6。

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
- 最后更新：2026-07-30。

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


## 2026-07-30 R3.3 追加交接

- R3.2 收口 Head `e879f0692d2bd330b166df561cd8a90d4542a5ce` 的
  Run `30494219667` 已 8/8 success。
- R3.3 已实现目标持仓只读预览、人工确认、过期预览冲突与重复确认去重。
- 确认只追加官方交易事件；现金与持仓由官方重放计算，不新增平行事实源。
- 实现 Head `311664759a51f8eb8ec700417b20c2e17fa155e8` 的
  Run `30514223674` 为 8/8 success；后端 `4981 passed`，
  PortfolioPage `29/29 passed`。
- 收口 Head `d4615cd407ba88ed43f9da129c8c89583358a98a` 的
  Run `30514843576` 为 8/8 success；R3.3 Judge 已完成。
- 下一迁移切片：R3.4 股票专用备份与恢复。


## 2026-07-30 R3.4 追加交接

- R3.4 已实现股票账本版本化 JSON 导出、只读恢复预览、过期预览检测和
  单事务整套替换。
- 备份只包含账户、交易、资金和公司行动；派生持仓由官方账本重放，不导入缓存。
- 私有仓库 Actions 分钟耗尽后，公开前安全审计未发现密钥或真实数据；用户授权
  将仓库改为 Public，标准 GitHub 托管 Runner 恢复。
- 日期摘要修复 Commit `8355d92a81b8f951a8ee7bcb703e89585cb8de5e`；
  异步测试稳定性修复 Commit `56c887502e218efa146a20ab86c928008e9035d6`。
- 实现 Head Run `30519559480` 为 8/8 success；后端 `4987 passed`，
  PortfolioPage `31/31 passed`。
- 最终收口 Head `a5b999717e57fe3c78da5c65adadcb1f05b71f95` 的 Run
  `30520589917` 为 8/8 success；R3.4 Judge 已完成。
- Windows 实机和真实备份仍未执行；下一迁移切片为 R3.5 应用内手动周期报告。

## 2026-07-30 R3.5 追加交接

- 新增七个应用内手动周期入口：本周至今、上一周、下周展望、5周、10周、
  1个月和2个月。
- 周期事实只从 `HistoryService.get_history_list()` / `AnalysisHistory` 读取；
  股票、ETF 与市场复盘分区返回。
- 下周展望只使用最近 14 个自然日内的合格正式历史，不调用模型；无合格数据时
  返回固定不足提示。
- 展望快照使用 `report_type=period_outlook` 保存来源 ID；没有新表或新列，普通
  股票历史和回测不会把快照当作分析事实。
- Web 初次打开不生成；只有用户选择周期并点击后才执行唯一 POST 人工入口。
- 实现 Head `4b563bc63e9638731f2a17ed25129de095046ef4` 的 Run
  `30525590779` 为 8/8 success；Backend `5005 passed`，Web `55/55 passed`
  且 Build 成功。
- 当前只待 Judge 文档收口后的最终 Head CI；PR #3 保持 Draft。
- Windows 实机、真实历史/数据库、模型调用、定时器和自动推送均未执行；
  R3.6 只能由总控审核 R3.5 后另行下发。

## 2026-07-30 Work2 / R3.6 新交接

Work1 已永久关闭，旧“PR #3 保持 Draft”只在合并前有效；PR #3 现已合并。R3.1–R3.5 已进入 main。Work2 在 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9` 上以独立分支和独立 Draft PR 实现 Windows 便携安全更新。云端最高 Judge 为 `IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`，不得自行进入 R3.7。

## 2026-07-30 R3.6 最终交接

当前唯一活动项为 Draft PR `#6`，分支 `codex-xbl3c5`，Base `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。Head `71404954407a9a3a6362a398465fc822b1351c72` 的 CI Run `30547333980` 已 8/8 success。旧 PR #5 已关闭并标记为 superseded。Judge 为 `IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`，继续 `DRAFT_HOLD`；下一步只能是验证本次 artifact 收口的新 Head CI，并等待 R5 Windows 实机验收授权，不得进入 R3.7。


## 2026-07-30 PR #7 R5 失败交接

PR #7 Head `d489a795b6089575a1fd61a27c9b28e2f3cb1b03` / Run `30564032072` 虽为 8/8 success，但 Windows 11 隔离验收中冻结后端因 `fake_useragent.data` 和浏览器数据未进入 PyInstaller 产物而立即崩溃。失败 Artifact SHA-256 `203e41a35e2cd081a20640f514c9de417bd507cbd9b8a2f097a4d0bed36cda1a` 已作废。当前只修复同一 Draft PR #7：双平台收集 `fake_useragent`、真实 UserAgent/efinance 探针、Windows 动态端口冻结 EXE 启动门。新 Head CI 与 Head-bound Artifact 完成前状态为 `R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`。


## 2026-07-30 PR #8 CI 失败交接

Draft PR #8 的 Run `30576678660` 失败：真实冻结启动门继承 `GITHUB_ACTIONS=true`，命中 `main.py` 现有服务保护条件，出现“进程存活但服务未启动”。不得删除或绕开 `main.py` 保护；启动门必须只在冻结子进程期间覆盖 `GITHUB_ACTIONS=false`，同时设置 Python UTF-8 环境，并在 finally 恢复所有原值与清理进程树。当前保持 `R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`，等待同一 PR #8 新 Head CI 和 Artifact。

## 2026-07-31 Work3 / R3.7 交接

- Work2/R5 已完成并进入 `main`；Work3 固定 Base 为
  `097bb5d60aa42f13737ac4d9db2f582bde50f995`，唯一活动项是 Draft PR `#11`。
- R3.7 已完成 `safeStorage`/DPAPI 版本化 vault、窄 IPC、`.env` 绑定、backend
  环境注入、导入/导出边界和固定 Head 假凭据/产物扫描。
- 经过四次独立安全复审，已无 Critical/Important。首轮固定远端 Head
  `b23c698b32b09749e907f1f4f7be1c056445a52e` 的 Run `30640475137` 已 8/8
  success；Windows Job `91189042298` 的 checkout、safeStorage 假凭据 PASS 和
  最终产物扫描 PASS 均绑定该 Head，Artifact ID 为 `8798100943`。
- 下一动作只是发布上述证据到现有 Draft PR，并验证证据提交自身的八项最终 CI。
- 禁止使用真实凭据/数据，禁止 Ready、合并、main 直写、Tag、Release 或进入
  R3.8/后续阶段；最终 Judge 上限仍为 `DRAFT_HOLD`。

### R3.7 已复审 Head CI 更新

- Head `b23c698b32b09749e907f1f4f7be1c056445a52e` 的 Run `30640475137` 已
  8/8 success；Backend `5027 passed, 4 deselected, 499 subtests passed`。
- Windows Job `91189042298` 已证明精确 Head checkout、真实 `safeStorage` 假凭据 PASS、
  仓库根 source 扫描与 ZIP/解包/`win-unpacked` artifact 扫描 PASS；所有 Head 标记一致。
- 当前只剩证据收口 Commit 的最终 8 Job 复验；复验结果必须写入 Draft PR
  元数据而不再改变 Head。
