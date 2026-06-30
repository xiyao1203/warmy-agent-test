"""Unit tests for security scanner adapters."""

from __future__ import annotations

import pytest
from agenttest.modules.security.adapters import (
    ScannerUnavailableError,
    create_scanner,
)
from agenttest.modules.security.adapters.promptfoo_adapter import (
    PromptfooOutputError,
    PromptfooScanner,
    _redact_tool_error,
)


def test_create_scanner_rejects_missing_binary() -> None:
    with pytest.raises(
        ScannerUnavailableError,
        match="Promptfoo runtime is not installed",
    ):
        create_scanner(promptfoo_bin="nonexistent_promptfoo_binary")


def test_invalid_promptfoo_output_is_not_converted_to_a_finding() -> None:
    scanner = PromptfooScanner("/usr/bin/promptfoo")

    with pytest.raises(PromptfooOutputError, match="invalid JSON"):
        scanner._parse_output("not-json")


def test_scanner_requires_a_real_agent_endpoint() -> None:
    scanner = PromptfooScanner("/usr/bin/promptfoo")

    with pytest.raises(ValueError, match="agent_endpoint is required"):
        scanner._build_config(None, "full")


def test_promptfoo_error_redacts_bearer_tokens() -> None:
    assert "secret-value" not in _redact_tool_error(
        "request failed Authorization: Bearer secret-value"
    )
