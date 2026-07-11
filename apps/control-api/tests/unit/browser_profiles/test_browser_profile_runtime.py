from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.browser_profiles.infrastructure import runtime


def profile(tmp_path: Path) -> BrowserProfile:
    item = BrowserProfile.create(
        project_id=uuid4(),
        name="TapNow",
        target_domain="app.tapnow.ai",
        created_by=uuid4(),
        now=datetime.now(UTC),
    )
    item.user_data_dir = str(tmp_path / "profile")
    return item


def test_normalise_login_url_uses_url_or_domain() -> None:
    assert (
        runtime.normalise_login_url("https://app.example.com/login", "app.example.com")
        == "https://app.example.com/login"
    )
    assert runtime.normalise_login_url("", "app.example.com") == "https://app.example.com"


def test_start_binds_cdp_to_loopback_and_persists_profile_dir(monkeypatch, tmp_path: Path) -> None:
    launched: list[list[str]] = []
    monkeypatch.setattr(runtime, "find_browser_executable", lambda: "/bin/echo")
    monkeypatch.setattr(runtime, "find_free_port", lambda _start=9222: 9333)
    monkeypatch.setattr(
        runtime,
        "wait_for_cdp",
        lambda port, _timeout=10: f"ws://127.0.0.1:{port}/devtools/browser/id",
    )

    class Process:
        pid = 123

        def poll(self):
            return None

    def popen(args, **_kwargs):
        launched.append(args)
        return Process()

    monkeypatch.setattr(runtime.subprocess, "Popen", popen)
    item = profile(tmp_path)
    manager = runtime.ManagedBrowserProfileRuntime(tmp_path / "profiles")
    item.user_data_dir = manager.profile_dir(item.id)

    manager._start_sync(item, "https://app.tapnow.ai/login")

    assert item.status == "running"
    assert item.cdp_port == 9333
    assert item.cdp_endpoint.startswith("ws://127.0.0.1:9333/")
    assert "--remote-debugging-address=127.0.0.1" in launched[0]
    assert f"--user-data-dir={item.user_data_dir}" in launched[0]


def test_cleanup_stale_singletons_preserves_live_profile_files(monkeypatch, tmp_path: Path) -> None:
    item = profile(tmp_path)
    profile_dir = Path(item.user_data_dir)
    profile_dir.mkdir(parents=True)
    (profile_dir / "Cookies").write_text("keep")
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie", "DevToolsActivePort"):
        (profile_dir / name).write_text("stale")
    monkeypatch.setattr(runtime, "profile_owner_pid", lambda _path: None)

    runtime.cleanup_stale_singletons(profile_dir)

    assert (profile_dir / "Cookies").read_text() == "keep"
    assert not (profile_dir / "SingletonLock").exists()
    assert not (profile_dir / "SingletonSocket").exists()
    assert not (profile_dir / "SingletonCookie").exists()
    assert not (profile_dir / "DevToolsActivePort").exists()


def test_stop_terminates_then_kills_unresponsive_process(tmp_path: Path) -> None:
    calls: list[str] = []

    class Process:
        def poll(self):
            return None

        def terminate(self):
            calls.append("terminate")

        def wait(self, timeout):
            calls.append(f"wait:{timeout}")
            raise runtime.subprocess.TimeoutExpired("chrome", timeout)

        def kill(self):
            calls.append("kill")

    profile_id = uuid4()
    manager = runtime.ManagedBrowserProfileRuntime(tmp_path)
    manager._processes[profile_id] = Process()

    manager._stop_sync(profile_id)

    assert calls == ["terminate", "wait:5", "kill"]
    assert profile_id not in manager._processes


def test_export_storage_state_includes_indexed_db(tmp_path: Path) -> None:
    calls: list[object] = []

    class Context:
        def storage_state(self, **kwargs):
            calls.append(kwargs)
            return {"cookies": [], "origins": []}

    class Browser:
        contexts = [Context()]

    class Chromium:
        def connect_over_cdp(self, endpoint):
            calls.append(endpoint)
            return Browser()

    class Playwright:
        chromium = Chromium()

    class Manager:
        def __enter__(self):
            return Playwright()

        def __exit__(self, *_args):
            return None

    item = profile(tmp_path)
    item.status = "running"
    item.cdp_endpoint = "ws://127.0.0.1:9333/devtools/browser/id"
    manager = runtime.ManagedBrowserProfileRuntime(tmp_path, playwright_factory=lambda: Manager())

    state = manager._export_storage_state_sync(item)

    assert state == {"cookies": [], "origins": []}
    assert calls == [item.cdp_endpoint, {"indexed_db": True}]
