from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.loader import TagConfig, SourceConfig, TagsConfig, SourcesConfig


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.publish.output_dir = str(tmp_path / "output")
    settings.publish.site_title = "测试站点"
    settings.publish.site_description = "测试描述"
    return settings


def _make_tags_cfg(tags: list[dict]) -> TagsConfig:
    return TagsConfig(tags=[TagConfig(**t) for t in tags])


def _make_sources_cfg(sources: list[dict]) -> SourcesConfig:
    return SourcesConfig(sources=[SourceConfig(**s) for s in sources])


def _make_summary(
    tag: str,
    source_ids: list[str],
    summary: str = "摘要内容",
    item_count: int = 5,
) -> MagicMock:
    s = MagicMock()
    s.tag = tag
    s.source_ids = source_ids
    s.source_count = len(source_ids)
    s.summary = summary
    s.item_count = item_count
    return s


# ── Step 1: config model order defaults ─────────────────────────────────────

def test_order_default_tag():
    tag = TagConfig(id="AI", desc="人工智能")
    assert tag.order == 999


def test_order_default_source():
    src = SourceConfig(id="src1", type="rss", tags=["AI"], schedule="0 9 * * *")
    assert src.order == 999


def test_order_explicit():
    tag = TagConfig(id="AI", desc="人工智能", order=10)
    assert tag.order == 10


# ── Step 2: backward compat — yaml without order field ──────────────────────

def test_backward_compat_no_order():
    """不含 order 字段的配置加载不报错，order 默认 999"""
    from config.loader import load_tags, load_sources
    tags_cfg = load_tags()
    sources_cfg = load_sources()
    # 所有 tag/source 都有 order 属性（可能是 yaml 中配置的值或默认 999）
    for t in tags_cfg.tags:
        assert isinstance(t.order, int)
    for s in sources_cfg.sources:
        assert isinstance(s.order, int)


# ── Step 3: list_available_dates ─────────────────────────────────────────────

def _make_settings_with_output(output_dir: Path) -> MagicMock:
    """构造仅含 publish.output_dir 的 settings mock"""
    s = MagicMock()
    s.publish.output_dir = str(output_dir)
    return s


def test_list_available_dates(tmp_path: Path):
    summaries_dir = tmp_path / "summaries"
    summaries_dir.mkdir()
    (summaries_dir / "2026-03-20.json").write_text("[]")
    (summaries_dir / "2026-03-19.json").write_text("[]")
    (summaries_dir / "2026-03-18.json").write_text("[]")
    # 应被忽略的文件
    (summaries_dir / "not-a-date.json").write_text("[]")
    (summaries_dir / "2026-03-20.json.tmp").write_text("[]")
    (summaries_dir / "readme.txt").write_text("ignore")

    nonexistent_output = tmp_path / "no_output"
    with patch("storage.repository._data_dir", return_value=tmp_path), \
         patch("config.loader.load_settings",
               return_value=_make_settings_with_output(nonexistent_output)):
        from storage.repository import list_available_dates
        dates = list_available_dates()

    assert dates == ["2026-03-20", "2026-03-19", "2026-03-18"]


def test_list_available_dates_empty(tmp_path: Path):
    nonexistent_output = tmp_path / "no_output"
    with patch("storage.repository._data_dir", return_value=tmp_path), \
         patch("config.loader.load_settings",
               return_value=_make_settings_with_output(nonexistent_output)):
        from storage.repository import list_available_dates
        assert list_available_dates() == []


def test_list_available_dates_no_dir(tmp_path: Path):
    nonexistent = tmp_path / "no_such_dir"
    nonexistent_output = tmp_path / "no_output"
    with patch("storage.repository._data_dir", return_value=nonexistent), \
         patch("config.loader.load_settings",
               return_value=_make_settings_with_output(nonexistent_output)):
        from storage.repository import list_available_dates
        assert list_available_dates() == []


def test_list_available_dates_from_output_dir(tmp_path: Path):
    """来源二：output/{date}/index.html 补充历史日期（无 summaries）"""
    output_dir = tmp_path / "output"
    for d in ["2026-03-17", "2026-03-16"]:
        (output_dir / d).mkdir(parents=True)
        (output_dir / d / "index.html").write_text("<html/>")
    # 不应被识别：无 index.html 或格式不符
    (output_dir / "assets").mkdir()
    (output_dir / "2026-03-15").mkdir()  # 无 index.html

    nonexistent_data = tmp_path / "no_data"
    with patch("storage.repository._data_dir", return_value=nonexistent_data), \
         patch("config.loader.load_settings",
               return_value=_make_settings_with_output(output_dir)):
        from storage.repository import list_available_dates
        dates = list_available_dates()

    assert dates == ["2026-03-17", "2026-03-16"]


def test_list_available_dates_merges_both_sources(tmp_path: Path):
    """来源一和来源二合并去重，按日期降序返回"""
    # 来源一：summaries
    summaries_dir = tmp_path / "summaries"
    summaries_dir.mkdir()
    (summaries_dir / "2026-03-20.json").write_text("[]")
    (summaries_dir / "2026-03-19.json").write_text("[]")

    # 来源二：output（含一个与来源一重叠的日期）
    output_dir = tmp_path / "output"
    for d in ["2026-03-19", "2026-03-17"]:
        (output_dir / d).mkdir(parents=True)
        (output_dir / d / "index.html").write_text("<html/>")

    with patch("storage.repository._data_dir", return_value=tmp_path), \
         patch("config.loader.load_settings",
               return_value=_make_settings_with_output(output_dir)):
        from storage.repository import list_available_dates
        dates = list_available_dates()

    # 去重后降序：20 > 19 > 17
    assert dates == ["2026-03-20", "2026-03-19", "2026-03-17"]


