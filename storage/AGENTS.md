<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-20 -->

# storage

## Purpose
存储模块，定义系统的统一数据格式，并负责原始数据的转换与本地持久化。是整个系统的数据中枢：collector 产出的原始数据在此转换为统一结构，analyzer 从此读取待分析数据，publisher 从此读取摘要结果。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `save_items()`、`load_items()` 等核心接口 |
| `models.py` | 统一数据结构定义：`UnifiedItem`（采集条目）和 `SummaryResult`（摘要结果）|
| `converter.py` | 原始数据转换器：将 `RawItem` 转换为 `UnifiedItem`，按信息源类型分发 |
| `repository.py` | 本地持久化：读写 JSON/SQLite，按日期分区存储 |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- `models.py` 中的数据结构是全系统的契约，修改前需评估对 collector/analyzer/publisher 的影响
- 持久化格式优先选择 JSON（可读性好，便于调试），数据量大时可迁移到 SQLite
- 数据按日期分区存储，路径约定：`data/items/YYYY-MM-DD.json`（单文件）和 `data/summaries/YYYY-MM-DD.json`（单文件）
- `converter.py` 中每种信息源类型对应一个转换函数，新增信息源时在此扩展

### Testing Requirements
- **单元测试必须完善**，使用 `pytest`
- `models.py` 的序列化/反序列化需有测试
- `converter.py` 的转换逻辑需覆盖各信息源类型

### Common Patterns
统一数据结构（pydantic v2 BaseModel）：
```python
class UnifiedItem(BaseModel):
    id: str                    # 唯一标识（source_id + 原始 id 的 hash）
    source_id: str             # 来源信息源 id
    title: str
    content: str               # 正文或摘要
    url: str
    published_at: datetime
    tags: list[str]            # 来自信息源配置的标签
    raw_data: dict             # 保留原始字段，便于调试

class SummaryResult(BaseModel):
    date: str                  # YYYY-MM-DD
    tag: str                   # 按标签维度
    source_id: str             # 按信息源维度
    summary: str               # AI 生成的摘要内容（markdown 格式）
    item_count: int            # 本次分析的条目数
    generated_at: datetime
```

## Dependencies

### Internal
- `config/sources.yaml` — 读取标签映射规则（用于转换时打标签）
- 被 `collector/`、`analyzer/`、`publisher/` 依赖

### External
- `pydantic>=2.0` — 数据校验
- 标准库 `json`（当前持久化格式）

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
