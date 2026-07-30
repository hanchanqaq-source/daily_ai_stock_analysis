# AGENTS.md

本文件用于约束本仓库的默认开发流程，目标是减少重复沟通、减少返工，并让改动和当前项目结构保持一致。

如果本文件与仓库中的脚本、工作流、代码现状不一致，以实际可执行内容为准，并在相关改动中顺手修正文档，避免规则继续漂移。

<!-- BEGIN PP02 PROJECT CONTROL OVERLAY -->
## 0. PP02 Project Control Overlay｜PP02 项目控制补充规则

本节仅补充 PP02 的项目控制规则；删除本标记区块后，其余内容必须与官方
`v3.28.0`（`905c339d80ad2daa6fd2bab3bb10267b23c7ac1c`）中的 `AGENTS.md`
完全一致。

### 0.1 项目身份与角色锁

- 项目：`PP02｜AI 每日股票分析`，仓库：`hanchanqaq-source/daily_ai_stock_analysis`。
- 官方业务基线：`ZhuLinsen/daily_stock_analysis` 的 `v3.28.0`，固定 Commit
  `905c339d80ad2daa6fd2bab3bb10267b23c7ac1c`；项目控制框架版本为
  `P000/P001 V1.5.6`。
- PP02 只包含股票业务。基金业务属于 PP03，不得迁入本仓库。
- 未显式提供 Work 启动标记时，默认 `CHAT_ROLE=PROJECT_CONTROL`；收到
  `CHAT_ROLE=WORK`、`WORK_ID`、`ROLE_LOCK=TRUE` 后，只能执行该 Work，
  不得串用其他聊天、项目或 Work 的状态和授权。

### 0.2 当前状态与交接

- `_ai-dev/PROJECT_STATUS.md` 是唯一当前状态真源。其他台账只承担需求、历史、
  阻塞或导航职责；发生冲突时，先依据可验证证据修正状态，不得直接宣称完成。
- 新聊天从 `_ai-dev/AI_HANDOFF.md` 接手，并依次读取
  `_ai-dev/PROJECT_STATUS.md`、`_ai-dev/WORK_TASK.md` 和相关验收材料。
- 每个 Work 在 `_ai-dev/WORK_TASK.md` 固定目标、范围、非目标、验收和授权，
  在 `_ai-dev/WORK_RETURN.md` 记录真实结果、未验证项、阻塞与 Judge。
- 应明确区分 `未运行`、`未验证`、`部分完成`、`通过` 和 `阻塞`；旧 Work 的
  已完成历史不得因新 Work 启动而回退。

### 0.3 Plan Challenge Gate 与主线范围锁

- 进入 Build 前先搜索已有代码和文档，确认是否已有实现、契约或上游能力。
- 仅在存在产品分歧、范围冲突、不可逆风险或关键证据缺口时提问；一次只问一个
  决策问题，并给出可选择方案、推荐理由和不做事项。
- 已由任务书或总控明确的事项不得重复询问。没有待决产品问题时，Plan Challenge
  可记录为“0 个问题，通过”。
- 同一时间只允许一个 Active Goal。当前 Work 以外的想法写入 Backlog，不自动
  启动后续阶段；R0 不得顺带执行 R1–R7。

### 0.4 用户交互与五项快捷操作

- 默认用户不是程序员：用中文、短句和可验证结果说明进度；普通、低风险、可逆
  的连续步骤可直接执行，不要求用户逐条输入命令。
- 用户说“继续”：在当前授权范围内执行下一安全步骤。
- 用户说“状态”：只读回传当前阶段、证据、阻塞和下一动作。
- 用户说“暂停”或“停止”：立即停止新的工具调用和远程写入。
- 用户说“回滚”：先说明目标、影响和可恢复性；未经精确授权不执行破坏性操作。
- 用户说“总结”：按 Work 回传格式给出完成、验证、风险、Judge 和待授权事项。

### 0.5 授权、清理与能力边界

- Commit、分支、Push、PR、Ready、合并、Release、真实账号、付费服务、真实数据
  和密钥操作分别受精确授权约束；一项授权不得推导出另一项。
