# PP02 安装、启动、验证与恢复

本文件记录 PP02 的最小操作入口。更完整的官方说明继续使用 [`full-guide.md`](full-guide.md)、[`DEPLOY.md`](DEPLOY.md) 和 [`FAQ.md`](FAQ.md)，不在这里复制第二套长教程。

## 0. 当前 v3.28.0 R0 操作入口

当前唯一状态见 [`../_ai-dev/PROJECT_STATUS.md`](../_ai-dev/PROJECT_STATUS.md)，正式
基线记录见 [`pp02/UPSTREAM_BASELINE.md`](pp02/UPSTREAM_BASELINE.md)。

```bash
git rev-parse HEAD
git diff --check
python scripts/check_ai_assets.py
```

R0 候选必须以官方 `v3.28.0` 固定 Commit
`905c339d80ad2daa6fd2bab3bb10267b23c7ac1c` 为完整业务树，并只增加批准的 PP02
控制层和 CI 最小只读权限。不得加载真实 `.env`、真实账号、真实数据库、通知或
付费服务。先完成最低完整性硬门并持久化候选，再执行完整 Python、Web、Desktop、
AI 治理和差异验证；Draft PR CI 未触发前必须明确写“未触发”。

云端结果不能替代 Windows 实机结果；Windows 当前状态为
`NOT_VERIFIED_IN_CLOUD`。本 Work 不执行 Ready、合并、修改 `main` 或 Release。

## 1. 身份核对（Work 1 历史）

开始操作前确认：

```bash
git remote -v
git rev-parse HEAD
git status -sb
```

预期仓库是 `hanchanqaq-source/daily_ai_stock_analysis`，并保留名为 `upstream` 的官方来源 `ZhuLinsen/daily_stock_analysis`。若指向旧混合仓库，立即停止写入。

## 2. 原始基线核对（Work 1 历史）

```bash
git fetch upstream tag v3.27.0
git rev-parse 'v3.27.0^{}'
git merge-base --is-ancestor b36c721415560e48115ad4444d5af2125fc53f5c HEAD
```

Tag 名以上游 `ZhuLinsen/daily_stock_analysis` 为真源。第二条命令必须输出 `b36c721415560e48115ad4444d5af2125fc53f5c`；第三条必须成功。PP02 管理层提交位于该基线之后，目标仓库无需复制同名 Tag。

## 3. 环境与依赖

- Python：官方部署文档要求 3.10+
- Web：`apps/dsa-web/package.json` 要求 Node `>=20.19.0 <27`、npm `>=10`

在独立虚拟环境中安装后端依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install flake8 pytest
```

Windows PowerShell 激活命令：

```powershell
.\.venv\Scripts\Activate.ps1
```

不得读取或提交真实 `.env`。需要配置时只从 `.env.example` 复制到本机，并由用户在本机填写。

## 4. 确定性验证

AI 协作资产：

```bash
python scripts/check_ai_assets.py
```

后端最小语法检查：

```bash
./scripts/ci_gate.sh syntax
```

官方离线门禁：

```bash
./scripts/ci_gate.sh
```

Web：

```bash
cd apps/dsa-web
npm ci
npm run lint
npm test -- src/pages/__tests__/PortfolioPage.test.tsx
npm run build
```

## 5. 快捷持仓验收边界

- 必须先调用预览，再由用户明确确认；预览阶段不得新增任何账本事件。
- 确认前若当前持仓已变化，旧预览必须返回冲突并要求重新预览。
- 成功确认只新增一条带唯一标识的官方交易事件；不要为同一买卖再写资金流水。
- 现金、成本和持仓结果必须由官方事件重放得出；禁止直接改
  `portfolio_positions`、lots 或快照。
- 空库/fixture 可在 R3 使用；真实用户持仓继续等待 R6 精确授权。

## 5.1 股票备份与恢复验收边界

- 在持仓页点击导出后才生成 `pp02-stock-portfolio-backup.json`；不得把备份文件、
  真实数据库或截图提交到 GitHub。
- 恢复必须先选择 JSON 并查看替换预览；只有用户再次明确确认后才写库。
- 预览令牌绑定备份内容和当前账本；预览后任一方变化都必须重新预览。
- 恢复采用整套 `replace`，不是静默合并；写入在官方组合写锁和单事务内完成，
  失败时原账本不变。
- 只恢复账户、交易、资金和公司行动；`portfolio_positions`、lots 和快照会被
  清除并从官方事件重新计算。
- API 验收入口：
  `GET /api/v1/portfolio/backup/export`、
  `POST /api/v1/portfolio/backup/preview`、
  `POST /api/v1/portfolio/backup/restore`。
- R3 只使用空库或 fixture；真实备份导出、覆盖和迁移仍等待 R6 精确授权。

## 5.2 手动周期报告验收边界

- Web `/period-report` 初次打开不得生成报告；选择周期并点击后才调用
  `POST /api/v1/period-report/generate`。
- 七个周期入口为本周至今、上一周、下周展望、5周、10周、1个月和2个月；
  日期边界均为闭区间。
- 股票、ETF 与市场复盘必须分区展示；事实只来自正式分析历史和市场复盘历史。
- 下周展望只使用截至日向前 14 个自然日内的合格记录；无合格记录时必须显示
  “近期有效数据不足，暂不能形成下周展望。”
- 展望必须展示方向、置信度、依据、风险、失效条件、数据截至时间和来源数量，
  并显示“下周展望基于已有历史分析形成，仅供参考，不代表确定结果。”
- 快照写入现有 `AnalysisHistory`，`report_type=period_outlook`；来源记录 ID
  必须保留，且快照不得进入普通股票历史聚合或回测。
- 验收期间不得连接模型、行情、新闻、通知或调度入口；不得新增 cron、后台任务、
  自动发送或第二套报告事实表。

## 6. 本地启动

仅启动 API 与 Web 服务、由用户手动触发分析：

```bash
python main.py --serve-only
```

默认只在本机验证，通过 `http://127.0.0.1:8000` 打开。Work 1 不开放公网，不连接真实付费服务、通知或自动交易。

