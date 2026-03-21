from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from storage.models import DigestResult, UnifiedItem


# ── helpers ─────────────────────────────────────────────────────────────────


def _make_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.publish.output_dir = str(tmp_path / "output")
    settings.publish.site_title = "测试站点"
    settings.publish.site_description = "测试描述"
    return settings


def _make_digest(date: str = "2026-03-21", digest: str = "今日综合摘要内容") -> DigestResult:
    return DigestResult(
        date=date,
        digest=digest,
        generated_at=datetime(2026, 3, 21, 10, 0, 0, tzinfo=timezone.utc),
    )




def _make_item(
    item_id: str,
    source_id: str,
    tags: list[str],
    title: str = "标题",
    content: str = "内容",
) -> UnifiedItem:
    return UnifiedItem(
        id=item_id,
        source_id=source_id,
        title=title,
        content=content,
        url=f"https://example.com/{item_id}",
        published_at=datetime(2026, 3, 21, 9, 0, 0, tzinfo=timezone.utc),
        tags=tags,
        raw_data={},
    )


# ── Step 1: DigestResult model ───────────────────────────────────────────────

def test_digest_result_fields():
    d = _make_digest()
    assert d.date == "2026-03-21"
    assert d.digest == "今日综合摘要内容"
    assert d.generated_at.tzinfo is not None


def test_digest_result_json_roundtrip():
    d = _make_digest()
    json_str = d.model_dump_json()
    d2 = DigestResult.model_validate_json(json_str)
    assert d2.date == d.date
    assert d2.digest == d.digest


# ── Step 2: save_digest / load_digest ────────────────────────────────────────

def test_save_and_load_digest(tmp_path: Path):
    with patch("storage.repository._data_dir", return_value=tmp_path):
        from storage.repository import save_digest, load_digest
        d = _make_digest()
        save_digest(d)

        loaded = load_digest("2026-03-21")
        assert loaded is not None
        assert loaded.date == "2026-03-21"
        assert loaded.digest == "今日综合摘要内容"


def test_load_digest_missing(tmp_path: Path):
    with patch("storage.repository._data_dir", return_value=tmp_path):
        from storage.repository import load_digest
        result = load_digest("2026-03-21")
        assert result is None


def test_save_digest_creates_dir(tmp_path: Path):
    with patch("storage.repository._data_dir", return_value=tmp_path):
        from storage.repository import save_digest
        d = _make_digest()
        save_digest(d)
        assert (tmp_path / "digest" / "2026-03-21.json").exists()


# ── Step 3: renderer passes digest_html to templates ─────────────────────────

def _make_tags_cfg(tags: list[dict]):
    from config.loader import TagConfig, TagsConfig
    return TagsConfig(tags=[TagConfig(**t) for t in tags])


def _make_sources_cfg(sources: list[dict]):
    from config.loader import SourceConfig, SourcesConfig
    return SourcesConfig(sources=[SourceConfig(**s) for s in sources])


def _make_summary(tag: str, source_ids: list[str]) -> MagicMock:
    s = MagicMock()
    s.tag = tag
    s.source_ids = source_ids
    s.source_count = len(source_ids)
    s.summary = "摘要内容"
    s.item_count = 3
    return s


def test_renderer_shows_digest(tmp_path: Path):
    """当 digest 存在时，页面顶部应包含今日摘要区块"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])
    digest = _make_digest(digest="**今日要点**：AI 领域有重大进展。")

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=["2026-03-21"]), \
         patch("publisher.renderer.load_summaries", return_value=[_make_summary("AI", ["src1"])]), \
         patch("publisher.renderer.load_digest", return_value=digest):
        from publisher.renderer import render
        render("2026-03-21")

    home_html = (tmp_path / "output" / "index.html").read_text()
    date_html = (tmp_path / "output" / "2026-03-21" / "index.html").read_text()

    assert "今日摘要" in home_html
    assert "今日摘要" in date_html
    # markdown 加粗应被转换为 <strong>
    assert "<strong>" in home_html


def test_renderer_no_digest(tmp_path: Path):
    """当 digest 不存在时，页面正常渲染，不显示今日摘要区块"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=["2026-03-21"]), \
         patch("publisher.renderer.load_summaries", return_value=[_make_summary("AI", ["src1"])]), \
         patch("publisher.renderer.load_digest", return_value=None):
        from publisher.renderer import render
        render("2026-03-21")

    home_html = (tmp_path / "output" / "index.html").read_text()
    date_html = (tmp_path / "output" / "2026-03-21" / "index.html").read_text()

    assert "今日摘要" not in home_html
    assert "今日摘要" not in date_html
    # 页面其他内容正常渲染
    assert "人工智能" in home_html


# ── Step 4: PromptsConfig digest field ───────────────────────────────────────

