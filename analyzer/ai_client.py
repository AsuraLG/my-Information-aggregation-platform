from __future__ import annotations

import logging
import re

import anthropic
from openai import APIError as OpenAIAPIError
from openai import OpenAI

logger = logging.getLogger(__name__)


def _strip_thinking(text: str) -> str:
    return re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL).strip()


def _call_anthropic(
    prompt: str,
    model: str,
    max_tokens: int,
    api_key: str,
    base_url: str | None = None,
    system: str | None = None,
) -> str:
    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    client = anthropic.Anthropic(**kwargs)
    create_kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    if system:
        create_kwargs["system"] = system
    message = client.messages.create(**create_kwargs)
    for block in message.content:
        if block.type == "text":
            return _strip_thinking(block.text)
    return ""


def _call_openai(
    prompt: str,
    model: str,
    max_tokens: int,
    api_key: str,
    base_url: str | None = None,
    system: str | None = None,
) -> str:
    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    client = OpenAI(**kwargs)
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )
    content = response.choices[0].message.content or ""
    return _strip_thinking(content)


def call_ai(
    provider_type: str,
    prompt: str,
    model: str,
    max_tokens: int,
    api_key: str | None = None,
    base_url: str | None = None,
    system: str | None = None,
) -> str:
    """按 provider_type 调用对应 AI API，返回生成的文本内容；失败时返回空字符串"""
    if not api_key:
        logger.error("未配置 api_key（settings.yaml ai.api_key 或 INFO_AGG_AI_API_KEY 环境变量）")
        return ""

    try:
        if provider_type == "anthropic":
            return _call_anthropic(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url=base_url,
                system=system,
            )
        if provider_type == "openai":
            return _call_openai(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url=base_url,
                system=system,
            )
        logger.error("不支持的 AI provider_type: %s", provider_type)
        return ""
    except anthropic.APIStatusError as e:
        logger.error("Anthropic API 错误 [%s]: %s", e.status_code, e.message)
        return ""
    except OpenAIAPIError as e:
        logger.error("OpenAI API 错误: %s", e)
        return ""
    except Exception as e:
        logger.error("AI 调用失败: %s", e)
        return ""