- 当前 Work 的授权只覆盖独立分支、正常 Commit、Draft PR、GitHub Actions 检查
  及范围内修复；不覆盖 Ready、合并、改写 `main`、Release 或真实数据处理。
- 不读取、输出或上传 Token、PAT、密码、真实 `.env` 或真实用户数据。
- 工作产物只保留可复核的状态、报告和必要证据；临时缓存、日志、截图与生成物
  不进入仓库。不得删除官方规则、License、来源信息或未经确认的用户改动。
- Superpowers/Skills 只提供执行方法；P000/P001 仍负责项目身份、范围、状态、
  授权与 Judge，工具方法不得替代项目控制结论。
### 0.6 统一执行端自动路由（PP02-AUTO-ROUTER-001 v1.1）

- `AUTO_ROUTING=TRUE`、`USER_SELECTS_TOOL=FALSE`、`INHERITANCE=ALL_WORKS`。
  用户只需提出目标或发送“下一步”“继续”“暂停”“停止”，不负责选择执行工具。
- 总控掌握完整路线、划分大步、决定执行端、审核结果和管理授权门；Work 负责
  当前大步的连续执行、协调、报告和 Judge；Codex 负责代码、终端、调试、构建、
  完整测试、候选恢复及 Windows 实机验收；GitHub App 负责仓库、分支、Commit、
  Draft PR 和 CI，不决定业务范围。
- 需求清点、范围确认、方案、文档、台账、报告、Judge、资料对比和 GitHub 只读
  核验由当前 Work 直接完成；代码或多文件联动自动路由 Codex；仓库写入及 CI
  自动调用 GitHub App。同一任务只能有一个主要执行端，不得重复施工。
- 云端 Codex 负责云端仓库施工和 CI；Windows 本机 Codex 只在正式 Windows
  验收阶段使用，并从固定 PR Head 建立全新隔离目录。云端检查不得冒充 Windows
  实机验收；普通程序开发不使用 CUDA，只有明确 GPU 计算任务才使用。
- 在已批准范围内，普通开发测试、非默认分支 Commit、Draft PR 更新和范围内 CI
  修复不重复询问。Ready、合并、Release、默认分支写入、真实数据、重要本机文件、
  大型依赖、付费服务、范围扩大及其他不可逆操作仍需单独授权。本条在 PP02
  控制层内优先于下方通用“每次 Commit 均确认”的默认规则。
- Work2、Work3 及后续 Work 继承本路由机制，但不自动继承业务范围、仓库/分支/PR、
  真实数据、本机目录、大型依赖、Ready/合并/Release、付费服务或不可逆授权；
  每个 Work 开始时由总控重新明确目标、环境和有效授权。
- 每个大步开始必须显示当前大步、当前 Work、主要执行端、云端/本机、GitHub 使用
  与用户是否需要操作；无需操作时写明“用户操作：无需操作，等待完成报告。”
- 用户发送“暂停”或“停止”后，不再启动新工具调用或远程写入，保留安全完成结果
  并返回恢复点。
- 本规则只调整未完成路线和未来 Work；R0 及其他已验收历史不得回退或重做。
  旧版路由规则保留历史记录，并标记为由 v1.1 替代。

### 0.7 五项核心治理硬门（PP02-GOVERNANCE-GATE-001）

本节只强化现有 PP02 控制层，不改变官方 `v3.28.0` 业务底座，不创建平行状态、
路线、验证系统或辅助主项目。

#### 连续执行与用户规则 Judge 门

- 一次指令默认完成一个完整可验收大段；普通分析、修改、测试、范围内修复、文档
  和状态更新连续执行，不按文件或微步骤反复要求用户发送“下一步”。
- Work 收口时自动同步 `_ai-dev/PROJECT_STATUS.md`、`_ai-dev/AI_HANDOFF.md` 和
  `_ai-dev/WORK_RETURN.md`。交付优先使用完整文件或完整复制块。
- 只有 Publish Changes、Commit、Push、PR、Merge、Release、真实数据迁移、API、
  密钥、付费服务、明显范围变化或无法自行解除的真实 Blocker 才暂停；已有精确
  授权覆盖的普通分支 Commit、Draft PR 更新和范围内 CI 修复不重复确认。
