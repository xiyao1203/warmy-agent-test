"""Playwright Runner Temporal Activity。

使用 Playwright 执行浏览器自动化测试，采集截图和 Trace。
当 Playwright 未安装时降级为 mock 模式。
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
    trace_path: str | None = None
    error_message: str | None = None


@activity.defn
async def run_playwright_case(inp: PlaywrightTaskInput) -> PlaywrightResult:
    """执行 Playwright 浏览器用例。

    Temporal Activity，支持心跳上报和超时重试。
    """
    activity.heartbeat({"run_case_id": inp.run_case_id, "url": inp.url})

    try:
        from playwright.async_api import async_playwright  # type: ignore[import-untyped]
    except ImportError:
        return _mock_result(inp)

    step_results: list[PlaywrightStepResult] = []
    screenshots: list[str] = []
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
                activity.heartbeat({
                    "run_case_id": inp.run_case_id,
                    "step": i,
                    "action": step.get("action", ""),
                })

                start_ts = datetime.now(UTC)
                try:
                    await _execute_step(page, step, inp.timeout_ms)
                    screenshot = await page.screenshot()
                    screenshot_b64 = base64.b64encode(screenshot).decode()
                    screenshots.append(screenshot_b64)
                    step_results.append(PlaywrightStepResult(
                        step_index=i,
                        action=step.get("action", ""),
                        target=step.get("target", ""),
                        status="passed",
                        screenshot_base64=screenshot_b64,
                        duration_ms=int((datetime.now(UTC) - start_ts).total_seconds() * 1000),
                    ))
                except Exception as exc:
                    step_results.append(PlaywrightStepResult(
                        step_index=i,
                        action=step.get("action", ""),
                        target=step.get("target", ""),
                        status="error",
                        error=str(exc),
                        duration_ms=int((datetime.now(UTC) - start_ts).total_seconds() * 1000),
                    ))

            await browser.close()

    except Exception as exc:
        return PlaywrightResult(
            run_case_id=inp.run_case_id,
            status="error",
            steps=step_results,
            final_url=final_url,
            page_title=page_title,
            screenshots=screenshots,
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


def _mock_result(inp: PlaywrightTaskInput) -> PlaywrightResult:
    """Playwright 不可用时的 mock 结果。"""
    return PlaywrightResult(
        run_case_id=inp.run_case_id,
        status="skipped",
        steps=[PlaywrightStepResult(
            step_index=0,
            action="mock",
            target=inp.url,
            status="skipped",
        )],
        final_url=inp.url,
        page_title="Playwright 不可用",
        error_message="Playwright 未安装，跳过浏览器测试",
    )
