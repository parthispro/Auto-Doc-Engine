"""
sanitizer.py — Telemetry sanitization layer.

Replaces sensitive identifiers (IPs, hashes, hostnames) with
clinical placeholders before any AI processing or output generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Regex patterns ────────────────────────────────────────────────────────────

# IPv4
_IPV4 = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# IPv6 (simplified)
_IPV6 = re.compile(r"\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")

# MD5 / SHA1 / SHA256 / SHA512 hashes
_HASH = re.compile(
    r"\b([a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64}|[a-fA-F0-9]{128})\b"
)

# URLs (preserve path structure but redact host)
_URL_HOST = re.compile(
    r"(https?://)([\w\-\.]+)((?:/[^\s]*)?)"
)

# Private/RFC1918 ranges to explicitly redact
_PRIVATE_RANGES = re.compile(
    r"\b(10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)\b"
)

# Common flag formats: CTF{...} / FLAG{...} / HTB{...} etc.
_FLAG = re.compile(
    r"\b([A-Za-z0-9_]{1,10})\{([^}]{4,})\}", re.IGNORECASE
)


@dataclass
class SanitizationResult:
    text: str
    replacements: list[tuple[str, str]] = field(default_factory=list)

    def log(self, original: str, replacement: str) -> None:
        self.replacements.append((original, replacement))


def sanitize(raw: str, redact_flags: bool = False) -> SanitizationResult:
    """
    Apply sanitization pipeline to raw telemetry.

    Args:
        raw:          The raw input string.
        redact_flags: If True, also redact captured flag values.

    Returns:
        SanitizationResult with sanitized text and replacement log.
    """
    result = SanitizationResult(text=raw)

    # 1. Private IP ranges first (more specific)
    def _replace_private_ip(m: re.Match) -> str:
        placeholder = "[REDACTED_PRIVATE_IP]"
        result.log(m.group(0), placeholder)
        return placeholder

    result.text = _PRIVATE_RANGES.sub(_replace_private_ip, result.text)

    # 2. All other IPv4
    def _replace_ipv4(m: re.Match) -> str:
        if "[REDACTED" in m.group(0):
            return m.group(0)
        placeholder = "[REDACTED_IP]"
        result.log(m.group(0), placeholder)
        return placeholder

    result.text = _IPV4.sub(_replace_ipv4, result.text)

    # 3. IPv6
    def _replace_ipv6(m: re.Match) -> str:
        placeholder = "[REDACTED_IPV6]"
        result.log(m.group(0), placeholder)
        return placeholder

    result.text = _IPV6.sub(_replace_ipv6, result.text)

    # 4. Hashes
    def _replace_hash(m: re.Match) -> str:
        h = m.group(0)
        length_map = {32: "MD5", 40: "SHA1", 64: "SHA256", 128: "SHA512"}
        algo = length_map.get(len(h), "HASH")
        placeholder = f"[REDACTED_{algo}_HASH]"
        result.log(h, placeholder)
        return placeholder

    result.text = _HASH.sub(_replace_hash, result.text)

    # 5. URL host redaction — keep scheme + path
    def _replace_url(m: re.Match) -> str:
        scheme, host, path = m.group(1), m.group(2), m.group(3)
        placeholder = f"{scheme}[REDACTED_HOST]{path}"
        result.log(host, "[REDACTED_HOST]")
        return placeholder

    result.text = _URL_HOST.sub(_replace_url, result.text)

    # 6. Flags (optional)
    if redact_flags:
        def _replace_flag(m: re.Match) -> str:
            placeholder = f"{m.group(1)}{{[REDACTED_FLAG]}}"
            result.log(m.group(0), placeholder)
            return placeholder

        result.text = _FLAG.sub(_replace_flag, result.text)

    return result
