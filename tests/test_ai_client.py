from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from analyzer.ai_client import _strip_thinking, call_ai


def test_strip_thinking_removes_thinking_block() -> None:
    text = "<thinking>hidden</thinking>最终答案"
    assert _strip_thinking(text) == "最终答案"


def test_call_ai_routes_to_anthropic() -> None:
    with patch("analyzer.ai_client._call_anthropic", return_value="anthropic-result") as mock_call:
        result = call_ai(
            provider_type="anthropic",
            prompt="hello",
            model="claude-test",
            max_tokens=256,
            api_key="test-key",
            system="sys",
        )

    assert result == "anthropic-result"
    assert mock_call.call_args.kwargs["prompt"] == "hello"
    assert mock_call.call_args.kwargs["system"] == "sys"


def test_call_ai_routes_to_openai() -> None:
    with patch("analyzer.ai_client._call_openai", return_value="openai-result") as mock_call:
        result = call_ai(
            provider_type="openai",
            prompt="hello",
            model="gpt-test",
            max_tokens=256,
            api_key="test-key",
            base_url="https://example.com/v1",
        )

    assert result == "openai-result"
    assert mock_call.call_args.kwargs["model"] == "gpt-test"
    assert mock_call.call_args.kwargs["base_url"] == "https://example.com/v1"


def test_call_ai_returns_empty_when_provider_unsupported() -> None:
    result = call_ai(
        provider_type="unknown",
        prompt="hello",
        model="test-model",
        max_tokens=256,
        api_key="test-key",
    )

    assert result == ""


def test_call_ai_returns_empty_when_api_key_missing() -> None:
    result = call_ai(
        provider_type="anthropic",
        prompt="hello",
        model="test-model",
        max_tokens=256,
        api_key=None,
    )

    assert result == ""


def test_call_ai_extracts_openai_message_content() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="<thinking>hidden</thinking>可见内容"))]
    )
    client = MagicMock()
    client.chat.completions.create.return_value = response

    with patch("analyzer.ai_client.OpenAI", return_value=client):
        result = call_ai(
            provider_type="openai",
            prompt="hello",
            model="gpt-test",
            max_tokens=256,
            api_key="test-key",
            system="sys",
        )

    assert result == "可见内容"
    create_kwargs = client.chat.completions.create.call_args.kwargs
    assert create_kwargs["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
    ]


def test_call_ai_extracts_first_anthropic_text_block() -> None:
    message = SimpleNamespace(
        content=[
            SimpleNamespace(type="tool_use", text="ignored"),
            SimpleNamespace(type="text", text="<thinking>hidden</thinking>可见内容"),
        ]
    )
    client = MagicMock()
    client.messages.create.return_value = message

    with patch("analyzer.ai_client.anthropic.Anthropic", return_value=client):
        result = call_ai(
            provider_type="anthropic",
            prompt="hello",
            model="claude-test",
            max_tokens=256,
            api_key="test-key",
            base_url="https://example.com",
        )

    assert result == "可见内容"
    create_kwargs = client.messages.create.call_args.kwargs
    assert create_kwargs["messages"] == [{"role": "user", "content": "hello"}]
    assert create_kwargs["model"] == "claude-test"
    assert create_kwargs["max_tokens"] == 256
