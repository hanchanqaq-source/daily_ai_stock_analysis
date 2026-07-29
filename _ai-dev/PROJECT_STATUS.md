# PP02 当前状态

> 本文件是 PP02 唯一当前状态真源。其他文档出现冲突时，以本文件和可验证证据为准。

```text
PROJECT_ID=PP02
PROJECT_NAME=AI 每日股票分析
CHAT_ROLE=WORK
WORK_ID=WORK-PP02-CLOUD-REBUILD-001
ROLE_LOCK=TRUE
APPLICATION_BASE_VERSION=3.28.0
FRAMEWORK_TEMPLATE_VERSION=1.5.6
PROJECT_WORK_VERSION=pp02-cloud-rebuild-work.1
CURRENT_STAGE=R3.2 / Final Head CI
CURRENT_WORK=手动默认、云端调度关闭和自动通知总开关已实现并通过实现Head完整CI
ACTIVE_GOAL=追加R3.2 Judge台账并验证文档收口后的最终PR Head
CURRENT_STATUS=R3_2_IMPLEMENTATION_CI_PASSED_FINAL_HEAD_CI_PENDING
ACTIVE_BLOCKER=NONE
NEXT_ACTION=最终Head CI通过后保持Draft；下一迁移切片为R3.3官方账本快捷持仓
AUTHORIZATION_REQUIRED=FALSE_FOR_FINAL_HEAD_VALIDATION; READY/MERGE/MAIN/RELEASE/REAL_DATA_REQUIRE_NEW_AUTHORIZATION
LAST_UPDATED=2026-07-29
```

## 已验证基线

- 官方底座：`v3.28.0` /
  `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c`。
- Draft PR：`#3`，分支 `agent/pp02-v3.28.0-cloud-rebuild`，保持 Draft。
- R0 最终 Head `1327e402ac9d88e711ca4ef8de174118f427ad0e` 的 GitHub Actions
  Run `30221540882` 为 7/7 success。
- 远程 `main` 未因 R1/R2 改动。

## R1/R2 当前裁决

- R1：需求、保留/调整/不迁移分类和冲突处理已确认。
- PP02 保持单用户；旧用户档案、切换、隔离和用户级备份全部不迁移。
- 官方账户/组合事件账本是持仓唯一事实源。
- R2：迁移拆为 R3.1–R3.7；R3.1 已完成，当前收口 R3.2 手动默认与自动通知总开关。
- Windows 实机验收为 `Deferred`，不把 D 盘目录缺失登记为云端阻塞。

## 当前保护边界

- PR #3 不转 Ready、不合并、不发布 Release。
- 不接触真实 `.env`、Token、API Key、Webhook 或真实数据库。
- 不迁移基金、多用户或旧平行持仓表。
- R3.2 只允许手动默认、自动调度/发送安全门、设置帮助、对应测试和文档。

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
- Windows 实机仍为 Deferred；未使用真实通知渠道、凭据、付费服务或真实数据。
