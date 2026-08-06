# 桌面端打包说明 (Electron + React UI)

本项目可打包为桌面应用，使用 Electron 作为桌面壳，`apps/dsa-web` 的 React UI 作为界面。

## 架构说明

- React UI（Vite 构建）由本地 FastAPI 服务托管
- Electron 启动时自动拉起后端服务，等待 `/api/health` 就绪后加载 UI
- Windows 便携/安装模式下，用户配置文件 `.env` 和数据库放在 exe 同级目录；macOS 打包版使用 Electron 用户数据目录保存运行时配置
- 桌面端会自动从本机 `8000-8100` 选择可用端口，并把实际选择的端口同步给内置后端；桌面端不依赖 `.env` 里的 `WEBUI_PORT` 来决定窗口连接地址，避免用户改端口后 Electron 仍等待旧端口导致启动超时
- Desktop backend 默认随 `requirements.txt` 安装并冻结 `futu-api==10.8.6808`；Windows/macOS 构建脚本会在源码环境和 PyInstaller 产物中分别执行 `import futu`，防止发布包只安装但未携带 SDK。

### Windows 程序文件与启动参数保护

Windows 构建在 electron-builder 完成签名阶段后，会为最终桌面 EXE 和冻结后端
EXE 生成闭合的 `resources/pp02-runtime-integrity.json`。清单只记录产品身份、版本、
固定相对路径、文件大小和 SHA-256，不记录用户目录、配置、数据库或凭据。安装包与
免安装 ZIP 都携带同一份清单；CI 和正式 Release 还会在最终 ZIP 解压后再次核验。

打包版桌面端在启动后端之前核对自身运行路径、两份 EXE 的路径、大小与 SHA-256。
清单缺失、路径改名或文件内容变化时会停止启动，不会执行后端，也不会启动分析任务。
后端同时要求桌面模式必须带完整的 `--serve-only --host <本机回环地址> --port
<1..65535>` 参数；参数被截断或混入大盘复盘、定时、个股、回测等模式时，会在加载
配置和数据库之前退出。打包版桌面端固定只监听 `127.0.0.1`，不会继承 `.env` 中的
公网监听值。

用户看到“程序文件或启动参数校验失败”时，应关闭当前程序，从本项目官方 GitHub
Release 重新下载安装包；PP02 不会自动删除、隔离、改名或修复系统文件，也不会修改
杀毒软件设置。此保护用于阻止异常程序进入业务流程，不能替代系统级安全扫描。

## 本地开发

一键启动（开发模式）：

```bash
powershell -ExecutionPolicy Bypass -File scripts\run-desktop.ps1
```

或手动执行：

1) 构建 React UI（输出到 `static/`）

```bash
cd apps/dsa-web
npm install
npm run build
```

2) 启动 Electron 应用（自动拉起后端）

```bash
cd apps/dsa-desktop
npm install
npm run dev
```

首次运行时会自动从 `.env.example` 复制生成 `.env`。

## 打包 (Windows)

### 前置条件

- Node.js 22.12+（Desktop 构建链要求；独立 Web CI 仍使用 Node 20）
- Python 3.10+
- 开启 Windows 开发者模式（electron-builder 需要创建符号链接）
  - 设置 -> 隐私和安全性 -> 开发者选项 -> 开发者模式

### 一键打包

```bash
powershell -ExecutionPolicy Bypass -File scripts\build-all.ps1
```

该脚本会依次执行：
1. 构建 React UI
2. 安装 Python 依赖
3. PyInstaller 打包后端
4. electron-builder 打包桌面应用

当前 Windows 安装包使用 NSIS 向导式安装流程，仅支持当前用户安装且已禁用管理员提权，安装时可手动选择目标目录（例如非 C 盘）。安装器通过 NSIS `.onVerifyInstDir` 回调在安装器层面阻止选择 `Program Files`、`Windows` 等系统保护目录——选择这些路径时"下一步"按钮会被自动禁用。安装完成后，桌面端仍会按现有逻辑在安装目录旁生成/读取 `.env`、`data/stock_analysis.db`（含 `data/stock_analysis.db-wal` / `data/stock_analysis.db-shm`）和 `logs/desktop.log`。推荐使用默认的 per-user 安装目录。如果不想安装，仍可继续分发 `win-unpacked` 免安装包。

