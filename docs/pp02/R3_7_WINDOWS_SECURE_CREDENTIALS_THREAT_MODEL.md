# R3.7 Windows 安全凭据威胁模型与设计

> 状态：总控已批准进入 Work3 实施。本文冻结 R3.7 的安全边界、设计和验收标准。

## 1. 目标与非目标

R3.7 只解决 Windows Desktop 敏感配置的本机静态存储风险：API Key、Token、
Password、Secret、Webhook capability URL 等敏感值不得继续以明文写入 `.env`，
不得通过设置读取接口或配置导出回传明文。

非目标：

- 不保护已经登录同一 Windows 用户且能读取目标进程内存的恶意软件。
- 不保护用户主动粘贴到第三方程序、截图或自行导出的明文。
- 不为 Web、Docker、Linux 或 macOS 新增跨平台密钥服务。
- 不迁移旧项目的 DPAPI 部分实现、旧密钥或真实 `.env`。
- 不改变模型、通知、行情或调度的业务语义。
- 不使用真实密钥、真实通知渠道或真实账号做测试。

## 2. 受保护资产

- 模型和搜索服务的 API Key / Token。
- 邮件密码、Bot Token、签名 Secret。
- Webhook URL、Gotify/ntfy/AstrBot endpoint 等 capability URL。
- 自定义 LLM channel 的 API Key、API Keys 和 Extra Headers。
- 任何由配置注册表标记为 `is_sensitive=true` 的字段。

## 3. 信任边界与攻击面

| 边界 | 风险 | 控制 |
| --- | --- | --- |
| Web renderer → preload | XSS/恶意子 frame 调用高权限能力 | `contextIsolation=true`；只暴露窄 IPC；主进程校验 sender 和主 frame |
| preload → Electron main | 任意 key、超大值、mask 误写 | 主进程重新分类、格式/数量/长度校验；mask 为 no-op |
| Electron main → vault file | 明文落盘、半写、损坏 | 仅保存 `safeStorage.encryptString()` 的 base64；临时文件 + 原子 replace；版本/产品身份校验 |
| vault → backend child | 日志或命令行泄漏 | 只通过 child environment 注入；不放 argv；secure mode 不转发 backend stdout/stderr payload，日志只记阶段元数据 |
| backend config API | 读取、保存或导出明文 | 所有敏感字段统一 mask；Windows secure mode 拒绝把明文敏感值写入 `.env`；导出剔除敏感 assignment |
| 更新/备份/PR/CI | 密钥进入包、artifact、日志或仓库 | vault 位于 Electron `userData`，不进入安装包和便携 ZIP；只用固定假密钥验收；扫描源码、导出和日志 |

## 4. 选定方案

采用 Electron `safeStorage`。在 Windows 上它由当前 Windows 用户上下文的 DPAPI
提供静态加密。凭据仓库位于 Electron `userData`，使用版本化 JSON：

```json
{
  "version": 1,
  "productId": "com.hanchanqaq.pp02.aidailystockanalysis",
  "configVersion": "<mtime-ns>:<sha256-of-env-bytes>",
  "entries": {
    "EXAMPLE_API_KEY": "<DPAPI ciphertext as base64>"
  }
}
```

安全属性：

1. Windows Desktop 的敏感值只有 vault 一个持久化事实源。
2. renderer 永远没有“读取明文”IPC；只能提交替换/删除并查询存在状态。
3. 主进程启动或安全重启 backend 时解密，明文仅进入 Electron/Backend 进程内存。
4. backend 通过 `DSA_SECURE_CREDENTIAL_MODE=windows_dpapi` 和仅含字段名的
   `DSA_SECURE_CREDENTIAL_KEYS` 识别安全注入值。
5. Windows secure mode 下，backend 对敏感值返回统一 mask，并拒绝明文持久化。
6. 配置导出保留非敏感配置与注释，但删除全部敏感 assignment；不导出密文 vault。
7. 导入文件中的敏感 assignment 在 Windows Desktop 不直接写 `.env`；用户必须在
   设置页重新输入，由 safeStorage 保存。
8. `safeStorage` 不可用、vault 产品身份/版本非法、base64 非法或解密失败时 fail closed；
   不回退到 `basic_text`、明文 `.env` 或静默空值。
