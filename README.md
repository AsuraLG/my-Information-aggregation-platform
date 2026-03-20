# 个人信息聚合平台

自动采集多个信息源（RSS / GitHub Trending），通过 AI 生成每日摘要，并发布到 GitHub Pages 静态站点。

## 功能

- **多源采集**：RSS 订阅 + GitHub Trending，按 cron 表达式定时运行
- **AI 摘要**：调用 Anthropic 兼容 API，按标签使用不同 prompt 模板，支持 system/user 双提示词
- **静态发布**：Jinja2 渲染 HTML，通过 `ghp-import` 推送到 `gh-pages` 分支
- **配置驱动**：信息源、标签、prompt、调度、AI 参数均通过 YAML 配置，代码不硬编码业务参数

## 项目结构

```
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
export INFO_AGG_AI_MODEL="claude-3-5-haiku-20241022"
export INFO_AGG_AI_API_KEY="sk-..."
export INFO_AGG_AI_BASE_URL="https://..."   # 可选，自定义端点/代理
```

### 3. 手动运行

```bash
# 采集所有信息源
uv run python main.py collect

# 采集指定信息源
uv run python main.py collect --source hacker_news

# 分析（默认昨天）
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

## 配置说明

### 信息源（`config/sources.yaml`）

```yaml
sources:
  - id: "hacker_news"
    desc: "Hacker News"        # 页面展示名称
    type: rss
    url: "https://news.ycombinator.com/rss"
    tags: ["tech", "programming"]
    schedule: "0 */6 * * *"   # cron，UTC 时区
```

支持的 `type`：`rss`、`github_trending`

### 标签（`config/tags.yaml`）

```yaml
tags:
  - id: "tech"
    desc: "科技资讯"    # 页面展示名称
```

`sources.yaml` 中的 `tags` 字段引用 `id`，页面渲染时自动替换为 `desc`。

### AI Prompt（`config/prompts.yaml`）

支持按标签配置不同 prompt，未匹配的标签使用 `default`：

```yaml
default:
  system: "你是一个信息摘要助手..."
  user: "以下是 {date} 来自「{source_id}」的内容：\n\n{items_text}"

tags:
  python:
    system: "你是一个 Python 技术摘要助手..."
    user: "..."
```

可用变量：`{date}`、`{tag}`、`{source_id}`、`{items_text}`

## GitHub Pages 部署

1. 在仓库设置中启用 GitHub Pages，Source 选择 `gh-pages` 分支
2. 确保本地 git remote `origin` 指向目标仓库
3. 运行 `uv run python main.py publish` 即可推送

## 开发环境

- Python 3.9.6
- 包管理：[uv](https://docs.astral.sh/uv/)
- 主要依赖：`anthropic`、`feedparser`、`apscheduler`、`jinja2`、`mistune`、`ghp-import`
