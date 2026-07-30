# R3.6 Windows 便携安全更新实现

## 范围与基线

- Work1 已永久关闭；Work2 接管 R3.6。
- PR #3 已合并，R3.1–R3.5 已进入 `main`。
- R3.6 起点为 `0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`，使用独立分支 `agent/pp02-work2-r3-6-windows-portable-update` 和独立 Draft PR。
- NSIS 继续使用 `electron-updater`；只有带有效 `pp02-portable-release.json` 且不存在 NSIS 卸载器的 Windows 包才进入便携链路。

## 安全链路

启动检查只读取 GitHub Release 元数据并展示版本、说明和精确资产名。用户点击“安全更新”后，程序才下载同一 tag 下唯一的 ZIP/SHA 配对。校验依次覆盖 SHA 文件名绑定、ZIP 摘要、产品/版本/tag/packageKind、危险路径与 Zip Slip、链接、重复路径、展开限制，以及清单中每个文件的大小和摘要。

校验完成前不会停止后端或启动替换助手。通过后生成带随机 token 的 JSON 计划，并以隐藏、分离的 PowerShell 进程执行。助手二次约束根目录和相对路径，备份环境、SQLite/WAL/SHM、旧清单及受管理旧文件，只替换清单文件。首次无旧清单时不推测删除；`.env`、`data/`、`logs/` 和未知文件始终不受管理。

新版本必须同时通过产品/版本身份、后端健康、主页 HTTP 和 Electron 主窗口加载 token 回执。失败时助手停止新进程、恢复程序及运行时状态并重启旧版。

## 发布契约

Release 和 Windows CI 复用 `scripts/prepare-portable-release.js`：从干净 `win-unpacked` stage 生成清单、排除用户状态、压缩、重新解包校验，并生成绑定精确 ZIP 文件名的 `.zip.sha256`。CI 只构建候选，不发布；正式 Release 保留 NSIS、`latest.yml` 和 blockmap。

## 验收边界

云端实现与 GitHub Actions 不能替代 Windows 真机验收。最高结论为：

`IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`

## PR #5 Judge 修复

助手作为 `extraResources` 中的真实文件打包，并在切换前复制到独立临时目录。下载器只允许 GitHub 官方 Release 资产主机，限制 HTTPS 重定向并分别设置连接、响应和总超时。ZIP 全部校验完成后才停止旧后端；助手确认旧 Electron 退出后记录 `.env`、DB、WAL、SHM、旧清单的存在状态并备份。回滚先停止新 Electron 进程树及冻结后端，恢复旧程序、旧清单和运行时文件，同时删除更新前不存在而新版本创建的文件。

新版本从命令行接收明确的 token、plan 和 readySignal 路径；主页加载成功后将实际端口、产品、版本、token、Electron PID 和后端 PID 写入指定回执。助手仅验证该回执及动态端口的健康和主页 HTTP，不扫描备份目录，也不固定端口。

## 最终收口与 CI 候选

唯一活动项为 Draft PR `#6` / `codex-xbl3c5`，Base `main@0f9afe8b1095e869cc9bbaa7306b13989b0a8ff9`。Head `71404954407a9a3a6362a398465fc822b1351c72` 的 CI Run `30547333980` 已 8/8 success；旧 PR #5 已关闭并由 PR #6 取代。

Windows CI 在 ZIP 与 SHA 完整验证后上传以 PR Head SHA 命名的临时候选 artifact，包含精确的便携 ZIP 和 `.zip.sha256`，保留 14 天且缺失即失败。该 artifact 只服务于后续 R5 Windows 验收，不是 GitHub Release，不改变版本、Tag 或发布状态。

当前结论：`IMPLEMENTATION PASS — R5 WINDOWS VALIDATION REQUIRED`；`DRAFT_HOLD`。


## PR #7 R5 Windows 基础启动返工

Head `d489a795b6089575a1fd61a27c9b28e2f3cb1b03` / Run `30564032072` 的旧 Artifact 在 Windows 11 隔离验收中因缺少 `fake_useragent.data` 和浏览器数据而启动失败，已禁止继续用于回滚模拟。

修复将 `fake-useragent` 约束为 `>=1.4.0,<3.0.0`（当前构建环境实际验证 2.2.0），Windows 与 macOS PyInstaller 均使用 `--collect-all fake_useragent`。冻结探针必须实际构造 `UserAgent` 并导入 `data_provider.efinance_fetcher`，从而覆盖 Eastmoney patch 的启动链。Windows 候选上传前还会在隔离临时 `.env`、数据库和日志目录中选择动态端口，真实启动 `stock_analysis.exe --serve-only`，等待健康与主页 HTTP 200，并在 finally 中终止进程树。任一步失败都会阻断 Artifact。

当前状态：`R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`。只有新 Head 完整 CI 通过并生成新的 Head-bound Artifact 后，才能重新进入 R5 基础启动验收。


## PR #8 CI 环境隔离修复

CI Run `30576678660` 暴露启动门环境契约：Actions Runner 的 `GITHUB_ACTIONS=true` 会命中 `main.py` 既有保护条件，使冻结进程存在但 serve-only 服务不启动。该保护条件不得删除。

Windows smoke 在启动冻结 EXE 前保存 `GITHUB_ACTIONS`、`PYTHONUTF8` 和 `PYTHONIOENCODING`，仅对子进程准备阶段设置 `GITHUB_ACTIONS=false`、`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`；finally 恢复全部变量并终止进程树。动态端口健康和主页 HTTP 200 仍是强制成功条件。当前保持 `R5_WINDOWS_BASIC_VALIDATION_FAILED — REWORK_REQUIRED — DRAFT_HOLD`，等待 PR #8 新 Head 完整 CI 与新 Artifact。
