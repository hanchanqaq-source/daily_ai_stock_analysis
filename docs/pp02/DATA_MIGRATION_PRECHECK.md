# PP02 数据迁移预检

## R0 边界

本文件只识别官方仓库声明的数据位置、Schema、迁移机制和兼容风险。R0 未读取、
复制或迁移任何真实用户数据，未加载真实 `.env`，未连接真实行情、通知或付费账号。

## 官方声明

| 项目 | 官方证据 | 预检结论 |
| --- | --- | --- |
| 默认数据库 | `src/config.py` 的 `DATABASE_PATH=./data/stock_analysis.db` | 路径可配置；不得把本机文件带入候选 |
| 存储与 Schema | `src/storage.py` | SQLAlchemy 模型、建表与内置 Schema 迁移在官方代码中 |
| Repository 层 | `src/repositories/` | 业务访问应通过现有 Repository，不新增平行数据库层 |
| SQLite 并发 | `SQLITE_WAL_ENABLED`、busy timeout、写入重试 | 迁移演练需保留官方并发参数 |
| 导入能力 | `src/services/import_parser.py`、`portfolio_import_service.py` | 仅说明官方能力存在，不证明旧数据格式兼容 |
| 锁文件 | `src/core/market_review_lock.py` | `market_review.lock` 是运行状态，不属于迁移数据 |

## 兼容风险

- 旧仓库 Schema 版本、表名、索引、唯一约束和迁移记录尚未用脱敏副本比对。
- 用户、股票自选、持仓、报告、调度和通知配置可能具有不同外键或业务语义。
- 基金相关表属于 PP03 边界，不能原样迁入 PP02。
- SQLite WAL/SHM、锁文件、缓存、日志、报告图片和临时导出物不能当作主数据复制。
- 直接打开真实数据库可能触发官方自动迁移，必须在获得专门授权和备份后进行。

## 后续脱敏演练门

R4 只允许空库、fixture 或经用户明确授权的脱敏副本：

1. 记录副本哈希、Schema 和迁移前备份。
2. 在隔离环境运行只读 Schema 比较。
3. 为每张保留表定义字段映射、丢弃项和回滚点。
4. 在复制品上执行迁移并验证行数、约束和抽样结果。
5. 输出可重复脚本与失败恢复步骤。

真实数据迁移属于 R6，必须单独授权；本次结论为 `NOT_PERFORMED`。
