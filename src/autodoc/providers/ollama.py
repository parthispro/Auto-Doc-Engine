"""
ollama.py — Local Ollama inference provider.

Connects to a locally running Ollama daemon (http://localhost:11434 by default).
Uses the /api/chat endpoint with streaming disabled.

Requires: `ollama` running and the target model pulled.
  ollama pull llama3
"""

from __future__ import annotations

import json

import requests

from autodoc.providers.base import BaseProvider, ProviderError

_TIMEOUT = 300  # local inference can be slow


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(
        self, host: str = "http://localhost:11434", model: str = "llama3"
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._chat_url = f"{self._host}/api/chat"

    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.2
    ) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": temperature},
            "stream": False,
        }

        try:
            resp = requests.post(self._chat_url, json=payload, timeout=_TIMEOUT)
        except requests.exceptions.ConnectionError as exc:
            raise ProviderError(
                f"Cannot connect to Ollama at {self._host}. "
                "Is 'ollama serve' running?"
            ) from exc
        except requests.exceptions.Timeout:
            raise ProviderError(
                "Ollama request timed out (>5 min). Try a smaller model."
            )

        if not resp.ok:
            raise ProviderError(f"Ollama error {resp.status_code}: {resp.text[:400]}")

        try:
            data = resp.json()
            return data["message"]["content"]
        except (KeyError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Failed to parse Ollama response: {exc}") from exc

    def health_check(self) -> bool:
        try:
            resp = requests.get(f"{self._host}/api/tags", timeout=5)
            return resp.ok
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError,
        ):
            return False

    def list_models(self) -> list[str]:
        """Return list of locally available model names."""
        try:
            resp = requests.get(f"{self._host}/api/tags", timeout=5)
            if resp.ok:
                return [m["name"] for m in resp.json().get("models", [])]
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError,
        ):
            return []
        return []

