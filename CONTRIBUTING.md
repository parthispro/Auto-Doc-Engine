# Contributing to Auto-Doc Engine

Thank you for your interest in contributing. This document covers everything you need.

---

## Development Setup

```bash
git clone https://github.com/youruser/auto-doc-engine
cd auto-doc-engine

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"   # installs pytest, ruff, black
cp .env.example .env      # configure at least one provider key
```

---

## Project Layout

```
src/autodoc/
├── filters/      → Noise filtration + sanitization
├── providers/    → AI backends (Gemini, HuggingFace, Ollama)
├── renderers/    → Output format generation (MD/HTML/PDF)
├── engine.py     → Pipeline orchestrator
├── cli.py        → Click CLI entry point
├── config.py     → Config loader
└── prompt_builder.py → Prompt assembly
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 19 tests must pass before submitting a PR.

---

## Adding a New Provider

1. Create `src/autodoc/providers/yourprovider.py`
2. Subclass `BaseProvider` from `providers/base.py`
3. Implement `generate(system_prompt, user_prompt, temperature) -> str`
4. Optionally override `health_check() -> bool`
5. Register it in `providers/__init__.py` → `get_provider()` factory
6. Add the provider name to the `--provider` CLI choice in `cli.py`
7. Document in `README.md` and `.env.example`

---

## Code Style

```bash
ruff check src/ tests/       # lint
black src/ tests/            # format
```

- Line length: 100 characters
- Type hints required on all public functions
- Docstrings required on all public classes and methods

---

## Submitting a Pull Request

1. Fork the repo and create a feature branch: `git checkout -b feat/your-feature`
2. Write tests for any new functionality
3. Ensure `pytest tests/ -v` passes fully
4. Run `ruff check` and `black` before committing
5. Open a PR with a clear description of what changed and why

---

## Reporting Issues

Please include:
- OS and Python version (`python3 --version`)
- Provider being used
- Sanitized (no real IPs/keys) reproduction steps
- Full error output

