"""
cli.py — Auto-Doc Engine command-line interface.

Entry point: autodoc  (installed via pyproject.toml)

Usage examples:
  # From a log file
  autodoc run -f session.log -n "Web - SQL Injection" -d web -l medium

  # From stdin (pipe)
  cat session.log | autodoc run --stdin -n "Pwn - ret2libc" -d pwn

  # Use a specific provider
  autodoc run -f session.log -n "Crypto - AES ECB" --provider huggingface

  # Check provider health
  autodoc health

  # List Ollama models
  autodoc models
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from autodoc.config import config
from autodoc.engine import Engine
from autodoc.providers import ProviderError, get_provider
from autodoc.providers.ollama import OllamaProvider

console = Console()
err_console = Console(stderr=True)


# ── Shared Options ─────────────────────────────────────────────────────────────


def _provider_option():
    return click.option(
        "--provider",
        "-p",
        type=click.Choice(
            ["gemini", "huggingface", "ollama", "auto"], case_sensitive=False
        ),
        default=None,
        help="AI provider to use. Defaults to AUTODOC_PROVIDER env var or 'auto'.",
    )


def _api_key_option():
    return click.option(
        "--api-key",
        "-k",
        default=None,
        metavar="KEY",
        help="Override API key for the selected provider.",
    )


# ── CLI Group ─────────────────────────────────────────────────────────────────


@click.group()
@click.version_option(package_name="auto-doc-engine")
def main():
    """
    \b
    ╔══════════════════════════════════╗
    ║   AUTO-DOC ENGINE  v1.1.0        ║
    ║   CTF Telemetry → Writeup        ║
    ╚══════════════════════════════════╝

    Synthesize clinical, portfolio-grade CTF writeups from raw terminal telemetry.
    """


# ── run command ───────────────────────────────────────────────────────────────


@main.command()
@click.option(
    "--file",
    "-f",
    "input_file",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to raw telemetry log file.",
)
@click.option(
    "--stdin",
    "from_stdin",
    is_flag=True,
    help="Read raw telemetry from stdin (pipe mode).",
)
@click.option(
    "--name",
    "-n",
    "challenge_name",
    default="Unknown Challenge",
    show_default=True,
    help="Challenge name or identifier.",
)
@click.option(
    "--domain",
    "-d",
    type=click.Choice(
        ["pwn", "web", "crypto", "osint", "rev", "misc", "general"],
        case_sensitive=False,
    ),
    default="general",
    show_default=True,
    help="Security domain.",
)
@click.option(
    "--difficulty",
    "-l",
    type=click.Choice(
        ["easy", "medium", "hard", "insane", "unknown"], case_sensitive=False
    ),
    default="unknown",
    show_default=True,
    help="Challenge difficulty.",
)
@click.option(
    "--output",
    "-o",
    "output_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory. Defaults to ./reports.",
)
@click.option(
    "--format",
    "formats",
    multiple=True,
    type=click.Choice(["md", "html", "pdf"], case_sensitive=False),
    default=["md", "html", "pdf"],
    show_default=True,
    help="Output format(s). Can be specified multiple times.",
)
@_provider_option()
@_api_key_option()
@click.option(
    "--redact-flags",
    is_flag=True,
    default=False,
    help="Also redact captured flag values in the output.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Print detailed pipeline steps.",
)
@click.option(
    "--preview",
    is_flag=True,
    default=False,
    help="Print the generated Markdown to stdout after synthesis.",
)
def run(
    input_file,
    from_stdin,
    challenge_name,
    domain,
    difficulty,
    output_dir,
    formats,
    provider,
    api_key,
    redact_flags,
    verbose,
    preview,
):
    """Synthesize a writeup from a telemetry log file or stdin."""

    # ── Read input ─────────────────────────────────────────────────────────
    if from_stdin:
        if sys.stdin.isatty():
            err_console.print(
                "[red]Error:[/red] --stdin specified but no data on stdin."
            )
            raise SystemExit(1)
        telemetry = sys.stdin.read()
    elif input_file:
        telemetry = input_file.read_text(encoding="utf-8", errors="replace")
    else:
        err_console.print(
            "[red]Error:[/red] Provide --file/-f or --stdin.\n"
            "Run [bold]autodoc run --help[/bold] for usage."
        )
        raise SystemExit(1)

    if not telemetry.strip():
        err_console.print("[red]Error:[/red] Input telemetry is empty.")
        raise SystemExit(1)

    # ── Override config if API key passed ──────────────────────────────────
    cfg = config
    if api_key and provider:
        key_map = {
            "gemini": "gemini_api_key",
            "huggingface": "hf_api_key",
        }
        if provider in key_map:
            setattr(cfg, key_map[provider], api_key)

    # ── Banner ─────────────────────────────────────────────────────────────
    console.print(
        Panel(
            f"[bold white]{challenge_name}[/bold white]\n"
            f"[dim]Domain:[/dim] [cyan]{domain.upper()}[/cyan]  "
            f"[dim]Difficulty:[/dim] [yellow]{difficulty.upper()}[/yellow]  "
            f"[dim]Provider:[/dim] [green]{provider or cfg.provider or 'auto'}[/green]",
            title="[bold blue]AUTO-DOC ENGINE[/bold blue]",
            border_style="blue",
        )
    )

    # ── Run engine ─────────────────────────────────────────────────────────
    engine = Engine(cfg=cfg)
    try:
        result = engine.run(
            telemetry=telemetry,
            challenge_name=challenge_name,
            domain=domain,
            difficulty=difficulty,
            output_dir=output_dir,
            formats=list(formats),
            provider_override=provider,
            redact_flags=redact_flags,
            verbose=verbose,
        )
    except ProviderError as e:
        err_console.print(f"[bold red]Provider Error:[/bold red] {e}")
        raise SystemExit(1)

    # ── Results table ──────────────────────────────────────────────────────
    table = Table(box=box.ROUNDED, border_style="green", show_header=True)
    table.add_column("Format", style="bold cyan", width=8)
    table.add_column("Path", style="white")

    for fmt, path in result.written_files.items():
        table.add_row(fmt.upper(), str(path))

    console.print("\n[bold green]✓ Writeup synthesized successfully[/bold green]")
    console.print(table)
    console.print(
        f"  [dim]Identifiers sanitized:[/dim] [yellow]{result.replacements_count}[/yellow]  "
        f"[dim]Provider:[/dim] [green]{result.provider_used}[/green]"
    )

    # ── Warnings ───────────────────────────────────────────────────────────
    for w in result.warnings:
        console.print(f"  [yellow]⚠[/yellow] {w}")

    # ── Preview ────────────────────────────────────────────────────────────
    if preview:
        console.print("\n" + "─" * 60)
        console.print(result.writeup_md)


# ── health command ────────────────────────────────────────────────────────────


@main.command()
@_provider_option()
@_api_key_option()
def health(provider, api_key):
    """Check connectivity and health of AI provider backends."""
    from autodoc.providers import GeminiProvider, HuggingFaceProvider, OllamaProvider

    cfg = config

    providers_to_check = []

    if provider:
        providers_to_check = [get_provider(cfg)]
    else:
        # Check all configured providers
        if cfg.gemini_api_key:
            providers_to_check.append(
                GeminiProvider(api_key=cfg.gemini_api_key, model=cfg.gemini_model)
            )
        if cfg.hf_api_key:
            providers_to_check.append(
                HuggingFaceProvider(api_key=cfg.hf_api_key, model=cfg.hf_model)
            )
        providers_to_check.append(
            OllamaProvider(host=cfg.ollama_host, model=cfg.ollama_model)
        )

    table = Table(
        box=box.ROUNDED, title="Provider Health Check", title_style="bold blue"
    )
    table.add_column("Provider", style="bold cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for p in providers_to_check:
        ok = p.health_check()
        status = (
            "[bold green]✓ ONLINE[/bold green]"
            if ok
            else "[bold red]✗ OFFLINE[/bold red]"
        )
        details = ""
        if isinstance(p, OllamaProvider):
            models = p.list_models()
            details = (
                f"{len(models)} model(s) available" if ok else "daemon not running"
            )
        elif isinstance(p, GeminiProvider):
            details = p._model_name
        elif isinstance(p, HuggingFaceProvider):
            details = p._model
        table.add_row(p.name, status, details)

    console.print(table)


# ── models command ────────────────────────────────────────────────────────────


@main.command()
@click.option(
    "--host", default=None, help="Ollama host URL. Defaults to OLLAMA_HOST env."
)
def models(host):
    """List locally available Ollama models."""
    host = host or config.ollama_host
    p = OllamaProvider(host=host)
    model_list = p.list_models()

    if not model_list:
        console.print(
            f"[yellow]No models found[/yellow] at [dim]{host}[/dim]\n"
            "Is [bold]ollama serve[/bold] running? Try: [bold]ollama pull llama3[/bold]"
        )
        return

    table = Table(box=box.SIMPLE, title=f"Ollama Models @ {host}", title_style="bold")
    table.add_column("Model Name", style="cyan")
    for m in model_list:
        table.add_row(m)

    console.print(table)


# ── config command ────────────────────────────────────────────────────────────


@main.command("config")
def show_config():
    """Show current resolved configuration (redacts secret keys)."""
    cfg = config

    def _mask(val: str | None) -> str:
        if not val:
            return "[dim]not set[/dim]"
        return val[:6] + "…" + val[-4:] if len(val) > 12 else "***"

    table = Table(
        box=box.ROUNDED, title="Current Configuration", title_style="bold blue"
    )
    table.add_column("Key", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Provider", cfg.provider or "auto")
    table.add_row("Gemini API Key", _mask(cfg.gemini_api_key))
    table.add_row("Gemini Model", cfg.gemini_model)
    table.add_row("HF API Key", _mask(cfg.hf_api_key))
    table.add_row("HF Model", cfg.hf_model)
    table.add_row("HF Endpoint", cfg.hf_endpoint or "[dim]serverless[/dim]")
    table.add_row("Ollama Host", cfg.ollama_host)
    table.add_row("Ollama Model", cfg.ollama_model)
    table.add_row("Output Dir", str(cfg.output_dir))
    table.add_row("Output Formats", ", ".join(cfg.output_formats))
    table.add_row("Sanitize", str(cfg.sanitize))
    table.add_row("Temperature", str(cfg.temperature))

    console.print(table)


if __name__ == "__main__":
    main()
