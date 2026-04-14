from __future__ import annotations

from dataclasses import dataclass

try:
    from llama_index.llms.openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment,misc]

try:
    from llama_index.llms.anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore[assignment,misc]

try:
    from llama_index.llms.gemini import Gemini
except ImportError:  # pragma: no cover
    Gemini = None  # type: ignore[assignment,misc]

try:
    from llama_index.embeddings.openai import OpenAIEmbedding
except ImportError:  # pragma: no cover
    OpenAIEmbedding = None  # type: ignore[assignment,misc]


@dataclass
class LLMProvider:
    name: str
    display_name: str
    models: list[str]
    embed_models: list[str]


PROVIDERS: dict[str, LLMProvider] = {
    "openai": LLMProvider(
        name="openai",
        display_name="OpenAI",
        models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
        embed_models=["text-embedding-3-small", "text-embedding-3-large"],
    ),
    "anthropic": LLMProvider(
        name="anthropic",
        display_name="Anthropic",
        models=["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        embed_models=[],
    ),
    "gemini": LLMProvider(
        name="gemini",
        display_name="Google Gemini",
        models=["gemini-2.0-flash", "gemini-2.0-pro"],
        embed_models=[],
    ),
}

LLM_CONSTRUCTORS = {
    "openai": lambda model, api_key: OpenAI(model=model, api_key=api_key),
    "anthropic": lambda model, api_key: Anthropic(model=model, api_key=api_key),
    "gemini": lambda model, api_key: Gemini(model=model, api_key=api_key),
}


class ProviderManager:
    """Manages LLM and embedding model creation across multiple providers."""

    def list_providers(self) -> list[LLMProvider]:
        """Return all registered LLM providers."""
        return list(PROVIDERS.values())

    def get_models(self, provider_name: str) -> list[str]:
        """Return available LLM model names for the given provider.

        Raises:
            ValueError: If provider_name is not a known provider.
        """
        if provider_name not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name!r}")
        return PROVIDERS[provider_name].models

    def get_embed_models(self, provider_name: str) -> list[str]:
        """Return available embedding model names for the given provider.

        Raises:
            ValueError: If provider_name is not a known provider.
        """
        if provider_name not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name!r}")
        return PROVIDERS[provider_name].embed_models

    def create_llm(self, provider_name: str, model: str, api_key: str) -> object:
        """Create and return a LlamaIndex LLM instance for the given provider.

        Raises:
            ValueError: If provider_name is not a known provider.
        """
        if provider_name not in LLM_CONSTRUCTORS:
            raise ValueError(f"Unknown provider: {provider_name!r}")
        return LLM_CONSTRUCTORS[provider_name](model, api_key)

    def create_embed_model(
        self,
        provider_name: str,
        api_key: str,
        model: str = "text-embedding-3-small",
    ) -> object:
        """Create and return a LlamaIndex embedding model for the given provider.

        Raises:
            ValueError: If the provider does not support embedding models.
        """
        provider = PROVIDERS.get(provider_name)
        if provider is None:
            raise ValueError(f"Unknown provider: {provider_name!r}")
        if not provider.embed_models:
            raise ValueError(
                f"Provider {provider_name!r} does not support embedding models"
            )
        return OpenAIEmbedding(model=model, api_key=api_key)
