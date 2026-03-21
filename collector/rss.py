from __future__ import annotations

import logging
from typing import Any

import feedparser
import requests

from collector.base import BaseCollector, RawItem

logger = logging.getLogger(__name__)

_TIMEOUT = 15
_USER_AGENT = "Mozilla/5.0 (compatible; info-aggregator/1.0)"


class RSSCollector(BaseCollector):
    """RSS/Atom feed 采集器"""

    def __init__(self, source_id: str, url: str) -> None:
        super().__init__(source_id)
        self.url = url

    def fetch(self) -> list[RawItem]:
        try:
            response = requests.get(
                self.url,
                timeout=_TIMEOUT,
                headers={"User-Agent": _USER_AGENT},
            )
            response.raise_for_status()
        except Exception as e:
            logger.warning("RSS 请求失败 [%s]: %s", self.source_id, e)
            return []

        content_type = response.headers.get("Content-Type", "")
        text = response.text.lstrip()
        if "html" in content_type.lower() or text.startswith("<!DOCTYPE html") or text.startswith("<html"):
            logger.warning("RSS 返回非 feed 内容 [%s]: content_type=%s", self.source_id, content_type or "unknown")
            return []

        try:
            feed = feedparser.parse(response.text)
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
