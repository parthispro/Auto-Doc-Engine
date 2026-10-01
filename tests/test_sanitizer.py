"""
tests/test_sanitizer.py — Unit tests for the sanitization layer.
"""

from autodoc.filters.sanitizer import sanitize


class TestIPRedaction:
    def test_public_ipv4(self):
        result = sanitize("target is at 8.8.8.8 and 1.1.1.1")
        assert "8.8.8.8" not in result.text
        assert "1.1.1.1" not in result.text
        assert "[REDACTED_IP]" in result.text

    def test_private_ipv4(self):
        result = sanitize("pivot to 192.168.1.100 via 10.0.0.1")
        assert "192.168.1.100" not in result.text
        assert "10.0.0.1" not in result.text
        assert "[REDACTED_PRIVATE_IP]" in result.text

    def test_no_false_positive_versions(self):
        result = sanitize("Python 3.14.6 is installed")
        # Version numbers like 3.14.6 should NOT be redacted (only 4 octets)
        assert "3.14.6" in result.text


class TestHashRedaction:
    def test_md5(self):
        result = sanitize("hash: 5f4dcc3b5aa765d61d8327deb882cf99")
        assert "5f4dcc3b5aa765d61d8327deb882cf99" not in result.text
        assert "[REDACTED_MD5_HASH]" in result.text

    def test_sha256(self):
        h = "a" * 64
        result = sanitize(f"sha256: {h}")
        assert h not in result.text
        assert "[REDACTED_SHA256_HASH]" in result.text

    def test_replacement_logged(self):
        h = "b" * 40  # SHA1
        result = sanitize(h)
        assert any(h in orig for orig, _ in result.replacements)


class TestURLRedaction:
    def test_url_host_redacted(self):
        result = sanitize("curl http://target.ctf.local/api/flag")
        assert "target.ctf.local" not in result.text
        assert "[REDACTED_HOST]" in result.text
        # Path should be preserved
        assert "/api/flag" in result.text

    def test_https(self):
        result = sanitize("GET https://ctf-box.hackthebox.eu/endpoint")
        assert "ctf-box.hackthebox.eu" not in result.text
        assert "https://[REDACTED_HOST]/endpoint" in result.text


class TestFlagRedaction:
    def test_flag_preserved_by_default(self):
        result = sanitize("FLAG{s3cr3t_v4lu3_here}")
        assert "FLAG{s3cr3t_v4lu3_here}" in result.text

    def test_flag_redacted_when_requested(self):
        result = sanitize("CTF{th1s_1s_th3_fl4g}", redact_flags=True)
        assert "th1s_1s_th3_fl4g" not in result.text
        assert "[REDACTED_FLAG]" in result.text
