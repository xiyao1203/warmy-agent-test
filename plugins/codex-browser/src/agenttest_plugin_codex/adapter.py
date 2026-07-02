"""Codex Browser Agent Adapter。

实现 AgentAdapter 协议，调用 Codex CLI 执行浏览器探索式测试。
支持临时实例和持久实例两种浏览器生命周期模式。
"""

from __future__ import annotations

from time import monotonic

from agenttest_plugin_codex.chrome_pool import start_profile as pool_start_profile
from agenttest_plugin_codex.codex_invoker import (
    CodexRawOutput,
    capture_storage_state,
    ensure_persistent_chrome,
    extract_json_result,
    invoke_codex,
    load_storage_state,
)
from agenttest_plugin_codex.contracts import (
    BrowserMode,
    CodexBrowserInput,
    CodexBrowserResult,
)
from agenttest_plugin_codex.profile_registry import get_profile


class CodexBrowserAdapter:
    """Codex 浏览器探索适配器。

    调用 OpenAI Codex CLI（内置 Playwright MCP），
    直接在 Google Chrome 中执行自然语言描述的测试意图，
    返回结构化结果。
    """

    def __init__(self) -> None:
        pass

    async def execute(self, request: CodexBrowserInput) -> CodexBrowserResult:
        """执行 Codex 浏览器探索。

        Args:
            request: 包含 test_intent、target_url 等参数。

        Returns:
            CodexBrowserResult 包含状态、截图、日志和生成的脚本。
        """
        started = monotonic()

        # ── 持久模式：确保 Chrome 就绪 ──────────────────
        cdp_endpoint = request.cdp_endpoint
        storage_state_path = ""

        if request.browser_profile_id:
            # 从 registry 加载 Profile，启动 Chrome
            profile = get_profile("", request.browser_profile_id)
            if profile is not None:
                cdp_endpoint = await pool_start_profile(
                    profile, headless=request.headless,
                )
                if profile.storage_state_path:
                    storage_state_path = profile.storage_state_path
        elif request.browser_mode == BrowserMode.PERSISTENT and not cdp_endpoint:
            try:
                cdp_endpoint = await ensure_persistent_chrome(
                    headless=request.headless,
                )
            except Exception as exc:
                return CodexBrowserResult(
                    status="error",
                    error_message=f"持久 Chrome 启动失败: {exc}",
                )

        # ── 解析 storageState（profile 已提供则跳过） ────
        if not storage_state_path:
            if request.storage_state.enabled and request.storage_state_key:
                storage_state_path = load_storage_state(
                    key=request.storage_state_key,
                    storage_dir=request.storage_state.storage_dir,
                    ttl_hours=request.storage_state.ttl_hours,
                ) or ""

        try:
            raw = await invoke_codex(
                test_intent=request.test_intent,
                target_url=request.target_url,
                headless=request.headless,
                timeout_seconds=request.timeout_seconds,
                model=request.model,
                model_provider=request.model_provider,
                browser_mode=request.browser_mode,
                cdp_endpoint=cdp_endpoint,
                storage_state_path=storage_state_path,
                credentials=request.credentials or None,
            )
        except Exception as exc:
            return CodexBrowserResult(
                status="error",
                error_message=f"Codex CLI 调用失败: {exc}",
            )

        duration_seconds = monotonic() - started
        json_result = extract_json_result(raw)

        status = _normalise_status(str(json_result.get("status", "error")))
        screenshots = _extract_screenshots(json_result)
        execution_log = _build_log(raw, json_result, duration_seconds)
        generated_script = _extract_script(json_result)

        # ── storageState 采集（持久模式 + 登录操作） ────
        storage_state_updated = False
        new_storage_state_path = ""
        if (
            request.browser_mode == BrowserMode.PERSISTENT
            and request.storage_state.enabled
            and request.storage_state_key
            and cdp_endpoint
            and status != "error"
        ):
            login_detected = _detect_login_activity(json_result, request.credentials)
            if login_detected or not storage_state_path:
                # 登录操作已执行 或 首次无 storageState → 采集保存
                new_storage_state_path = await capture_storage_state(
                    cdp_endpoint=cdp_endpoint,
                    target_url=request.target_url,
                    key=request.storage_state_key,
                    storage_dir=request.storage_state.storage_dir,
                    existing_storage_state_path=storage_state_path,
                )
                storage_state_updated = bool(new_storage_state_path)

        return CodexBrowserResult(
            status=status,
            screenshots=screenshots,
            execution_log=execution_log,
            generated_script=generated_script,
            allure_data=_build_allure_data(json_result, status, duration_seconds),
            error_message=(
                str(json_result.get("detail"))
                if status == "error"
                else None
            ),
            storage_state_updated=storage_state_updated,
            storage_state_path=new_storage_state_path,
        )


def _normalise_status(raw: str) -> str:
    return {"pass": "passed", "fail": "failed"}.get(raw, raw)


def _detect_login_activity(
    result: dict[str, object],
    credentials: dict[str, str] | None = None,
) -> bool:
    """检测 Codex 执行步骤中是否包含登录操作。

    判断依据：
    1. 步骤 action 含登录关键词
    2. 有凭据时，步骤中出现了用户名/密码填写动作
    """
    login_keywords = ("登录", "login", "signin", "sign-in", "认证")
    steps = result.get("steps", [])
    if not isinstance(steps, list):
        return False
    for step in steps:
        if not isinstance(step, dict):
            continue
        action = str(step.get("action", "")).lower()
        if any(kw in action for kw in login_keywords):
            return True
        if credentials:
            cred_values = [v.lower() for v in credentials.values() if v]
            if any(v in action for v in cred_values):
                return True
    return False


def _extract_screenshots(result: dict[str, object]) -> list[str]:
    steps = result.get("steps")
    if not isinstance(steps, list):
        return []
    screenshots: list[str] = []
    for step in steps:
        if isinstance(step, dict):
            screenshot = step.get("screenshot")
            if isinstance(screenshot, str) and screenshot:
                screenshots.append(screenshot)
    return screenshots


def _extract_script(result: dict[str, object]) -> str | None:
    script = result.get("generated_script")
    return str(script) if isinstance(script, str) and script else None


def _build_log(
    raw: CodexRawOutput,
    result: dict[str, object],
    duration: float,
) -> str:
    summary = result.get("summary", "")
    return (
        f"=== Codex CLI 执行日志 ===\n"
        f"耗时: {duration:.1f}s\n"
        f"退出码: {raw.returncode}\n"
        f"结果摘要: {summary}\n"
        f"\n--- stdout ---\n{raw.stdout}\n"
        f"\n--- stderr ---\n{raw.stderr}"
    )


def _build_allure_data(
    result: dict[str, object],
    status: str,
    duration: float,
) -> dict[str, object]:
    steps = result.get("steps", [])
    return {
        "name": "Codex Browser Test",
        "status": status,
        "duration": duration,
        "steps": (
            [
                {
                    "name": str(s.get("action", "")),
                    "status": (
                        "passed"
                        if str(s.get("result", "")).lower() != "failed"
                        else "failed"
                    ),
                }
                for s in steps
                if isinstance(s, dict)
            ]
            if isinstance(steps, list)
            else []
        ),
        "summary": str(result.get("summary", "")),
    }
