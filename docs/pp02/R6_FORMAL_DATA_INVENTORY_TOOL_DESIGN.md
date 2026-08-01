# PP02 R6-A 正式数据安全盘点工具设计

## 决策状态

- 用户决定：采用建议，在云端开发正式数据盘点工具。
- 当前阶段：Work5 / R6-A 最终本地验证和独立复核通过，独立 Draft PR 固定 Head CI
  待验证；用户已
  于 2026-08-01 批准按本设计实施。
- 固定起点：Work4 Draft PR #12 Head
  `a220e9e146e14722561bc084ec4e5306b30d36c7`。
- 分支关系：Work5 使用独立分支；Draft PR 初始以 Work4 分支为 Base，仅显示
  Work5 增量。PR #12 无需先合并，Work5 也不得借此合并或发布。
- 开发环境：云端 Linux；只使用动态生成的空库和人工假数据库。
- 最终运行环境：后续另行授权的 Windows 本机验收。
- 数据边界：本 Work 不读取、复制、上传、迁移或修改任何真实数据库。

## 白话用途

本工具是“数据库安全体检器”，不是迁移器。它解决的唯一问题是：用户不确定旧版
PP02 是否保存过需要保留的正式股票账本数据。

未来在 Windows 本机运行时，用户或本机 Codex 明确选择一个候选 SQLite 数据库，
工具先制作两套本地备份，再只对临时检查副本执行完整性、表结构和 `COUNT(*)`
检查，最后只报告以下四类正式事件各有多少条：

- `portfolio_accounts`：股票账户；
- `portfolio_trades`：买入、卖出等交易事件；
- `portfolio_cash_ledger`：入金、出金等现金流水；
- `portfolio_corporate_actions`：分红、送股、拆股等公司行动。

报告不包含账户名、券商名、股票代码、金额、日期、备注或任何数据行。盘点完成后
也不会自动进入迁移；只有发现正式数据，才回到下一次精确迁移授权门。

## 方案比较与裁决

1. **采用：显式数据库路径 + 双备份 + 临时只读检查副本。** 不自动搜索个人
   目录；先保住原文件，再只读取固定表名和计数。该方案风险最小、结果足够支持
   “是否需要迁移”的决定。
2. 不采用：自动扫描整台 Windows 电脑。它会扩大到无关个人目录和数据库，且无法
   保证候选都属于 PP02。
3. 不采用：把盘点逻辑直接并入 R4/R6 迁移器。它会混淆“只检查”和“会写目标库”
   的授权边界，也可能导入项目数据库模块并触发建表或 Schema 升级。

## 组件与责任

### `src/services/formal_data_inventory_service.py`

这是不导入 `src.storage`、SQLAlchemy、配置或应用启动模块的独立安全核心：

- 只接受调用方显式传入的一个 SQLite 文件和一个全新输出目录；
- 拒绝符号链接、Windows reparse point、非普通文件和与源文件重合的输出；
- 在读取数据库内容前记录主文件及已有 `-wal`、`-shm` 的大小、修改时间和
  SHA-256；
- 将主文件和已有 sidecar 分别复制到 `backup-a` 与 `backup-b`；
- 复制后再次计算源文件指纹；任一文件变化、缺失或备份哈希不一致时失败关闭；
- 两套正式备份均不直接打开；另从 `backup-a` 建立自动清理的检查副本；
- 只用 Python 标准库 `sqlite3` 打开检查副本，启用 `query_only`，执行
  `PRAGMA integrity_check`、固定表的 Schema 检查和 `COUNT(*)`；
- 任何异常只向外返回稳定错误码，不把路径、SQL、行值或底层异常写进报告。

### `scripts/pp02_formal_data_inventory.py`

提供薄 CLI，并设置三道硬门：

- 必须运行在 Windows 原生 Python；Linux、WSL 和远程容器立即返回
  `wrong_environment`；
- 必须显式传入 `--source`、`--output-dir` 和
  `--confirm-apps-closed`；不提供目录扫描或自动候选发现；
- 输出目录必须是新目录，并且不得位于 Git 仓库内。

成功时标准输出只包含最终裁决；失败时标准错误只包含稳定错误码。CLI 不导入项目
数据库模型，也不调用 R4 的迁移演练服务。

