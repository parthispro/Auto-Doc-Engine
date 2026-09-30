"""
base.py — Abstract base for all AI provider backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """All providers must implement generate()."""

    name: str = "base"

    @abstractmethod
    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.2
    ) -> str:
        """
        Call the underlying model and return the generated Markdown writeup.

        Args:
            system_prompt: The clinical synthesis instructions.
            user_prompt:   The telemetry-laden user turn.
            temperature:   Sampling temperature (0.0–1.0).

        Returns:
            Raw Markdown string of the generated writeup.

        Raises:
            ProviderError: On any unrecoverable API/model failure.
        """

    def health_check(self) -> bool:
        """
        Quick liveness check. Returns True if provider is reachable.
        Default implementation tries a minimal generate() call.
        """
        try:
            self.generate("ping", "pong", temperature=0.0)
            return True
        except Exception:
            return False


class ProviderError(RuntimeError):
    """Raised when a provider fails to generate output."""
