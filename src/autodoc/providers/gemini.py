"""
gemini.py — Google Gemini API provider.

Primary synthesis backend. Uses gemini-2.5-pro by default.
Falls back gracefully on quota exhaustion (429) or network errors.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autodoc.providers.base import BaseProvider, ProviderError

if TYPE_CHECKING:
    pass


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-pro") -> None:
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ProviderError(
                "google-generativeai is not installed. Run: pip install google-generativeai"
            ) from e

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.2
    ) -> str:
        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
            generation_config=self._genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=8192,
            ),
        )

        retries = 3
        for attempt in range(retries):
            try:
                response = model.generate_content(user_prompt)
                return response.text
            except Exception as exc:
                error_str = str(exc)
                # Rate-limit: back off and retry
                if "429" in error_str and attempt < retries - 1:
                    wait = 2 ** (attempt + 2)
                    time.sleep(wait)
                    continue
                raise ProviderError(f"Gemini generation failed: {exc}") from exc

        raise ProviderError("Gemini generation failed after all retries.")

    def health_check(self) -> bool:
        try:
            model = self._genai.GenerativeModel(model_name=self._model_name)
            model.generate_content("ping")
            return True
        except Exception:
            return False
