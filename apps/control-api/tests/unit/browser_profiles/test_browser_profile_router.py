from __future__ import annotations

import os
import subprocess
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


def test_launch_existing_running_profile_opens_login_url(monkeypatch, tmp_path: Path) -> None:
    opened: list[tuple[int, str]] = []
    monkeypatch.setattr(
        router, "_read_cdp_endpoint", lambda _port: "ws://127.0.0.1:9222/devtools/browser/abc"
    )
    monkeypatch.setattr(router, "_open_cdp_url", lambda port, url: opened.append((port, url)))

    profile = {
        "profile_id": "profile-1",
        "project_id": "project-1",
        "cdp_port": 9222,
        "status": "running",
        "target_domain": "app.example.com",
        "user_data_dir": str(tmp_path),
    }

    assert (
        router._launch_browser_profile(profile, "https://app.example.com/login")
        == "ws://127.0.0.1:9222/devtools/browser/abc"
    )
    assert opened == [(9222, "https://app.example.com/login")]


def test_launch_stopped_profile_replaces_busy_port(monkeypatch, tmp_path: Path) -> None:
    launched: list[list[str]] = []
    monkeypatch.setattr(router, "_is_port_free", lambda port: port == 9223)
    monkeypatch.setattr(router, "_find_browser_executable", lambda: "/bin/echo")
    monkeypatch.setattr(router, "_find_free_port", lambda _start=9222: 9223)
    monkeypatch.setattr(
        router, "_wait_for_cdp", lambda port: f"ws://127.0.0.1:{port}/devtools/browser/abc"
    )
    monkeypatch.setattr(router, "_used_ports", lambda _project_id: {9222})

    class FakeProcess:
        def poll(self) -> int | None:
            return None

        def kill(self) -> None:
            return None

    def fake_popen(args: list[str], **_kwargs) -> FakeProcess:
        launched.append(args)
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    profile = {
        "profile_id": "profile-1",
        "project_id": "project-1",
        "cdp_port": 9222,
        "status": "stopped",
        "target_domain": "app.example.com",
        "user_data_dir": str(tmp_path),
    }

    endpoint = router._launch_browser_profile(profile, "")

    assert endpoint == "ws://127.0.0.1:9223/devtools/browser/abc"
    assert profile["cdp_port"] == 9223
    assert "--remote-debugging-port=9223" in launched[0]


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
