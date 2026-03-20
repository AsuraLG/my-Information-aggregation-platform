from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

from collector.base import BaseCollector, RawItem

logger = logging.getLogger(__name__)

_BASE_URL = "https://github.com/trending"
_TIMEOUT = 15


class GitHubTrendingCollector(BaseCollector):
    """GitHub Trending 页面采集器（无官方 API，解析 HTML）"""

    def __init__(self, source_id: str, language: str = "", period: str = "daily") -> None:
        super().__init__(source_id)
        self.language = language
        self.period = period  # daily / weekly / monthly

    def fetch(self) -> list[RawItem]:
        url = f"{_BASE_URL}/{self.language}" if self.language else _BASE_URL
        params = {"since": self.period}
        try:
            resp = requests.get(url, params=params, timeout=_TIMEOUT, headers={
                "User-Agent": "Mozilla/5.0 (compatible; info-aggregator/1.0)"
            })
            resp.raise_for_status()
        except Exception as e:
            logger.warning("GitHub Trending 请求失败 [%s]: %s", self.source_id, e)
            return []

        try:
            return self._parse(resp.text)
        except Exception as e:
            # TODO: 考虑缓存上次成功结果
            logger.warning("GitHub Trending 解析失败 [%s] selector=article.Box-row: %s", self.source_id, e)
            return []

    def _parse(self, html: str) -> list[RawItem]:
        soup = BeautifulSoup(html, "html.parser")
        repos = soup.select("article.Box-row")
        if not repos:
            logger.warning("GitHub Trending 未找到仓库列表 [%s]，页面结构可能已变更", self.source_id)
            return []

        items = []
        for repo in repos:
            try:
                # 仓库名
                name_tag = repo.select_one("h2 a")
                if not name_tag:
                    continue
                repo_path = name_tag.get("href", "").strip("/")
                name = repo_path.replace("/", " / ")
                repo_url = f"https://github.com/{repo_path}"

                # 描述
                desc_tag = repo.select_one("p")
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                # Star 数
                stars_tag = repo.select_one("a[href$='/stargazers']")
                stars = stars_tag.get_text(strip=True) if stars_tag else ""

                # 语言
                lang_tag = repo.select_one("span[itemprop='programmingLanguage']")
                lang = lang_tag.get_text(strip=True) if lang_tag else ""

                items.append(RawItem(
                    source_id=self.source_id,
                    raw_data={
                        "name": name,
                        "url": repo_url,
                        "description": description,
                        "stars": stars,
                        "language": lang,
                    }
                ))
            except Exception as e:
                logger.warning("GitHub Trending 单条解析失败 [%s]: %s", self.source_id, e)
                continue

        logger.info("GitHub Trending 采集完成 [%s]: %d 条", self.source_id, len(items))
        return items
