"""Unit tests for security scanner adapters."""

from __future__ import annotations

import pytest

from agenttest.modules.security.adapters import create_scanner
from agenttest.modules.security.adapters.mock_scanner import MockScanner


@pytest.mark.asyncio
async def test_mock_scanner_returns_findings() -> None:
    scanner = MockScanner()
    findings = await scanner.run_scan()
    assert len(findings) == 3
    assert findings[0]["category"] == "injection"
    assert findings[1]["category"] == "leak"
    assert findings[2]["category"] == "jailbreak"


@pytest.mark.asyncio
async def test_mock_scanner_findings_have_required_fields() -> None:
    scanner = MockScanner()
    findings = await scanner.run_scan()
    for f in findings:
        assert "category" in f
        assert "severity" in f
        assert "title" in f
        assert "description" in f
        assert "score" in f


@pytest.mark.asyncio
async def test_create_scanner_returns_mock_when_promptfoo_missing() -> None:
    # Promptfoo not installed in test env, should fallback to MockScanner
    scanner = create_scanner(promptfoo_bin="nonexistent_promptfoo_binary")
    assert isinstance(scanner, MockScanner)
    findings = await scanner.run_scan()
    assert len(findings) > 0
