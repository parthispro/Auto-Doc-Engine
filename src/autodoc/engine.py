"""
engine.py — Core orchestrator for the Auto-Doc Engine.

Pipeline:
  raw telemetry
      → noise filter
      → sanitizer
      → prompt builder
      → AI provider (Gemini / HuggingFace / Ollama)
      → renderer (MD + HTML + PDF)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from autodoc.config import Config
from autodoc.config import config as _default_config
from autodoc.filters.noise import filter_noise, segment_by_tool
from autodoc.filters.sanitizer import sanitize
from autodoc.prompt_builder import build_prompt
from autodoc.providers import ProviderError, get_provider
from autodoc.renderers.markdown import render

console = Console(stderr=True)


def _slugify(text: str) -> str:
    """Convert a challenge name to a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:64]


@dataclass
class EngineResult:
    """Result object returned by Engine.run()."""

    writeup_md: str
    written_files: dict[str, Path]
    replacements_count: int
    provider_used: str
    challenge_name: str
    warnings: list[str] = field(default_factory=list)

    @property
    def primary_output(self) -> Path:
        """Return the most useful output file (md > html > pdf)."""
        for fmt in ("md", "html", "pdf"):
            if fmt in self.written_files:
                return self.written_files[fmt]
        return next(iter(self.written_files.values()))


class Engine:
    """
    Main orchestrator. Instantiate once, call run() per engagement.

    Args:
        cfg: Config object. Defaults to the singleton loaded from environment.
    """

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or _default_config

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def run(
        self,
        telemetry: str,
        challenge_name: str = "Unknown Challenge",
        domain: str = "General",
        difficulty: str = "Unknown",
        output_dir: Path | None = None,
        formats: list[str] | None = None,
        provider_override: str | None = None,
        redact_flags: bool = False,
        verbose: bool = False,
    ) -> EngineResult:
        """
        Run the full synthesis pipeline.

        Args:
            telemetry:         Raw terminal/tool output string.
            challenge_name:    CTF challenge identifier.
            domain:            Security domain (pwn, web, crypto, osint, …).
            difficulty:        Challenge difficulty label.
            output_dir:        Directory to write output files.
            formats:           Output formats list ['md', 'html', 'pdf'].
            provider_override: Force a specific provider ('gemini', 'huggingface', 'ollama').
            redact_flags:      If True, also redact captured flag values.
            verbose:           Print detailed pipeline steps.

        Returns:
            EngineResult with all output paths and metadata.
        """
        cfg = self.cfg
        out_dir = output_dir or cfg.output_dir
        fmts = formats or cfg.output_formats
        warnings: list[str] = []

        if provider_override:
            cfg = Config(**{**cfg.__dict__, "provider": provider_override})

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            console=console,
            transient=True,
        ) as progress:

            # ── Step 1: Noise Filter ─────────────────────────────────────────
            task = progress.add_task("Filtering noise from telemetry…", total=None)
            filtered = filter_noise(telemetry, preserve_failures=True)
            if verbose:
                segs = segment_by_tool(filtered)
                console.print(
                    Panel(
                        f"Detected tool segments: [bold]{', '.join(segs.keys())}[/bold]",
                        title="[dim]Noise Filter[/dim]",
                        border_style="dim",
                    )
                )
            progress.remove_task(task)

            # ── Step 2: Sanitization ─────────────────────────────────────────
            task = progress.add_task("Sanitizing identifiers…", total=None)
            san_result = sanitize(filtered, redact_flags=redact_flags)
            n_replacements = len(san_result.replacements)
            if verbose and n_replacements:
                console.print(f"  [dim]Sanitized {n_replacements} identifier(s)[/dim]")
            progress.remove_task(task)

            # ── Step 3: Build Prompt ─────────────────────────────────────────
            task = progress.add_task("Building synthesis prompt…", total=None)
            system_prompt, user_prompt = build_prompt(
                telemetry=san_result.text,
                challenge_name=challenge_name,
                domain=domain,
                difficulty=difficulty,
            )
            progress.remove_task(task)

            # ── Step 4: AI Synthesis ─────────────────────────────────────────
            task = progress.add_task("Synthesizing writeup…", total=None)
            provider = get_provider(cfg)
            provider_name = provider.name

            if verbose:
                console.print(f"  [dim]Provider: [bold]{provider_name}[/bold][/dim]")

            writeup_md = self._call_with_fallback(
                provider=provider,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                cfg=cfg,
                warnings=warnings,
                verbose=verbose,
            )
            progress.remove_task(task)

            # ── Step 5: Render ───────────────────────────────────────────────
            task = progress.add_task("Rendering output files…", total=None)
            slug = _slugify(challenge_name)
            written = render(
                content=writeup_md,
                output_dir=out_dir,
                slug=slug,
                title=challenge_name,
                domain=domain,
                difficulty=difficulty,
                formats=fmts,
            )

            if "pdf_skipped" in written:
                warnings.append(
                    "PDF output skipped — pandoc not found. "
                    "Install pandoc: https://pandoc.org/installing.html"
                )
                del written["pdf_skipped"]

            progress.remove_task(task)

        return EngineResult(
            writeup_md=writeup_md,
            written_files=written,
            replacements_count=n_replacements,
            provider_used=provider_name,
            challenge_name=challenge_name,
            warnings=warnings,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _call_with_fallback(
        self,
        provider,
        system_prompt: str,
        user_prompt: str,
        cfg: Config,
        warnings: list[str],
        verbose: bool,
    ) -> str:
        """
        Try primary provider; on failure cascade through the fallback chain.

        Fallback order: Gemini → HuggingFace → Ollama
        """
        from autodoc.providers import (
            HuggingFaceProvider,
            OllamaProvider,
        )

        fallback_chain = []
        if not isinstance(provider, HuggingFaceProvider) and cfg.hf_api_key:
            fallback_chain.append(
                HuggingFaceProvider(
                    api_key=cfg.hf_api_key,
                    model=cfg.hf_model,
                    endpoint=cfg.hf_endpoint,
                )
            )
        if not isinstance(provider, OllamaProvider):
            fallback_chain.append(
                OllamaProvider(host=cfg.ollama_host, model=cfg.ollama_model)
            )

        # Try primary
        try:
            return provider.generate(system_prompt, user_prompt, cfg.temperature)
        except ProviderError as primary_err:
            warnings.append(f"Primary provider ({provider.name}) failed: {primary_err}")
            console.print(
                f"  [yellow]⚠ {provider.name} failed — trying fallback…[/yellow]"
            )

        # Try fallbacks
        for fallback in fallback_chain:
            try:
                if verbose:
                    console.print(f"  [dim]Falling back to: {fallback.name}[/dim]")
                result = fallback.generate(system_prompt, user_prompt, cfg.temperature)
                warnings.append(f"Used fallback provider: {fallback.name}")
                return result
            except ProviderError as fb_err:
                warnings.append(f"Fallback provider ({fallback.name}) failed: {fb_err}")
                continue

        raise ProviderError(
            "All providers failed. Check your API keys and connectivity."
        )

