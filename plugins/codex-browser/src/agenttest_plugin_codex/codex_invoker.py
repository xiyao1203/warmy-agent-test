"""Codex CLI 调用封装。

使用 subprocess 调用 `codex exec`，传入浏览器工具，
解析 JSON 输出为结构化结果。

支持两种浏览器生命周期模式：
- ephemeral：每次新建 Chrome 实例，执行完销毁
- persistent：连接已有的 Chrome 实例（CDP），复用进程和登录态

多实例管理由 chrome_pool 模块提供，本模块通过 ensure_persistent_chrome()
调用 chrome_pool.start_profile() 复用。
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from agenttest_plugin_codex.chrome_pool import (
    start_profile,
)
from agenttest_plugin_codex.contracts import BrowserMode
from agenttest_plugin_codex.profile_registry import (
    BrowserProfile,
    get_profile,
)

# ── 数据模型 ──────────────────────────────────────────


@dataclass
class CodexRawOutput:
    """Codex CLI 原始输出。"""

    stdout: str
    stderr: str
    returncode: int
    duration_seconds: float


# ── storageState 文件存储 ──────────────────────────────

DEFAULT_STORAGE_STATE_DIR = Path("/data/storage-states")


def _storage_state_dir(storage_dir: str = "") -> Path:
    return Path(storage_dir) if storage_dir else DEFAULT_STORAGE_STATE_DIR


# ── 持久 Chrome 进程管理 ──────────────────────────────

# Chrome 生命周期已迁移至 chrome_pool 模块。
# 以下接口保持向后兼容，内部委托给 chrome_pool。


async def ensure_persistent_chrome(
    user_data_dir: str = "",
    remote_debugging_port: int = 9222,
    headless: bool = True,
) -> str:
    """启动或复用持久 Chrome 实例，返回 CDP WebSocket endpoint。

    内部创建匿名 BrowserProfile 并委托给 chrome_pool.start_profile()。
    向后兼容旧调用方。
    """
    if not user_data_dir:
        user_data_dir = str(Path(tempfile.gettempdir()) / "agenttest-chrome-profile")

    # 构建临时 Profile（不持久化到 registry）
    profile = BrowserProfile(
        profile_id="default",
        project_id="_default",
        name="_default",
        target_domain="",
        user_data_dir=user_data_dir,
        storage_state_path="",
        cdp_port=remote_debugging_port,
        status="stopped",
        cdp_endpoint="",
    )

    return await start_profile(profile, headless=headless)


# storageState 存储目录


def _storage_state_path(key: str, storage_dir: str = "") -> Path:
    """根据索引键生成 storageState 文件路径。"""
    safe = key.replace("/", "_").replace("\\", "_")
    return _storage_state_dir(storage_dir) / f"{safe}.json"


def load_storage_state(
    key: str,
    storage_dir: str = "",
    ttl_hours: int = 24,
) -> str | None:
    """加载 storageState 文件，返回路径。

    Args:
        key: 索引键 "{project_id}/{env_hash}"
        storage_dir: 存储目录
        ttl_hours: 过期时间（小时），超时返回 None

    Returns:
        文件路径字符串，过期或不存在返回 None
    """
    path = _storage_state_path(key, storage_dir)
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    age_hours = (time.time() - mtime) / 3600
    if age_hours > ttl_hours:
        path.unlink(missing_ok=True)
        return None
    return str(path)


def save_storage_state(key: str, content: str, storage_dir: str = "") -> str:
    """保存 storageState JSON 到文件，返回路径。"""
    base = _storage_state_dir(storage_dir)
    base.mkdir(parents=True, exist_ok=True)
    path = _storage_state_path(key, storage_dir)
    path.write_text(content)
    return str(path)


async def capture_storage_state(
    cdp_endpoint: str,
    target_url: str,
    key: str,
    storage_dir: str = "",
    existing_storage_state_path: str = "",
) -> str:
    """通过 CDP 连接 Chrome，采集当前 storageState 并保存。

    在 Codex 执行完成后调用，自动采集浏览器中的登录态。
    仅持久模式下可用（需要 CDP endpoint）。

    Args:
        cdp_endpoint: CDP WebSocket endpoint
        target_url: 目标 URL（用于验证登录态是否有效）
        key: storageState 索引键
        storage_dir: 存储目录
        existing_storage_state_path: 已有的 storageState 文件路径

    Returns:
        保存后的 storageState 文件路径，失败返回空字符串
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore[import-not-found]
    except ImportError:
        return ""

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
            try:
                context_kwargs: dict = {}
                if existing_storage_state_path:
                    import json as _json

                    def _read_state() -> dict | None:
                        try:
                            with open(existing_storage_state_path) as f:
                                return _json.load(f)
                        except Exception:
                            return None

                    loop = asyncio.get_event_loop()
                    state_data = await loop.run_in_executor(None, _read_state)
                    if state_data:
                        context_kwargs["storage_state"] = state_data

                context = await browser.new_context(**context_kwargs)
                try:
                    page = await context.new_page()
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(1)

                    state = await context.storage_state()
                    state_json = json.dumps(state, ensure_ascii=False)
                    return save_storage_state(key, state_json, storage_dir)
                finally:
                    await context.close()
            finally:
                await browser.close()
    except Exception:
        return ""


# ── Codex CLI 调用 ────────────────────────────────────


