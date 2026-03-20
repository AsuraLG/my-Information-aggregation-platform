from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


class UnifiedItem(BaseModel):
    """统一格式的信息条目"""
    id: str                      # source_id + url 的 hash
    source_id: str               # 来源信息源 id
    title: str
    content: str                 # 正文或摘要
    url: str
    published_at: datetime       # UTC 时间
    tags: list[str]              # 来自信息源配置的标签
    raw_data: dict               # 保留原始字段，便于调试


class SummaryResult(BaseModel):
    """AI 分析摘要结果"""
    date: str                    # YYYY-MM-DD（UTC）
    tag: str                     # 按标签维度
    source_id: Optional[str]     # 按信息源维度（None 表示跨源汇总）
    summary: str                 # AI 生成的摘要内容
    item_count: int              # 本次分析的条目数
    generated_at: datetime       # UTC 时间
