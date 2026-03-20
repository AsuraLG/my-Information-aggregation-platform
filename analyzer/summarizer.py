from __future__ import annotations

import logging
from datetime import datetime, timezone

from config.loader import load_settings, load_prompts
from storage.models import UnifiedItem, SummaryResult
from storage.repository import load_items, save_summaries
from analyzer.ai_client import call_ai
from analyzer.prompt_builder import build_prompt

logger = logging.getLogger(__name__)


def run_analysis(date: str) -> list[SummaryResult]:
    """对指定日期的所有条目按 (tag, source_id) 分组进行 AI 分析，返回摘要列表"""
    settings = load_settings()
    prompts_cfg = load_prompts()

    # 配置文件优先，环境变量兜底
    import os
    resolved_model = settings.ai.model or os.environ.get("INFO_AGG_AI_MODEL") or None
    resolved_api_key = settings.ai.api_key or os.environ.get("INFO_AGG_AI_API_KEY") or None
    resolved_base_url = settings.ai.base_url or os.environ.get("INFO_AGG_AI_BASE_URL") or None

    if not resolved_model:
        logger.error("未配置 AI 模型（settings.yaml ai.model 或 INFO_AGG_AI_MODEL 环境变量）")
        return []
    if not resolved_api_key:
        logger.error("未配置 API Key（settings.yaml ai.api_key 或 INFO_AGG_AI_API_KEY 环境变量）")
        return []

    items = load_items(date)
    if not items:
        logger.info("日期 [%s] 无条目，跳过分析", date)
        return []

    # 按 (tag, source_id) 分组
    groups: dict[tuple[str, str], list[UnifiedItem]] = {}
    for item in items:
        for tag in item.tags:
            key = (tag, item.source_id)
            groups.setdefault(key, []).append(item)

    results: list[SummaryResult] = []
    for (tag, source_id), group_items in groups.items():
        logger.info("分析 [%s] tag=%s source=%s 共 %d 条", date, tag, source_id, len(group_items))

        system_prompt, user_prompt = build_prompt(
            items=group_items,
            date=date,
            tag=tag,
            source_id=source_id,
            prompts_cfg=prompts_cfg,
        )

        summary_text = call_ai(
            prompt=user_prompt,
            model=resolved_model,
            max_tokens=settings.ai.max_tokens,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            system=system_prompt,
        )

        if not summary_text:
            logger.warning("AI 分析返回空结果 [%s] tag=%s source=%s", date, tag, source_id)
            continue

        results.append(SummaryResult(
            date=date,
            tag=tag,
            source_id=source_id,
            summary=summary_text,
            item_count=len(group_items),
            generated_at=datetime.now(timezone.utc),
        ))

    if results:
        save_summaries(results)
        logger.info("分析完成 [%s]: 共生成 %d 条摘要", date, len(results))

    return results