## GitHub CI 自动打包并发布 Release

仓库已支持通过 GitHub Actions 自动构建桌面端并上传到 GitHub Releases：

- 工作流：`.github/workflows/desktop-release.yml`
- 触发方式：
  - 推送语义化 tag（如 `v3.2.12`）后自动触发
  - 在 Actions 页面手动触发并指定 `release_tag`
- 产物：
  - Windows 安装包：Release 附件和本地 `apps/dsa-desktop/dist/` 中统一为 `pp02-ai-daily-stock-analysis-windows-installer-<tag>.exe`
  - Windows 自动更新元数据：Release 附件会额外保留 `latest.yml` 和 `*.blockmap`，供安装版桌面端后台下载与校验更新；普通用户无需手动下载这些元数据。下载完成后用户确认“重启安装”时，桌面端会先停止内置后端、备份运行时文件，并以静默模式执行安装器。
  - Windows 免安装包：`pp02-ai-daily-stock-analysis-windows-noinstall-<tag>.zip`
  - macOS Intel：`pp02-ai-daily-stock-analysis-macos-x64-<tag>.dmg`
  - macOS Apple Silicon：`pp02-ai-daily-stock-analysis-macos-arm64-<tag>.dmg`

### macOS 提示“应用已损坏，无法打开”

当前 macOS DMG 尚未使用 Apple Developer 证书签名和公证。构建配置会显式生成 unsigned 应用，在 PyInstaller 产物首次执行前清理残缺签名，并通过 electron-builder `afterPack` hook 在 DMG 创建前再次清理完整 `.app`；CI 还会检查 Electron 原始 `.app` 和 DMG 挂载后的 `.app`，阻止再次发布带有 `code has no resources but signature indicates they must be present` 等损坏签名的产物。该处理只能缓解 v3.27.0 的残缺签名缺陷，**不会让应用获得 Apple 信任**。通过浏览器下载后，macOS Gatekeeper 仍可能提示“无法验证开发者”、阻止启动，或要求用户人工确认。

请按以下顺序排查：

