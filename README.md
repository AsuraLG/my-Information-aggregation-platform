# 个人信息聚合平台

自动采集多个信息源（RSS / GitHub Trending），通过 AI 生成每日摘要，并发布到 GitHub Pages 静态站点。

## 功能

- **多源采集**：RSS 订阅 + GitHub Trending，按 cron 表达式为每个信息源独立定时运行
- **AI 摘要**：支持 Anthropic / OpenAI 兼容 API，按标签聚合生成摘要，并额外生成当日综合 digest，支持 system/user 双提示词
- **静态发布**：Jinja2 渲染 HTML，通过 `ghp-import` 推送到 `gh-pages` 分支
- **配置驱动**：信息源、标签、prompt、调度、AI 参数均通过 YAML 配置，代码不硬编码业务参数
- **多种调度方式**：支持手动 CLI、APScheduler 长期运行、GitHub Actions 三种使用模式

## 项目结构

```
├── .github/workflows/     # GitHub Actions 工作流
│   ├── collect.yml            # 采集工作流
│   ├── analyze.yml            # 分析工作流
│   └── publish.yml            # 发布工作流
├── collector/          # 采集层：RSS、GitHub Trending
├── storage/            # 存储层：JSON 原子写入，统一数据模型
├── analyzer/           # 分析层：AI 摘要生成
├── publisher/          # 发布层：HTML 渲染 + GitHub Pages 部署
├── scheduler/          # 调度层：APScheduler 定时任务
├── config/             # 配置文件
│   ├── sources.yaml        # 信息源定义
│   ├── tags.yaml           # 标签定义（id + 中文描述）
│   ├── prompts.yaml        # AI prompt 模板
│   ├── schedule.yaml       # 分析/发布调度
│   ├── settings.yaml       # 全局设置（本地，不提交）
│   └── settings.yaml.example  # 配置模板
└── main.py             # CLI 入口
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置

```bash
cp config/settings.yaml.example config/settings.yaml
```

编辑 `config/settings.yaml`，填写 AI 配置。也可以通过环境变量（优先级低于配置文件）：

```bash
export INFO_AGG_AI_PROVIDER_TYPE="anthropic"   # 必填，可选 anthropic / openai
export INFO_AGG_AI_MODEL="claude-3-5-haiku-20241022"
export INFO_AGG_AI_API_KEY="sk-..."
export INFO_AGG_AI_BASE_URL="https://..."     # 可选，自定义端点/代理
export INFO_AGG_AI_MAX_TOKENS="1024"          # 可选
```

### 3. 手动运行

```bash
# 采集所有信息源
uv run python main.py collect

# 采集指定信息源
uv run python main.py collect --source github_trending_python

# 分析（默认昨天，按 schedule.yaml 中的 timezone 解释）
uv run python main.py analyze

# 分析指定日期
uv run python main.py analyze --date 2026-03-20

# 渲染并发布到 GitHub Pages
uv run python main.py publish

