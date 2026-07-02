"""Codex Browser Temporal Activity。

在 Temporal Worker 中执行 Codex CLI 浏览器探索，
采集截图、日志和生成的 Playwright 脚本。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from temporalio import activity

try:
    from agenttest_plugin_codex.contracts import BrowserMode
except ImportError:  # pragma: no cover — 插件未安装时回退
    BrowserMode = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class CodexBrowserTaskInput:
    """Codex 浏览器探索输入。"""

    run_case_id: str
    test_intent: str
    target_url: str
    headless: bool = True
    timeout_seconds: int = 120
    model: str = "gpt-4o"
    model_provider: str = ""
    browser_profile_id: str = ""
    browser_mode: str = "ephemeral"
    storage_state_key: str = ""
    credentials: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodexBrowserResult:
    """Codex 浏览器探索结果。"""

    run_case_id: str
    status: str
    screenshots: list[str] = field(default_factory=list)
    execution_log: str = ""
    generated_script: str | None = None
    allure_data: dict[str, object] | None = None
    error_message: str | None = None
    duration_ms: int = 0


@activity.defn
async def run_codex_browser_case(inp: CodexBrowserTaskInput) -> CodexBrowserResult:
    """执行 Codex 浏览器探索用例。

    Temporal Activity，支持心跳上报和超时重试。
    当 Codex CLI 不可用时返回明确错误，不伪造成功。
    """
    activity.heartbeat({"run_case_id": inp.run_case_id, "target_url": inp.target_url})

    started = datetime.now(UTC)

    try:
        from agenttest_plugin_codex.adapter import CodexBrowserAdapter
        from agenttest_plugin_codex.contracts import (
            CodexBrowserInput,
            StorageStateConfig,
        )
    except ImportError:
        return CodexBrowserResult(
            run_case_id=inp.run_case_id,
            status="error",
            error_message="Codex Browser 插件未安装",
            duration_ms=_elapsed_ms(started),
        )

    adapter = CodexBrowserAdapter()
    try:
        resolved_mode = _resolve_browser_mode(inp.browser_mode)
        result = await adapter.execute(
            CodexBrowserInput(
                test_intent=inp.test_intent,
                target_url=inp.target_url,
                headless=inp.headless,
                timeout_seconds=inp.timeout_seconds,
                model=inp.model,
                model_provider=inp.model_provider,
                browser_profile_id=inp.browser_profile_id,
                browser_mode=resolved_mode,
                storage_state=StorageStateConfig(
                    enabled=bool(inp.storage_state_key),
                ),
                storage_state_key=inp.storage_state_key,
                credentials=inp.credentials,
            )
        )
    except Exception as exc:
        return CodexBrowserResult(
            run_case_id=inp.run_case_id,
            status="error",
            error_message=f"Codex 执行异常: {exc}",
            duration_ms=_elapsed_ms(started),
        )

    return CodexBrowserResult(
        run_case_id=inp.run_case_id,
        status=result.status,
        screenshots=list(result.screenshots),
        execution_log=result.execution_log,
        generated_script=result.generated_script,
        allure_data=(
            dict(result.allure_data) if result.allure_data else None
        ),
        error_message=result.error_message,
        duration_ms=_elapsed_ms(started),
    )


def _elapsed_ms(started: datetime) -> int:
    return int((datetime.now(UTC) - started).total_seconds() * 1000)


def _resolve_browser_mode(raw: str) -> BrowserMode:
    """将字符串解析为 BrowserMode，无效值或插件未安装时回退到 EPHEMERAL。"""
    if BrowserMode is None:
        from agenttest_plugin_codex.contracts import BrowserMode as BM
        try:
            return BM(raw)
        except ValueError:
            return BM.EPHEMERAL
    try:
        return BrowserMode(raw)
    except ValueError:
        return BrowserMode.EPHEMERAL


def build_allure_json_result(
    result: CodexBrowserResult,
) -> str:
    """将 CodexBrowserResult 转为 Allure JSON 测试结果。"""
    allure_data = result.allure_data or {}
    return json.dumps(
        {
            "name": f"Codex Browser — {result.run_case_id}",
            "status": result.status,
            "statusDetails": {
                "message": result.error_message or "",
            },
            "stage": "finished",
            "steps": allure_data.get("steps", []),
            "attachments": [
                {
                    "name": f"screenshot_{i}.png",
                    "type": "image/png",
                    "source": screenshot[:100],
                }
                for i, screenshot in enumerate(result.screenshots)
            ],
            "parameters": [
                {"name": "test_intent", "value": "see execution_log"},
                {"name": "execution_log", "value": result.execution_log[:500]},
            ],
        },
        ensure_ascii=False,
    )
