"""Chrome 进程池。

管理多个持久 Chrome 实例，每个实例绑定一个 BrowserProfile。

替换 codex_invoker.py 中的全局单例模式：
  _PERSISTENT_CHROME_PROCESS / _CDP_WS_ENDPOINT
  → _chrome_pool: dict[str, ChromeInstance]
"""

from __future__ import annotations

import asyncio
import atexit
import http.client
import json
import shutil
import signal
from dataclasses import dataclass
from pathlib import Path

from agenttest_plugin_codex.profile_registry import (
    BrowserProfile,
    update_profile,
)

# ── Chromium 查找 ─────────────────────────────────────

def _find_chromium() -> str:
    """查找 Chromium/Chrome 可执行文件路径。"""
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    # Playwright 缓存路径（macOS）
    pw_cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    if pw_cache.is_dir():
        for entry in sorted(pw_cache.iterdir(), reverse=True):
            if not entry.name.startswith("chromium-"):
                continue
            for subdir, app_name, exe_name in (
                ("chrome-mac", "Chromium.app", "Chromium"),
                ("chrome-mac-arm64", "Google Chrome for Testing.app",
                 "Google Chrome for Testing"),
            ):
                candidate = (
                    entry / subdir / app_name / "Contents" / "MacOS" / exe_name
                )
                if candidate.is_file():
                    return str(candidate)
            for exe in sorted(entry.rglob("Chromium"), reverse=True):
                if exe.is_file() and "Contents/MacOS/" in str(exe):
                    return str(exe)
            for exe in sorted(
                entry.rglob("Google Chrome for Testing"), reverse=True,
            ):
                if exe.is_file() and "Contents/MacOS/" in str(exe):
                    return str(exe)
    # Linux 缓存路径
    pw_cache_linux = Path.home() / ".cache" / "ms-playwright"
    if pw_cache_linux.is_dir():
        for entry in sorted(pw_cache_linux.iterdir(), reverse=True):
            if entry.name.startswith("chromium-"):
                candidate = entry / "chrome-linux" / "chrome"
                if candidate.is_file():
                    return str(candidate)
    raise RuntimeError(
        "未找到 Chromium/Chrome，请安装: npx playwright install chromium"
    )


# ── CDP 辅助 ──────────────────────────────────────────

def _http_get(path: str, host: str = "127.0.0.1", port: int = 9222) -> str | None:
    """同步 HTTP GET，返回响应体或 None。"""
    try:
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("GET", path)
        resp = conn.getresponse()
        if resp.status == 200:
            return resp.read().decode()
        return None
    except Exception:
        return None


async def _cdp_health_check(endpoint: str) -> bool:
    """检查 CDP endpoint 是否存活（非阻塞）。"""
    import re as _re

    m = _re.match(r"ws://([^:/]+):(\d+)", endpoint)
    if not m:
        return False
    host, port = m.group(1), int(m.group(2))

    loop = asyncio.get_event_loop()

    def _check() -> bool:
        return _http_get("/json/version", host, port) is not None

    return await loop.run_in_executor(None, _check)


async def _wait_for_cdp(port: int, wait_seconds: int = 10) -> str:
    """轮询等待 CDP 就绪，返回 WebSocket endpoint。"""

    def _poll() -> tuple[bool, str]:
        body = _http_get("/json/version", port=port)
        if body:
            data = json.loads(body)
            ws = data.get("webSocketDebuggerUrl", "")
            if ws:
                return True, ws
        return False, ""

    loop = asyncio.get_event_loop()
    deadline = loop.time() + wait_seconds
    while loop.time() < deadline:
        ok, ws = await loop.run_in_executor(None, _poll)
        if ok:
            return ws
        await asyncio.sleep(0.5)
    raise RuntimeError(f"Chrome CDP 未在 {wait_seconds}s 内就绪（端口 {port}）")


# ── 进程池 ────────────────────────────────────────────

@dataclass
class ChromeInstance:
    """运行中的 Chrome 实例。"""

    profile_id: str
    process: asyncio.subprocess.Process
    cdp_endpoint: str
    cdp_port: int


_chrome_pool: dict[str, ChromeInstance] = {}


async def start_profile(
    profile: BrowserProfile,
    headless: bool = True,
) -> str:
    """启动 Profile 对应的 Chrome 实例，返回 CDP WebSocket endpoint。

    如果实例已在运行且 CDP 健康，直接复用。
    """
    if profile.profile_id in _chrome_pool:
        existing = _chrome_pool[profile.profile_id]
        if await _cdp_health_check(existing.cdp_endpoint):
            return existing.cdp_endpoint
        # 旧进程已死，清理
        await _cleanup_dead(existing)

    return await _launch_chrome(profile, headless)


async def _launch_chrome(profile: BrowserProfile, headless: bool) -> str:
    """启动新的 Chrome 进程（非阻塞）。"""
    chromium = _find_chromium()
    args = [
        chromium,
        f"--remote-debugging-port={profile.cdp_port}",
        f"--user-data-dir={profile.user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if headless:
        args.append("--headless=new")

    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        cdp_endpoint = await _wait_for_cdp(profile.cdp_port, wait_seconds=10)
    except RuntimeError:
        try:
            process.kill()
        except Exception:
            pass
        await process.wait()
        raise

    instance = ChromeInstance(
        profile_id=profile.profile_id,
        process=process,
        cdp_endpoint=cdp_endpoint,
        cdp_port=profile.cdp_port,
    )
    _chrome_pool[profile.profile_id] = instance

    # 更新 registry 状态
    update_profile(
        profile.project_id,
        profile.profile_id,
        status="running",
        cdp_endpoint=cdp_endpoint,
    )

    return cdp_endpoint


async def stop_profile(profile_id: str, project_id: str = "") -> None:
    """停止 Profile 对应的 Chrome 实例，保留 user-data-dir。"""
    instance = _chrome_pool.pop(profile_id, None)
    if instance is None:
        return

    await _terminate_process(instance.process)

    if project_id:
        update_profile(project_id, profile_id, status="stopped", cdp_endpoint="")


def get_profile_endpoint(profile_id: str) -> str | None:
    """获取运行中实例的 CDP endpoint，不在运行返回 None。"""
    instance = _chrome_pool.get(profile_id)
    if instance is None:
        return None
    return instance.cdp_endpoint


def stop_all() -> None:
    """停止所有 Chrome 实例（atexit 回调）。"""
    for instance in list(_chrome_pool.values()):
        try:
            instance.process.kill()
        except Exception:
            pass
    _chrome_pool.clear()


async def _terminate_process(process: asyncio.subprocess.Process) -> None:
    """优雅终止 Chrome 进程：SIGTERM → 5s 超时 → SIGKILL。"""
    try:
        process.send_signal(signal.SIGTERM)
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except TimeoutError:
            process.kill()
            await process.wait()
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


async def _cleanup_dead(instance: ChromeInstance) -> None:
    """清理已死亡的 Chrome 进程引用。"""
    try:
        instance.process.kill()
    except Exception:
        pass
    _chrome_pool.pop(instance.profile_id, None)


# ── atexit ────────────────────────────────────────────

atexit.register(stop_all)


# ── 兼容旧接口 ────────────────────────────────────────

# _find_chromium, _cdp_health_check, _wait_for_cdp 由 codex_invoker.py
# 通过 import 复用，保持函数签名兼容。
