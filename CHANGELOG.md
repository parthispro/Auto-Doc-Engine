# Changelog

All notable changes to Auto-Doc Engine are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-09-29

### Added
- Core synthesis pipeline: Noise Filter → Sanitizer → Prompt Builder → AI Provider → Renderer
- **Providers**: Google Gemini 2.5 Pro, Hugging Face Inference API, Ollama local daemon
- **Auto-cascade fallback**: Gemini → HuggingFace → Ollama on provider failure
- **Sanitizer**: IPv4/IPv6, MD5/SHA1/SHA256/SHA512 hashes, URL host redaction; optional flag redaction
- **Noise filter**: ANSI escape stripping, backspace removal, ping loop collapse, nmap/gobuster boilerplate removal, `[PIVOT]` annotation for failed attempts, tool segmentation heuristics
- **Renderer**: Markdown (always), dark-themed self-contained HTML (Jinja2), PDF (pandoc + wkhtmltopdf fallback)
- **CLI**: `autodoc run`, `autodoc health`, `autodoc models`, `autodoc config` subcommands
- Dual input modes: `--file` and `--stdin` (pipe-compatible)
- Per-run provider override via `--provider` flag
- Rich terminal UI with progress spinner and results table
- 19 unit tests covering sanitizer and noise filter
- Demo telemetry file for end-to-end testing
- `.env.example` configuration template
- `~/.autodoc/config.toml` support for user-level persistent config

