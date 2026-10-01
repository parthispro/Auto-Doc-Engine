---
name: ctf-writeup
description: Synthesize clinical, portfolio-grade CTF writeups from raw terminal telemetry using Auto-Doc-Engine.
---

# CTF Writeup Generation
When tasked with creating a writeup or report for a CTF challenge, use the Auto-Doc-Engine CLI.

## Prerequisites
1. **Verify API Access Internally:** Check for the presence of the `GEMINI_API_KEY` in your native environment context. DO NOT execute shell commands to print the key. If missing, halt and prompt the user to export it.
2. **Deterministic Telemetry:** Locate the physical log file mapped to the `AUTODOC_TELEMETRY_PATH` environment variable. If this variable is not set, prompt the user for the explicit filepath. Do not guess the file.

## Execution
Run the `autodoc` command to synthesize the writeup. Dynamically infer the challenge name, domain, and difficulty.

```bash
autodoc run -f "$AUTODOC_TELEMETRY_PATH" -n "<inferred_challenge_name>" -d <inferred_domain> -l <inferred_difficulty> --provider gemini
```

**Inference Fallbacks:**
* **Domains:** `pwn`, `web`, `crypto`, `osint`, `rev`, `misc`. (Default to `general` if unknown).
* **Difficulties:** `easy`, `medium`, `hard`, `insane`. (Default to `unknown` if unknown).

## Post-Execution
The engine will generate artifacts in the `./reports/` directory. Do not attempt to read or print the contents of the `.pdf` or `.html` files. Output the absolute file paths to the user.