Schema 检查只比较以下固定列名，不读取列值，也不导入应用模型：

| 表 | 必需列 |
| --- | --- |
| `portfolio_accounts` | `id`、`owner_id`、`name`、`broker`、`market`、`base_currency`、`is_active`、`created_at`、`updated_at` |
| `portfolio_trades` | `id`、`account_id`、`trade_uid`、`symbol`、`market`、`currency`、`trade_date`、`side`、`quantity`、`price`、`fee`、`tax`、`note`、`dedup_hash`、`created_at` |
| `portfolio_cash_ledger` | `id`、`account_id`、`event_date`、`direction`、`amount`、`currency`、`note`、`created_at` |
| `portfolio_corporate_actions` | `id`、`account_id`、`symbol`、`market`、`currency`、`effective_date`、`action_type`、`cash_dividend_per_share`、`split_ratio`、`note`、`created_at` |

### `tests/test_formal_data_inventory.py`

全部数据库在测试临时目录动态生成，且只含空库或人工假数据。测试不提交 `.db`、
备份、报告或日志，覆盖：

- 四表均为空、任一表有数据和完全没有四张正式表；
- 部分正式表、缺少必需列、损坏 SQLite 和完整性失败；
- 双备份内容一致、源文件不变、WAL/SHM 随主文件一起保护；
- 复制期间源文件变化、已有输出目录、源/输出重合、符号链接或 reparse point；
- Linux/WSL 环境拒绝、未确认程序关闭拒绝；
- 报告和 stdout/stderr 不泄漏人工账户名、股票代码、金额或备注；
- 测试通过 monkeypatch 模拟 Windows 环境；云端测试绝不解除正式 CLI 的 Windows
  环境硬门。

## 数据流

1. 用户关闭旧版与当前版 PP02 程序。
2. 用户或 Windows 本机 Codex明确指定一个候选 `stock_analysis.db`。
3. CLI 检查 Windows 环境、人工关闭确认、路径和新输出目录。
4. 服务记录源主文件及 sidecar 指纹。
5. 服务生成 `backup-a` 和 `backup-b`，逐文件核对 SHA-256。
6. 服务再次核对源指纹；源有变化则停止，绝不继续盘点。
7. 服务从 `backup-a` 生成临时检查副本，只读检查完整性、Schema 和四项计数。
8. 服务原子写入一份值受限 JSON 报告，清理临时检查副本，保留两套本地备份。
9. 用户只根据最终裁决决定是否进入下一次精确迁移授权门。

## 实现入口与后续 Windows 用法

- 安全核心：`src/services/formal_data_inventory_service.py`；只使用 Python 标准库。
- Windows CLI：`scripts/pp02_formal_data_inventory.py`；没有自动扫描或迁移入口。
- 固定报告名：`pp02-formal-data-inventory-report.json`。
- 固定备份目录：`backup-a`、`backup-b`；两套备份通过逐文件 SHA-256 复核后才允许
  检查临时副本。

后续获得 Windows 真实盘点精确授权、关闭旧版和当前版 PP02 后，在固定 PR Head 的
Windows 原生隔离候选中运行：

```powershell
$sourcePath = Read-Host "旧数据库的完整路径"
$outputDirectory = Read-Host "全新本地输出目录的完整路径"
python scripts/pp02_formal_data_inventory.py `
  --source $sourcePath `
  --output-dir $outputDirectory `
  --confirm-apps-closed
