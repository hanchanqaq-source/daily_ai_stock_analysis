# PP02 当前状态

> 本文件是 PP02 唯一当前状态真源。其他文档出现冲突时，以本文件和可验证证据为准。

```text
PROJECT_ID=PP02
PROJECT_NAME=AI 每日股票分析
CHAT_ROLE=WORK
TOP_LEVEL_WORK=WORK2
WORK_ID=WORK-002
PREVIOUS_WORK=WORK1_COMPLETED_AND_LOCKED
ROLE_LOCK=TRUE
APPLICATION_BASE_VERSION=3.28.0
FRAMEWORK_TEMPLATE_VERSION=1.5.6
PROJECT_WORK_VERSION=pp02-work2-r3.6
CURRENT_STAGE=Work2 / R3.6 / Governance Reconciliation / Build
CURRENT_WORK=R3.6 Windows便携更新
ACTIVE_GOAL=在Draft PR #7内合入已批准治理硬门并使状态与Git和CI一致；完成后等待R5 Windows实机验收授权
CURRENT_STATUS=R3_6_IMPLEMENTATION_PASS_GOVERNANCE_RECONCILIATION_IN_PROGRESS; DRAFT_HOLD
LAST_VALID_COMMIT=7104bbc5b1f5a1c6ed9863f87472014c72eb79e8
LAST_SUCCESSFUL_TEST=PR7_HEAD_7104BBC5_CI_RUN_30552446534_SUCCESS_8_OF_8
ACTIVE_BLOCKER=NONE
NEXT_ACTION=完成PR7治理归并、本地验证、最终Head CI和Judge；之后停在R5 Windows实机验收授权门
AUTHORIZATION_REQUIRED=FALSE_FOR_APPROVED_R3_6_BRANCH_COMMIT_DRAFT_PR_AND_CI; READY/MERGE/MAIN/RELEASE/REAL_DATA_REQUIRE_NEW_AUTHORIZATION
LAST_UPDATED=2026-07-30
```

## 已验证基线

- 官方底座：`v3.28.0` /
  `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c`。
- PR `#3` 已合并；远程 `main` 当前有效检查点为合并 Commit
  `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- R3.5 最终 Head `508eb268c78d6172dac22160c9dc0550f83653a6` 的 GitHub Actions
  Run `30526590693` 为 8/8 success。
- R3.6 当前唯一活动项为 Draft PR `#7`，分支 `codex-4z7ady`；实际当前 Head
  始终以 GitHub PR 为准，不在提交内自引用。
- 最后有效 R3.6 实现检查点为
  `7104bbc5b1f5a1c6ed9863f87472014c72eb79e8`，Run `30552446534`
  为 8/8 success。
- 治理硬门来源为 Draft PR `#4` / Head
  `9c136a4662f7ed817deb63019b3c106fe73cface`，本轮将其提交历史归并到 PR #7；
  PR #4 在 PR #7 最终 Head CI 通过前保持未合并。
- 治理恢复检查点
  `6ab647a7c2c2dca90c3a0c1626f270860073b443` 的 Run `30540208702` 成功。
- 状态/Judge 收口检查点 `d45bdfadf22cf7beb5e1f6777490091ed5cac438`
  的 Run `30540784009` 也成功：Change Detection、AI Governance、Backend Gate
  和 Docker Build 通过；Backend 为
  `5005 passed, 4 deselected, 51 warnings, 494 subtests passed`。Web/Desktop
  因本段仅修改治理文档而按路径规则跳过。

## Work 边界纠正与治理检查点

- Work1 的职责是官方稳定版干净底座，已完成并永久锁定。
- R0–R7 的后续改造按当前有效管理口径归属 Work2；聊天窗口名称不得改变归属。
- 旧 `WORK-PP02-CLOUD-REBUILD-001` 及“继续同一 Work1”记录保留为历史，
  由本次 Work2 纠正记录替代其当前身份效力，不倒改已完成提交和测试。
- `PP02-GOVERNANCE-GATE-001` 已批准：只强化现有 Overlay、四份 `_ai-dev`
  文件和现有路线台账，不创建平行状态文件或复杂验证系统。
- 当前较长任务必须显示 `Plan → Build → Test → CI → Judge`、当前 Blocker 和
  用户操作；回复结束后不得声称仍在后台执行。

## 当前工具恢复

