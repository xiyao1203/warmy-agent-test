"""Codex browser profile execution policy tests."""

from __future__ import annotations

from agenttest_api_runner.workflow import _codex_browser_mode


def test_browser_profile_defaults_to_persistent_mode() -> None:
    assert _codex_browser_mode({}, {"browser_profile_id": "profile-1"}) == "persistent"


def test_case_browser_profile_defaults_to_persistent_mode() -> None:
    assert _codex_browser_mode({"browser_profile_id": "profile-1"}, {}) == "persistent"


def test_explicit_browser_mode_wins() -> None:
    assert (
        _codex_browser_mode(
            {"browser_mode": "ephemeral", "browser_profile_id": "profile-1"},
            {"browser_profile_id": "profile-2"},
        )
        == "ephemeral"
    )


def test_without_browser_profile_keeps_ephemeral_mode() -> None:
    assert _codex_browser_mode({}, {}) == "ephemeral"
