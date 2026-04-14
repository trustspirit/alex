from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from backend.llm.provider_manager import ProviderManager


def test_register_and_list_providers():
    manager = ProviderManager()
    providers = manager.list_providers()
    names = [p.name for p in providers]
    assert "openai" in names
    assert "anthropic" in names
    assert "gemini" in names


def test_get_available_models():
    manager = ProviderManager()
    models = manager.get_models("openai")
    assert len(models) > 0
    assert any("gpt-4o" in m for m in models)


def test_get_models_unknown_provider():
    manager = ProviderManager()
    with pytest.raises(ValueError, match="Unknown provider"):
        manager.get_models("unknown_provider")


def test_get_embed_models_openai():
    manager = ProviderManager()
    embed_models = manager.get_embed_models("openai")
    assert len(embed_models) > 0
    assert "text-embedding-3-small" in embed_models


def test_get_embed_models_anthropic_empty():
    manager = ProviderManager()
    embed_models = manager.get_embed_models("anthropic")
    assert embed_models == []


def test_create_llm_instance():
    manager = ProviderManager()
    with patch("backend.llm.provider_manager.OpenAI") as MockLLM:
        mock_instance = MagicMock()
        MockLLM.return_value = mock_instance
        llm = manager.create_llm("openai", "gpt-4o", api_key="sk-test")
        assert llm is mock_instance


def test_create_llm_anthropic():
    manager = ProviderManager()
    with patch("backend.llm.provider_manager.Anthropic") as MockLLM:
        mock_instance = MagicMock()
        MockLLM.return_value = mock_instance
        llm = manager.create_llm("anthropic", "claude-sonnet-4-6", api_key="sk-ant-test")
        assert llm is mock_instance


def test_create_llm_gemini():
    manager = ProviderManager()
    with patch("backend.llm.provider_manager.Gemini") as MockLLM:
        mock_instance = MagicMock()
        MockLLM.return_value = mock_instance
        llm = manager.create_llm("gemini", "gemini-2.0-flash", api_key="gm-test")
        assert llm is mock_instance


def test_create_llm_unknown_provider():
    manager = ProviderManager()
    with pytest.raises(ValueError, match="Unknown provider"):
        manager.create_llm("unknown", "some-model", api_key="key")


def test_create_embed_model():
    manager = ProviderManager()
    with patch("backend.llm.provider_manager.OpenAIEmbedding") as MockEmbed:
        mock_instance = MagicMock()
        MockEmbed.return_value = mock_instance
        embed = manager.create_embed_model("openai", api_key="sk-test")
        assert embed is mock_instance


def test_create_embed_model_custom_model():
    manager = ProviderManager()
    with patch("backend.llm.provider_manager.OpenAIEmbedding") as MockEmbed:
        mock_instance = MagicMock()
        MockEmbed.return_value = mock_instance
        embed = manager.create_embed_model(
            "openai", api_key="sk-test", model="text-embedding-3-large"
        )
        MockEmbed.assert_called_once_with(
            model="text-embedding-3-large", api_key="sk-test"
        )
        assert embed is mock_instance


def test_create_embed_model_unsupported_provider():
    manager = ProviderManager()
    with pytest.raises(ValueError, match="does not support"):
        manager.create_embed_model("anthropic", api_key="sk-ant-test")