- 失败位置：发布前检查发现当前环境没有 GitHub CLI `gh`。
- 已保存状态：12 个治理文件的本地补丁与本地 Test 均已完成。
- 恢复条件：已连接 GitHub App 可使用 Git Data API 完成同一已授权发布范围。
- 备用路线：直接创建 Blob、Tree、Commit、独立分支和 Draft PR；不安装 `gh`、
  不发起设备登录、不让用户承担技术恢复。
- 第一次 Git Data 发布 Commit `d846af7ce50b892d9f5e16222b4e544ef01b1d46`
  中，超长 `docs/CHANGELOG.md` 经终端文本转发被截断；其余 11 个文件与本地一致。
- 恢复路线：从 GitHub `main` 直接读取完整 Changelog，插入本次单条文档记录，
  在同一分支追加修复 Commit，再逐文件比较远端树。
- 恢复结果：Commit `6ab647a7c2c2dca90c3a0c1626f270860073b443`
  已恢复完整 Changelog；12 个远端 Blob SHA 与本地逐一一致。
- 本地 `git diff` 在超长文件比较时发生段错误，已改用逐文件 Blob SHA 作为备用
  验证；`python scripts/check_ai_assets.py` 与 `git diff --check` 同时通过。
- Blocker 已解除；没有重跑整个 Work，没有让用户安装 `gh` 或重新认证。

## R1/R2 当前裁决

- R1：需求、保留/调整/不迁移分类和冲突处理已确认。
- PP02 保持单用户；旧用户档案、切换、隔离和用户级备份全部不迁移。
- 官方账户/组合事件账本是持仓唯一事实源。
- R2：迁移拆为 R3.1–R3.7；R3.1–R3.5 已完成，当前执行 R3.6
  Windows 便携更新。
- Windows 实机验收为 `Deferred`，不把 D 盘目录缺失登记为云端阻塞。

## 当前保护边界

- R3.6 新 PR 只允许保持 Draft；不得转 Ready、合并、修改 `main` 或发布 Release。
- 不接触真实 `.env`、Token、API Key、Webhook 或真实数据库。
- 不迁移基金、多用户或旧平行持仓表。
- 当前 PR #7 治理归并只允许修改现有 PP02 控制规则、状态、任务、交接、回传、
  路线和追加式变更记录；不得借机修改 R3.6 业务代码。
- R3.6 不新增 AI 调用、定时器、自动通知、真实数据入口、基金或多用户能力。
- 仓库经只读安全审计和用户授权后已改为 Public；PR、分支和 Actions 历史公开，
  但真实数据、密钥和备份文件仍不得进入仓库。

## R3.1 实现与验证证据

- 测试先行 RED：Commit `c762825102f22b1352949244c12148b821b80b87`，
  CI Run `30487941321` 的 `desktop-test` 按预期失败；47项旧测试通过，
  2项新 PP02 身份测试因仍指向官方仓库/名称失败。
- 首次 GREEN：Commit `c7e483928a92ed1ed589c68647acb554e3b5ee41`；
  Desktop 49/49 通过，但 macOS 包门暴露旧固定 App 路径。
- 根因修复：Commit `639d2bc8fc605fbe553fb9c16df7137042bb2079`，
  将 macOS 未签名 App 与 DMG 验收路径同步为 PP02 productName。
- 实现 Head CI：Run `30488603501`，8/8 success。
- 收口 Head `1740fa3655b5eed55c7e4ebda81523ca8095e176` 的 Run `30489293885` 为 8/8 success；R3.1 Judge 已完成。
- PR #3 仍为 Draft；Windows 实机、Ready、合并、Release 和真实数据均未执行。


## R3.2 实现与验证证据

- 行为测试 RED：Commit `68dab6a7d54b81f196b642b1352a0a41aa2b8eb5`，
  Run `30491953318` 为 9 个预期失败，覆盖配置、Workflow、CLI、运行时调度、
  Alert Worker、Web/API 分析和市场复盘。
- GREEN 实现：Commit `61939ec76384d5c198aecf98e8b413fe13cfdd85`；
  删除默认 cron，新增 `AUTO_NOTIFICATION_ENABLED=false` 并贯穿全部自动发送入口。
- 集成回归根因修正：Commit `5316b5ea2ececd9aff0ced556e897f0738dad317`；
  将旧的默认发送断言改为默认关闭，并补齐设置页中英文帮助元数据。
- 实现 Head CI：Run `30493475960`，8/8 success；后端
  `4976 passed, 4 deselected`，Web、Docker、Desktop 单测及 Windows/macOS 包门均通过。
