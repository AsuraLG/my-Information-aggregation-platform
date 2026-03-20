from __future__ import annotations

import logging
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


class TagsConfig(BaseModel):
    tags: list[TagConfig]


# ── 信息源配置 ──────────────────────────────────────────────

class SourceConfig(BaseModel):
    id: str
    type: str  # "rss" | "github_trending"
    tags: list[str]
    schedule: str  # cron 表达式
    desc: str = ""  # 展示用描述，为空时回退到 id

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


# ── AI 配置 ─────────────────────────────────────────────────

class AIConfig(BaseModel):
    model: Optional[str] = None     # 优先使用；为 None 时回退到 INFO_AGG_AI_MODEL 环境变量，最终默认 claude-3-5-haiku-20241022
    max_tokens: int = 1024
    api_key: Optional[str] = None   # 优先使用；为 None 时回退到 INFO_AGG_AI_API_KEY 环境变量
    base_url: Optional[str] = None  # 优先使用；为 None 时回退到 INFO_AGG_AI_BASE_URL 环境变量


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
