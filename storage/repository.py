from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from storage.models import UnifiedItem, SummaryResult, DigestResult

logger = logging.getLogger(__name__)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _data_dir() -> Path:
    from config.loader import load_settings
    settings = load_settings()
    return Path(settings.storage.data_dir)


def _items_path(date: str) -> Path:
    return _data_dir() / "items" / f"{date}.json"


def _summaries_path(date: str) -> Path:
    return _data_dir() / "summaries" / f"{date}.json"


def _digest_path(date: str) -> Path:
    return _data_dir() / "digest" / f"{date}.json"


def _atomic_write(path: Path, content: str) -> None:
    """原子写入：先写 .tmp 文件，完成后 os.replace() 覆盖目标"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def save_items(items: list[UnifiedItem], date: str | None = None) -> None:
    """将 UnifiedItem 列表追加写入当日 JSON 文件（原子写入）"""
    if not items:
        return
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    path = _items_path(date)
    existing = load_items(date)

    # 去重：以 id 为 key
    existing_ids = {item.id for item in existing}
    new_items = [item for item in items if item.id not in existing_ids]
    if not new_items:
        logger.info("无新增条目（全部重复），跳过写入 [%s]", date)
        return

    all_items = existing + new_items
    content = json.dumps(
        [json.loads(item.model_dump_json()) for item in all_items],
        ensure_ascii=False,
        indent=2,
    )
    _atomic_write(path, content)
    logger.info("存储完成 [%s]: 新增 %d 条，共 %d 条", date, len(new_items), len(all_items))


def load_items(date: str) -> list[UnifiedItem]:
    """读取指定日期的 UnifiedItem 列表"""
    path = _items_path(date)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [UnifiedItem(**item) for item in data]
    except Exception as e:
        logger.error("读取 items 失败 [%s]: %s", date, e)
        return []


def save_summaries(results: list[SummaryResult]) -> None:
    """将 SummaryResult 列表写入对应日期的 JSON 文件（原子写入）"""
    if not results:
        return
    # 按日期分组写入
    by_date: dict[str, list[SummaryResult]] = {}
    for r in results:
        by_date.setdefault(r.date, []).append(r)

    for date, date_results in by_date.items():
        path = _summaries_path(date)
        content = json.dumps(
            [json.loads(r.model_dump_json()) for r in date_results],
            ensure_ascii=False,
            indent=2,
        )
        _atomic_write(path, content)
        logger.info("摘要存储完成 [%s]: %d 条", date, len(date_results))


def load_summaries(date: str) -> list[SummaryResult]:
    """读取指定日期的 SummaryResult 列表"""
    path = _summaries_path(date)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [SummaryResult(**item) for item in data]
    except Exception as e:
        logger.error("读取 summaries 失败 [%s]: %s", date, e)
        return []


def list_available_dates() -> list[str]:
    """扫描所有已知来源，返回降序排列的日期列表。

    来源一：data/summaries/*.json（本地运行的权威来源）
    来源二：output/{date}/index.html（GitHub Actions 模式下从 gh-pages 恢复的历史 HTML）
    两个来源合并去重，确保 GitHub Actions 场景下历史归档日期不丢失。
    """
    dates: set[str] = set()

    # 来源一：data/summaries/*.json
    summaries_dir = _data_dir() / "summaries"
    if summaries_dir.exists():
        for f in summaries_dir.iterdir():
            if f.is_file() and f.suffix == ".json" and _DATE_RE.match(f.stem):
                dates.add(f.stem)

    # 来源二：output/{date}/index.html（GitHub Actions 恢复的历史页面）
    from config.loader import load_settings
    output_dir = Path(load_settings().publish.output_dir)
    if output_dir.exists():
        for d in output_dir.iterdir():
            if d.is_dir() and _DATE_RE.match(d.name) and (d / "index.html").exists():
                dates.add(d.name)

    return sorted(dates, reverse=True)


def save_digest(result: DigestResult) -> None:
    """将 DigestResult 写入 data/digest/{date}.json（原子写入）"""
    path = _digest_path(result.date)
    content = json.dumps(
        json.loads(result.model_dump_json()),
        ensure_ascii=False,
        indent=2,
    )
    _atomic_write(path, content)
    logger.info("日报摘要存储完成 [%s]", result.date)


def load_digest(date: str) -> DigestResult | None:
    """读取指定日期的 DigestResult，不存在时返回 None"""
    path = _digest_path(date)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return DigestResult(**data)
    except Exception as e:
        logger.error("读取 digest 失败 [%s]: %s", date, e)
        return None
