<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-20 -->

# storage

## Purpose
存储模块，定义系统的统一数据格式，并负责原始数据的转换与本地持久化。是整个系统的数据中枢：collector 产出的原始数据在此转换为统一结构，analyzer 从此读取待分析数据并写回标签摘要与当日 digest，publisher 从此读取摘要结果。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `save_items()`、`load_items()` 等核心接口 |
| `models.py` | 统一数据结构定义：`UnifiedItem`、`SummaryResult`、`DigestResult` |
| `converter.py` | 原始数据转换器：将 `RawItem` 转换为 `UnifiedItem`，按信息源类型分发 |
| `repository.py` | 本地持久化：按日期读写 JSON 文件，包含 items / summaries / digest |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- `models.py` 中的数据结构是全系统的契约，修改前需评估对 collector/analyzer/publisher 的影响
- 持久化格式当前为 JSON（强调可读性和可调试性）
- 数据按日期分区存储，路径约定：`data/items/YYYY-MM-DD.json`、`data/summaries/YYYY-MM-DD.json`、`data/digest/YYYY-MM-DD.json`
- `converter.py` 中每种信息源类型对应一个转换函数，新增信息源时在此扩展
- repository 写入采用原子写入，避免中途中断导致文件损坏

### Testing Requirements
- **单元测试必须完善**，使用 `pytest`
- `models.py` 的序列化/反序列化需有测试
- `converter.py` 的转换逻辑需覆盖各信息源类型
- `repository.py` 需覆盖摘要和 digest 的读写行为

### Common Patterns
统一数据结构（pydantic v2 BaseModel）：
```python
class UnifiedItem(BaseModel):
    id: str
    source_id: str
    title: str
    content: str
    url: str
    published_at: datetime
    tags: list[str]
    raw_data: dict

class SummaryResult(BaseModel):
    date: str
    tag: str
    summary: str
    item_count: int
    source_ids: list[str]
    source_count: int
    generated_at: datetime

class DigestResult(BaseModel):
    date: str
    digest: str
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