# 验证配置是否正确
uv run python main.py
```

### 4. 启动调度器（长期运行）

```bash
uv run python main.py run
```

### 5. GitHub Actions 调度（推荐用于 GitHub 托管）

项目提供三个 GitHub Actions 工作流，可在 GitHub 上实现全自动调度，无需本地服务器：

| 工作流 | 触发方式 | 说明 |
|--------|---------|------|
| `collect.yml` | 定时 + 手动 | 采集所有信息源，上传数据为 Artifact |
| `analyze.yml` | 定时 + 手动 | 下载采集数据，AI 分析生成摘要 |
| `publish.yml` | Analyze 成功后自动触发 + 手动 | 下载分析数据，部署到 GitHub Pages |

**使用前准备**：在仓库 Settings → Secrets and variables → Actions 中添加以下 Secrets：

- `INFO_AGG_AI_PROVIDER_TYPE` — AI 提供商（`anthropic` / `openai`）
- `INFO_AGG_AI_MODEL` — 模型名称
- `INFO_AGG_AI_API_KEY` — API 密钥
- `INFO_AGG_AI_BASE_URL` — API 端点（可选）

**手动触发**：在仓库 Actions 页面选择对应工作流，点击 "Run workflow" 即可。

> **注意**：GitHub Actions 模式和 APScheduler 模式（`main.py run`）的调度是独立的。
> Actions 的 cron 在 `.github/workflows/*.yml` 中配置（UTC 时区），APScheduler 的 cron 在 `config/sources.yaml` 和 `config/schedule.yaml` 中配置（按 `timezone` 字段解释）。

## 配置说明

### AI 配置（`config/settings.yaml`）

`ai.provider_type` 为必填项，可选：`anthropic`、`openai`。配置优先级为：`settings.yaml` > `INFO_AGG_AI_*` 环境变量。

```yaml
ai:
  provider_type: "anthropic"
  model: "claude-3-5-haiku-20241022"
  max_tokens: 1024
  api_key: "sk-..."
  base_url: "https://..."  # 可选
```

### 信息源（`config/sources.yaml`）

`sources.yaml` 中每个信息源的 `schedule` 都会注册成一个独立采集 job，只采集该信息源；不同信息源的采集任务与分析/发布任务使用独立执行器，可并行运行。**注意**：`schedule` 字段仅在 APScheduler 模式（`main.py run`）下生效，GitHub Actions 模式下的调度时间在 `.github/workflows/*.yml` 中独立配置。

```yaml
sources:
  - id: "github_trending_python"
    desc: "GitHub Trending · Python"   # 页面展示名称
    type: github_trending
    language: "python"
    period: "daily"
    tags: ["AI", "python", "opensource"]
    schedule: "0 10 * * *"   # cron，按 config/schedule.yaml 中的 timezone 解释（默认 Asia/Shanghai）
```

支持的 `type`：`rss`、`github_trending`

### 调度（`config/schedule.yaml`）

```yaml
timezone: "Asia/Shanghai"
analysis_schedule: "0 9 * * *"
```

- `timezone` 控制 scheduler cron 的解释时区，以及未显式传入 `--date` 时 analyze/publish 默认“昨天”的日期语义。
- `analysis_schedule` 继续保持配置驱动，仅定义分析/发布任务 cron。

### 标签（`config/tags.yaml`）

```yaml
tags:
  - id: "AI"
    desc: "人工智能"    # 页面展示名称
```

`sources.yaml` 中的 `tags` 字段引用 `id`，页面渲染时自动替换为 `desc`。

### AI Prompt（`config/prompts.yaml`）

支持按标签配置不同 prompt，未匹配的标签使用 `default`；此外还支持单独的 `digest` 模板用于生成当日综合摘要：

```yaml
default:
  system: "你是一个信息摘要助手..."
  user: "以下是 {date} 标签「{tag}」下的原始信息，共覆盖 {source_count} 个来源、{item_count} 条原始信息。\n来源包括：{source_ids_text}\n\n{items_text}"

digest:
  system: "你是一个信息聚合助手..."
  user: "以下是 {date} 的各标签整合摘要：\n\n{summaries_text}"

tags:
  python:
    system: "你是一个 Python 技术摘要助手..."
    user: "..."
```

可用变量：`{date}`、`{tag}`、`{items_text}`、`{source_ids_text}`、`{source_count}`、`{item_count}`；`digest` 模板额外使用 `{summaries_text}`。

## GitHub Pages 部署

1. 在仓库设置中启用 GitHub Pages，Source 选择 `gh-pages` 分支
2. 确保本地 git remote `origin` 指向目标仓库
3. 运行 `uv run python main.py publish` 即可推送

## 开发环境

- Python 3.9.6
- 包管理：[uv](https://docs.astral.sh/uv/)
- 主要依赖：`anthropic`、`openai`、`feedparser`、`apscheduler`、`jinja2`、`mistune`、`ghp-import`
