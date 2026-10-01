# Security Policy

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

If you discover a security issue (e.g., a sanitization bypass that leaks real IPs
or API keys into generated output), please report it privately:

1. Email the maintainer directly - pgx2201@proton.me
2. Or use GitHub's **"Report a vulnerability"** button in the Security tab

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

I aim to acknowledge reports within **50 hours** and release a patch within **~~7-10 days**
for confirmed critical issues.

## Scope

| In scope | Out of scope |
|---|---|
| Sanitizer bypasses (IP/hash leaks) | Issues with third-party AI provider APIs |
| API key exposure in output files | Rate limiting by external providers |
| Path traversal in output directory | Model hallucinations in generated content |