- 每个 Work 开始和 Judge 前必须核对：完整大段、减少重复确认、中文白话、英文
  界面同时标注中文含义、技术操作优先由 Codex 完成、真实进度、完整交付、默认
  用户不是程序员。任一项违反且未纠正时，Judge 不得完全通过。

#### 工具异常恢复门

- `_ai-dev/PROJECT_STATUS.md` 与 `_ai-dev/AI_HANDOFF.md` 必须记录
  `CURRENT_WORK`、`LAST_VALID_COMMIT`、`LAST_SUCCESSFUL_TEST`、
  `ACTIVE_BLOCKER` 和 `NEXT_ACTION`。
- Codex、云端任务、GitHub 或构建异常时，先核对真实 Git 与测试状态，从最后有效
  检查点继续；不得默认重跑整个 Work，也不得把技术恢复转交给用户。
- 无法恢复时必须说明失败位置、已保存状态、恢复条件和备用路线；Blocker 未解除
  前不得进入下一 Work。

#### Work 边界与范围漂移门

- `_ai-dev/WORK_TASK.md` 必须明确 `ACTIVE_GOAL`、允许做、禁止做、验收标准和
  授权门。当前 Work 外的新需求只进入 Backlog，不提前塞入当前 Work。
- 已完成 Work 永久锁定；后续修正必须追加变更原因和影响，不倒改完成历史。
- 辅助工具与测试不得变成新的主项目。检测到范围漂移时设置
  `SCOPE_DRIFT_BLOCKED`，纠正前 Judge 不得通过。

#### 唯一状态真源与证据优先级

- 项目唯一当前状态真源固定为 `_ai-dev/PROJECT_STATUS.md`；禁止创建
  `00_PROJECT_STATUS.md`、版本副本或其他平行状态文件。
- Work 开始、Plan 确认、Build 完成、Test 完成或失败、CI 结果、Blocker 出现或
  解除、Judge、授权门、Work 收口和交接时，都要同步当前状态。
- 状态冲突按以下顺序裁决：真实项目文件 → Git 实际状态 → 实际测试结果 →
  GitHub CI → `_ai-dev/PROJECT_STATUS.md` → 聊天描述。聊天不得覆盖可验证事实。

#### 长任务可见进度与新增 Judge 项

- 较长任务必须显示 `Plan → Build → Test → CI → Judge`，并说明当前正在做什么、
  当前 Blocker 和是否需要用户操作；不得声称在回复结束后仍会后台继续执行。
- Judge 还必须确认：用户未承担不必要的人工中转、用户规则全部执行、工具异常有
  恢复检查点、Work 未串段或跑偏、`PROJECT_STATUS` 与 Git/测试/CI 一致。

<!-- END PP02 PROJECT CONTROL OVERLAY -->
## 1. 硬规则

- 遵循现有目录边界：
  - 后端逻辑优先放在 `src/`、`data_provider/`、`api/`、`bot/`
  - Web 前端改动在 `apps/dsa-web/`
  - 桌面端改动在 `apps/dsa-desktop/`
  - 部署与流水线改动在 `scripts/`、`.github/workflows/`、`docker/`