```

要求：

- `$sourcePath` 只能是人工明确选择的一个 SQLite 文件，不支持目录或候选搜索；
- `$outputDirectory` 必须不存在、位于 Git 仓库外，且不得与源文件重合；
- 省略 `--confirm-apps-closed`、在 Linux/WSL 中运行或输出位于 Git 仓库内都会在
  备份前拒绝；
- 无效参数或重复的单值路径参数只返回 `invalid_arguments`，不会回显原始参数或路径；
- 主文件快照和两套备份复制前后都会复查 rollback journal；若清理未验证输出失败，
  会显式返回 `untrusted_output_cleanup_failed`，不得把残留目录当作有效备份；
- 成功时标准输出只显示 `FORMAL_DATA_FOUND` 或 `NO_FORMAL_DATA_FOUND`；
- 安全前提不成立时标准错误只显示稳定错误码，若双备份已经验证则本地保留
  `INVENTORY_BLOCKED` 受限报告和两套备份；
- 输出目录、报告和备份只保留在 Windows 本机，不上传到 GitHub、Actions、PR、
  artifact、日志、截图或云端会话。

本命令不会自动迁移。`FORMAL_DATA_FOUND` 只表示需要回到下一次精确迁移授权门；
`NO_FORMAL_DATA_FOUND` 只表示所选数据库的四类正式账本为空或不存在。云端测试和
CI 即使全部通过，也只证明工具对空库/人工假库的行为，不代表 Windows 真实盘点已
执行或通过。

## 输出契约

报告固定只允许以下信息：

```json
{
  "report_version": 1,
  "project_id": "PP02",
  "status": "FORMAL_DATA_FOUND",
  "backup": {
    "copies": 2,
    "verified": true,
    "source_unchanged": true,
    "included_sidecars": ["-wal", "-shm"]
  },
  "database": {
    "integrity_ok": true,
    "schema_compatible": true,
    "counts": {
      "portfolio_accounts": 1,
      "portfolio_trades": 1,
      "portfolio_cash_ledger": 1,
      "portfolio_corporate_actions": 1
    }
  },
  "privacy": {
    "row_values_selected": false,
    "row_values_reported": false,
    "real_data_uploaded": false,
    "migration_performed": false
  }
}
```

`status` 只允许：

- `FORMAL_DATA_FOUND`：四张表完整，且任意一张计数大于 0；
- `NO_FORMAL_DATA_FOUND`：四张表完整且全部为 0，或四张表全部不存在；
- `INVENTORY_BLOCKED`：数据库损坏、正式表只存在一部分、必需列缺失、源在备份
  期间变化、备份不一致或其他安全前提不成立。

错误报告不包含源路径、输出路径、文件名、表定义、SQL、异常正文或数据值。

## 安全与失败处理

- 源数据库和 sidecar 永不以写模式打开；不执行建表、升级、迁移、恢复或清理。
- 两套备份都必须完成并通过哈希复核，才允许读取检查副本。
- 若源旁存在回滚日志 `-journal`，视为程序未正常关闭或数据库状态不稳定，立即以
  `INVENTORY_BLOCKED` 停止，不复制、不盘点。
- 备份阶段失败时删除本次未完成的临时输出，但不删除或修改源文件。
- 盘点阶段失败时保留已经验证的两套备份，写入值受限的
  `INVENTORY_BLOCKED` 报告，便于人工判断；不自动重试或换库。
- 输出目录和报告只留在 Windows 本机，不进入 Git、PR、Actions、artifact、日志、
  截图或云端会话。
- 云端只能验证假库行为；不得把 CI PASS 表述成 Windows 真实数据盘点通过。

## 非目标

- 不搜索 Windows 整盘或无关个人目录；
- 不识别或输出任意数据行；
- 不迁移基金、用户档案、旧平行持仓、派生持仓、缓存、日志或凭据；
- 不生成迁移目标库，不调用备份恢复 API，不执行真实迁移；
- 不 Ready、不合并、不写 `main`、不 Tag、不 Release；
- 不把 PR #12 的 R4 合成迁移演练当作真实数据工具。

## 验收门

1. 新测试先因模块/CLI 缺失按预期 RED，再编写最小实现转 GREEN。
2. 专项测试必须证明双备份、源不变、只读计数、环境拒绝和隐私输出契约。
3. 关联回归、完整离线后端门、AI 治理、语法和 `git diff --check` 通过。
4. Base-to-Head 安全复审确认没有跟踪 `.db`、sidecar、备份、报告、日志、真实数据、
   密钥、新依赖或 Workflow 放宽。
5. 独立 Draft PR 的固定 Head 完整 GitHub CI 通过；PR 保持 Draft。
6. Work5 的最高 Judge 仅为“云端工具实现通过，Windows 真实盘点待精确授权”。

## 自审

- 设计只回答“有没有需要保留的正式数据”，不提前回答“如何迁移”。
- 工具与 R4 迁移演练分离，且不导入可能触发建表/迁移的项目模块。
- 云端开发、Windows 本机运行、真实数据不上传三个边界没有冲突。
- 所有成功与失败状态、输入、输出、回滚和隐私要求均可由自动测试验证。
