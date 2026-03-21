<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-20 -->

# analyzer

## Purpose
AI 分析模块，负责对已采集并标准化的数据执行摘要分析。当前实现按“标签”维度聚合同日条目生成摘要，并在标签摘要完成后进一步生成当日综合摘要（digest）。Prompt 模板从 `config/prompts.yaml` 读取，支持默认模板、按标签覆盖模板，以及独立的 digest 模板。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `run_analysis(date: str)` 统一调用接口 |
| `summarizer.py` | 核心分析逻辑：按标签分组数据、调用 AI 生成标签摘要，并进一步生成当日 digest |
| `prompt_builder.py` | Prompt 构建器：从配置加载模板，填充变量（日期、标签、条目列表、来源列表等）|
| `ai_client.py` | AI 服务客户端封装：统一调用 Anthropic 兼容接口 |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- `run_analysis(date)` 分析指定日期的数据，默认分析前一天
- 当前分析维度是：**按 tag 聚合生成摘要**，不是“tag → source”二级摘要
- 标签摘要完成后，会基于全部标签摘要再生成一条当日综合摘要（digest）
- AI 调用需处理空结果、超时、API 错误，失败时记录日志并跳过（不中断整体流程）
- AI 配置来自 `config/settings.yaml`，并支持 `INFO_AGG_AI_*` 环境变量兜底
- 每次分析结果通过 `storage.repository` 写入，不直接操作文件

### Testing Requirements
- **单元测试必须完善**，使用 `pytest`
- AI 调用需可 mock（避免测试时产生真实费用）
- 覆盖：正常分析、空数据、AI 调用失败的降级处理、digest 生成逻辑

### Common Patterns
分析流程约定：
```python
# summarizer.py 核心逻辑
def run_analysis(date: str) -> list[SummaryResult]:
    items = storage.load_items(date)          # 加载当日数据
    grouped = group_by_tag(items)             # 按标签分组

    results = []
    for tag, group_items in grouped.items():
        prompt = prompt_builder.build(...)
        summary = ai_client.complete(prompt)
        results.append(SummaryResult(...))

    storage.save_summaries(results)
    storage.save_digest(...)
    return results
```

## Dependencies

### Internal
- `storage/` — 读取 `UnifiedItem`，写入 `SummaryResult` 与 `DigestResult`
- `config/prompts.yaml` — 读取 Prompt 模板
- `config/settings.yaml` — 读取 AI 模型配置

### External
- `anthropic` — AI 调用（Anthropic 兼容 API）

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
