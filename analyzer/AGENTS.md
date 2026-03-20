<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-19 -->

# analyzer

## Purpose
AI 分析模块，负责对已采集并标准化的数据执行摘要分析。按"标签 → 信息源"二级分类维度调用 AI 生成摘要，结果写回 `storage/` 持久化。Prompt 模板从 `config/prompts.yaml` 读取，支持按标签或信息源配置不同 Prompt。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `run_analysis(date: str)` 统一调用接口 |
| `summarizer.py` | 核心分析逻辑：按标签和信息源维度分组数据，批量调用 AI 生成摘要 |
| `prompt_builder.py` | Prompt 构建器：从配置加载模板，填充变量（日期、标签、条目列表等）|
| `ai_client.py` | AI 服务客户端封装：统一调用接口，屏蔽具体 AI SDK 差异 |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- `run_analysis(date)` 分析指定日期的数据，默认分析前一天
- 分析维度：先按标签分组，再在每个标签内按信息源细分，共两级摘要
- AI 调用需处理限流、超时、API 错误，失败时记录日志并跳过（不中断整体流程）
- `ai_client.py` 应支持切换不同 AI 提供商（Anthropic/OpenAI），通过 `config/settings.yaml` 配置
- 每次分析结果通过 `storage.repository` 写入，不直接操作文件

### Testing Requirements
- AI 调用需可 mock，避免测试时产生真实费用
- 测试覆盖：正常分析、空数据、AI 调用失败的降级处理

### Common Patterns
分析流程约定：
```python
# summarizer.py 核心逻辑
def run_analysis(date: str) -> list[SummaryResult]:
    items = storage.load_items(date)          # 加载当日数据
    grouped = group_by_tag_and_source(items)  # 按标签→信息源分组

    results = []
    for tag, sources in grouped.items():
        for source_id, source_items in sources.items():
            prompt = prompt_builder.build(tag, source_id, source_items)
            summary = ai_client.complete(prompt)
            results.append(SummaryResult(
                date=date, tag=tag, source_id=source_id,
                summary=summary, item_count=len(source_items)
            ))

    storage.save_summaries(results)
    return results
```

## Dependencies

### Internal
- `storage/` — 读取 `UnifiedItem`，写入 `SummaryResult`
- `config/prompts.yaml` — 读取 Prompt 模板
- `config/settings.yaml` — 读取 AI 模型配置

### External
- `anthropic` 或 `openai` SDK — AI 调用
- `jinja2` — Prompt 模板渲染（如需复杂模板）

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
