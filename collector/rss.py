from __future__ import annotations

import logging
from typing import Any

import feedparser

from collector.base import BaseCollector, RawItem

logger = logging.getLogger(__name__)


class RSSCollector(BaseCollector):
    """RSS/Atom feed 采集器"""

    def __init__(self, source_id: str, url: str) -> None:
        super().__init__(source_id)
        self.url = url

    def fetch(self) -> list[RawItem]:
        try:
            feed = feedparser.parse(self.url)
            if feed.bozo and not feed.entries:
                logger.warning("RSS 解析异常 [%s]: %s", self.source_id, feed.bozo_exception)
                return []

            items = []
            for entry in feed.entries:
                raw: dict[str, Any] = {
                    "title": getattr(entry, "title", ""),
                    "link": getattr(entry, "link", ""),
                    "summary": getattr(entry, "summary", ""),
                    "published": getattr(entry, "published", ""),
                    "id": getattr(entry, "id", getattr(entry, "link", "")),
                }
                items.append(RawItem(source_id=self.source_id, raw_data=raw))

            logger.info("RSS 采集完成 [%s]: %d 条", self.source_id, len(items))
            return items

        except Exception as e:
            logger.warning("RSS 采集失败 [%s]: %s", self.source_id, e)
            return []