1. 只从项目的 [GitHub Releases](https://github.com/hanchanqaq-source/daily_ai_stock_analysis/releases) 下载附件，并确认安装包架构与 Mac 一致：Apple 芯片（M1/M2/M3/M4 等）使用 `pp02-ai-daily-stock-analysis-macos-arm64-<tag>.dmg`，Intel 芯片使用 `pp02-ai-daily-stock-analysis-macos-x64-<tag>.dmg`。不要对第三方转载或来源不明的安装包绕过 Gatekeeper。
2. 打开 DMG，将 `PP02 AI Daily Stock Analysis` 拖入“应用程序”后尝试启动一次。若被拦截，进入“系统设置 -> 隐私与安全性”，在安全性提示处确认应用名称，然后点击“仍要打开”，按系统提示再次确认。较旧 macOS 的对应入口为“系统偏好设置 -> 安全性与隐私 -> 通用”。
3. 仅当安装包确认来自上述官方 Release、且“仍要打开”仍无法放行时，打开“终端”清除该应用的下载隔离属性，然后重新启动：

```bash
xattr -dr com.apple.quarantine "/Applications/PP02 AI Daily Stock Analysis.app"
```

如果应用不在 `/Applications`，请将命令中的路径替换为实际 `.app` 路径。不要对整个“应用程序”目录执行 `xattr`，也不要对来源不明的应用执行此命令。不同 macOS 版本可能仍拒绝 unsigned 应用，清除 quarantine 不保证能够放行。长期彻底消除该提示需要在发布流程中接入 Apple Developer 签名与 notarization（公证），不属于上述临时放行步骤。

维护者可用以下命令区分“预期的 unsigned 拒绝”和“不可发布的残缺签名”：

```bash
codesign -d "/Applications/PP02 AI Daily Stock Analysis.app"
spctl --assess --type execute --verbose=4 "/Applications/PP02 AI Daily Stock Analysis.app"
```

当前 unsigned 产物的 `codesign -d` 预期包含 `code object is not signed at all`，`spctl` 预期拒绝；如果输出 `code has no resources but signature indicates they must be present` 或其它签名损坏信息，应视为发布阻断。

建议发布流程：

1. 合并代码到 `main`
2. 由自动打 tag 工作流生成版本（或手动创建 tag）
3. `desktop-release` 工作流自动构建并把两个平台安装包附加到对应 GitHub Release

## 发版前可复现验证（桌面更新链路）

桌面端自动更新链路依赖 Windows NSIS 安装产物、`latest.yml` 与 `*.blockmap` 元数据。
PR 的 `desktop-futu-package-windows` 与正式 `desktop-release` Windows Job 现在都会在
Node 22 下调用同一个 `scripts/verify-windows-installer.ps1`：对本次 Job 自己创建的
`RUNNER_TEMP/pp02-installer-verify-*` 目录执行静默安装，核对版本、资源、冻结后端和
HKCU 卸载登记，启动到 `Main UI loaded in`，停止后再次启动，并在应用仍运行时只调用
一次官方卸载器，确认应用/后端进程归零、程序文件及登记消失。
首次启动前，验证器还会调用 `scripts/windows-defender-scan.js` 对真实安装目录执行
Microsoft Defender 自定义扫描；候选和发布工作流也会扫描安装器、元数据、免安装
ZIP、解包目录和最终发布目录。扫描器不可用、病毒库过期、引擎非 Normal 模式、
发现威胁或扫描出错都会阻止候选上传或 Release 发布，并保留绑定精确 Head 的报告。

卸载助手与一个闭合的两项清单一起放在安装目录的 `resources` 下。助手从自身位置
推导安装根，只匹配清单中桌面 EXE 和冻结后端的完整路径；NSIS 不通过命令行传入
安装根、程序名或后端路径。CI 会读取助手写入验收诊断目录的脱敏 JSON，只记录执行
状态和初始/最终数量，不记录机器范围进程、凭据或用户数据。Windows 合同还会启动
一个位于外部目录的同名对照进程，要求卸载助手保留它。

验证器只允许删除它已确认归属于本次运行且在执行前不存在的临时目录，不扫描或删除
既有 PP02 安装目录和用户目录。CI 生命周期验证不替代正式 Release 的可见安装向导、
空数据、安全默认和重启验收；后者仍须在授权后的 Windows 实机上单独执行。

Windows 上可先运行验证器自身的失败进程与清理边界契约：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/tests/verify-windows-installer-contract.ps1
```

再对明确的候选安装器执行完整生命周期验证：

```powershell
$version = (Get-Content apps/dsa-desktop/package.json -Raw | ConvertFrom-Json).version
$installer = Get-Item "apps/dsa-desktop/dist/pp02-ai-daily-stock-analysis-windows-installer-v$version.exe"
$root = Join-Path $env:RUNNER_TEMP "pp02-installer-verify-$((git rev-parse HEAD).Trim())"
$diagnostics = Join-Path $env:RUNNER_TEMP "pp02-installer-diagnostics-$((git rev-parse HEAD).Trim())"
$defenderReports = Join-Path $env:RUNNER_TEMP "pp02-defender-reports-$((git rev-parse HEAD).Trim())"
New-Item -ItemType Directory -Path $defenderReports -Force | Out-Null
powershell -ExecutionPolicy Bypass -File scripts/verify-windows-installer.ps1 `
  -InstallerPath $installer.FullName `
  -ExpectedVersion $version `
  -InstallRoot $root `
  -DiagnosticRoot $diagnostics `
  -ExpectedCommitSha ((git rev-parse HEAD).Trim()) `
  -MalwareScannerPath scripts/windows-defender-scan.js `
  -MalwareReportPath (Join-Path $defenderReports 'installed.json')
```

Linux 无法直接执行该 Windows 安装器门；以 PR 固定 Head 的 `windows-latest` Job
输出为准，不得把 Linux 静态检查冒充安装验证。

1. 先构建 Web 静态产物（桌面端主窗口与设置页入口依赖）

```bash
cd apps/dsa-web
npm ci
npm run lint
npm run build
```

2. 回到桌面端，补齐依赖、运行 preload 单测、再执行 Electron 打包

```bash
cd ../dsa-desktop
npm ci
npm test
npm run build
```

在 Windows 发布复核环境，还可额外执行：

```powershell
./scripts/verify-desktop-updater-artifacts.ps1 -ReleaseTag v$(node -p "require('./apps/dsa-desktop/package.json').version")
```

> 预期当前执行环境不支持生成 Windows NSIS 安装器时，请在交付说明中明确注明平台限制，并要求指定的 Windows 发布链路复核人补齐该项验证。

3. 检查更新元数据是否产出

```bash
ls -1 dist | sort
ls -1 dist/*.yml dist/*.blockmap 2>/dev/null || true
```

4. 强制对齐版本与发布附件（可在 Windows 环境或能产出 NSIS 产物的执行器上复核）

```bash
RELEASE_TAG="v$(node -p \"require('./package.json').version\")"
REPO="hanchanqaq-source/daily_ai_stock_analysis"

for f in dist/*latest.yml dist/*.blockmap dist/pp02-ai-daily-stock-analysis-windows-installer-*.exe; do
  [ -f \"$f\" ] && echo \"[FOUND] $f\"
done

if [ -f dist/latest.yml ]; then
  echo \"---- latest.yml 版本片段 ----\"
  grep -E \"^version:|^files:|^sha512:\" dist/latest.yml
fi

echo \"---- Release 清单（人工核对）----\"
echo \"Release Tag: $RELEASE_TAG\"
echo \"Release 地址: https://github.com/$REPO/releases/tag/$RELEASE_TAG\"
echo \"应核对附件是否包含:\"
echo \"- pp02-ai-daily-stock-analysis-windows-installer-*.exe\"
echo \"- latest.yml\"
echo \"- *.blockmap\"
echo \"并确保 latest.yml 中 version 与 tag 的语义化版本一致，path/url 与安装包附件名一致\"
```

5a. 建议在 PR 描述里记录的“可复核输出”（Windows）：

```bash
echo "release-tag=${RELEASE_TAG}"
echo "latest.yml version:"
grep -E "^version:" dist/latest.yml
echo "latest.yml files:"
sed -n '1,80p' dist/latest.yml
echo "packaging artifacts:"
ls -1 dist/*.yml dist/*.blockmap dist/*installer*.exe 2>/dev/null | sort
```

Windows 发布链路复核清单（在 PR 后由发布团队/维护者执行）：

- release/tag 与 `pp02-ai-daily-stock-analysis-windows-installer-<tag>.exe` 的版本号一致；
- `latest.yml`、`pp02-ai-daily-stock-analysis-windows-installer-<tag>.exe`、`*.blockmap` 同 tag 同步出现且可下载；
- `latest.yml` 中 `version` 与 Release tag 语义一致（去掉 `v` 前缀后比对），且 `path` / `files.url` 与安装包附件名一致；
- 如缺少上述文件或 `release-tag` 不匹配，需标注阻断并补齐 `desktop-release` 打包流程。

5. Windows/NSIS 产物与发布附件一致性请在 Windows 环境手动验证（可人工触发发布流程），并在升级后核对运行时文件留存：

   1. 安装前后分别记录安装目录中的 `.env`、`data/stock_analysis.db`、`data/stock_analysis.db-wal`、`data/stock_analysis.db-shm`、`logs/desktop.log` 的 SHA256；
   2. 确认桌面端下一次启动后，上述文件仍存在且与安装前记录一致；
   3. 如不一致，可在应用退出后检查用户数据目录中的 `.dsa-desktop-update-backup` 是否清理完整，并结合最新日志串联排查。

Windows 平台建议使用 PowerShell 执行：

```bash
Get-FileHash .env,data\\stock_analysis.db,data\\stock_analysis.db-wal,data\\stock_analysis.db-shm,logs\\desktop.log -Algorithm SHA256
```

说明：应用已在 Windows NSIS 安装版的“重启安装”前停止内置后端、备份安装目录旁上述运行时文件，并以静默模式运行更新安装器，目的是避免安装向导抢先覆盖仍在运行的桌面端进程，同时降低更新过程中文件丢失风险；若恢复失败，桌面端会显示更新安装错误并保留手动下载路径供回退处理。此次修复仅改动 Windows 更新安装链路与内置后端进程生命周期处理，不涉及设置保存语义、模型运行时清理策略或配置迁移行为。

### 分步打包

1) 构建 React UI

