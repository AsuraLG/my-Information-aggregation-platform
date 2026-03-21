from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from config.loader import PromptTemplate, PromptsConfig
from storage.models import UnifiedItem


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
        published_at=datetime(2026, 3, 21, 10, 0, 0, tzinfo=timezone.utc),
        tags=tags,
        raw_data={"id": item_id},
    )


def _make_prompts_cfg() -> PromptsConfig:
    return PromptsConfig(
        default=PromptTemplate(
            system="系统：{date}|{tag}|{source_count}",
            user=(
                "日期={date}\n"
                "标签={tag}\n"
                "来源数={source_count}\n"
                "来源={source_ids_text}\n"
                "条目数={item_count}\n"
                "内容:\n{items_text}"
            ),
        )
    )


def test_build_prompt_supports_multi_source_tag_only_summary() -> None:
    from analyzer.prompt_builder import build_prompt

    prompts_cfg = _make_prompts_cfg()
    items = [
        _make_item("1", "src_a", ["AI"], title="第一条", content="第一条内容"),
        _make_item("2", "src_b", ["AI"], title="第二条", content="第二条内容"),
    ]

    system_prompt, user_prompt = build_prompt(
        items=items,
        date="2026-03-21",
        tag="AI",
        prompts_cfg=prompts_cfg,
        source_ids=["src_a", "src_b"],
    )

    assert system_prompt == "系统：2026-03-21|AI|2"
    assert "标签=AI" in user_prompt
    assert "来源数=2" in user_prompt
    assert "来源=src_a、src_b" in user_prompt
    assert "条目数=2" in user_prompt
    assert "第一条" in user_prompt
    assert "第二条" in user_prompt


def test_run_analysis_groups_by_tag_and_keeps_source_aggregation() -> None:
    from analyzer.summarizer import run_analysis

    prompts_cfg = _make_prompts_cfg()
    settings = MagicMock()
    settings.ai.model = "test-model"
    settings.ai.api_key = "test-key"
    settings.ai.base_url = None
    settings.ai.max_tokens = 512

    items = [
        _make_item("1", "src_a", ["AI", "python"], title="A1"),
        _make_item("2", "src_b", ["AI"], title="A2"),
        _make_item("3", "src_a", ["python"], title="P1"),
    ]

    call_ai_results = iter(["AI摘要", "Python摘要", "日报摘要"])

    with patch("analyzer.summarizer.load_settings", return_value=settings), \
         patch("analyzer.summarizer.load_prompts", return_value=prompts_cfg), \
         patch("analyzer.summarizer.load_items", return_value=items), \
         patch("analyzer.summarizer.call_ai", side_effect=lambda **_: next(call_ai_results)) as mock_call_ai, \
         patch("analyzer.summarizer.save_summaries") as mock_save_summaries, \
         patch("analyzer.summarizer.save_digest") as mock_save_digest:
        results = run_analysis("2026-03-21")

    assert len(results) == 2
    assert {result.tag for result in results} == {"AI", "python"}

    by_tag = {result.tag: result for result in results}
    assert by_tag["AI"].item_count == 2
    assert by_tag["AI"].source_ids == ["src_a", "src_b"]
    assert by_tag["AI"].source_count == 2

    assert by_tag["python"].item_count == 2
    assert by_tag["python"].source_ids == ["src_a"]
    assert by_tag["python"].source_count == 1

    mock_save_summaries.assert_called_once()
    saved_results = mock_save_summaries.call_args.args[0]
    assert len(saved_results) == 2

    mock_save_digest.assert_called_once()
    digest_result = mock_save_digest.call_args.args[0]
    assert digest_result.date == "2026-03-21"
    assert digest_result.digest == "日报摘要"

    assert mock_call_ai.call_count == 3
    first_prompt = mock_call_ai.call_args_list[0].kwargs["prompt"]
    second_prompt = mock_call_ai.call_args_list[1].kwargs["prompt"]
    digest_prompt = mock_call_ai.call_args_list[2].kwargs["prompt"]

    assert "来源=src_a、src_b" in first_prompt or "来源=src_a、src_b" in second_prompt
    assert "来源数=2" in first_prompt or "来源数=2" in second_prompt
    assert "【AI】" in digest_prompt
    assert "【python】" in digest_prompt