- 未经明确确认，不执行 `git commit`、`git tag`、`git push`。
- commit message 使用英文，不添加 `Co-Authored-By`。
- 不写死密钥、账号、路径、模型名、端口或环境差异逻辑。
- 优先复用现有模块、配置入口、脚本和测试，不新增平行实现。
- 默认稳定性优先于“顺手优化”；非当前任务直接需要的重构、抽象和基础设施迁移一律克制。
- 新增配置项时，必须同步更新 `.env.example` 和相关文档。
- 涉及用户可见能力、CLI/API 行为、部署方式、通知方式、报告结构变化时，必须同步更新相关文档与 `docs/CHANGELOG.md`。
- 修改报告格式、报告渲染效果或 Web UI 界面时，PR 描述必须附受影响报告 / 页面截图；涉及前后差异时优先附前后对比，无法截图时说明原因与替代可视证据。
- Issue / PR 过程截图、审查截图、一次性验收截图和临时可视证据不得作为仓库文件合入；应放在 PR 描述、PR 评论、GitHub 附件、Actions artifact 或外部可访问证据链接中。产品长期文档确需保留的示意图除外，但文件名和文档语义必须脱离具体 issue / PR 编号。
- `docs/CHANGELOG.md` 的 `[Unreleased]` 段使用**扁平格式**：每条独立一行，格式为 `- [类型] 描述`，类型取值：`新功能`/`改进`/`修复`/`文档`/`测试`/`chore`；**禁止在 `[Unreleased]` 内新增 `### 类目标题`**，以减少并发 PR 的 merge 冲突。发版时由 maintainer 汇总整理成带标题的正式格式。
- `README.md` 只用于项目定位、核心能力总览、快速开始、主要入口、赞助/合作等首页级信息；非必要不更新 README，避免持续膨胀。
- 更细的模块行为、页面交互、专题配置、排障说明、字段契约、实现语义和边界条件，优先更新对应 `docs/*.md` 或专题文档，不写入 README。
- 变更中英双语文档之一时，需评估另一份是否需要同步；若未同步，交付说明里要写明原因。
- 注释、docstring、日志文案以清晰准确为准，不强制要求英文，但应与文件语境保持一致。

## 1.1 PR 标题规范（非阻断建议）

- 推荐使用 `<类型>: <修改内容>` 作为 PR 标题，例如 `fix: 修复大盘分析历史记录丢失`，优先类型为 `fix`/`feat`/`refactor`/`docs`/`chore`/`test`/`ci`。
- 标题应描述实际变更内容，建议不添加 `[codex]`、`codex`、`autocode`、`copilot` 或其他工具/agent 来源前缀。
- 该规范仅用于协作可读性与一致性提示，不应单独作为 review process blocker。

## 1.2 贡献质量底线

- 本仓库不接受以堆叠代码量、扩大 diff 面、补丁式响应 review 来替代真实设计收敛的 PR。
- 贡献质量以是否解决明确问题、是否最小化影响面、是否保持现有契约一致、是否覆盖真实风险路径为准；不以新增行数、文件数量、功能宣传或“看起来完整”为准。
- 请不要把本仓库当作低成本试验场、简历展示场或 contribution farming 场所。任何 PR 都必须证明作者理解当前系统契约，并完成基本自审、集成和验证。
- 使用 AI 辅助开发本身不是问题；问题是提交 AI 生成后未经人工语义审查、未验证、未收敛的代码。此类 PR 会按低质量提交处理。
- review 反馈后，不接受只在被指出的位置追加局部 patch。作者必须重新检查同一业务语义涉及的所有入口、配置、测试、文档、workflow 和用户可见路径。
- 如果一个 PR 在多轮 review 后仍持续出现同类契约漂移、重复 fallback、测试绕过真实风险层、PR body 与实际 diff 不一致等问题，维护者可以要求关闭重做，而不是继续逐点 review。

## 2. AI 协作资产治理

- `AGENTS.md` 是仓库内 AI 协作规则的唯一真源。
- `CLAUDE.md` 必须是指向 `AGENTS.md` 的软链接，用于兼容 Claude 生态。
- `.github/copilot-instructions.md` 与 `.github/instructions/*.instructions.md` 是 GitHub Copilot / Coding Agent 的镜像或分层补充；若与本文件冲突，以 `AGENTS.md` 为准。
- 仓库协作 skill 存放在 `.claude/skills/`，分析产物存放在 `.claude/reviews/`；前者可以入库，后者默认视为本地产物。
- 根目录 `SKILL.md` 与 `docs/openclaw-skill-integration.md` 属于产品或外部集成说明，不是仓库协作规则真源。
- 若未来新增 `.agents/skills/` 或其他 agent 专用目录，必须先明确单一真源，再通过脚本或镜像同步；禁止手工长期维护多份同义内容。
- 修改 AI 协作治理资产时，执行：

```bash
python scripts/check_ai_assets.py
```

## 3. 仓库速览

- 项目定位：股票智能分析系统，覆盖 A 股、港股、美股。
- 主流程：抓取数据 -> 技术分析/新闻检索 -> LLM 分析 -> 生成报告 -> 通知推送。
- 关键入口：
  - `main.py`：分析任务主入口
  - `server.py`：FastAPI 服务入口
  - `apps/dsa-web/`：Web 前端
  - `apps/dsa-desktop/`：Electron 桌面端
  - `.github/workflows/`：CI、发布、每日任务