# ── Step 4: ordering logic ───────────────────────────────────────────────────

def test_order_sorting(tmp_path: Path):
    """ordered_summaries 按 tag order 排序，并输出 tag-only 来源说明"""
    from publisher.renderer import _build_ordered_summaries

    tag_id_to_info = {
        "python": ("Python技术", 20),
        "AI": ("人工智能", 10),
    }
    source_id_to_info = {
        "src_b": ("Source B", 20),
        "src_a": ("Source A", 10),
    }
    summaries = [
        _make_summary("python", ["src_b", "src_a"]),
        _make_summary("AI", ["src_a"]),
    ]

    result = _build_ordered_summaries(summaries, tag_id_to_info, source_id_to_info)

    assert result[0]["tag_desc"] == "人工智能"
    assert result[1]["tag_desc"] == "Python技术"
    assert result[1]["source_count"] == 2
    assert result[1]["source_descs"] == ["Source B", "Source A"]
    assert result[1]["sources_label"] == "Source B、Source A"


# ── Step 5: CST timezone ─────────────────────────────────────────────────────

def test_cst_timezone(tmp_path: Path):
    """generated_at 字符串以 CST 结尾，格式为 YYYY-MM-DD HH:MM CST"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=["2026-03-20"]), \
         patch("publisher.renderer.load_summaries", return_value=[_make_summary("AI", ["src1"])]):
        from publisher.renderer import render
        render("2026-03-20")

    home_html = (tmp_path / "output" / "index.html").read_text()
    assert "CST" in home_html
    # 格式验证：包含 YYYY-MM-DD HH:MM CST 模式
    import re
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} CST", home_html)


# ── Step 6: date subdir output ───────────────────────────────────────────────

def test_date_subdir_output(tmp_path: Path):
    """render() 生成 output/{date}/index.html"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=["2026-03-20"]), \
         patch("publisher.renderer.load_summaries", return_value=[_make_summary("AI", ["src1"])]):
        from publisher.renderer import render
        result = render("2026-03-20")

    assert result == tmp_path / "output" / "2026-03-20" / "index.html"
    assert result.exists()


# ── Step 7: home page generated ──────────────────────────────────────────────

def test_home_page_generated(tmp_path: Path):
    """render() 生成 output/index.html"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=["2026-03-20"]), \
         patch("publisher.renderer.load_summaries", return_value=[_make_summary("AI", ["src1"])]):
        from publisher.renderer import render
        render("2026-03-20")

    assert (tmp_path / "output" / "index.html").exists()


# ── Step 8: date nav links ───────────────────────────────────────────────────

def test_date_nav_links(tmp_path: Path):
    """日期页面 HTML 包含前一天/后一天导航链接"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])
    all_dates = ["2026-03-21", "2026-03-20", "2026-03-19"]

    def mock_load_summaries(date: str):
        return [_make_summary("AI", ["src1"])]

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=all_dates), \
         patch("publisher.renderer.load_summaries", side_effect=mock_load_summaries):
        from publisher.renderer import render
        render("2026-03-20")

    html = (tmp_path / "output" / "2026-03-20" / "index.html").read_text()
    assert "../2026-03-19/index.html" in html  # prev (older)
    assert "../2026-03-21/index.html" in html  # next (newer)


# ── Step 9: date nav boundary ────────────────────────────────────────────────

def test_date_nav_boundary(tmp_path: Path):
    """最早日期无 prev_date，最新日期无 next_date"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])
    all_dates = ["2026-03-21", "2026-03-19"]

    def mock_load_summaries(date: str):
        return [_make_summary("AI", ["src1"])]

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=all_dates), \
         patch("publisher.renderer.load_summaries", side_effect=mock_load_summaries):
        from publisher.renderer import render
        render("2026-03-21")

    newest_html = (tmp_path / "output" / "2026-03-21" / "index.html").read_text()
    oldest_html = (tmp_path / "output" / "2026-03-19" / "index.html").read_text()

    # 最新日期：有 prev（更早），无 next（更新）
    assert "../2026-03-19/index.html" in newest_html
    assert "../2026-03-21/index.html" not in newest_html

    # 最早日期：有 next（更新），无 prev（更早）
    assert "../2026-03-21/index.html" in oldest_html
    assert "../2026-03-19/index.html" not in oldest_html


# ── Step 10: full rebuild ────────────────────────────────────────────────────

def test_full_rebuild(tmp_path: Path):
    """render() 全量重建：所有历史日期子目录均被生成"""
    settings = _make_settings(tmp_path)
    tags_cfg = _make_tags_cfg([{"id": "AI", "desc": "人工智能", "order": 10}])
    sources_cfg = _make_sources_cfg([
        {"id": "src1", "type": "rss", "tags": ["AI"], "schedule": "0 9 * * *", "desc": "Source 1", "order": 10}
    ])
    all_dates = ["2026-03-20", "2026-03-19", "2026-03-18"]

    def mock_load_summaries(date: str):
        return [_make_summary("AI", ["src1"])]

    with patch("publisher.renderer.load_settings", return_value=settings), \
         patch("publisher.renderer.load_tags", return_value=tags_cfg), \
         patch("publisher.renderer.load_sources", return_value=sources_cfg), \
         patch("publisher.renderer.list_available_dates", return_value=all_dates), \
         patch("publisher.renderer.load_summaries", side_effect=mock_load_summaries):
        from publisher.renderer import render
        render("2026-03-20")

    for d in all_dates:
        assert (tmp_path / "output" / d / "index.html").exists(), f"缺少 {d} 页面"
