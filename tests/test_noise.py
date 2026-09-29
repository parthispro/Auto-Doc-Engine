"""
tests/test_noise.py — Unit tests for the noise filtration layer.
"""

import pytest
from autodoc.filters.noise import filter_noise, segment_by_tool


class TestNoiseFilter:
    def test_strips_ansi(self):
        raw = "\x1b[32mSome green text\x1b[0m"
        assert "\x1b" not in filter_noise(raw)
        assert "Some green text" in filter_noise(raw)

    def test_collapses_repeated_ping(self):
        lines = "\n".join(
            [f"64 bytes from 1.1.1.1: icmp_seq={i} ttl=64 time=10.1 ms" for i in range(10)]
        )
        result = filter_noise(lines)
        assert result.count("icmp_seq") == 0  # all ping lines stripped

    def test_marks_failed_connections_as_pivot(self):
        raw = "curl: (7) Failed to connect: Connection refused"
        result = filter_noise(raw, preserve_failures=True)
        assert "[PIVOT" in result
        assert "Connection refused" in result

    def test_drops_failed_connections_when_not_preserving(self):
        raw = "ssh: connect to host 10.0.0.1 port 22: Connection refused"
        result = filter_noise(raw, preserve_failures=False)
        assert "Connection refused" not in result

    def test_collapses_repeated_identical_lines(self):
        raw = "\n".join(["[INFO] Trying..." for _ in range(10)])
        result = filter_noise(raw)
        assert "repeated" in result  # truncation marker added
        assert result.count("[INFO] Trying...") < 10

    def test_strips_gobuster_boilerplate(self):
        raw = (
            "===============================================================\n"
            "Gobuster v3.6\n"
            "by OJ Reeves\n"
            "===============================================================\n"
            "/admin  (Status: 200)"
        )
        result = filter_noise(raw)
        assert "Gobuster v3" not in result
        assert "/admin" in result


class TestSegmentByTool:
    def test_segments_nmap(self):
        raw = "nmap -sV 10.0.0.1\nPORT  STATE  SERVICE\n80/tcp open  http"
        segs = segment_by_tool(raw)
        assert "nmap" in segs

    def test_segments_gdb(self):
        raw = "gef> break *main\ngef> run\ngef> x/20x $rsp"
        segs = segment_by_tool(raw)
        assert "gdb/gef" in segs

    def test_unknown_goes_to_other(self):
        raw = "some random output line"
        segs = segment_by_tool(raw)
        assert "_other" in segs
