from __future__ import annotations

import logging
import re

import anthropic

logger = logging.getLogger(__name__)


def call_ai(
    prompt: str,
    model: str,
    max_tokens: int,
    api_key: str | None = None,
    base_url: str | None = None,
    system: str | None = None,
) -> str:
    """调用 Anthropic 兼容 API，返回生成的文本内容；失败时返回空字符串"""
    if not api_key:
        logger.error("未配置 api_key（settings.yaml ai.api_key 或 INFO_AGG_AI_API_KEY 环境变量）")
        return ""

    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    try:
        client = anthropic.Anthropic(**kwargs)
        create_kwargs: dict = dict(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            create_kwargs["system"] = system
        message = client.messages.create(**create_kwargs)
        # 遍历 content 块，取第一个 text 类型（跳过 thinking 块）
        for block in message.content:
            if block.type == "text":
                # 剥离模型在文本中内联输出的 <thinking>...</thinking> 标签
                text = re.sub(r"<thinking>.*?</thinking>", "", block.text, flags=re.DOTALL)
                return text.strip()
        return ""
    except anthropic.APIStatusError as e:
        logger.error("Anthropic API 错误 [%s]: %s", e.status_code, e.message)
        return ""
    except Exception as e:
        logger.error("AI 调用失败: %s", e)
        return ""
