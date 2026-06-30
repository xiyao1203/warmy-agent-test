"""Unit tests for Playwright activity."""

from __future__ import annotations

from agenttest_api_runner.playwright_activity import (
    PlaywrightStepResult,
    PlaywrightTaskInput,
    dependency_unavailable_result,
)


def test_missing_playwright_is_an_explicit_error() -> None:
    inp = PlaywrightTaskInput(
        run_case_id="case-1",
        url="https://example.com",
        steps=[{"action": "goto", "target": "https://example.com"}],
    )
    result = dependency_unavailable_result(inp)
    assert result.status == "error"
    assert result.run_case_id == "case-1"
    assert result.page_title == ""
    assert result.steps == []
    assert result.error_message == "Playwright runtime is not installed"


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
        PlaywrightStepResult(
            step_index=1,
            action="click",
            target="#btn",
            status="error",
            error="not found",
        ),
    ]
    all_passed = all(s.status == "passed" for s in steps)
    assert all_passed is False