9. vault 与 `.env` 原始字节的精确版本绑定；版本不一致时拒绝解密注入，防止崩溃窗口
   把新凭据交给旧 endpoint 或把旧凭据交给新 endpoint。

## 5. 数据流

### 保存

1. renderer 把当前 draft 交给 backend 现有校验接口，不落盘。
2. Electron main 对敏感字段建立唯一待提交事务，只在内存中生成密文。
3. 非敏感字段先由现有 backend 配置服务写 `.env`，但不重载运行时。
4. Electron main 重新计算 `.env` 精确版本；只有与 backend 返回版本完全一致时才将
   版本与 vault 一并原子提交。任何中途崩溃都会在下次启动因版本不匹配而 fail closed。
5. Electron main 在验证事务已提交后清除残留敏感 assignment，并安全重启 backend。
6. 新 backend 从 vault 解密并通过 child environment 获得敏感值；设置页重新读取时只见 mask。

### 读取和使用

1. renderer 读取配置时，敏感字段只得到 mask、存在状态和 `windows_dpapi` 来源。
2. backend 内部消费者继续通过现有 `Config`/环境变量契约读取，无需新增第二套业务配置 API。
3. 模型/通知测试若选择“使用已保存凭据”，只能使用标记为安全注入的运行时值。

### 导出/导入

- 导出：删除敏感 assignment，不包含明文或密文；文件头声明凭据不会随备份导出。
- 导入：非敏感项沿用版本冲突保护；Windows Desktop 在 dotenv 解析前先扫描原始
  assignment 键，支持裸键、单引号键、双引号键及可选 `export`。因此例如 value
  引号不完整但仍存在合法敏感键的畸形行也返回明确拒绝，不静默丢弃。

## 6. 故障策略

- 加密不可用：拒绝保存，保留原 vault 和 `.env`。
- vault 写入失败：原 vault 保持可用；不重启 backend。
- `.env` 非敏感更新失败：不提交待处理 vault 事务。
- `.env` 已更新但 vault 未提交即崩溃/失败：旧 vault 的版本绑定与新 `.env` 不一致；
  下次启动拒绝注入任何凭据，不把错配组合交给外部 endpoint。
- vault 提交后 backend 重启失败：保留已加密 vault，显示可操作错误；下次启动继续使用同一 vault。
- vault 损坏或密文不可解：拒绝向 backend 注入任何 vault 值，错误消息不得包含密文或明文。
- renderer 刷新/崩溃留下的待提交事务：仅驻留主进程内存并有短期失效时间；不落盘。

## 7. 测试与验收

### 自动测试

- CredentialVault：Windows/加密可用门、原子写、增删、mask no-op、产品身份、损坏、
  解密失败、无明文落盘、字段和值大小限制。
- Desktop IPC：只允许主窗口主 frame；不暴露 read；敏感字段分类；backend env 注入；
  保存后安全重启；错误不含假密钥。
- Backend：所有敏感字段 mask；secure mode 拒绝明文 `.env` 写入；导出无敏感 assignment；
  非 Desktop 兼容路径不回退。
- Web：Desktop save 分离敏感/非敏感项；失败不显示明文；导出提示不再声称包含凭据。
- CI contract：Windows Job 必须执行假密钥 harness，并且 artifact/log/仓库根目录
  source 扫描不包含假密钥明文。

### 固定 Head Windows 假密钥验收

在 `windows-latest`、固定 PR Head 上运行 Electron harness：

1. 用仓库内明确标记的假密钥写入临时 vault。
2. 证明 vault 文件不含假密钥明文且可由同一 Windows 用户解密使用。
3. 证明导出的 `.env` 不含假密钥、密文字段或敏感 assignment。
4. 证明错误、stdout/stderr、源码、最终 ZIP、解包目录和上传 artifact 不含派生假密钥明文。
5. 记录 PR Head SHA、Run、Job 与结果；Head 改变后旧验收自动失效。

## 8. 回滚

代码回滚通过 revert R3.7 commits 完成。vault 不自动解密回写 `.env`；如回滚到旧版本，
用户必须重新配置凭据。该限制防止“回滚”成为明文导出通道。