```bash
cd apps/dsa-web
npm install
npm run build
```

2) 按现有脚本打包 Python 后端（脚本已内置 AlphaSift、Futu SDK 与 AkShare 数据文件收集）

- Windows：

```bash
powershell -ExecutionPolicy Bypass -File scripts\build-backend.ps1
```

- macOS：

```bash
bash scripts/build-backend-macos.sh
```

该脚本会在安装依赖后执行 `--collect-all alphasift`、`--collect-all futu` 和 `--collect-data akshare`。构建完成后会通过冻结可执行文件校验 `alphasift.dsa_adapter`、`futu`、`orjson` 均可导入，并确认 AkShare 的 `file_fold/calendar.json` 已进入冻结产物，避免发行包在热点题材、Futu 持仓导入或日线增强路径中因缺少依赖/package data 降级。PR 主 CI 在 `requirements.txt`、Futu broker、Desktop 打包入口或相关 workflow 变化时，会分别运行 `desktop-futu-package-windows` 与 `desktop-futu-package-macos` 阻断检查。

3) 打包 Electron 桌面应用

```bash
cd apps/dsa-desktop
npm install
npm run build
```

打包产物位于 `apps/dsa-desktop/dist/`。Windows 安装器会生成 `pp02-ai-daily-stock-analysis-windows-installer-<tag>.exe`，安装向导中可选择安装目录。

