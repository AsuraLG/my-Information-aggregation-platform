<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-20 -->

# collector

## Purpose
采集模块，负责从外部信息源拉取原始数据。第一版支持两类信息源：RSS 订阅和 GitHub Trending。采集结果交给 `storage/` 模块转换为统一格式后持久化，collector 本身不直接写库。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `run_collection(source_config)` 统一调用接口 |
| `base.py` | 采集器基类 `BaseCollector`，定义 `fetch() -> list[RawItem]` 接口 |
| `rss.py` | RSS 采集器，解析 RSS/Atom feed，返回原始条目列表 |
| `github_trending.py` | GitHub Trending 采集器，抓取指定语言/周期的 Trending 仓库列表 |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- 每个采集器继承 `BaseCollector`，实现 `fetch()` 方法
- `fetch()` 只负责拉取和解析原始数据，**不做格式转换**，格式转换在 `storage/` 中完成
- 采集器应处理网络超时、HTTP 错误、解析失败等异常，记录日志后继续（不中断整体调度）
- GitHub Trending 无官方 API，需通过 HTTP 抓取页面或使用第三方库

### Testing Requirements
- **单元测试必须完善**，使用 `pytest`
- 网络请求需可 mock
- 覆盖：正常采集、网络超时、空结果、解析异常

### Common Patterns
采集器接口约定：
```python
from dataclasses import dataclass
from typing import Any

@dataclass
class RawItem:
    source_id: str       # 对应 config/sources.yaml 中的 id
    raw_data: dict[str, Any]  # 原始字段，不做标准化

class BaseCollector:
    def fetch(self) -> list[RawItem]:
        raise NotImplementedError
```

## Dependencies

### Internal
- `config/sources.yaml` — 读取信息源配置
- `storage/` — 采集结果传递给 storage 模块做格式转换

### External
- `feedparser` — RSS/Atom 解析
- `requests` / `httpx` — HTTP 请求
- `beautifulsoup4` — GitHub Trending 页面解析（如需）

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
