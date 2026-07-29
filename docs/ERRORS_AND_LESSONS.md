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


## 2026-07-29｜产品级安全默认必须同步集成断言与设置帮助

- 现象：自动通知总开关实现后，完整后端门只剩 2 项失败：旧集成测试仍断言默认
  `notify=true`，新设置字段缺少 Web 帮助元数据。
- 根因：实现已改变产品级默认，但一个跨层测试和一个用户可见配置消费者未同步。
- 修复：将无显式开启的 API 集成断言改为 `notify=false`；为设置 Registry 补
  `help_key`，并补齐中英文标题、说明和帮助。
- 验证：安全默认改动必须同时覆盖真实入口行为、旧集成断言、配置 Registry、
  Web lint/build 和完整离线测试；仅让新增单元测试通过不足以收口。
