<!-- Generated: 2026-03-19 | Updated: 2026-03-19 -->

# my-Information-aggregation-platform

## Purpose
个人使用的信息聚合工具，支持本地或单机服务器部署。核心流程：定时采集 RSS 与 GitHub Trending 信息 → 转换为统一格式落库 → 按标签和信息源维度执行 AI 摘要分析 → 生成静态页面发布到 GitHub Pages。

整个系统以配置文件驱动，无 Web 管理后台，目标是稳定跑通完整闭环，无需人工干预。

## Key Files

| File | Description |
|------|-------------|
| `README.md` | 项目概述（待补充） |
| `requirement_analysis.md` | 需求分析文档 |
| `LICENSE` | MIT License — 版权归 AsuraLG (2026) |
| `.gitignore` | Python 项目忽略规则 |
| `AGENTS.md` | 本文件 — AI Agent 导航文档 |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `config/` | 配置文件目录：信息源、标签规则、Prompt、调度配置（见 `config/AGENTS.md`） |
| `collector/` | 采集模块：RSS 与 GitHub Trending 数据抓取（见 `collector/AGENTS.md`） |
| `storage/` | 存储模块：统一格式数据结构定义与本地持久化（见 `storage/AGENTS.md`） |
| `analyzer/` | 分析模块：AI 摘要分析，按标签和信息源维度输出（见 `analyzer/AGENTS.md`） |
| `publisher/` | 发布模块：静态页面生成与 GitHub Pages 自动发布（见 `publisher/AGENTS.md`） |
| `scheduler/` | 调度模块：定时任务管理，驱动采集与分析的执行节奏（见 `scheduler/AGENTS.md`） |

## For AI Agents

### 架构概览
系统是一个 4 层流水线，各层职责严格分离：

```
[scheduler] ──触发──> [collector] ──原始数据──> [storage]
                                                    │
                                              统一格式数据
                                                    │
[scheduler] ──触发──> [analyzer] <──消费──────────┘
                          │
                      摘要结果
                          │
                    [publisher] ──生成──> GitHub Pages
```

### Working In This Directory
- **语言**: Python 3.9.6，使用 `python` 命令（不用 `python3`）
- **包管理**: 优先使用 `uv`，其次 `pip`
- **代码风格**: PEP 8，4 空格缩进，所有函数加类型注解
- **作者**: `ligen20`，版权年份 `2026`
- 修改任何模块前，先阅读对应目录的 `AGENTS.md`
- 各模块之间通过 `storage/` 的统一数据格式解耦，不直接互相调用

### Testing Requirements
- 添加单元测试前需与用户确认
- 使用 `pytest`

### Common Patterns
- 配置文件驱动：所有可变参数（信息源、标签、Prompt、调度时间）均在 `config/` 中定义
- 统一数据格式：所有信息源采集结果必须转换为 `storage/` 定义的统一结构后再持久化
- 模块入口：每个子模块提供独立可调用的入口函数，供 `scheduler/` 调用

## Dependencies

### Internal
- `config/` 被所有模块读取
- `storage/` 被 `collector/`、`analyzer/`、`publisher/` 共同依赖
- `scheduler/` 依赖 `collector/` 和 `analyzer/` 的入口函数

### External
_待确定。候选依赖：_
- `feedparser` — RSS 解析
- `requests` / `httpx` — HTTP 请求
- `APScheduler` / `schedule` — 定时任务
- Anthropic / OpenAI SDK — AI 分析
- `jinja2` — 静态页面模板渲染
- `PyGithub` / `ghp-import` — GitHub Pages 发布

## Spec Reference
完整需求规格见 `.omc/specs/deep-interview-personal-information-aggregation-platform-mvp.md`
- 最终歧义度：12.9%（已通过 20% 阈值）
- 核心验收标准：整个闭环能够在无人干预下稳定重复执行

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
