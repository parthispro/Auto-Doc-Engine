<div align="center">

<h1>⚡ Auto-Doc Engine</h1>

<p><strong>Clinical CTF writeup synthesis from raw terminal telemetry.</strong></p>

<p>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/providers-Gemini%20%7C%20HuggingFace%20%7C%20Ollama-purple?style=flat-square" alt="Providers">
  <img src="https://img.shields.io/badge/output-MD%20%7C%20HTML%20%7C%20PDF-orange?style=flat-square" alt="Output">
  <img src="https://img.shields.io/badge/tests-19%20passed-brightgreen?style=flat-square" alt="Tests">
</p>

<p>
  Auto-Doc Engine ingests raw, multi-domain CTF engagement logs — GDB sessions,<br>
  Burp Suite proxy output, nmap scans, SQL payloads, OSINT queries — and synthesizes<br>
  structured, portfolio-grade technical writeups automatically.
</p>

</div>

---

## Table of Contents

- [How It Works](#how-it-works)
- [Output Schema](#output-schema)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [AI Providers](#ai-providers)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

---

## How It Works

```
Raw Telemetry  (file / stdin / pipe)
        │
        ▼
┌───────────────────────┐
│   Noise Filter        │  Strip ANSI codes, backspaces, ping loops,
│   filters/noise.py    │  nmap/gobuster boilerplate, repeated lines.
│                       │  Annotate failed attempts as [PIVOT] markers.
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│   Sanitizer           │  Redact IPv4/IPv6, MD5/SHA hashes, URL hosts.
│   filters/sanitizer.py│  Optional flag value redaction.
│                       │  Every replacement is logged for audit.
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│   Prompt Builder      │  Assemble clinical system prompt + telemetry
│   prompt_builder.py   │  into the 5-section writeup schema.
└──────────┬────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│   AI Provider  (auto-cascade on failure)      │
│                                              │
│   1.  Google Gemini 2.5 Pro   (primary)      │
│   2.  Hugging Face Inference  (fallback)     │
│   3.  Ollama  local daemon    (last resort)  │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌───────────────────────┐
│   Renderer            │  .md  (always)
│   renderers/          │  .html (dark-themed, self-contained)
│   markdown.py         │  .pdf  (via pandoc / wkhtmltopdf)
└───────────────────────┘
```

---

## Output Schema

Every synthesized writeup enforces exactly five clinical sections:

| Section | Content |
|---|---|
| **Objective** | One-sentence definition of the target and goal |
| **Initial Enumeration** | Exposed attack surface — ports, endpoints, services, metadata |
| **Methodology & Pivots** | Chronological attack path; failed attempts documented as `[PIVOT]` |
| **Exploitation** | Exact method + raw, unmodified final payload in a fenced code block |
| **Impact / Flag** | Final outcome; captured flag on its own line |

---

## Quick Start

```bash
git clone https://github.com/youruser/auto-doc-engine
cd auto-doc-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env        # add your GEMINI_API_KEY

autodoc run \
  -f examples/demo_telemetry.txt \
  --name "HTB — SQL Injection Login Bypass" \
  --domain web --difficulty easy --preview
```

---

## Installation

### Requirements

| Requirement | Version |
|---|---|
| Python | ≥ 3.10 |
| pandoc *(optional, for PDF)* | any |

### Steps

```bash
# 1. Clone
git clone https://github.com/youruser/auto-doc-engine
cd auto-doc-engine

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows

# 3. Install
pip install -e .                # production
pip install -e ".[dev]"         # + pytest, ruff, black

# 4. Configure
cp .env.example .env
nano .env                       # add at least one API key

# 5. Verify
autodoc config
autodoc health
```

### PDF support (optional)

```bash
# Ubuntu / Debian / Kali
sudo apt install pandoc texlive-xetex

# macOS
brew install pandoc
```

---

## Configuration

All settings resolve in this priority order:
**Environment variable → `~/.autodoc/config.toml` → `.env` file → built-in defaults**

| Variable | Default | Description |
|---|---|---|
| `AUTODOC_PROVIDER` | `auto` | Active provider: `gemini` · `huggingface` · `ollama` · `auto` |
| `GEMINI_API_KEY` | — | [Google AI Studio](https://aistudio.google.com/app/apikey) key |
| `GEMINI_MODEL` | `gemini-2.5-pro` | Gemini model name |
| `HF_API_KEY` | — | [Hugging Face](https://huggingface.co/settings/tokens) User Access Token |
| `HF_MODEL` | `mistralai/Mistral-7B-Instruct-v0.3` | HF model ID |
| `HF_ENDPOINT` | — | Custom HF Dedicated Endpoint URL (overrides serverless) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama daemon URL |
| `OLLAMA_MODEL` | `llama3` | Local model to use |
| `AUTODOC_OUTPUT_DIR` | `./reports` | Output directory for all generated files |
| `AUTODOC_SANITIZE` | `true` | Enable/disable IP + hash redaction |

> **Never commit `.env`** — it's in `.gitignore` by default.

---

## Usage

### Synthesize from a log file

```bash
autodoc run \
  --file session.log \
  --name "Web — Blind SQL Injection" \
  --domain web \
  --difficulty medium
```

### Pipe from stdin

```bash
cat session.log | autodoc run --stdin \
  --name "Pwn — ret2libc" \
  --domain pwn \
  --difficulty hard
```

### Record a live session and pipe directly

```bash
script -q -c "your_ctf_commands_here" /dev/stdout | \
  autodoc run --stdin --name "Live Session" --domain misc
```

### Force a specific provider

```bash
autodoc run -f session.log --name "Crypto" --provider huggingface
autodoc run -f session.log --name "OSINT"  --provider ollama
```

### Pass an API key inline (no `.env` needed)

```bash
autodoc run -f session.log --name "Test" \
  --provider gemini --api-key AIza...yourkey
```

### Select output formats

```bash
# Only markdown
autodoc run -f session.log --name "Test" --format md

# Markdown + HTML only (skip PDF)
autodoc run -f session.log --name "Test" --format md --format html
```

### Additional flags

| Flag | Effect |
|---|---|
| `--preview` / `-v` | Print generated Markdown to terminal after synthesis |
| `--verbose` | Show pipeline steps and provider selection detail |
| `--redact-flags` | Also redact captured flag values in the output |
| `-o PATH` | Override output directory |

### Utility commands

```bash
autodoc health      # Ping all configured providers
autodoc models      # List locally available Ollama models
autodoc config      # Show resolved config (API keys masked)
autodoc --version   # Print version
```

---

## AI Providers

### Provider comparison

| Provider | Quality | Speed | Cost | Requires |
|---|---|---|---|---|
| Google Gemini 2.5 Pro | ★★★★★ | Fast | API key (free tier available) | `GEMINI_API_KEY` |
| HuggingFace Inference | ★★★☆☆ | Medium | Free tier / paid | `HF_API_KEY` |
| Ollama (local) | ★★★☆☆ | Slow | Free | Running daemon |

### Auto-cascade fallback

When `AUTODOC_PROVIDER=auto` (the default):

```
Gemini  ──(fail)──►  HuggingFace  ──(fail)──►  Ollama
```

Every fallback is logged as a warning in the terminal summary.

### Local Ollama setup

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Start daemon
ollama serve

# Pull a model (one-time, ~4 GB)
ollama pull llama3

# Verify
autodoc models
```

---

## Project Structure

```
auto-doc-engine/
│
├── src/autodoc/
│   ├── __init__.py             # Package version
│   ├── cli.py                  # Click CLI: run / health / models / config
│   ├── engine.py               # Pipeline orchestrator
│   ├── config.py               # Config loader (env / toml / .env / defaults)
│   ├── prompt_builder.py       # System + user prompt assembly
│   │
│   ├── filters/
│   │   ├── noise.py            # ANSI strip, ping collapse, PIVOT annotation
│   │   └── sanitizer.py        # IP / hash / URL / flag redaction
│   │
│   ├── providers/
│   │   ├── base.py             # Abstract BaseProvider interface
│   │   ├── __init__.py         # Registry + auto-cascade factory
│   │   ├── gemini.py           # Google Gemini backend
│   │   ├── huggingface.py      # HuggingFace Inference API backend
│   │   └── ollama.py           # Local Ollama backend
│   │
│   └── renderers/
│       └── markdown.py         # MD + dark HTML + PDF renderer
│
├── tests/
│   ├── test_sanitizer.py       # 10 sanitizer unit tests
│   └── test_noise.py           # 9 noise filter unit tests
│
├── examples/
│   └── demo_telemetry.txt      # Sample CTF web challenge session log
│
├── .env.example                # Config template (copy → .env)
├── .gitignore
├── pyproject.toml              # Build config + dependencies
├── LICENSE
├── CONTRIBUTING.md
└── CHANGELOG.md
```

---

## Running Tests

```bash
# Activate venv first
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --tb=short
```

**Expected:** `19 passed` in under 1 second.

---

## Supported Security Domains

| Flag | Domain |
|---|---|
| `pwn` | Binary exploitation, ROP chains, GDB/GEF sessions |
| `web` | SQLi, XSS, SSRF, Burp Suite / curl proxy logs |
| `crypto` | Cipher analysis, key extraction, Python crypto scripts |
| `osint` | Search queries, metadata extraction, relationship mapping |
| `rev` | Reverse engineering, disassembly, decompilation logs |
| `misc` | Everything else |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

[MIT](LICENSE) © 2026 Auto-Doc Engine Contributors
