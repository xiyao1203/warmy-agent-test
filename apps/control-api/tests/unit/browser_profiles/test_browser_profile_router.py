from __future__ import annotations

import os
from pathlib import Path

from agenttest.modules.browser_profiles.api import router


def test_normalise_login_url_uses_explicit_url() -> None:
    assert (
        router._normalise_login_url("https://app.example.com/login", "app.example.com")
        == "https://app.example.com/login"
    )


def test_normalise_login_url_adds_https_to_domain() -> None:
    assert router._normalise_login_url("", "app.example.com") == "https://app.example.com"
    assert (
        router._normalise_login_url("app.example.com/login", "") == "https://app.example.com/login"
    )


def test_find_browser_executable_uses_configured_path(tmp_path: Path, monkeypatch) -> None:
    browser = tmp_path / "chrome"
    browser.write_text("#!/bin/sh\n")
    browser.chmod(0o755)
    monkeypatch.setenv("AGENTTEST_CHROME_PATH", str(browser))

    assert router._find_browser_executable() == str(browser)


def test_find_browser_executable_reports_missing(monkeypatch) -> None:
    monkeypatch.setenv("AGENTTEST_CHROME_PATH", "/missing/chrome")
    monkeypatch.setattr(router.shutil, "which", lambda _name: None)
    original_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if str(self).startswith("/Applications/"):
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(os, "access", lambda *_args: False)

    try:
        router._find_browser_executable()
    except RuntimeError as exc:
        assert "未找到 Chrome/Chromium" in str(exc)
    else:
        raise AssertionError("expected missing browser error")