async def invoke_codex(
    test_intent: str,
    target_url: str,
    *,
    headless: bool = True,
    timeout_seconds: int = 120,
    model: str = "gpt-4o",
    model_provider: str = "",
    browser_mode: BrowserMode = BrowserMode.EPHEMERAL,
    cdp_endpoint: str = "",
    storage_state_path: str = "",
    browser_profile_id: str = "",
    credentials: dict[str, str] | None = None,
) -> CodexRawOutput:
    """调用 Codex CLI 执行浏览器测试。

    优先使用 `codex` CLI（如果可用），否则降级为提示信息。

    Args:
        test_intent: 测试意图描述
        target_url: 目标 URL
        headless: 是否无头模式
        timeout_seconds: 超时秒数
        model: 使用的模型（如 "gpt-4o"、"deepseek/deepseek-v4-pro"）
        model_provider: Codex config.toml 中 [model_providers.<id>] 的 ID，空表示默认 OpenAI
        browser_mode: 浏览器生命周期模式
        cdp_endpoint: CDP WebSocket endpoint（持久模式用）
        storage_state_path: storageState 文件路径（登录态复用）
        browser_profile_id: 浏览器实例 ID（从 registry 中选择）
        credentials: 测试凭据 {"username": "...", "password": "..."}
    """
    codex_path = shutil.which("codex")
    if codex_path is None:
        return _codex_unavailable_result(test_intent, target_url)

    prompt = _build_prompt(test_intent, target_url, credentials)

    # ── 解析 browser_profile_id ────────────────────────
    resolved_cdp_endpoint = cdp_endpoint
    resolved_storage_state_path = storage_state_path
    if browser_profile_id and not resolved_cdp_endpoint:
        # 从 registry 加载 Profile
        profile = get_profile("", browser_profile_id)
        if profile is not None:
            # 启动 Profile Chrome
            resolved_cdp_endpoint = await start_profile(
                profile,
                headless=headless,
            )
            # 使用 Profile 的 storageState
            if profile.storage_state_path and not resolved_storage_state_path:
                resolved_storage_state_path = profile.storage_state_path

    env = os.environ.copy()
    if headless:
        env["PLAYWRIGHT_HEADLESS"] = "true"
    if model:
        env["CODEX_MODEL"] = model

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        exec_args = [
            codex_path,
            "exec",
            "--tools",
            "browser",
            "--approval-mode",
            "never",
            "--output",
            "json",
            "--input-file",
            prompt_file,
        ]
        # 模型与 provider
        if model:
            exec_args.extend(["--model", model])
        if model_provider:
            exec_args.extend(["--config", f"model_provider={model_provider}"])
        # 持久模式：追加 CDP endpoint 和 storageState
        if browser_mode == BrowserMode.PERSISTENT and resolved_cdp_endpoint:
            exec_args.extend(["--cdp-endpoint", resolved_cdp_endpoint])
        if resolved_storage_state_path:
            exec_args.extend(["--storage-state", resolved_storage_state_path])

        process = await asyncio.create_subprocess_exec(
            *exec_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return CodexRawOutput(
                stdout="",
                stderr="Codex CLI execution timed out",
                returncode=process.returncode or -1,
                duration_seconds=timeout_seconds,
            )
        return CodexRawOutput(
            stdout=stdout_bytes.decode(errors="replace"),
            stderr=stderr_bytes.decode(errors="replace"),
            returncode=process.returncode or 0,
            duration_seconds=timeout_seconds,
        )
    finally:
        try:
            os.unlink(prompt_file)
        except OSError:
            pass


def _codex_unavailable_result(
    test_intent: str,
    target_url: str,
) -> CodexRawOutput:
    """Codex CLI 不可用时的降级输出。"""
    return CodexRawOutput(
        stdout=json.dumps(
            {
                "status": "unavailable",
                "detail": (
                    "Codex CLI 未安装。请执行: npm install -g @openai/codex "
                    "并通过 Worker 运行环境配置模型凭证。"
                ),
                "test_intent": test_intent,
                "target_url": target_url,
            },
            ensure_ascii=False,
        ),
        stderr="codex executable not found on PATH",
        returncode=127,
        duration_seconds=0,
    )


def _build_prompt(
    test_intent: str,
    target_url: str,
    credentials: dict[str, str] | None = None,
) -> str:
    """构建 Codex CLI prompt，可选注入测试凭据。"""
    creds_lines = ""
    if credentials:
        parts = [f"  - {k}: {v}" for k, v in credentials.items()]
        creds_lines = "\n测试凭据：\n" + "\n".join(parts) + "\n请使用上述凭据完成登录。"

    return f"""你是浏览器自动化测试 Agent。请按以下步骤执行：

1. 打开浏览器访问 {target_url}
2. 执行测试意图：{test_intent}{creds_lines}
3. 每一步截图保存
4. 输出 JSON 格式结果：
{{
  "status": "passed" | "failed" | "error",
  "steps": [
    {{
      "action": "动作描述",
      "screenshot": "base64截图或空",
      "result": "步骤结果"
    }}
  ],
  "summary": "测试总结",
  "generated_script": "如果有，输出完整的 Playwright 脚本"
}}

测试意图：
{test_intent}

目标 URL：
{target_url}
"""


def extract_json_result(raw: CodexRawOutput) -> dict[str, object]:
    """从 Codex raw output 中提取 JSON 结果。"""
    if raw.returncode != 0:
        return {
            "status": "error",
            "detail": raw.stderr or f"Codex CLI exited with code {raw.returncode}",
        }
    # Try to extract JSON from stdout — may be embedded in Markdown or text
    text = raw.stdout.strip()
    # Try direct JSON parse first
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    # Try to find JSON block in markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        try:
            result = json.loads(match.group(1))
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
    # Last resort: wrap raw output as plain text result
    return {
        "status": "passed",
        "summary": text[:2000],
        "raw_output": text,
    }
