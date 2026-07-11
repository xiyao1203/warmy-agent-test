from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import socket
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast
from urllib.error import URLError
from urllib.request import urlopen
from uuid import UUID

from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


def normalise_login_url(login_url: str, target_domain: str) -> str:
    value = (login_url or target_domain or "").strip()
    if not value:
        return "about:blank"
    return value if re.match(r"^https?://", value, re.IGNORECASE) else f"https://{value}"


def find_browser_executable() -> str:
    configured = os.environ.get("AGENTTEST_CHROME_PATH", "").strip()
    candidates = [
        configured,
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
        shutil.which("google-chrome") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("未找到 Chrome/Chromium，请安装浏览器或设置 AGENTTEST_CHROME_PATH")


def find_free_port(start: int = 9222) -> int:
    for port in range(start, start + 1000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("无法找到空闲 CDP 端口")


def read_cdp_endpoint(port: int) -> str:
    with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=0.5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    endpoint = payload.get("webSocketDebuggerUrl")
    if not isinstance(endpoint, str) or not endpoint.startswith("ws://127.0.0.1:"):
        raise RuntimeError("Chrome 未返回安全的本地 CDP 地址")
    return endpoint


def wait_for_cdp(port: int, timeout_seconds: float = 10) -> str:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return read_cdp_endpoint(port)
        except (OSError, RuntimeError, URLError) as error:
            last_error = error
            time.sleep(0.2)
    raise RuntimeError(f"Chrome 启动超时，无法连接本地 CDP: {last_error}")


def profile_owner_pid(profile_dir: Path) -> int | None:
    lock = profile_dir / "SingletonLock"
    try:
        if not lock.is_symlink():
            return None
        pid = int(os.readlink(lock).rsplit("-", 1)[-1])
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def cleanup_stale_singletons(profile_dir: Path) -> None:
    if profile_owner_pid(profile_dir):
        return
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie", "DevToolsActivePort"):
        path = profile_dir / name
        try:
            if path.exists() or path.is_symlink():
                path.unlink()
        except OSError:
            continue


class ManagedBrowserProfileRuntime:
    def __init__(
        self,
        root: Path,
        *,
        playwright_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._root = root.expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._root.chmod(0o700)
        self._processes: dict[UUID, subprocess.Popen] = {}
        if playwright_factory is None:
            from playwright.sync_api import sync_playwright

            playwright_factory = sync_playwright
        self._playwright_factory = playwright_factory

    def profile_dir(self, profile_id: UUID) -> str:
        return str(self._root / str(profile_id) / "profile")

    async def start(self, profile: BrowserProfile, login_url: str) -> None:
        await asyncio.to_thread(self._start_sync, profile, login_url)

    def _start_sync(self, profile: BrowserProfile, login_url: str) -> None:
        process = self._processes.get(profile.id)
        if process is not None and process.poll() is None and profile.cdp_port:
            profile.cdp_endpoint = wait_for_cdp(profile.cdp_port, 3)
            profile.status = "running"
            return
        profile_dir = Path(profile.user_data_dir or self.profile_dir(profile.id)).resolve()
        if self._root not in profile_dir.parents:
            raise RuntimeError("浏览器实例目录不在受控运行时根目录")
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_dir.chmod(0o700)
        cleanup_stale_singletons(profile_dir)
        port = find_free_port()
        command = [
            find_browser_executable(),
            f"--remote-debugging-port={port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--new-window",
            normalise_login_url(login_url, profile.target_domain),
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._processes[profile.id] = process
        try:
            endpoint = wait_for_cdp(port, 10)
        except Exception:
            self._stop_sync(profile.id)
            raise
        profile.user_data_dir = str(profile_dir)
        profile.cdp_port = port
        profile.cdp_endpoint = endpoint
        profile.status = "running"

    async def stop(self, profile_id: UUID) -> None:
        await asyncio.to_thread(self._stop_sync, profile_id)

    def _stop_sync(self, profile_id: UUID) -> None:
        process = self._processes.pop(profile_id, None)
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    async def export_storage_state(self, profile: BrowserProfile) -> dict:
        return await asyncio.to_thread(self._export_storage_state_sync, profile)

    def _export_storage_state_sync(self, profile: BrowserProfile) -> dict:
        endpoint = profile.cdp_endpoint or (
            f"http://127.0.0.1:{profile.cdp_port}" if profile.cdp_port else ""
        )
        if not endpoint:
            raise RuntimeError("浏览器实例未运行，无法导出登录态")
        with self._playwright_factory() as playwright:
            browser = playwright.chromium.connect_over_cdp(endpoint)
            contexts = list(browser.contexts or [])
            if not contexts:
                raise RuntimeError("浏览器上下文未就绪")
            state = contexts[0].storage_state(indexed_db=True)
        if not isinstance(state, dict):
            raise RuntimeError("浏览器登录态导出格式无效")
        return state

    async def verify(self, profile: BrowserProfile, storage_state: dict) -> bool:
        return await asyncio.to_thread(self._verify_sync, profile, storage_state)

    def _verify_sync(self, profile: BrowserProfile, storage_state: dict) -> bool:
        target_url = normalise_login_url("", profile.target_domain)
        with self._playwright_factory() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(storage_state=cast(Any, storage_state))
            try:
                page = context.new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=30_000)
                final_url = str(page.url or "").lower()
                return not any(marker in final_url for marker in ("/login", "/signin", "/sign-in"))
            finally:
                context.close()
                browser.close()
