# 错误与经验

本文件记录 PP02 开发过程中可复用的错误、根因、修复和验证方法。

## 2026-07-29｜Electron productName 变更必须同步 macOS 验收路径

- 现象：electron-builder 已成功生成新名称的 `.app` 和 DMG，但
  `scripts/build-desktop-macos.sh` 返回“expected one unpacked macOS app, found 0”。
- 根因：`package.json` 的 `productName` 已改为
  `PP02 AI Daily Stock Analysis`，验收脚本仍用旧固定路径
  `Daily Stock Analysis.app` 查找未打包应用及 DMG 内应用。
- 修复：同步两个 App 路径，并在 Desktop 单测中同时断言 PP02 名称存在、旧固定
  路径不存在。
- 验证：必须同时运行 Desktop Node 单测和 macOS unsigned Desktop package 门；
  单看 electron-builder 成功不足以证明验收脚本兼容新产品名。
