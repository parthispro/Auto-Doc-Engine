"""
noise.py — Telemetry noise filtration layer.

Strips boilerplate, repetitive enumeration, raw typos/backspaces,
and failed ping loops from raw terminal telemetry before AI synthesis.
"""

from __future__ import annotations

import re

# ── Patterns to DROP entirely ─────────────────────────────────────────────────

# Backspace sequences (raw terminal artifacts)
_BACKSPACE = re.compile(r".\x08")  # char followed by BS

# ANSI escape codes
_ANSI = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

# Repetitive ping lines
_PING_LINE = re.compile(
    r"^\d+ bytes from .+: icmp_seq=\d+ ttl=\d+ time=[\d\.]+ ms$", re.MULTILINE
)

# nmap boilerplate headers/footers
_NMAP_BOILERPLATE = re.compile(
    r"^(Starting Nmap \d|Nmap scan report|Host is up|Nmap done|Read data files).*$",
    re.MULTILINE,
)

# gobuster / ffuf / feroxbuster noise (non-finding lines)
_ENUM_NOISE = re.compile(
    r"^(Progress:|Finished|Starting gobuster|===============|by OJ Reeves|Gobuster v).*$",
    re.MULTILINE,
)

# Blank ping/nc connection refused lines
_CONN_REFUSED = re.compile(
    r"^.*(Connection refused|Network unreachable|No route to host).*$", re.MULTILINE
)

# Raw ^C / ^D / terminal control
_CTRL = re.compile(r"\^[CD]")

# Repeated identical lines (3+ in a row → collapse to one)
_REPEATED_LINES: None = None  # handled procedurally below

# Empty/whitespace-only lines collapsed to single blank
_MULTI_BLANK = re.compile(r"\n{3,}")

# ── Patterns to FLAG (retain but mark as pivot) ───────────────────────────────
_FAILED_ATTEMPT = re.compile(
    r"(Permission denied|Invalid syntax|Segmentation fault|Connection timed out"
    r"|No such file|command not found|403 Forbidden|401 Unauthorized)",
    re.IGNORECASE,
)


def _collapse_repeated_lines(text: str) -> str:
    """Collapse 3+ consecutive identical lines into one."""
    lines = text.splitlines()
    out: list[str] = []
    prev, count = None, 0
    for line in lines:
        stripped = line.strip()
        if stripped == prev:
            count += 1
            if count < 3:
                out.append(line)
            elif count == 3:
                out.append(f"  [... repeated {count}+ times, truncated ...]")
        else:
            prev, count = stripped, 1
            out.append(line)
    return "\n".join(out)


def filter_noise(
    raw: str,
    preserve_failures: bool = True,
) -> str:
    """
    Strip noise from raw telemetry.

    Args:
        raw:               Raw terminal/tool output string.
        preserve_failures: If True, keep lines matching _FAILED_ATTEMPT
                           even if they would otherwise be stripped,
                           annotating them as [PIVOT] markers.

    Returns:
        Cleaned telemetry string.
    """
    text = raw

    # 1. Strip ANSI escape codes
    text = _ANSI.sub("", text)

    # 2. Strip backspace artifacts
    while _BACKSPACE.search(text):
        text = _BACKSPACE.sub("", text)

    # 3. Strip raw terminal control chars
    text = _CTRL.sub("", text)

    # 4. Strip repetitive ping output
    text = _PING_LINE.sub("", text)

    # 5. Strip nmap boilerplate
    text = _NMAP_BOILERPLATE.sub("", text)

    # 6. Strip enumeration tool noise
    text = _ENUM_NOISE.sub("", text)

    # 7. Handle failed connection lines
    if preserve_failures:

        def _mark_pivot(m: re.Match) -> str:
            return f"[PIVOT — FAILED] {m.group(0)}"

        text = _CONN_REFUSED.sub(_mark_pivot, text)
    else:
        text = _CONN_REFUSED.sub("", text)

    # 8. Collapse repeated lines
    text = _collapse_repeated_lines(text)

    # 9. Collapse excess blank lines
    text = _MULTI_BLANK.sub("\n\n", text)

    return text.strip()


def segment_by_tool(raw: str) -> dict[str, list[str]]:
    """
    Heuristically segment raw telemetry into per-tool blocks.

    Returns a dict mapping tool name → list of output blocks.
    This helps the AI provider understand context switches.
    """
    tool_patterns: list[tuple[str, re.Pattern]] = [
        ("nmap", re.compile(r"nmap\s", re.IGNORECASE)),
        ("gdb/gef", re.compile(r"(gdb|gef|pwndbg)\s*>", re.IGNORECASE)),
        ("burpsuite", re.compile(r"(Burp Suite|burp proxy)", re.IGNORECASE)),
        ("sqlmap", re.compile(r"sqlmap\s", re.IGNORECASE)),
        ("gobuster", re.compile(r"gobuster\s", re.IGNORECASE)),
        ("curl", re.compile(r"curl\s", re.IGNORECASE)),
        ("python", re.compile(r"python3?\s", re.IGNORECASE)),
        ("ffuf", re.compile(r"ffuf\s", re.IGNORECASE)),
        ("john", re.compile(r"john\s|hashcat\s", re.IGNORECASE)),
    ]

    segments: dict[str, list[str]] = {"_other": []}
    current_tool = "_other"
    current_block: list[str] = []

    for line in raw.splitlines():
        matched_tool = None
        for tool_name, pattern in tool_patterns:
            if pattern.search(line):
                matched_tool = tool_name
                break

        if matched_tool and matched_tool != current_tool:
            if current_block:
                segments.setdefault(current_tool, []).append("\n".join(current_block))
                current_block = []
            current_tool = matched_tool

        current_block.append(line)

    if current_block:
        segments.setdefault(current_tool, []).append("\n".join(current_block))

    return segments
