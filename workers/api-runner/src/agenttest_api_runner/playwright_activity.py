"""Playwright Runner Temporal Activity。

使用 Playwright 执行浏览器自动化测试，采集截图和 Trace。
运行时依赖缺失会返回明确错误，绝不伪造跳过或成功结果。
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import UTC, datetime

from temporalio import activity


@dataclass(frozen=True, slots=True)
class PlaywrightTaskInput:
    """Playwright 用例执行输入。"""

    run_case_id: str
    url: str
    steps: list[dict[str, str]]
    timeout_ms: int = 30000


@dataclass(frozen=True, slots=True)
class PlaywrightStepResult:
    """单步执行结果。"""

    step_index: int
    action: str
    target: str
    status: str
    screenshot_base64: str | None = None
    duration_ms: int = 0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PlaywrightResult:
    """Playwright 用例执行结果。"""

    run_case_id: str
    status: str
    steps: list[PlaywrightStepResult]
    final_url: str
    page_title: str
    screenshots: list[str] = field(default_factory=list)
    canvas_nodes: list[dict[str, object]] = field(default_factory=list)
    canvas_connections: list[dict[str, object]] = field(default_factory=list)
    trace_path: str | None = None
    error_message: str | None = None


@activity.defn
async def run_playwright_case(inp: PlaywrightTaskInput) -> PlaywrightResult:
    """执行 Playwright 浏览器用例。

    Temporal Activity，支持心跳上报和超时重试。
    """
    activity.heartbeat({"run_case_id": inp.run_case_id, "url": inp.url})

    try:
        from playwright.async_api import async_playwright  # type: ignore[import-not-found]
    except ImportError:
        return dependency_unavailable_result(inp)

    step_results: list[PlaywrightStepResult] = []
    screenshots: list[str] = []
    canvas_nodes: list[dict[str, object]] = []
    canvas_connections: list[dict[str, object]] = []
    final_url = inp.url
    page_title = ""

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to start URL
            await page.goto(inp.url, timeout=inp.timeout_ms)
            final_url = page.url
            page_title = await page.title()

            for i, step in enumerate(inp.steps):
                activity.heartbeat(
                    {
                        "run_case_id": inp.run_case_id,
                        "step": i,
                        "action": step.get("action", ""),
                    }
                )

                start_ts = datetime.now(UTC)
                try:
                    await _execute_step(page, step, inp.timeout_ms)
                    screenshot = await page.screenshot()
                    screenshot_b64 = base64.b64encode(screenshot).decode()
                    screenshots.append(screenshot_b64)
                    step_results.append(
                        PlaywrightStepResult(
                            step_index=i,
                            action=step.get("action", ""),
                            target=step.get("target", ""),
                            status="passed",
                            screenshot_base64=screenshot_b64,
                            duration_ms=int((datetime.now(UTC) - start_ts).total_seconds() * 1000),
                        )
                    )
                except Exception as exc:
                    step_results.append(
                        PlaywrightStepResult(
                            step_index=i,
                            action=step.get("action", ""),
                            target=step.get("target", ""),
                            status="error",
                            error=str(exc),
                            duration_ms=int((datetime.now(UTC) - start_ts).total_seconds() * 1000),
                        )
                    )

            # ── 采集 Canvas 状态（关闭浏览器前） ───────────────────
            all_steps_passed = all(s.status == "passed" for s in step_results)
            if all_steps_passed:
                try:
                    import json

                    canvas_raw = await page.evaluate(
                        "(() => { try { return JSON.stringify({ nodes: window.__canvasState?.nodes || [], connections: window.__canvasState?.connections || [] }); } catch(e) { return '{}'; } })()"  # noqa: E501
                    )
                    parsed = json.loads(canvas_raw) if isinstance(canvas_raw, str) else {}
                    raw_nodes = parsed.get("nodes", [])
                    raw_connections = parsed.get("connections", [])
                    if isinstance(raw_nodes, list):
                        canvas_nodes = [
                            dict(n) for n in raw_nodes if isinstance(n, dict)
                        ]
                    if isinstance(raw_connections, list):
                        canvas_connections = [
                            dict(c) for c in raw_connections
                            if isinstance(c, dict)
                        ]
                except Exception:
                    pass

            await browser.close()

    except Exception as exc:
        return PlaywrightResult(
            run_case_id=inp.run_case_id,
            status="error",
            steps=step_results,
            final_url=final_url,
            page_title=page_title,
            screenshots=screenshots,
            canvas_nodes=canvas_nodes,
            canvas_connections=canvas_connections,
            error_message=str(exc),
        )

    all_passed = all(s.status == "passed" for s in step_results)
    return PlaywrightResult(
        run_case_id=inp.run_case_id,
        status="passed" if all_passed else "failed",
        steps=step_results,
        final_url=final_url,
        page_title=page_title,
        screenshots=screenshots,
        canvas_nodes=canvas_nodes,
        canvas_connections=canvas_connections,
    )


async def _execute_step(page, step: dict[str, str], timeout_ms: int) -> None:
    """执行单个步骤。"""
    action = step.get("action", "")
    target = step.get("target", "")
    value = step.get("value", "")

    if action == "goto":
        await page.goto(target, timeout=timeout_ms)
    elif action == "click":
        await page.click(target, timeout=timeout_ms)
    elif action == "fill":
        await page.fill(target, value, timeout=timeout_ms)
    elif action == "wait":
        await page.wait_for_selector(target, timeout=timeout_ms)
    elif action == "screenshot":
        pass  # Screenshot is taken after each step anyway
    else:
        raise ValueError(f"Unknown action: {action}")


def dependency_unavailable_result(inp: PlaywrightTaskInput) -> PlaywrightResult:
    """返回不可与通过/跳过混淆的依赖错误。"""
    return PlaywrightResult(
        run_case_id=inp.run_case_id,
        status="error",
        steps=[],
        final_url=inp.url,
        page_title="",
        error_message="Playwright runtime is not installed",
    )