## 目录结构

Windows 安装包模式下，安装器仅支持当前用户安装且已禁用管理员提权，用户可在安装向导中选择安装目录；安装器会在安装器层面阻止选择 `Program Files`、`Windows` 等系统保护目录（选择时"下一步"按钮自动禁用），安装完成后，应用会在安装目录旁生成/读取 `.env`、`data/stock_analysis.db`（含 `data/stock_analysis.db-wal` / `data/stock_analysis.db-shm`）和 `logs/desktop.log`。请保留默认的 per-user 安装位置或选择其他用户可写目录。

`win-unpacked` 免安装模式下，目录结构如下：

```
win-unpacked/
  PP02 AI Daily Stock Analysis.exe    <- 双击启动
  .env                        <- 用户配置文件（首次启动自动生成）
  data/
    stock_analysis.db         <- 数据库主文件
    stock_analysis.db-wal     <- WAL 日志文件（更新备份/恢复）
    stock_analysis.db-shm     <- WAL 共享元文件（更新备份/恢复）
  logs/
    desktop.log               <- 运行日志
  resources/
    .env.example              <- 配置模板
    backend/
      stock_analysis.exe      <- 后端服务
```

## 配置文件说明

- Windows 桌面端的 `.env` 放在 exe 同目录下
- macOS 打包版的 `.env`、`data/` 和 `logs/` 放在 Electron 用户数据目录，避免替换 `.app` 时丢失
- 首次启动时自动从 `.env.example` 复制生成
- 从旧版本升级时，如果旧 `.app` 包内部的 `.env`、`data/stock_analysis.db` 或日志文件仍可访问，新版本会在目标文件不存在时自动迁移到用户数据目录；已有目标文件不会被覆盖
- 用户需要编辑 `.env` 配置以下内容：
  - `GEMINI_API_KEY` 或 `OPENAI_API_KEY`：AI 分析必需
  - `STOCK_LIST`：自选股列表（逗号分隔）
  - 其他可选配置参考 `.env.example`

