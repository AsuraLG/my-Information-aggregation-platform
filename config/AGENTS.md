<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-19 -->

# config

## Purpose
配置文件目录，驱动整个系统的行为。所有可变参数均在此定义，包括：信息源列表与采集规则、标签分类规则、AI 分析 Prompt 模板、调度执行时间。系统无 Web 管理后台，用户通过直接编辑这些配置文件来控制系统行为。

## Key Files

| File | Description |
|------|-------------|
| `sources.yaml` | 信息源配置：RSS 订阅列表、GitHub Trending 抓取配置，每个信息源绑定标签规则和采集频率 |
| `tags.yaml` | 标签体系定义：全局统一的标签列表与分类规则 |
| `prompts.yaml` | AI 分析 Prompt 模板：可按标签或信息源维度配置不同 Prompt |
| `schedule.yaml` | 调度配置：采集任务和分析任务的执行时间/频率 |
| `settings.yaml` | 全局设置：存储路径、GitHub Pages 仓库地址、AI 模型选择等 |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- 配置文件使用 YAML 格式，保持可读性优先
- 修改配置 schema 时，必须同步更新读取该配置的模块代码
- `sources.yaml` 中每个信息源必须包含：类型（rss/github_trending）、标识符、标签映射规则、采集频率
- 标签在 `tags.yaml` 中统一定义，其他配置文件中只能引用已定义的标签名，不能随意新增
- Prompt 模板支持变量插值（如 `{date}`、`{tag}`、`{source}`）

### Testing Requirements
- 配置文件变更后，运行配置加载模块的验证函数确认 schema 合法
- 不需要单独的单元测试，但需要 schema 校验逻辑

### Common Patterns
配置文件示例结构（`sources.yaml`）：
```yaml
sources:
  - id: "hacker_news"
    type: rss
    url: "https://news.ycombinator.com/rss"
    tags: ["tech", "programming"]
    schedule: "0 */6 * * *"  # 每6小时

  - id: "github_trending_python"
    type: github_trending
    language: "python"
    period: "daily"
    tags: ["python", "opensource"]
    schedule: "0 8 * * *"  # 每天8点
```

## Dependencies

### Internal
- 被 `collector/`、`analyzer/`、`publisher/`、`scheduler/` 所有模块读取
- 是系统的唯一配置入口

### External
- `pyyaml` — YAML 解析
- `pydantic` — 配置 schema 校验（推荐）

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
