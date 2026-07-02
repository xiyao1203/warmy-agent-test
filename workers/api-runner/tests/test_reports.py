from __future__ import annotations

import json

from agenttest_api_runner.contracts import RunCaseResult, RunResult
from agenttest_api_runner.reports import build_reports


def make_result() -> RunResult:
    return RunResult(
        run_id="run-1",
        status="failed",
        cases=[
            RunCaseResult(
                run_case_id="case-1",
                status="passed",
                output={"message": "hello"},
                trace=[{"name": "http.request", "status": "ok"}],
                duration_ms=12,
            ),
            RunCaseResult(
                run_case_id="case-2",
                status="failed",
                error_type="AssertionError",
                error_message="missing expected text",
                trace=[{"name": "assert.contains", "status": "failed"}],
                duration_ms=8,
            ),
        ],
    )


def test_build_reports_emits_json_junit_and_html_artifacts() -> None:
    artifacts = build_reports(make_result())
    by_name = {artifact.name: artifact for artifact in artifacts}

    assert set(by_name) == {"run-result.json", "junit.xml", "report.html", "allure-results.json"}
    assert by_name["run-result.json"].content_type == "application/json"
    payload = json.loads(by_name["run-result.json"].content)
    assert payload["run_id"] == "run-1"
    assert payload["summary"] == {
        "passed": 1,
        "failed": 1,
        "error": 0,
        "cancelled": 0,
        "total": 2,
    }
    assert "<testsuite" in by_name["junit.xml"].content
    assert 'failures="1"' in by_name["junit.xml"].content
    assert "missing expected text" in by_name["junit.xml"].content
    assert "<!doctype html>" in by_name["report.html"].content.lower()
    assert "case-2" in by_name["report.html"].content


def test_build_reports_handles_one_hundred_cases() -> None:
    result = RunResult(
        run_id="run-100",
        status="passed",
        cases=[
            RunCaseResult(
                run_case_id=f"case-{index}",
                status="passed",
                output={"index": index},
                duration_ms=index,
            )
            for index in range(100)
        ],
    )

    artifacts = build_reports(result)
    json_payload = json.loads(artifacts[0].content)

    assert json_payload["summary"]["total"] == 100
    assert json_payload["summary"]["passed"] == 100
    assert 'tests="100"' in artifacts[1].content
