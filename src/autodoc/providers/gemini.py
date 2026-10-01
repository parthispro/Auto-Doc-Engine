"""
gemini.py — Google Gemini API provider.

Primary synthesis backend. Uses gemini-2.5-pro by default.
Falls back gracefully on quota exhaustion (429) or network errors.
"""

from __future__ import annotations

import time

from autodoc.providers.base import BaseProvider, ProviderError


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite") -> None:
        self.api_key = api_key.strip()
        self._model_name = model

        # Prefer new google-genai SDK, fallback to legacy google-generativeai
        try:
            import logging

            logging.getLogger("google.genai").setLevel(logging.ERROR)
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
            self._use_new_sdk = True
        except ImportError:
            try:
                import warnings

                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    import google.generativeai as genai_legacy

                genai_legacy.configure(api_key=self.api_key)
                self._genai_legacy = genai_legacy
                self._use_new_sdk = False
            except ImportError as e:
                raise ProviderError(
                    "Neither google-genai nor google-generativeai is installed. "
                    "Run: pip install google-genai"
                ) from e

    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.2
    ) -> str:
        retries = 3
        for attempt in range(retries):
            try:
                if self._use_new_sdk:
                    from google.genai import types

                    config = types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        max_output_tokens=8192,
                    )
                    response = self._client.models.generate_content(
                        model=self._model_name,
                        contents=user_prompt,
                        config=config,
                    )
                    return response.text
                model = self._genai_legacy.GenerativeModel(
                    model_name=self._model_name,
                    system_instruction=system_prompt,
                    generation_config=self._genai_legacy.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=8192,
                    ),
                )
                response = model.generate_content(user_prompt)
                return response.text
            except Exception as exc:
                error_str = str(exc)
                if ("429" in error_str or "503" in error_str) and attempt < retries - 1:
                    wait = 2 ** (attempt + 2)
                    time.sleep(wait)
                    continue
                raise ProviderError(f"Gemini generation failed: {exc}") from exc

        raise ProviderError("Gemini generation failed after all retries.")

    def health_check(self) -> bool:
        try:
            if self._use_new_sdk:
                self._client.models.generate_content(
                    model=self._model_name,
                    contents="ping",
                )
            else:
                model = self._genai_legacy.GenerativeModel(model_name=self._model_name)
                model.generate_content("ping")
            return True
        except Exception:  # noqa: BLE001
            return False
