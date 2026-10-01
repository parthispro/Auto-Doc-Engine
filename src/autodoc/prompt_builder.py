"""
prompt_builder.py — Constructs the synthesis prompt for AI providers.

Assembles the clinical system instructions + filtered telemetry into
a structured prompt that enforces the Auto-Doc output schema.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are the Auto-Doc Synthesis Engine. Your sole objective is to ingest \
pre-filtered, sanitized CTF engagement telemetry and produce a clinical, \
portfolio-grade technical writeup.

OPERATING DOCTRINE:
- Zero fluff. No corporate jargon. No motivational language.
- Strict adherence to technical reality — do not infer or fabricate steps.
- Preserve all final working payloads, scripts, and queries verbatim.
- Group related tool invocations into logical attack vector steps.
- If a failed attempt led to a necessary methodology pivot, document it clinically.
- All infrastructure identifiers are already sanitized; do not alter placeholders.

OUTPUT FORMAT — use exactly these section headers (Markdown H2):

## Objective
One sentence. Define the challenge/target and the goal.

## Initial Enumeration
Concise summary of exposed attack surface: ports, endpoints, services, metadata.
Use bullet points for findings. Cite specific tool outputs where relevant.

## Methodology & Pivots
Chronological attack path. Group steps logically. Use numbered sub-steps.
For failed attempts: document as > **[PIVOT]** — reason — what changed.
Do NOT omit pivots; they demonstrate analytical rigor.

## Exploitation
The exact method used to achieve the objective.
Include the raw, unmodified final payload / script / query in a fenced code block.
Specify language in the fence (python, sql, bash, etc.).

## Impact / Flag
The final outcome. State what was accessed, exfiltrated, or demonstrated.
If a flag was captured, present it on its own line as:
```
FLAG: <value>
```

CONSTRAINTS:
- Do not add sections beyond the five above.
- Do not add a preamble or closing remarks.
- Output pure Markdown. No HTML tags.
"""

USER_PROMPT_TEMPLATE = """\
TELEMETRY INPUT
===============
Challenge Name: {challenge_name}
Domain: {domain}
Difficulty: {difficulty}

--- RAW TELEMETRY (pre-filtered) ---
{telemetry}
--- END TELEMETRY ---

Synthesize the writeup now.
"""


def build_prompt(
    telemetry: str,
    challenge_name: str = "Unknown Challenge",
    domain: str = "General",
    difficulty: str = "Unknown",
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) tuple for the AI provider.

    Args:
        telemetry:       Pre-filtered, sanitized telemetry string.
        challenge_name:  CTF challenge name or identifier.
        domain:          Security domain (pwn, web, crypto, osint, etc.)
        difficulty:      Challenge difficulty rating.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(
        challenge_name=challenge_name,
        domain=domain,
        difficulty=difficulty,
        telemetry=telemetry,
    )
    return SYSTEM_PROMPT, user_prompt

