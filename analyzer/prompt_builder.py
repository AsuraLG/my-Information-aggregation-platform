from __future__ import annotations

from storage.models import UnifiedItem
from config.loader import PromptsConfig


def build_prompt(
    items: list[UnifiedItem],
    date: str,
    tag: str,
    prompts_cfg: PromptsConfig,
    source_ids: list[str] | None = None,
) -> tuple[str, str]:
    """返回 (system_prompt, user_prompt) 元组"""
    items_text = _format_items(items)
    template = prompts_cfg.tags.get(tag) or prompts_cfg.default
    resolved_source_ids = source_ids or []

    variables = dict(
        date=date,
        tag=tag,
        items_text=items_text,
        source_ids_text="、".join(resolved_source_ids),
        source_count=len(resolved_source_ids),
        item_count=len(items),
    )
    return template.system.format(**variables), template.user.format(**variables)


def _format_items(items: list[UnifiedItem]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. 【{item.title}】")
        if item.content:
            lines.append(f"   {item.content[:200]}")
        lines.append(f"   {item.url}")
    return "\n".join(lines)