- 手动“测试通知”保持独立；关闭总开关时分析、报告持久化和告警记录继续执行，
  仅抑制外部自动发送。
- 收口 Head `e879f0692d2bd330b166df561cd8a90d4542a5ce` 的 Run
  `30494219667` 为 8/8 success；R3.2 Judge 已完成。
- Windows 实机仍为 Deferred；未使用真实通知渠道、凭据、付费服务或真实数据。

## R3.3 实现与验证证据

- RED：Commit `f1ebae02f21a97d97418649c23db8401a8b3fc8f`；补充 Web
  专项测试门的 Commit `93d2a59b8eab77a2d6633898c4cbb5e93fb95d33`。
- RED Run `30513770957`：后端 5 项预期失败、其余 `4976 passed`；
  PortfolioPage 新测试按预期失败，原有 28 项通过。
- GREEN：Commit `311664759a51f8eb8ec700417b20c2e17fa155e8`。
- 实现 Head Run `30514223674`：8/8 success；后端
  `4981 passed, 4 deselected`，PortfolioPage `29/29 passed`。
- 预览只读；确认在原子事务内做过期检查和去重，只追加官方交易事件；
  现金变化由官方重放计算，不直接写 `portfolio_positions`。
- Windows 实机仍为 Deferred；未使用真实持仓、券商账户或真实数据库。
- 收口 Head `d4615cd407ba88ed43f9da129c8c89583358a98a` 的 Run
  `30514843576` 为 8/8 success；R3.3 Judge 已完成。

## R3.4 实现与验证证据

- RED：Commit `15e48e6000bd1a39e7db082e20897052affa558c` 与
  `b6a2cd2f02e2ebc3955bfb6276e1ffd63b3c6eac`；Run `30516073073`
  后端 6 项预期失败、其余 `4981 passed`；PortfolioPage 新增 2 项预期失败，
  原有 29 项通过。
- GREEN 初始 Head `85dbe71a26d175b6c2557900770b3260fea4a419`。
- 私有仓库 Actions 分钟耗尽导致 Run `30516696130` 零 Step 阻塞；公开前审计
  未发现密钥或真实数据，用户授权改为 Public 后标准 Runner 恢复。
- 日期摘要根因修复：Commit `8355d92a81b8f951a8ee7bcb703e89585cb8de5e`；
  明确把 `date/datetime` 规范化为 ISO 标量，未知对象仍拒绝序列化。
- Web 异步测试稳定性修复：
  Commit `56c887502e218efa146a20ab86c928008e9035d6`。
- 实现 Head Run `30519559480`：8/8 success；后端
  `4987 passed, 4 deselected, 50 warnings, 487 subtests passed`；
  PortfolioPage `31/31 passed`。
- 备份只包含账户、交易、资金和公司行动；预览只读，确认在单事务内整套替换，
  失败回滚，恢复后由官方账本重放派生持仓。
- Windows 实机仍为 Deferred；未导出、读取或恢复真实备份。

## R3.4 最终收口

- 最终 Head `a5b999717e57fe3c78da5c65adadcb1f05b71f95` 的 Run
  `30520589917` 为 8/8 success；后端 `4987 passed, 4 deselected`，
  PortfolioPage `31/31 passed`，Web Build 与双平台打包门全部通过。
- R3.4 Judge：`PASS`；PR #3 保持 Draft，`main` 未改变。

## R3.5 已确认产品契约

- 七个手动入口：本周至今、上一周、下周展望、5周、10周、1个月、2个月。
- 周期事实只来自 `HistoryService.get_history_list()` 和现有
  `AnalysisHistory`；股票/ETF 与市场复盘分区展示。
- 下周展望只使用最近 14 个自然日内的合格历史，不调用 AI；数据不足时固定显示
  “近期有效数据不足，暂不能形成下周展望。”
- 展望使用 `report_type=period_outlook` 写回现有分析历史，保存目标周、生成时间、
  来源记录 ID、方向、置信度、依据、风险与失效条件。
- 进入下一周后，上一周周期汇总可读取日期完全匹配的旧展望快照并列复盘。
- 页面免责声明固定为：
  “下周展望基于已有历史分析形成，仅供参考，不代表确定结果。”

## R3.5 实现与验证证据

- 计划 Commit `e7a71a806c8b5ac852348b58cd3c0d742410a17a`；服务、
  API、历史隔离和 Web 施工合并为后续四个逻辑 Commit。