- 核心职责：
  - `src/core/`：主流程编排
  - `src/services/`：业务服务层
  - `src/repositories/`：数据访问层
  - `src/reports/`：报告生成
  - `src/schemas/`：Schema / 数据结构
  - `data_provider/`：多数据源适配与 fallback
  - `api/`：FastAPI API
  - `bot/`：机器人接入
  - `scripts/`：本地脚本
  - `.github/scripts/`：GitHub 自动化脚本
  - `tests/`：pytest 测试
  - `docs/`：文档与说明

## 4. 常用命令

### 运行应用

```bash
python main.py
python main.py --debug
python main.py --dry-run
python main.py --stocks 600519,hk00700,AAPL
python main.py --market-review
python main.py --schedule
python main.py --serve
python main.py --serve-only
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### 后端验证

```bash
pip install -r requirements.txt
pip install flake8 pytest
./scripts/ci_gate.sh
python -m pytest -m "not network"
python -m py_compile <changed_python_files>
```

### Web / Desktop

```bash
cd apps/dsa-web
npm ci
npm run lint
npm run build

cd ../dsa-desktop
npm install
npm run build
```

### PR / CI 证据

```bash
gh pr view <pr_number>
gh pr checks <pr_number>
gh run view <run_id> --log-failed
```

## 5. 默认工作流

1. 先判断任务类型：`fix / feat / refactor / docs / chore / test / review`
2. 先读现有实现、配置、测试、脚本、工作流和文档，再动手修改。
3. 识别改动边界：后端 / API / Web / Desktop / Workflow / Docs / AI 协作资产。
4. 先判断是否命中高风险区域：配置语义、API / Schema、数据源 fallback、报告结构、认证、调度、发布流程、桌面端启动链路。
5. 只做和当前任务直接相关的最小改动，不顺手夹带无关重构。
6. 如果发现文档、脚本、工作流描述不一致，优先信任实际代码与工作流，再决定是否顺手修正文档。
7. 改完后按下面的验证矩阵执行检查。
8. 最终交付默认要说明：
   - 改了什么
   - 为什么这么改
   - 验证情况
   - 未验证项
   - 风险点
   - 回滚方式

## 6. 验证矩阵

### CI 覆盖原则

当前仓库 CI 主要包含：

| 检查项 | 来源 | 说明 | 是否阻断 |
| --- | --- | --- | --- |
| `ai-governance` | `.github/workflows/ci.yml` | 校验 `AGENTS.md` / `CLAUDE.md` / `.github` 指令 / `.claude/skills` 关系 | 是 |
| `backend-gate` | `.github/workflows/ci.yml` | 执行 `./scripts/ci_gate.sh` | 是 |
| `docker-build` | `.github/workflows/ci.yml` | Docker 构建与关键模块导入 smoke | 是 |
| `web-gate` | `.github/workflows/ci.yml` | 前端改动时执行 `npm run lint` + `npm run build` | 是（触发时） |
| `network-smoke` | `.github/workflows/network-smoke.yml` | `pytest -m network` + `scripts/test.sh quick` | 否，观测项 |
| `pr-review` | `.github/workflows/pr-review.yml` | PR 静态检查 + AI 审查 + 自动标签 | 否，辅助项 |

若 PR 上已有对应 CI 结果，可直接引用 CI 结论；若 CI 未覆盖改动面，或本地与 CI 环境差异较大，需要补充说明本地验证与缺口。

### 按改动面执行

- Python 后端改动：
  - 适用范围：`main.py`、`src/`、`data_provider/`、`api/`、`bot/`、`tests/`
  - 优先执行：`./scripts/ci_gate.sh`
  - 最低要求：`python -m py_compile <changed_python_files>`
  - 若影响 API、任务编排、报告生成、通知发送、数据源 fallback、认证、调度，交付说明中要写明是否覆盖了对应路径。

- Web 前端改动：
  - 适用范围：`apps/dsa-web/`
  - 默认执行：`cd apps/dsa-web && npm ci && npm run lint && npm run build`
  - 若涉及 API 联调、路由、状态管理、Markdown/图表渲染或认证状态，交付说明中要明确说明联动面和未覆盖风险。

- 桌面端改动：
  - 适用范围：`apps/dsa-desktop/`、`scripts/run-desktop.ps1`、`scripts/build-desktop*.ps1`、`scripts/build-*.sh`、`docs/desktop-package.md`
  - 默认执行：先构建 Web，再构建桌面端
  - 如受平台限制未能完整验证，需要明确说明是否验证了 Web 构建产物、Electron 构建以及 Release 工作流影响。

- API / Schema / 认证联动改动：
  - 适用范围：`api/**`、`src/schemas/**`、`src/services/**`、`apps/dsa-web/**`、`apps/dsa-desktop/**`
  - 至少覆盖对应后端验证 + 受影响客户端构建验证。
  - 若涉及登录、Cookie、会话、轮询状态、字段增删或枚举变化，必须明确写出兼容性影响。

- 文档与治理文件改动：
  - 适用范围：`README.md`、`docs/**`、`AGENTS.md`、`.github/copilot-instructions.md`、`.github/instructions/**`、`.claude/skills/**`
  - 不强制代码测试。
  - 需确认命令、配置项、文件名、工作流名称与实际仓库一致。
  - 改动 AI 协作治理资产时，执行 `python scripts/check_ai_assets.py`。

- 工作流 / 脚本 / Docker 改动：
  - 适用范围：`.github/**`、`scripts/**`、`docker/**`
  - 运行最接近改动面的本地验证。
  - 交付时说明影响了哪条流水线、发布路径或部署路径。
  - 若未执行 Docker / GitHub Actions 相关验证，明确说明原因与潜在风险。

- 网络或三方依赖相关改动：
  - 先跑离线或确定性检查。
  - 优先确认 timeout、retry、fallback、异常文案、降级路径是否仍然成立。
  - 若未执行在线验证，必须明确写出原因。

## 7. 稳定性护栏

- 配置与运行入口：
  - 修改 `.env` 语义、默认值、CLI 参数、服务启动方式、调度语义时，要同时评估本地运行、Docker、GitHub Actions、API、Web、Desktop 的影响。
  - 新配置优先做到“不配置也可运行，配置后增强能力”，避免叠加开关和互斥模式。

- 数据源与 fallback：
  - 修改 `data_provider/` 时，要关注数据源优先级、失败降级、字段标准化、缓存与超时策略。
  - 单一数据源失败不应拖垮整个分析流程，除非需求明确要求 fail-fast。

- API / Web / Desktop 兼容：
  - 改 API / Schema / 认证 / 报告载荷时，要同时检查后端、Web、Desktop 的兼容性。
  - 默认优先追加字段、保留旧字段或提供兼容层，避免无提示破坏现有客户端。

- 报告 / Prompt / 通知：
  - 修改报告结构、Prompt、提取器、通知模板、机器人链路时，要检查上游输入与下游消费方是否仍兼容。
  - 单一通知渠道失败不应拖垮整个分析主流程，除非需求明确要求 fail-fast。
  - 修改 `src/services/image_stock_extractor.py` 中 `EXTRACT_PROMPT` 时，要在 PR 描述中附完整最新 prompt。

- 工作流 / 发布 / 打包：
  - 修改自动 tag、Release、Docker 发布、日常分析或桌面端打包流程时，要评估触发条件、产物路径、权限边界和回滚方式。
  - 自动 tag 默认保持 opt-in：只有 commit title 含 `#patch`、`#minor`、`#major` 才触发版本号更新，除非需求明确要求改变发布策略。

## 8. Issue / PR / Skill 工作流

- 仓库内已有以下 skill，可优先复用：
  - `.claude/skills/analyze-issue/SKILL.md`
  - `.claude/skills/analyze-pr/SKILL.md`
  - `.claude/skills/fix-issue/SKILL.md`
- 如果任务明确是 issue 分析、PR 审查、issue 修复，优先按对应 skill 执行，并将产物保存到 `.claude/reviews/`。
- skill 中的命令、模板、验证顺序和交付结构必须与 `AGENTS.md` 保持一致。
- 每次进行 PR 创建 / 更新、PR 审查或 issue 分析前，必须先同步最新代码基线：先检查工作区状态并执行 `git fetch --all --prune`；若工作区干净且当前分支可 fast-forward，则执行 `git pull --ff-only`。如存在本地改动、冲突状态、未跟踪风险文件或无法 fast-forward，不得强行切分支、stash、reset 或覆盖本地状态；PR 审查 / issue 分析可改用已 fetch 的远端 refs/PR head 做分析，并在分析文档中明确记录未更新本地工作树的原因、当前本地 HEAD 与使用的远端基线；PR 创建 / 更新应先说明当前分支与目标基线差异，必要时请求用户确认 rebase、merge 或继续基于当前分支推进。
- skill 默认优先读取 CI / 工作流证据，再决定是否补本地验证。
- 除上述 PR 创建 / 更新、PR 审查 / issue 分析的安全 fast-forward 同步外，skill 不得默认执行 `git pull`、`git push`、`git tag`、`gh pr create` 等会改变远端或当前分支状态的操作；这些操作必须要求用户确认。
- PR 审查默认顺序：
  1. 必要性
  2. 关联性
  3. 标题建议（`<类型>: <修改内容>`，且不含工具/agent 前缀；不作为硬性阻断项）
  4. 描述完整性（对照 `.github/PULL_REQUEST_TEMPLATE.md`）
  5. 验证证据
  6. 实现正确性
  7. 合入判定
- 对 `fix` 类 PR，必须说明：原问题、根因、修复点、回归风险。
- 合入阻断条件：
  - 正确性或安全性问题
  - 阻断型 CI 未通过
  - PR 描述与实际改动内容实质性矛盾
  - 缺少回滚方案
  - 反复出现未收敛的契约漂移、补丁堆叠或验证证据失真

## 8.1 Review 反馈处理与补丁堆叠禁止

当你处理 review 反馈时，禁止只在 reviewer 点名的位置追加局部 patch 后声称“已全部修复”。你必须先重新理解 reviewer 指出的业务契约，再检查同一语义涉及的所有入口、配置、测试、文档、workflow 和用户可见路径。

收到 review 反馈后，必须按以下顺序处理：

1. 逐条列出 reviewer 指出的原问题。
2. 说明根因，不能只描述“改了哪几行”。
3. 找出同一语义影响的所有相关路径，例如 runtime、API/Web、CLI、diagnostics、workflow、docs、tests。
4. 修复完整契约，而不是只修复当前失败测试或当前评论行。
5. 补充能覆盖 reviewer 反例的回归测试、最终入口验证，或明确说明无法验证的原因。
6. 同步更新 PR body，保证 scope、验证结果、兼容性、风险和回滚方案与当前 head 一致。

如果你无法完成上述收敛，不要继续堆叠补丁，不要声称 ready for merge。应主动说明当前 PR 需要拆分、关闭重做，或请求维护者确认新的最小范围。

以下行为会被视为低质量 PR：

- 用 broad fallback、静默降级、`return False/None/[]` 掩盖不清晰的契约。
- 测试 mock 掉真实风险层，只证明局部实现通过。
- CI 通过后声称问题已关闭，但没有覆盖 reviewer 指出的反例。
- PR body 与实际 diff、验证结果或兼容风险不一致。
- review 后继续追加零散 patch，而不是重新收敛完整语义。
- 同一业务语义在 runtime、Web/API、docs、workflow、tests 中表现不一致。

CI 通过只能说明自动检查通过，不能替代人工语义收敛，也不能单独证明 reviewer 指出的反例已经关闭。

## 9. 交付与发布

- 默认交付结构：
  - `改了什么`
  - `为什么这么改`
  - `验证情况`
  - `未验证项`
  - `风险点`
  - `回滚方式`
- 如果是 `docs` 任务，可直接写：`Docs only, tests not run`，但仍需说明是否核对了命令和文件名。
- 自动 tag 默认不触发，只有 commit title 包含 `#patch`、`#minor`、`#major` 才会触发版本号更新。
- 手动打 tag 必须使用 annotated tag。
- 用户可见变更优先通过 PR 合入，并补齐 label 与验证说明。
