from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from collector.base import RawItem
from collector.rss import RSSCollector
from collector.github_trending import GitHubTrendingCollector

if TYPE_CHECKING:
    from config.loader import SourceConfig

logger = logging.getLogger(__name__)


def run_collection(source_cfg: "SourceConfig") -> list[RawItem]:
    """根据信息源配置创建对应采集器并执行采集，返回 RawItem 列表"""
    source_type = source_cfg.type
    source_id = source_cfg.id

    if source_type == "rss":
        url = source_cfg.url or ""
        if not url:
            logger.warning("RSS 信息源 [%s] 缺少 url 参数，跳过", source_id)
            return []
        collector = RSSCollector(source_id=source_id, url=url)

    elif source_type == "github_trending":
        language = source_cfg.language or ""
        period = source_cfg.period or "daily"
        collector = GitHubTrendingCollector(source_id=source_id, language=language, period=period)

    else:
        logger.warning("未知信息源类型 [%s]: %s，跳过", source_id, source_type)
        return []

    return collector.fetch()


__all__ = ["run_collection", "RawItem"]
