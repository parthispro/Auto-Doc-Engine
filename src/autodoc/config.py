"""
config.py — Central configuration loader.
Reads from .env, environment variables, or ~/.autodoc/config.toml (in priority order).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import tomllib
from dotenv import load_dotenv

# Load .env from CWD or project root
load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
load_dotenv(dotenv_path=Path.home() / ".autodoc" / ".env", override=False)

_USER_CONFIG = Path.home() / ".autodoc" / "config.toml"


def _load_toml() -> dict:
    if _USER_CONFIG.exists():
        with open(_USER_CONFIG, "rb") as fh:
            return tomllib.load(fh)
    return {}


_TOML = _load_toml()


def _get(key: str, section: str = "autodoc", default: str | None = None) -> str | None:
    """Resolve config value: env > toml > default."""
    env_val = os.environ.get(key.upper())
    if env_val:
        return env_val
    toml_val = _TOML.get(section, {}).get(key.lower())
    if toml_val:
        return str(toml_val)
    return default


@dataclass
class Config:
    # ── AI Provider ─────────────────────────────────────────────────────────
    provider: str = field(
        default_factory=lambda: _get("AUTODOC_PROVIDER", default="gemini")
    )

    # Gemini
    gemini_api_key: str | None = field(default_factory=lambda: _get("GEMINI_API_KEY"))
    gemini_model: str = field(
        default_factory=lambda: _get("GEMINI_MODEL", default="gemini-2.5-pro")
    )

    # Hugging Face
    hf_api_key: str | None = field(default_factory=lambda: _get("HF_API_KEY"))
    hf_model: str = field(
        default_factory=lambda: _get(
            "HF_MODEL", default="mistralai/Mistral-7B-Instruct-v0.3"
        )
    )
    hf_endpoint: str | None = field(
        default_factory=lambda: _get(
            "HF_ENDPOINT"
        )  # optional custom inference endpoint
    )

    # Ollama (local)
    ollama_host: str = field(
        default_factory=lambda: _get("OLLAMA_HOST", default="http://localhost:11434")
    )
    ollama_model: str = field(
        default_factory=lambda: _get("OLLAMA_MODEL", default="llama3")
    )

    # ── Output ───────────────────────────────────────────────────────────────
    output_dir: Path = field(
        default_factory=lambda: Path(_get("AUTODOC_OUTPUT_DIR", default="./reports"))
    )
    output_formats: list[str] = field(default_factory=lambda: ["md", "html", "pdf"])

    # ── Sanitization ─────────────────────────────────────────────────────────
    sanitize: bool = field(
        default_factory=lambda: _get("AUTODOC_SANITIZE", default="true").lower()
        == "true"
    )

    # ── Misc ─────────────────────────────────────────────────────────────────
    verbose: bool = False
    temperature: float = 0.2  # low temp → clinical, deterministic tone


# Singleton
config = Config()
