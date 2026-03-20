from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from config.loader import SourceConfig
from collector.base import RawItem
from storage.models import UnifiedItem

logger = logging.getLogger(__name__)


def _make_id(source_id: str, url: str) -> str:
    """生成唯一 id"""
    return hashlib.md5(f"{source_id}:{url}".encode()).hexdigest()


def _parse_datetime(value: Any) -> datetime:
    """尝试解析各种格式的时间字符串，失败时返回当前 UTC 时间"""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        import email.utils
        try:
            parsed = email.utils.parsedate_to_datetime(value)
            return parsed.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def convert_rss(item: RawItem, source_cfg: SourceConfig) -> UnifiedItem:
    """将 RSS RawItem 转换为 UnifiedItem"""
    d = item.raw_data
    url = d.get("link", "")
    return UnifiedItem(
        id=_make_id(item.source_id, url),
        source_id=item.source_id,
        title=d.get("title", ""),
        content=d.get("summary", ""),
        url=url,
        published_at=_parse_datetime(d.get("published", "")),
        tags=source_cfg.tags,
        raw_data=d,
    )


def convert_github_trending(item: RawItem, source_cfg: SourceConfig) -> UnifiedItem:
    """将 GitHub Trending RawItem 转换为 UnifiedItem"""
    d = item.raw_data
    url = d.get("url", "")
    title = d.get("name", "")
    description = d.get("description", "")
    stars = d.get("stars", "")
    content = f"{description}\n⭐ {stars}" if stars else description
    return UnifiedItem(
        id=_make_id(item.source_id, url),
        source_id=item.source_id,
        title=title,
        content=content,
        url=url,
        published_at=datetime.now(timezone.utc),
        tags=source_cfg.tags,
        raw_data=d,
    )


def convert(item: RawItem, source_cfg: SourceConfig) -> UnifiedItem | None:
    """按信息源类型分发转换"""
    try:
        if source_cfg.type == "rss":
            return convert_rss(item, source_cfg)
        elif source_cfg.type == "github_trending":
            return convert_github_trending(item, source_cfg)
        else:
            logger.warning("未知信息源类型: %s", source_cfg.type)
            return None
    except Exception as e:
        logger.warning("转换失败 [%s]: %s", item.source_id, e)
        return None
