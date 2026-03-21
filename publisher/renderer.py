from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import mistune
from jinja2 import Environment, FileSystemLoader

from config.loader import load_settings, load_tags, load_sources
from storage.repository import load_summaries, list_available_dates, load_digest

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_md = mistune.create_markdown(escape=True)
_CST = ZoneInfo("Asia/Shanghai")


def _build_ordered_summaries(
    summaries: list[Any],
    tag_id_to_info: dict[str, tuple[str, int]],
    source_id_to_info: dict[str, tuple[str, int]],
) -> list[dict[str, Any]]:
    """将 SummaryResult 列表按 tag order 排序，返回模板可用的有序结构。"""
    sorted_summaries = sorted(
        summaries,
        key=lambda summary: tag_id_to_info.get(summary.tag, (summary.tag, 999))[1],
    )

    ordered: list[dict[str, Any]] = []
    for summary in sorted_summaries:
        source_descs = [
            source_id_to_info.get(source_id, (source_id, 999))[0]
            for source_id in summary.source_ids
        ]
        ordered.append({
            "tag_desc": tag_id_to_info.get(summary.tag, (summary.tag, 999))[0],
            "summary_html": _md(summary.summary),
            "item_count": summary.item_count,
            "source_count": summary.source_count,
            "source_descs": source_descs,
            "sources_label": "、".join(source_descs),
        })
    return ordered


def _render_daily_page(
    env: Environment,
    date: str,
    all_dates: list[str],
    output_dir: Path,
    settings: Any,
    tag_id_to_info: dict[str, tuple[str, int]],
    source_id_to_info: dict[str, tuple[str, int]],
    generated_at: str,
) -> None:
    """渲染单个日期的页面到 output/{date}/index.html"""
    summaries = load_summaries(date)
    if not summaries:
        return

    ordered_summaries = _build_ordered_summaries(summaries, tag_id_to_info, source_id_to_info)

    # 计算前后日期导航（all_dates 降序，idx+1 是更早的日期）
    idx = all_dates.index(date) if date in all_dates else -1
    prev_date = all_dates[idx + 1] if idx >= 0 and idx + 1 < len(all_dates) else None
    next_date = all_dates[idx - 1] if idx > 0 else None

    digest = load_digest(date)
    digest_html = _md(digest.digest) if digest else None

    template = env.get_template("index.html")
    html = template.render(
        site_title=settings.publish.site_title,
        site_description=settings.publish.site_description,
        date=date,
        generated_at=generated_at,
        ordered_summaries=ordered_summaries,
        prev_date=prev_date,
        next_date=next_date,
        all_dates=all_dates,
        digest_html=digest_html,
    )

    date_dir = output_dir / date
    date_dir.mkdir(parents=True, exist_ok=True)
    (date_dir / "index.html").write_text(html, encoding="utf-8")


def render(date: str) -> Path:
    """全量重建所有历史日期页面 + 首页，返回本次 date 对应的页面路径。"""
    settings = load_settings()
    output_dir = Path(settings.publish.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tags_cfg = load_tags()
    sources_cfg = load_sources()
    tag_id_to_info = {t.id: (t.desc, t.order) for t in tags_cfg.tags}
    source_id_to_info = {s.id: ((s.desc or s.id), s.order) for s in sources_cfg.sources}

    generated_at = datetime.now(_CST).strftime("%Y-%m-%d %H:%M CST")
    all_dates = list_available_dates()

    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=True)

    # 全量重建：遍历所有历史日期
    for d in all_dates:
        _render_daily_page(env, d, all_dates, output_dir, settings, tag_id_to_info, source_id_to_info, generated_at)

    # 首页：展示本次 render 传入的 date 的内容 + 全部日期导航
    summaries = load_summaries(date)
    ordered_summaries = _build_ordered_summaries(summaries, tag_id_to_info, source_id_to_info)

    digest = load_digest(date)
    digest_html = _md(digest.digest) if digest else None

    home_tmpl = env.get_template("home.html")
    home_html = home_tmpl.render(
        site_title=settings.publish.site_title,
        site_description=settings.publish.site_description,
        date=date,
        generated_at=generated_at,
        ordered_summaries=ordered_summaries,
        dates=all_dates,
        digest_html=digest_html,
    )
    home_path = output_dir / "index.html"
    home_path.write_text(home_html, encoding="utf-8")

    logger.info("全量渲染完成: %d 个日期页面 + 首页", len(all_dates))
    return output_dir / date / "index.html"