def test_prompts_config_has_digest():
    from config.loader import PromptsConfig, PromptTemplate
    cfg = PromptsConfig(
        default=PromptTemplate(system="sys", user="usr"),
    )
    assert hasattr(cfg, "digest")
    assert cfg.digest.system
    assert "{date}" in cfg.digest.user
    assert "{summaries_text}" in cfg.digest.user


def test_prompts_config_digest_overridable():
    from config.loader import PromptsConfig, PromptTemplate
    custom = PromptTemplate(system="custom sys", user="custom {date} {summaries_text}")
    cfg = PromptsConfig(
        default=PromptTemplate(system="sys", user="usr"),
        digest=custom,
    )
    assert cfg.digest.system == "custom sys"


def test_build_prompt_uses_multi_source_tag_context():
    from analyzer.prompt_builder import build_prompt
    from config.loader import PromptTemplate, PromptsConfig

    prompts_cfg = PromptsConfig(
        default=PromptTemplate(
            system="系统：{tag} / {source_count} / {source_ids_text}",
            user="用户：{date} {tag} {source_count} {source_ids_text}\n{items_text}",
        ),
    )
    items = [
        _make_item("item-1", "src1", ["AI"], title="第一条", content="来自来源一"),
        _make_item("item-2", "src2", ["AI"], title="第二条", content="来自来源二"),
    ]

    system_prompt, user_prompt = build_prompt(
        items=items,
        date="2026-03-21",
        tag="AI",
        prompts_cfg=prompts_cfg,
        source_ids=["src1", "src2"],
    )

    assert system_prompt == "系统：AI / 2 / src1、src2"
    assert "用户：2026-03-21 AI 2 src1、src2" in user_prompt
    assert "来自「{source_id}」" not in user_prompt
    assert "【第一条】" in user_prompt
    assert "【第二条】" in user_prompt


def test_run_analysis_groups_items_by_tag_only():
    from analyzer.summarizer import run_analysis

    settings = MagicMock()
    settings.ai.provider_type = "anthropic"
    settings.ai.model = "test-model"
    settings.ai.api_key = "test-key"
    settings.ai.base_url = None
    settings.ai.max_tokens = 512

    prompts_cfg = MagicMock()
    prompts_cfg.digest.system = "digest-system"
    prompts_cfg.digest.user = "日期：{date}\n\n{summaries_text}"

    items = [
        _make_item("item-1", "src1", ["AI"], title="第一条", content="AI 内容一"),
        _make_item("item-2", "src2", ["AI"], title="第二条", content="AI 内容二"),
        _make_item("item-3", "src3", ["Python"], title="第三条", content="Python 内容"),
    ]

    ai_outputs = ["AI 标签摘要", "Python 标签摘要", "今日综合摘要"]

    with patch("analyzer.summarizer.load_settings", return_value=settings), \
         patch("analyzer.summarizer.load_prompts", return_value=prompts_cfg), \
         patch("analyzer.summarizer.load_items", return_value=items), \
         patch("analyzer.summarizer.build_prompt") as mock_build_prompt, \
         patch("analyzer.summarizer.call_ai", side_effect=ai_outputs) as mock_call_ai, \
         patch("analyzer.summarizer.save_summaries") as mock_save_summaries, \
         patch("analyzer.summarizer.save_digest") as mock_save_digest:
        mock_build_prompt.side_effect = [
            ("sys-ai", "user-ai"),
            ("sys-python", "user-python"),
        ]

        results = run_analysis("2026-03-21")

    assert len(results) == 2
    assert {result.tag for result in results} == {"AI", "Python"}

    ai_result = next(result for result in results if result.tag == "AI")
    python_result = next(result for result in results if result.tag == "Python")

    assert ai_result.item_count == 2
    assert ai_result.source_ids == ["src1", "src2"]
    assert ai_result.source_count == 2
    assert python_result.item_count == 1
    assert python_result.source_ids == ["src3"]
    assert python_result.source_count == 1

    assert mock_build_prompt.call_count == 2
    first_call = mock_build_prompt.call_args_list[0].kwargs
    second_call = mock_build_prompt.call_args_list[1].kwargs
    assert first_call["tag"] == "AI"
    assert first_call["source_ids"] == ["src1", "src2"]
    assert len(first_call["items"]) == 2
    assert second_call["tag"] == "Python"
    assert second_call["source_ids"] == ["src3"]
    assert len(second_call["items"]) == 1

    assert mock_call_ai.call_count == 3
    digest_prompt = mock_call_ai.call_args_list[-1].kwargs["prompt"]
    assert "【AI】" in digest_prompt
    assert "【Python】" in digest_prompt
    assert "覆盖来源：src1、src2" in digest_prompt
    assert "覆盖来源：src3" in digest_prompt

    mock_save_summaries.assert_called_once()
    mock_save_digest.assert_called_once()
