from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class RawItem(BaseModel):
    """采集器输出的原始数据，不做标准化"""
    source_id: str
    raw_data: dict[str, Any]


class BaseCollector(ABC):
    """所有采集器的基类"""

    def __init__(self, source_id: str) -> None:
        self.source_id = source_id

    @abstractmethod
    def fetch(self) -> list[RawItem]:
        """拉取原始数据，失败时返回空列表，不抛异常"""
        ...