### 配置备份 / 恢复 `.env`

- WebUI 与桌面端都可以从 `系统设置 -> 配置备份` 看到 `导出 .env` 和 `导入 .env` 按钮
- WebUI 非桌面运行时需要先开启管理员认证并完成登录；未开启认证时按钮会禁用，API 返回 `403`
- `导出 .env` 会导出当前**已保存**的 `.env` 备份文件；页面上尚未点击“保存配置”的本地草稿不会被导出
- `导入 .env` 会读取备份文件中的键值并合并到当前配置中，导入后会立即触发配置重载
- 导入是“键级覆盖”而不是整文件替换：备份文件中出现的键会覆盖当前值，未出现的键保持不变
- 如果当前页面还有未保存草稿，导入前会先提示确认，避免把本地草稿和已保存配置混在一起
- Web 端默认 `ADMIN_AUTH_ENABLED=false` 时，设置页会展示按钮为禁用态并提示先启用管理员鉴权；桌面端不受该配置影响，仍可直接使用配置备份/恢复能力。

> 建议：从旧版本升级的 macOS 用户仍可在升级前执行一次 `导出 .env` 作为保险；如果旧 `.app` 已经被整体替换，包内旧文件无法凭空恢复，只能通过备份导入。

### 设置页版本信息

- `系统设置 -> 版本信息` 中的“桌面端版本”由 Electron 主进程的 `app.getVersion()` 提供，并通过 preload bridge 暴露给前端
- 开发态 `npm run dev` 与打包态 `npm run build` / 安装包都会复用同一条版本注入链路，不再在 `preload.js` 里维护独立硬编码版本号
- `README.md` 继续保留安装和运行入口说明；这类桌面端运行时细节统一落在本专题文档维护，避免入门文档膨胀

### 局域网访问 Windows 桌面端 WebUI

- 桌面端默认仍按 `WEBUI_HOST=127.0.0.1` 只允许本机访问，避免安装后无意暴露后端服务
- 如需让同一局域网内其他设备访问，在桌面端 `.env` 或 `系统设置 -> WebUI 监听地址` 中设置 `WEBUI_HOST=0.0.0.0`，保存后重启桌面端
- 桌面端会自动选择 `8000-8100` 中可用端口并传给后端；常见情况下仍是 `8000`，若端口被占用，可在 `logs/desktop.log` 查看 `Using port ...` 和 `Backend launch command=...`
- Windows 防火墙或服务器安全组仍需放行实际监听端口；对外暴露前建议同时启用 `ADMIN_AUTH_ENABLED`
- 即使后端绑定 `0.0.0.0`，桌面窗口自身仍会使用本机可访问地址完成健康检查和页面加载

### 桌面端更新提醒

- 应用在主界面加载完成后会后台检查 GitHub Releases 的最新正式版，并与当前 `app.getVersion()` 做语义化版本比较
- Windows NSIS 安装版会通过内置 GitHub 更新源自动下载新版本；下载完成后弹出一次性提醒，用户确认后静默重启并安装
- 自动更新静默安装会复用当前安装目录；如果用户安装时选择了非默认目录或带空格目录，后续自动更新仍会覆盖同一目录
- `系统设置 -> 版本信息` 中的“桌面端更新”区域可手动检查更新；若更新已下载，会展示“重启安装”操作
- Windows 免安装包、开发态和 macOS DMG 仍保持“提醒 + 跳转下载页”的兼容路径，不会因为网络失败而阻断桌面端启动
- 版本检查失败、GitHub API 超时、更新元数据缺失或下载安装异常时，会记录到 `logs/desktop.log`，设置页手动检查时会展示错误状态