- 实现 Head `4b563bc63e9638731f2a17ed25129de095046ef4` 的 Run
  `30525590779` 为 8/8 success。
- 后端 `5005 passed, 4 deselected, 51 warnings, 494 subtests passed`；
  Web 阻断套件 `55/55 passed`，Web Production Build 成功。
- 七个周期边界、跨月/跨年、14 日有效期、股票/ETF/市场复盘分区、数据不足、
  来源追溯和上周展望并列复盘均有专项测试。
- 生成人工入口只有 `POST /api/v1/period-report/generate`；页面初次打开不请求，
  周期生成不调用模型、行情、新闻、通知或调度入口。
- 展望快照继续使用 `AnalysisHistory(report_type=period_outlook)`，未增加表或列；
  普通股票历史与回测显式排除该报告类型。
- 额外全量 Web 基线为 `1044 passed, 2 skipped, 1 failed`；唯一失败是既有
  `AlertRuleForm` JP/KR 选项测试与相邻既有“不显示 JP/KR”测试契约矛盾，
  不在 R3.5 正式 Web 阻断门内，未修改产品或旧测试掩盖该基线债。
- PR #3 保持 Draft；Windows 实机仍为 Deferred；未使用真实历史、真实数据库、
  模型、通知渠道或自动入口。

`R3_5_IMPLEMENTATION_CI_PASSED_FINAL_HEAD_CI_PENDING`

## 2026-07-30 Work2 / R3.6 接管

`WORK_ID=WORK-002`；`CURRENT_STAGE=R3.6 / Build-Test-Publish-CI`；`ACTIVE_GOAL=Windows 便携安全更新`。Work1 已永久关闭，PR #3 已合并，R3.1–R3.5 已进入 `main`。本轮基线 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`，独立分支 `agent/pp02-work2-r3-6-windows-portable-update`，只创建独立 Draft PR。Windows R5 真机验收、Ready、合并、Tag、Release 和真实数据继续禁止。

## 2026-07-30 Work2 / R3.6 Review 修复（历史，已由 PR #6 接管）

- 当时 Draft PR：`#5`；实际分支：`codex`。该 PR 现已关闭并标记为 superseded。
- 上一 Head：`e5cdb70`；CI Run `30543513470` 为 8/8 success，但 Work2 Judge 发现更新事务与真实运行行为阻断，不能据此判定通过。
- 先前 `PUBLISH_BLOCKED` 仅保留为历史说明，当前不再是 Active Blocker。
- 历史动作：收敛助手资源、下载重定向/超时、停止后备份、完整回滚、动态端口握手、严格便携身份和真实行为测试；成果后由 PR #6 接管。

## 2026-07-30 Work2 / R3.6 PR #6 收口（历史，已由 PR #7 取代）

- 当时活动 Draft PR：`#6`；分支：`codex-xbl3c5`；Base：`main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- 已验证 Head：`71404954407a9a3a6362a398465fc822b1351c72`；CI Run `30547333980` 为 8/8 success。
- PR #5 已关闭并由 PR #6 取代，只保留为 superseded 历史。
- 当时 Judge：`IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`；`DRAFT_HOLD`。
- 本轮只为 Windows CI 增加已验证便携候选 artifact，不修改便携更新业务行为、不升版本、不创建 Tag 或 Release。

## 2026-07-30 Work2 / R3.6 PR #7 治理归并

- 当前唯一活动项：Draft PR `#7`；分支 `codex-4z7ady`；Base
  `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。
- PR #7 实现检查点 `7104bbc5b1f5a1c6ed9863f87472014c72eb79e8` 的 Run
  `30552446534` 为 8/8 success，并已生成经 Windows Job 验证的 ZIP/SHA
  临时候选；该候选不是 Release，不能替代 R5 实机验收。
- 根因：PR #7 与治理 PR #4 从同一 `main` 基线并行分叉，代码与治理提交未汇合，
  导致 PR #7 的现行台账仍指向已关闭的 PR #6。
- 本轮只归并 PR #4 的治理提交、解决四个台账冲突并修正 PR/Head/CI 状态；
  不修改便携更新业务逻辑，不进入 R3.7。
- 当前本地基线：AI 治理通过；Desktop `60/60 passed`。归并后的最终 Head CI
  尚待本轮推送后核验，故继续 `DRAFT_HOLD`。

目标停止点：

`WORK2_R3_6_IMPLEMENTATION_JUDGED — R5_WINDOWS_VALIDATION_REQUIRED — DRAFT_HOLD`
