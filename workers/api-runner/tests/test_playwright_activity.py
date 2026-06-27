"""Unit tests for Playwright activity (mock mode)."""

from __future__ import annotations

from agenttest_api_runner.playwright_activity import (
    PlaywrightResult,
    PlaywrightStepResult,
    PlaywrightTaskInput,
    _mock_result,
)


def test_mock_result_returns_skipped() -> None:
    inp = PlaywrightTaskInput(
        run_case_id="case-1",
        url="https://example.com",
        steps=[{"action": "goto", "target": "https://example.com"}],
    )
    result = _mock_result(inp)
    assert result.status == "skipped"
    assert result.run_case_id == "case-1"
    assert result.page_title == "Playwright 不可用"
    assert len(result.steps) == 1
    assert result.steps[0].status == "skipped"


def test_playwright_task_input_defaults() -> None:
    inp = PlaywrightTaskInput(
        run_case_id="c1",
        url="https://test.com",
        steps=[],
    )
    assert inp.timeout_ms == 30000
    assert inp.steps == []


def test_playwright_step_result_fields() -> None:
    step = PlaywrightStepResult(
        step_index=0,
        action="click",
        target="#button",
        status="passed",
        duration_ms=150,
    )
    assert step.action == "click"
    assert step.status == "passed"
    assert step.duration_ms == 150
    assert step.screenshot_base64 is None
    assert step.error is None


def test_playwright_result_all_passed() -> None:
    steps = [
        PlaywrightStepResult(step_index=0, action="goto", target="url", status="passed"),
        PlaywrightStepResult(step_index=1, action="click", target="#btn", status="passed"),
    ]
    all_passed = all(s.status == "passed" for s in steps)
    assert all_passed is True


def test_playwright_result_has_failure() -> None:
    steps = [
        PlaywrightStepResult(step_index=0, action="goto", target="url", status="passed"),
        PlaywrightStepResult(step_index=1, action="click", target="#btn", status="error", error="not found"),
    ]
    all_passed = all(s.status == "passed" for s in steps)
    assert all_passed is False
