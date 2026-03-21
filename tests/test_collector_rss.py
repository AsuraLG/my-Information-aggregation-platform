from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from collector.rss import RSSCollector


def _make_response(text: str, content_type: str = "application/rss+xml") -> MagicMock:
    response = MagicMock()
    response.text = text
    response.headers = {"Content-Type": content_type}
    response.raise_for_status.return_value = None
    return response


def test_rss_collector_returns_empty_for_html_response() -> None:
    collector = RSSCollector("xiaoheihe_game_news", "https://example.com/feed")
    response = _make_response("<!DOCTYPE html><html><body>blocked</body></html>", "text/html")

    with patch("collector.rss.requests.get", return_value=response), \
         patch("collector.rss.feedparser.parse") as mock_parse:
        items = collector.fetch()

    assert items == []
    mock_parse.assert_not_called()


def test_rss_collector_returns_empty_for_bozo_feed_without_entries() -> None:
    collector = RSSCollector("xiaoheihe_game_news", "https://example.com/feed")
    response = _make_response("<rss>broken</rss>")
    feed = SimpleNamespace(bozo=True, bozo_exception=Exception("syntax error"), entries=[])

    with patch("collector.rss.requests.get", return_value=response), \
         patch("collector.rss.feedparser.parse", return_value=feed):
        items = collector.fetch()

    assert items == []


def test_rss_collector_parses_entries_from_response_text() -> None:
    collector = RSSCollector("xiaoheihe_game_news", "https://example.com/feed")
    response = _make_response("<rss><channel><item></item></channel></rss>")
    feed = SimpleNamespace(
        bozo=False,
        entries=[
            SimpleNamespace(
                title="标题",
                link="https://example.com/post",
                summary="摘要",
                published="2026-03-21",
                id="item-1",
            )
        ],
    )

    with patch("collector.rss.requests.get", return_value=response), \
         patch("collector.rss.feedparser.parse", return_value=feed) as mock_parse:
        items = collector.fetch()

    assert len(items) == 1
    assert items[0].source_id == "xiaoheihe_game_news"
    assert items[0].raw_data["title"] == "标题"
    assert items[0].raw_data["link"] == "https://example.com/post"
    mock_parse.assert_called_once_with(response.text)
