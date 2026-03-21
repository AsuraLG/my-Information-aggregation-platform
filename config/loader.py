from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent


# ── 标签配置 ────────────────────────────────────────────────

class TagConfig(BaseModel):
    id: str
    desc: str
    order: int = 999  # 展示排序，数值越小越靠前


class TagsConfig(BaseModel):
    tags: list[TagConfig]


# ── 信息源配置 ──────────────────────────────────────────────

class SourceConfig(BaseModel):
    id: str
    type: str  # "rss" | "github_trending"
    tags: list[str]
    schedule: str  # cron 表达式
    desc: str = ""  # 展示用描述，为空时回退到 id
    order: int = 999  # 展示排序，数值越小越靠前

    # RSS 专用
    url: Optional[str] = None

    # GitHub Trending 专用
    language: Optional[str] = None
    period: Optional[str] = "daily"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("rss", "github_trending"):
            raise ValueError(f"不支持的信息源类型: {v}，仅支持 rss / github_trending")
        return v


class SourcesConfig(BaseModel):
    sources: list[SourceConfig]


# ── 调度配置 ────────────────────────────────────────────────

class ScheduleConfig(BaseModel):
    analysis_schedule: str  # cron 表达式


# ── Prompt 配置 ─────────────────────────────────────────────

class PromptTemplate(BaseModel):
    system: str
    user: str


class PromptsConfig(BaseModel):
    default: PromptTemplate
    tags: dict[str, PromptTemplate] = {}
    digest: PromptTemplate = PromptTemplate(
        system="你是一个信息聚合助手。请根据以下各标签的整合摘要，生成一段简洁的今日综合摘要（100-200字），概括今天最值得关注的内容，语言简洁，适合快速浏览。",
        user="日期：{date}\n\n以下是今日各标签的整合摘要：\n{summaries_text}\n\n请生成今日综合摘要：",
    )


# ── AI 配置 ─────────────────────────────────────────────────

class AIConfig(BaseModel):
    provider_type: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 1024
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in ("anthropic", "openai"):
            raise ValueError(f"不支持的 AI provider_type: {v}，仅支持 anthropic / openai")
        return v


class ResolvedAIConfig(BaseModel):
    provider_type: str
    model: str
    max_tokens: int
    api_key: str
    base_url: Optional[str] = None


# ── 存储配置 ────────────────────────────────────────────────

class StorageConfig(BaseModel):
    data_dir: str = "data"


# ── 发布配置 ────────────────────────────────────────────────

class PublishConfig(BaseModel):
    output_dir: str = "output"
    github_remote: str = "origin"
    github_branch: str = "gh-pages"
    site_title: str = "我的信息聚合"
    site_description: str = ""


# ── 全局设置 ────────────────────────────────────────────────

class SettingsConfig(BaseModel):
    ai: AIConfig = AIConfig()
    storage: StorageConfig = StorageConfig()
    publish: PublishConfig = PublishConfig()


# ── 加载函数 ────────────────────────────────────────────────

def _load_yaml(filename: str) -> dict:
    path = CONFIG_DIR / filename
    if not path.exists():
        logger.error("配置文件不存在: %s", path)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_tags() -> TagsConfig:
    try:
        return TagsConfig(**_load_yaml("tags.yaml"))
    except Exception as e:
        logger.error("tags.yaml 配置错误: %s", e)
        sys.exit(1)


def validate_tags(tags_cfg: TagsConfig, sources_cfg: SourcesConfig) -> None:
    """校验 sources.yaml 中引用的 tag id 均在 tags.yaml 中定义"""
    valid_ids = {t.id for t in tags_cfg.tags}
    for src in sources_cfg.sources:
        for tag_id in src.tags:
            if tag_id not in valid_ids:
                logger.error(
                    "信息源 [%s] 引用了未定义的标签 id: %s（请在 tags.yaml 中添加）",
                    src.id, tag_id,
                )
                sys.exit(1)


def load_sources() -> SourcesConfig:
    try:
        return SourcesConfig(**_load_yaml("sources.yaml"))
    except Exception as e:
        logger.error("sources.yaml 配置错误: %s", e)
        sys.exit(1)


def load_schedule() -> ScheduleConfig:
    try:
        return ScheduleConfig(**_load_yaml("schedule.yaml"))
    except Exception as e:
        logger.error("schedule.yaml 配置错误: %s", e)
        sys.exit(1)


def load_prompts() -> PromptsConfig:
    try:
        return PromptsConfig(**_load_yaml("prompts.yaml"))
    except Exception as e:
        logger.error("prompts.yaml 配置错误: %s", e)
        sys.exit(1)


def load_settings() -> SettingsConfig:
    try:
        return SettingsConfig(**_load_yaml("settings.yaml"))
    except Exception as e:
        logger.error("settings.yaml 配置错误: %s", e)
        sys.exit(1)


def _get_env_int(name: str) -> int | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        logger.error("环境变量 %s 必须是整数，当前值: %s", name, value)
        return None


def resolve_ai_config(settings: SettingsConfig) -> ResolvedAIConfig | None:
    provider_type = settings.ai.provider_type or os.environ.get("INFO_AGG_AI_PROVIDER_TYPE") or None
    model = settings.ai.model or os.environ.get("INFO_AGG_AI_MODEL") or None
    api_key = settings.ai.api_key or os.environ.get("INFO_AGG_AI_API_KEY") or None
    base_url = settings.ai.base_url or os.environ.get("INFO_AGG_AI_BASE_URL") or None
    max_tokens = settings.ai.max_tokens
    env_max_tokens = _get_env_int("INFO_AGG_AI_MAX_TOKENS")
    if settings.ai.max_tokens == AIConfig.model_fields["max_tokens"].default and env_max_tokens is not None:
        max_tokens = env_max_tokens

    if not provider_type:
        logger.error(
            "未配置 AI provider_type（settings.yaml ai.provider_type 或 INFO_AGG_AI_PROVIDER_TYPE 环境变量）"
        )
        return None
    if provider_type not in ("anthropic", "openai"):
        logger.error("不支持的 AI provider_type: %s", provider_type)
        return None
    if not model:
        logger.error("未配置 AI 模型（settings.yaml ai.model 或 INFO_AGG_AI_MODEL 环境变量）")
        return None
    if not api_key:
        logger.error("未配置 API Key（settings.yaml ai.api_key 或 INFO_AGG_AI_API_KEY 环境变量）")
        return None

    return ResolvedAIConfig(
        provider_type=provider_type,
        model=model,
        max_tokens=max_tokens,
        api_key=api_key,
        base_url=base_url,
    )
