"""Profile 登录会话管理。

参照 Browserless Authenticated Profiles 的流程：
  POST /profile → 启动 Chrome → 登录 → Browserless.saveProfile → 持久化

提供两种模式：
- manual：启动可见 Chrome，用户人工登录后触发保存
- auto：Playwright 自动填写凭据并提交
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from agenttest_plugin_codex.chrome_pool import start_profile, stop_profile
from agenttest_plugin_codex.profile_registry import (
    BrowserProfile,
    update_profile,
)

# ── 登录态采集 ────────────────────────────────────────


async def setup_profile_login(
    profile: BrowserProfile,
    login_url: str,
    *,
    credentials: dict[str, str] | None = None,
    headless: bool = False,
    manual_timeout_seconds: int = 300,
) -> str:
    """为 Profile 执行登录并采集 storageState。

    流程：
    1. 启动 Chrome（带 profile.user_data_dir）
    2. connect_over_cdp，创建 Playwright context
    3. 导航到 login_url
    4. 若 credentials 非空：自动登录
       若 credentials 为空（manual 模式）：等待人工完成
    5. context.storage_state() → 保存 JSON
    6. 更新 profile.storage_state_path

    Args:
        profile: 浏览器实例配置
        login_url: 登录页面 URL
        credentials: 凭据 {"username": "...", "password": "..."}，空则人工登录
        headless: 是否无头（人工登录时必须 False）
        manual_timeout_seconds: 人工登录超时（秒）

    Returns:
        保存的 storageState 文件路径
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore[import-not-found]
    except ImportError:
        raise RuntimeError("需要安装 playwright: pip install playwright") from None

    # 启动 Chrome
    cdp_endpoint = await start_profile(profile, headless=headless)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(cdp_endpoint)

            # 若已有 storageState，先加载以复用已保存的登录态
            context_kwargs: dict = {}
            if profile.storage_state_path:
                existing = _read_state_file(profile.storage_state_path)
                if existing:
                    context_kwargs["storage_state"] = existing

            context = await browser.new_context(**context_kwargs)
            try:
                page = await context.new_page()
                await page.goto(login_url, wait_until="domcontentloaded", timeout=30000)

                if credentials:
                    await _auto_login(page, credentials)
                else:
                    await _manual_login_wait(page, manual_timeout_seconds)

                # 采集 storageState
                state = await context.storage_state()
                state_json = json.dumps(state, ensure_ascii=False)

                # 保存到文件
                state_dir = _storage_state_dir(profile)
                state_dir.mkdir(parents=True, exist_ok=True)
                state_path = state_dir / "storage-state.json"
                state_path.write_text(state_json)

                # 更新 profile
                update_profile(
                    profile.project_id,
                    profile.profile_id,
                    storage_state_path=str(state_path),
                )

                return str(state_path)
            finally:
                await context.close()
            # browser 无法直接在 connect_over_cdp 模式下 close
            # 由 chrome_pool.stop_profile() 管理
    except Exception:
        # 出错时停止 Chrome
        await stop_profile(profile.profile_id, profile.project_id)
        raise


async def save_profile_storage(
    profile: BrowserProfile,
) -> str:
    """为已运行的 Profile 采集 storageState（不重新登录）。

    适用场景：用户在 Chrome 中完成了人工登录后，
    调用此函数采集当前浏览器状态。

    要求 profile.status == "running"，CDP endpoint 可用。
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore[import-not-found]
    except ImportError:
        raise RuntimeError("需要安装 playwright: pip install playwright") from None

    if profile.status != "running" or not profile.cdp_endpoint:
        raise RuntimeError(f"Profile {profile.profile_id} 未运行，无法采集 storageState")

    endpoint = profile.cdp_endpoint
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(endpoint)
        try:
            # 获取默认 context 或创建新的
            contexts = browser.contexts
            target_context = contexts[0] if contexts else await browser.new_context()
            state = await target_context.storage_state()

            state_json = json.dumps(state, ensure_ascii=False)
            state_dir = _storage_state_dir(profile)
            state_dir.mkdir(parents=True, exist_ok=True)
            state_path = state_dir / "storage-state.json"
            state_path.write_text(state_json)

            update_profile(
                profile.project_id,
                profile.profile_id,
                storage_state_path=str(state_path),
            )
            return str(state_path)
        finally:
            # 不 close browser（connect_over_cdp 下不管理进程）
            pass


# ── 内部辅助 ──────────────────────────────────────────


def _storage_state_dir(profile: BrowserProfile) -> Path:
    """storageState 文件存储目录。"""
    return Path(profile.user_data_dir) / "storage-states"


async def _auto_login(page, credentials: dict[str, str]) -> None:
    """自动填写登录表单并提交。

    查找常见的登录表单元素并填写。
    """
    username = credentials.get("username", "")
    password = credentials.get("password", "")
    if not username and not password:
        return

    await page.wait_for_load_state("networkidle", timeout=10000)
    await asyncio.sleep(1)  # 等待 JS 渲染

    # 尝试常见用户名选择器
    username_selectors = [
        "input[name='username']",
        "input[name='email']",
        "input[type='email']",
        "input[name='user']",
        "input[id='username']",
        "input[id='email']",
        "#username",
        "#email",
    ]
    for sel in username_selectors:
        try:
            await page.fill(sel, username)
            break
        except Exception:
            continue

    # 尝试常见密码选择器
    password_selectors = [
        "input[name='password']",
        "input[type='password']",
        "#password",
    ]
    for sel in password_selectors:
        try:
            await page.fill(sel, password)
            break
        except Exception:
            continue

    # 尝试提交
    submit_selectors = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('登录')",
        "button:has-text('Sign in')",
        "button:has-text('Login')",
        "button:has-text('登 录')",
    ]
    for sel in submit_selectors:
        try:
            await page.click(sel)
            await page.wait_for_load_state("networkidle", timeout=15000)
            break
        except Exception:
            continue

    await asyncio.sleep(2)  # 等待登录后跳转


async def _manual_login_wait(page, timeout_seconds: int) -> None:
    """等待人工登录完成（不超时则在 timeout_seconds 后继续）。

    人工登录模式：页面可见，用户手动完成登录后按 Ctrl+C 或超时。
    """

    print(
        f"\n[Browser Profile] 请在 Chrome 窗口中完成登录。\n"
        f"登录完成后，按 Enter 继续（超时 {timeout_seconds}s）...\n"
    )

    try:
        # 非 headless 模式，等待用户输入或超时
        await asyncio.wait_for(
            _wait_for_enter(),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        print("[Browser Profile] 人工登录超时，保存当前浏览器状态。")
    except Exception:
        pass


async def _wait_for_enter() -> None:
    """在 executor 中等待 stdin 输入（不阻塞事件循环）。"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, input)


def _read_state_file(path: str) -> dict | None:
    """读取 storageState JSON 文件。"""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None
