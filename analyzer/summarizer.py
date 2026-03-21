from __future__ import annotations

import logging
from datetime import datetime, timezone

from config.loader import load_settings, load_prompts
from storage.models import UnifiedItem, SummaryResult, DigestResult
from storage.repository import load_items, save_summaries, save_digest
from analyzer.ai_client import call_ai
from analyzer.prompt_builder import build_prompt

logger = logging.getLogger(__name__)


def run_analysis(date: str) -> list[SummaryResult]:
    """对指定日期的所有条目按 tag 分组进行 AI 分析，返回摘要列表"""
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

    # 按 tag 分组
    groups: dict[str, list[UnifiedItem]] = {}
    for item in items:
        for tag in item.tags:
            groups.setdefault(tag, []).append(item)

    results: list[SummaryResult] = []
    for tag, group_items in groups.items():
        source_ids = sorted({item.source_id for item in group_items})
        logger.info(
            "分析 [%s] tag=%s 共 %d 条，覆盖 %d 个来源",
            date,
            tag,
            len(group_items),
            len(source_ids),
        )

        system_prompt, user_prompt = build_prompt(
            items=group_items,
            date=date,
            tag=tag,
            prompts_cfg=prompts_cfg,
            source_ids=source_ids,
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
            logger.warning("AI 分析返回空结果 [%s] tag=%s", date, tag)
            continue

        results.append(SummaryResult(
            date=date,
            tag=tag,
            summary=summary_text,
            item_count=len(group_items),
            source_ids=source_ids,
            source_count=len(source_ids),
            generated_at=datetime.now(timezone.utc),
        ))

    if results:
        save_summaries(results)
        logger.info("分析完成 [%s]: 共生成 %d 条摘要", date, len(results))

    # 第二步：合并所有摘要，生成当日综合日报摘要
    if results:
        summaries_text = "\n\n".join(
            f"【{r.tag}】\n覆盖来源：{'、'.join(r.source_ids)}\n原始信息：{r.item_count} 条\n{r.summary}"
            for r in results
        )
        digest_cfg = prompts_cfg.digest
        user_prompt = digest_cfg.user.format(date=date, summaries_text=summaries_text)
        digest_text = call_ai(
            prompt=user_prompt,
            model=resolved_model,
            max_tokens=settings.ai.max_tokens,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            system=digest_cfg.system,
        )
        if digest_text:
            save_digest(DigestResult(
                date=date,
                digest=digest_text,
                generated_at=datetime.now(timezone.utc),
            ))
            logger.info("日报摘要生成完成 [%s]", date)
        else:
            logger.warning("日报摘要 AI 返回空结果 [%s]", date)

    return results
