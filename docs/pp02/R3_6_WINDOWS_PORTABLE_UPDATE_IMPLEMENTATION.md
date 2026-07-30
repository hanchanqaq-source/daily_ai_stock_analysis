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