## 常见问题

### 启动后一直显示 "Preparing backend..."

1. 检查 `logs/desktop.log` 查看错误信息
2. 确认 `.env` 文件存在且配置正确
3. 确认端口 8000-8100 未被占用；桌面端会自动选择其中一个可用端口，无需通过 `.env` 手动改 `WEBUI_PORT`
4. 如果日志里显示 Electron 等待的端口和后端实际监听端口不一致，优先升级到包含桌面端端口同步修复的版本

### 后端启动报 ModuleNotFoundError

PyInstaller 打包时缺少模块，需要在 Windows 与 macOS 后端构建脚本中同步增加 `--hidden-import`，并对冻结产物执行运行时导入校验。当前脚本会显式安装、冻结并探测 LiteLLM 运行路径需要的 `orjson`；若日志包含 `No module named 'orjson'`，请升级到修复版本并重新构建，不能只在已发布目录中手工安装依赖。

如果日志提示缺少 `akshare/file_fold/calendar.json`，说明后端冻结产物没有完整收集 AkShare package data。请使用仓库当前的 `scripts/build-backend.ps1` 或 `scripts/build-backend-macos.sh` 重新构建；脚本会在生成桌面包前检查该文件，缺失时直接终止构建。

### UI 加载空白

确认 `static/index.html` 存在，如不存在需重新构建 React UI。

### macOS 升级后配置迁移

旧版本曾把运行时 `.env`、数据库和日志写在 `.app` 包内部。新版本改为使用 Electron 用户数据目录，并在旧 `.app` 包内文件仍可访问时做一次性迁移。迁移规则是“目标不存在才复制”，避免覆盖用户已经在新版本中保存的配置。

如果旧 `.app` 已经被整体替换，旧包内 `.env` 无法由新版本自动恢复。此时可使用升级前导出的 `.env` 在 `系统设置 -> 配置备份` 中手动导入；完成一次迁移或重新配置后，后续版本会继续复用用户数据目录，不再随 `.app` 替换丢失。

## 分发给用户

Windows 分发现在有两种方式：

1. 安装包：分发 `apps/dsa-desktop/dist/` 下的 `pp02-ai-daily-stock-analysis-windows-installer-<tag>.exe`，用户安装时可自行选择目标目录
2. 免安装包：将 `apps/dsa-desktop/dist/win-unpacked/` 整个文件夹打包发给用户

使用 `win-unpacked` 免安装包时，用户只需：

1. 解压文件夹
2. 仅在 `.env` 配置股票列表等非敏感项；API Key 等凭据在首次启动后从
   Desktop 设置页输入
3. 双击 `PP02 AI Daily Stock Analysis.exe` 启动

## PP02 Windows 便携安全更新（R3.6）

Windows NSIS 安装版仍由 `electron-updater` 自动下载，并由用户确认重启安装。PP02 便携版必须在包根目录带有 `pp02-portable-release.json`；启动时仅检查元数据，用户点击“安全更新”后才下载和校验。详细安全契约、清单字段、回滚与验证边界见 [`pp02/R3_6_WINDOWS_PORTABLE_UPDATE_IMPLEMENTATION.md`](pp02/R3_6_WINDOWS_PORTABLE_UPDATE_IMPLEMENTATION.md)。便携资产为 `pp02-ai-daily-stock-analysis-windows-noinstall-vX.Y.Z.zip` 及同名 `.zip.sha256`。

## PP02 Windows 安全凭据（R3.7）

Windows Desktop 的敏感配置保存到 Electron `userData` 下的 `safeStorage` /
DPAPI 加密 vault。设置页只显示遮罩和存在状态，配置导出不包含凭据或
vault 密文；恢复 `.env` 备份后需重新输入凭据。详细边界与故障处理见
[`pp02/R3_7_WINDOWS_SECURE_CREDENTIALS_THREAT_MODEL.md`](pp02/R3_7_WINDOWS_SECURE_CREDENTIALS_THREAT_MODEL.md)。
