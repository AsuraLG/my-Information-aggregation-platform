<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-20 -->

# config

## Purpose
配置文件目录，驱动整个系统的行为。所有可变参数均在此定义，包括：信息源列表与采集规则、标签分类规则、AI 分析 Prompt 模板、调度执行时间。系统无 Web 管理后台，用户通过直接编辑这些配置文件来控制系统行为。

## Key Files

| File | Description |
|------|-------------|
| `sources.yaml` | 信息源配置：RSS 订阅列表、GitHub Trending 抓取配置，每个信息源绑定标签规则、采集频率和展示描述（desc）|
| `tags.yaml` | 标签体系定义：全局统一的标签列表，每个标签含 id（引用标识）和 desc（展示描述）|
| `prompts.yaml` | AI 分析 Prompt 模板：system + user 双段，可按标签配置不同 Prompt |
| `schedule.yaml` | 调度配置：分析任务的执行时间/频率（cron 表达式，UTC 时区）|
| `settings.yaml` | 全局设置（本地，不提交）：存储路径、GitHub Pages 配置、AI 模型参数 |
| `settings.yaml.example` | settings.yaml 配置模板，提交到 git 供参考 |
| `loader.py` | 配置加载模块：pydantic v2 校验，load_sources/load_tags/load_settings 等函数 |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- 配置文件使用 YAML 格式，保持可读性优先
- 修改配置 schema 时，必须同步更新读取该配置的模块代码
- `sources.yaml` 中每个信息源必须包含：类型（rss/github_trending）、标识符、标签 id 列表、采集频率、展示描述（desc）
- 标签在 `tags.yaml` 中统一定义（id + desc），`sources.yaml` 中只引用 id，不能随意新增
- 新增标签时先在 `tags.yaml` 中定义，再在 `sources.yaml` 中引用；`validate_tags()` 会在启动时做交叉校验
- AI 配置优先级：`settings.yaml` > 环境变量（`INFO_AGG_AI_*` 前缀）
- Prompt 模板支持变量插值：`{date}`、`{tag}`、`{items_text}`、`{source_ids_text}`、`{source_count}`、`{item_count}`；digest 模板使用 `{summaries_text}`

### Testing Requirements
- 配置文件变更后，运行 `uv run python main.py` 验证配置加载和 `validate_tags()` 校验通过
- `loader.py` 的 pydantic 校验逻辑建议有单元测试覆盖

### Common Patterns
配置文件示例结构（`sources.yaml`）：
```yaml
sources:
  - id: "sebastian_raschka"
    type: rss
    url: "https://magazine.sebastianraschka.com/feed"
    tags: ["AI"]
    schedule: "0 9 * * *"

  - id: "github_trending_python"
    type: github_trending
    language: "python"
    period: "daily"
    tags: ["AI", "python", "opensource"]
    schedule: "0 9 * * *"
```

## Dependencies

### Internal
- 被 `collector/`、`analyzer/`、`publisher/`、`scheduler/` 所有模块读取
- 是系统的唯一配置入口

### External
- `pyyaml` — YAML 解析
- `pydantic>=2.0` — 配置 schema 校验

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
