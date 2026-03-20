from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mistune
from jinja2 import Environment, FileSystemLoader

from config.loader import load_settings, load_tags, load_sources
from storage.models import SummaryResult
from storage.repository import load_summaries

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_md = mistune.create_markdown(escape=True)


def render(date: str) -> Path:
    """将指定日期的摘要渲染为 HTML，写入 output_dir/index.html，返回输出路径"""
    settings = load_settings()
    output_dir = Path(settings.publish.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 构建 id→desc 映射，找不到时回退到 id 本身
    tags_cfg = load_tags()
    sources_cfg = load_sources()
    tag_id_to_desc = {t.id: t.desc for t in tags_cfg.tags}
    source_id_to_desc = {s.id: (s.desc or s.id) for s in sources_cfg.sources}

    summaries = load_summaries(date)

    # 按 tag desc 分组，每条记录附加渲染所需字段
    summaries_by_tag: dict[str, list[dict[str, Any]]] = {}
    for s in summaries:
        tag_desc = tag_id_to_desc.get(s.tag, s.tag)
        entry: dict[str, Any] = {
            "source_id": s.source_id,
            "source_desc": source_id_to_desc.get(s.source_id, s.source_id),
            "summary_html": _md(s.summary),
            "item_count": s.item_count,
        }
        summaries_by_tag.setdefault(tag_desc, []).append(entry)

    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("index.html")

    html = template.render(
        site_title=settings.publish.site_title,
        site_description=settings.publish.site_description,
        date=date,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        summaries_by_tag=summaries_by_tag,
    )

    output_path = output_dir / "index.html"
    output_path.write_text(html, encoding="utf-8")
    logger.info("页面渲染完成: %s (%d 个标签)", output_path, len(summaries_by_tag))
    return output_path
