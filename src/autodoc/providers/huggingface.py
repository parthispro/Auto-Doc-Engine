"""
huggingface.py — Hugging Face Inference API provider.

Supports both:
  - HF Inference API (serverless, free tier)
  - HF Dedicated Inference Endpoints (custom URL via HF_ENDPOINT)

Model default: mistralai/Mistral-7B-Instruct-v0.3
"""

from __future__ import annotations

import json
import requests
from autodoc.providers.base import BaseProvider, ProviderError

_HF_API_BASE = "https://api-inference.huggingface.co/models"
_CHAT_ENDPOINT = "https://api-inference.huggingface.co/v1/chat/completions"
_TIMEOUT = 120  # seconds


class HuggingFaceProvider(BaseProvider):
    name = "huggingface"

    def __init__(
        self,
        api_key: str,
        model: str = "mistralai/Mistral-7B-Instruct-v0.3",
        endpoint: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        # Custom endpoint overrides the serverless API
        self._endpoint = endpoint or _CHAT_ENDPOINT
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _build_chat_payload(
        self, system_prompt: str, user_prompt: str, temperature: float
    ) -> dict:
        return {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 8192,
            "stream": False,
        }

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        payload = self._build_chat_payload(system_prompt, user_prompt, temperature)

        try:
            resp = requests.post(
                self._endpoint,
                headers=self._headers,
                json=payload,
                timeout=_TIMEOUT,
            )
        except requests.exceptions.ConnectionError as exc:
            raise ProviderError(f"HuggingFace connection error: {exc}") from exc
        except requests.exceptions.Timeout:
            raise ProviderError("HuggingFace request timed out.")

        if resp.status_code == 503:
            # Model loading — parse estimated_time if available
            try:
                data = resp.json()
                wait = data.get("estimated_time", 20)
            except Exception:
                wait = 20
            raise ProviderError(
                f"HuggingFace model is loading. Retry in ~{wait}s. "
                "Use --provider ollama for immediate local inference."
            )

        if resp.status_code == 401:
            raise ProviderError("HuggingFace: Invalid API key (401 Unauthorized).")

        if not resp.ok:
            raise ProviderError(
                f"HuggingFace API error {resp.status_code}: {resp.text[:400]}"
            )

        try:
            data = resp.json()
            # OpenAI-compatible chat response format
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Failed to parse HuggingFace response: {exc}") from exc

    def health_check(self) -> bool:
        try:
            resp = requests.get(
                f"https://api-inference.huggingface.co/models/{self._model}",
                headers=self._headers,
                timeout=10,
            )
            return resp.status_code in (200, 503)  # 503 = loading, still reachable
        except Exception:
            return False
