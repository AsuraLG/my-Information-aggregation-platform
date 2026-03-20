from __future__ import annotations

from storage.models import UnifiedItem
from config.loader import PromptsConfig


def build_prompt(
    items: list[UnifiedItem],
    date: str,
    tag: str,
    source_id: str,
    prompts_cfg: PromptsConfig,
) -> tuple[str, str]:
    """返回 (system_prompt, user_prompt) 元组"""
    items_text = _format_items(items)
    template = prompts_cfg.tags.get(tag) or prompts_cfg.default

    variables = dict(date=date, tag=tag, source_id=source_id, items_text=items_text)
    return template.system.format(**variables), template.user.format(**variables)


def _format_items(items: list[UnifiedItem]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. 【{item.title}】")
        if item.content:
            lines.append(f"   {item.content[:200]}")
        lines.append(f"   {item.url}")
    return "\n".join(lines)
