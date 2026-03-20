from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from storage.models import UnifiedItem, SummaryResult
from storage.repository import save_items, load_items, save_summaries, load_summaries
from storage.converter import convert

if TYPE_CHECKING:
    from collector.base import RawItem
    from config.loader import SourceConfig

logger = logging.getLogger(__name__)


def convert_and_save(
    items: list["RawItem"],
    source_cfg: "SourceConfig",
    date: str | None = None,
) -> int:
    """将 RawItem 列表转换为 UnifiedItem 并存储，返回实际新增条数"""
    if not items:
        return 0

    unified = []
    for raw in items:
        result = convert(raw, source_cfg)
        if result is not None:
            unified.append(result)

    if not unified:
        logger.warning("转换后无有效条目 [%s]", source_cfg.id)
        return 0

    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    existing_count = len(load_items(date))
    save_items(unified, date)
    new_count = len(load_items(date)) - existing_count
    return max(new_count, 0)


__all__ = [
    "UnifiedItem",
    "SummaryResult",
    "save_items",
    "load_items",
    "save_summaries",
    "load_summaries",
    "convert_and_save",
]
