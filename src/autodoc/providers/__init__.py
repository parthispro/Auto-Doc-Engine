"""
__init__.py — Provider registry and factory.

Usage:
    from autodoc.providers import get_provider
    provider = get_provider(config)
"""

from __future__ import annotations

from autodoc.config import Config
from autodoc.providers.base import BaseProvider, ProviderError
from autodoc.providers.gemini import GeminiProvider
from autodoc.providers.huggingface import HuggingFaceProvider
from autodoc.providers.ollama import OllamaProvider


def get_provider(cfg: Config) -> BaseProvider:
    """
    Instantiate and return the correct provider based on config.

    Priority / fallback chain when provider == "auto":
      1. Gemini (if GEMINI_API_KEY set)
      2. HuggingFace (if HF_API_KEY set)
      3. Ollama (local, always last resort)
    """
    provider_name = (cfg.provider or "auto").lower()

    if provider_name == "gemini":
        if not cfg.gemini_api_key:
            raise ProviderError(
                "GEMINI_API_KEY is not set. Add it to .env or pass --api-key."
            )
        return GeminiProvider(api_key=cfg.gemini_api_key, model=cfg.gemini_model)

    if provider_name == "huggingface":
        if not cfg.hf_api_key:
            raise ProviderError(
                "HF_API_KEY is not set. Add it to .env or pass --api-key."
            )
        return HuggingFaceProvider(
            api_key=cfg.hf_api_key,
            model=cfg.hf_model,
            endpoint=cfg.hf_endpoint,
        )

    if provider_name == "ollama":
        return OllamaProvider(host=cfg.ollama_host, model=cfg.ollama_model)

    if provider_name == "auto":
        # Cascading fallback
        if cfg.gemini_api_key:
            return GeminiProvider(api_key=cfg.gemini_api_key, model=cfg.gemini_model)
        if cfg.hf_api_key:
            return HuggingFaceProvider(
                api_key=cfg.hf_api_key,
                model=cfg.hf_model,
                endpoint=cfg.hf_endpoint,
            )
        # Last resort: local Ollama
        return OllamaProvider(host=cfg.ollama_host, model=cfg.ollama_model)

    raise ProviderError(
        f"Unknown provider '{provider_name}'. "
        "Valid choices: gemini, huggingface, ollama, auto"
    )


__all__ = [
    "get_provider",
    "BaseProvider",
    "ProviderError",
    "GeminiProvider",
    "HuggingFaceProvider",
    "OllamaProvider",
]
