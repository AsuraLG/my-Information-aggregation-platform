from __future__ import annotations

from unittest.mock import MagicMock, patch

from config.loader import AIConfig, SettingsConfig, resolve_ai_config


def test_resolve_ai_config_prefers_settings_over_env() -> None:
    settings = SettingsConfig(
        ai=AIConfig(
            provider_type="anthropic",
            model="claude-test",
            max_tokens=2048,
            api_key="settings-key",
            base_url="https://settings.example",
        )
    )

    env = {
        "INFO_AGG_AI_PROVIDER_TYPE": "openai",
        "INFO_AGG_AI_MODEL": "gpt-test",
        "INFO_AGG_AI_API_KEY": "env-key",
        "INFO_AGG_AI_BASE_URL": "https://env.example",
        "INFO_AGG_AI_MAX_TOKENS": "1024",
    }

    with patch.dict("os.environ", env, clear=True):
        resolved = resolve_ai_config(settings)

    assert resolved is not None
    assert resolved.provider_type == "anthropic"
    assert resolved.model == "claude-test"
    assert resolved.api_key == "settings-key"
    assert resolved.base_url == "https://settings.example"
    assert resolved.max_tokens == 2048


def test_resolve_ai_config_uses_env_when_settings_missing() -> None:
    settings = SettingsConfig(ai=AIConfig())

    env = {
        "INFO_AGG_AI_PROVIDER_TYPE": "openai",
        "INFO_AGG_AI_MODEL": "gpt-5-mini",
        "INFO_AGG_AI_API_KEY": "env-key",
        "INFO_AGG_AI_BASE_URL": "https://env.example/v1",
        "INFO_AGG_AI_MAX_TOKENS": "4096",
    }

    with patch.dict("os.environ", env, clear=True):
        resolved = resolve_ai_config(settings)

    assert resolved is not None
    assert resolved.provider_type == "openai"
    assert resolved.model == "gpt-5-mini"
    assert resolved.api_key == "env-key"
    assert resolved.base_url == "https://env.example/v1"
    assert resolved.max_tokens == 4096


def test_resolve_ai_config_keeps_settings_max_tokens_when_explicit() -> None:
    settings = SettingsConfig(
        ai=AIConfig(
            provider_type="openai",
            model="gpt-test",
            max_tokens=512,
            api_key="settings-key",
        )
    )

    with patch.dict("os.environ", {"INFO_AGG_AI_MAX_TOKENS": "4096"}, clear=True):
        resolved = resolve_ai_config(settings)

    assert resolved is not None
    assert resolved.max_tokens == 512


def test_resolve_ai_config_returns_none_when_provider_missing() -> None:
    settings = SettingsConfig(
        ai=AIConfig(
            model="claude-test",
            api_key="test-key",
        )
    )

    with patch.dict("os.environ", {}, clear=True):
        resolved = resolve_ai_config(settings)

    assert resolved is None


def test_resolve_ai_config_returns_none_when_env_max_tokens_invalid() -> None:
    settings = SettingsConfig(ai=AIConfig())

    env = {
        "INFO_AGG_AI_PROVIDER_TYPE": "anthropic",
        "INFO_AGG_AI_MODEL": "claude-test",
        "INFO_AGG_AI_API_KEY": "env-key",
        "INFO_AGG_AI_MAX_TOKENS": "not-an-int",
    }

    with patch.dict("os.environ", env, clear=True):
        resolved = resolve_ai_config(settings)

    assert resolved is not None
    assert resolved.max_tokens == 1024
