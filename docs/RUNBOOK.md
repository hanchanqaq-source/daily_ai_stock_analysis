# PP02 安装、启动、验证与恢复

本文件记录 PP02 的最小操作入口。更完整的官方说明继续使用 [`full-guide.md`](full-guide.md)、[`DEPLOY.md`](DEPLOY.md) 和 [`FAQ.md`](FAQ.md)，不在这里复制第二套长教程。

## 1. 身份核对

开始操作前确认：

```bash
git remote -v
git rev-parse HEAD
git status -sb
```

预期仓库是 `hanchanqaq-source/daily_ai_stock_analysis`，并保留名为 `upstream` 的官方来源 `ZhuLinsen/daily_stock_analysis`。若指向旧混合仓库，立即停止写入。

## 2. 原始基线核对

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
npm run build
```

## 5. 本地启动

仅启动 API 与 Web 服务、由用户手动触发分析：

```bash
python main.py --serve-only
```

默认只在本机验证，通过 `http://127.0.0.1:8000` 打开。Work 1 不开放公网，不连接真实付费服务、通知或自动交易。

## 6. Work 1 差异验收

```bash
git diff --name-status b36c721415560e48115ad4444d5af2125fc53f5c..HEAD
git diff --stat b36c721415560e48115ad4444d5af2125fc53f5c..HEAD
```

Work 1 只允许出现获批的项目管理和文档差异；若出现 `src/`、`api/`、`data_provider/`、`apps/`、`bot/` 等业务代码变化，Judge 必须不通过。

## 7. 安全恢复

- 先记录当前分支、HEAD、状态和错误信息，再决定恢复方法。
- 不使用 `git reset --hard`、整目录清空或覆盖真实数据。
- 未提交改动与用户文件不明确时暂停并询问。
- 远端底座导入失败时保留失败证据，重新从已核验 Tag 建立，不用文件快照冒充历史。

## 8. 云端受限环境注意事项

- 若工作区不允许写入用户级缓存，把 pip/npm 缓存放到任务专用临时目录，不修改官方依赖清单。
- 若工作区会改写 Git 中的符号链接，应从准确提交树导出到临时目录后执行治理和 Web 构建检查，不能把工作区伪差异提交到仓库。
- 通过 Git Data API 发布管理文件时，必须逐个比较本地 `git hash-object` 与远端 Blob SHA。大型未改文件不得经过受输出上限影响的文本转发；应直接复用官方基线 Blob，避免截断。
- LiteLLM 无法在线刷新模型价格表时会回退到随包本地副本；这不阻塞无密钥的 Work 1 启动检查，但需要保留告警记录。
- 未配置 `STOCK_LIST`、模型密钥和通知渠道时，只验证服务启动、健康接口与静态 Web 页面；不得声称已完成真实股票分析验收。