## 7. Work 1 差异验收（历史）

```bash
git diff --name-status b36c721415560e48115ad4444d5af2125fc53f5c..HEAD
git diff --stat b36c721415560e48115ad4444d5af2125fc53f5c..HEAD
```

Work 1 只允许出现获批的项目管理和文档差异；若出现 `src/`、`api/`、`data_provider/`、`apps/`、`bot/` 等业务代码变化，Judge 必须不通过。

## 8. 安全恢复

- 先记录当前分支、HEAD、状态和错误信息，再决定恢复方法。
- 同步核对 `_ai-dev/PROJECT_STATUS.md` 与 `_ai-dev/AI_HANDOFF.md` 中的
  `CURRENT_WORK`、`LAST_VALID_COMMIT`、`LAST_SUCCESSFUL_TEST`、
  `ACTIVE_BLOCKER` 和 `NEXT_ACTION`。
- 恢复判断顺序固定为：真实项目文件 → Git 实际状态 → 实际测试结果 →
  GitHub CI → `_ai-dev/PROJECT_STATUS.md` → 聊天描述。
- 从 `LAST_VALID_COMMIT` 继续，只重跑受影响的验证；不得因工具异常默认重跑整个
  Work，也不得让用户承担命令、分支或构建恢复。
- 无法恢复时记录失败位置、已保存状态、恢复条件和备用路线；Blocker 未解除或
  `SCOPE_DRIFT_BLOCKED` 未清除前，不进入下一 Work。
- 不使用 `git reset --hard`、整目录清空或覆盖真实数据。
- 未提交改动与用户文件不明确时暂停并询问。
- 远端底座导入失败时保留失败证据，重新从已核验 Tag 建立，不用文件快照冒充历史。

## 9. 云端受限环境注意事项

- 若工作区不允许写入用户级缓存，把 pip/npm 缓存放到任务专用临时目录，不修改官方依赖清单。当前 npm 需使用大写 `NPM_CONFIG_CACHE`；只运行 Node 单测且 Electron 下载目录不可写时可使用 `npm ci --ignore-scripts`，但该方式不能作为 Electron 打包通过的证据。
- 若工作区会改写 Git 中的符号链接，应从准确提交树导出到临时目录后执行治理和 Web 构建检查，不能把工作区伪差异提交到仓库。
- 通过 Git Data API 发布管理文件时，必须逐个比较本地 `git hash-object` 与远端 Blob SHA。大型未改文件不得经过受输出上限影响的文本转发；应直接复用官方基线 Blob，避免截断。
- 若 Git Data 已创建 Commit 但引用接口无法移动既存 Codex 分支，不得强推或新建替代 PR；改用 Contents API 在同一分支连续提交，并在每一步核对返回 Blob SHA。超长文件仍须从远端完整原文在内存中变换。
- LiteLLM 无法在线刷新模型价格表时会回退到随包本地副本；这不阻塞无密钥的 Work 1 启动检查，但需要保留告警记录。
- 未配置 `STOCK_LIST`、模型密钥和通知渠道时，只验证服务启动、健康接口与静态 Web 页面；不得声称已完成真实股票分析验收。

## R3.6 便携更新排障

便携更新失败时不要删除 `.pp02-update-backup`。先保留更新计划、恢复元数据和本地日志，再确认当前根目录的 `.env`、SQLite DB/WAL/SHM 以及 `pp02-portable-release.json`。云端 CI 只能验证 Windows 候选构建，R5 必须在固定 PR Head 的全新 Windows 隔离目录执行。
