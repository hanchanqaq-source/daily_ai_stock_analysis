# WORK-PP02-CLOUD-REBUILD-001 回传

> 运行中记录；只有本 Work 的新鲜证据可以更新本文件。

## 实际完成

- 已核验远程 `main`、官方 v3.28.0 Commit、目标分支不存在和框架附件。
- 已在新的隔离目录从官方固定 Commit 建立完整业务树。
- 已接入批准的 P000/P001 V1.5.6 控制 Overlay，并通过最低完整性硬门。
- 已通过 GitHub App/Git Data 原子创建初始候选 Commit 和独立分支；远程 Commit
  与本地候选树一致。
- 已完成 Python、Web、Desktop、AI 治理、格式、白名单和安全范围的本轮本地验证。

## 修改范围

- `.github/workflows/ci.yml`：重放 Work 1 已接受的最小只读权限。
- `AGENTS.md`：官方规则不变，新增单一有标记的 PP02 控制 Overlay。
- `_ai-dev/`、既有 PP02 控制台账、`docs/INDEX.md` 和 `docs/pp02/`。
- 官方业务代码：相对官方 v3.28.0 零差异。

## 测试与 CI

| 项目 | 当前结果 |
| --- | --- |
| 最低完整性硬门 | 通过：格式、AI 治理、官方业务树、20 路径白名单、历史非回退、安全扫描、文件清单和树对象已核验 |
| 候选持久化 | 通过：初始 Commit `9a2588004ba3436faa2b61d489fc8eab564ccef4`；分支 `agent/pp02-v3.28.0-cloud-rebuild`；本地/远程树 `c157f143640d056892ba5b1345e65a63eb86babd` |
| Python 完整离线测试 | 通过：官方 `./scripts/ci_gate.sh`；`4966 passed`、`4 deselected`、`45 warnings`、`487 subtests passed` |
| Web lint / build | 通过：ESLint 成功，TypeScript + Vite 生产构建成功；本地 Node `24.14.0` / npm `11.9.0`，CI Node 20 尚待验证 |
| Desktop | 通过：`47 passed`；Windows/macOS 打包由 Draft PR CI 验证，Windows 实机仍为 `NOT_VERIFIED_IN_CLOUD` |
| AI 治理 | 通过：`python scripts/check_ai_assets.py` |
| 差异与安全 | 通过：格式、20 路径控制白名单、官方业务零差异、台账非回退、差异层密钥签名/真实数据/跨项目内容均无命中 |
| Draft PR | `#3`，目标 `main`，保持 Draft，未转 Ready、未合并 |
| Draft PR CI | 首轮 Run `30220968264` 通过：7 个 Job 全部 success；收口证据 Commit 只有在同一 PR 最终 Head CI 也通过后才可完成外部回传 |

## 未验证项、阻塞与风险

- 未验证：Windows 实机、真实数据。
- 当前阻塞：无。
- 风险：Windows CI 验证冻结后端，不等于 Windows 实机安装验收；旧 Work 1 CI
  不得复用。

## Backlog 与清理

- Backlog：R1–R7；见 `docs/pp02/REBUILD_ROADMAP.md`。
- 清理：旧工作树保持原样；新的重建目录必须保留到发布链路和回传完成。临时缓存
  仅在验证完成后清理。

## Judge

`PASS`——候选恢复、远程持久化、本地完整验证和本次 Draft PR 真实 CI 均通过；
PR 必须保持 Draft，不构成 Ready 或合并授权。外部最终回传只在本收口证据 Commit
的 Head CI 同样通过后发出。

下一 Work：未授权，当前 Work 完成后停止并等待总控。

## 2026-07-29 R1/R2 连续阶段回传

- R1 产品范围已确认：PP02 保持单用户，用户档案/切换/隔离/用户级备份不迁移。
- 官方账户/组合事件账本固定为持仓唯一事实源。
- R2 已将迁移拆成 R3.1–R3.7，并固定依赖、文件边界和验收出口。
- Windows 实机验收为 Deferred；D 盘目录缺失不属于云端阻塞。
- 当前进入 R3.1：PP02 身份与更新源。
- R1/R2 未修改业务代码、未处理真实数据、未改变 PR #3 Draft 状态。
