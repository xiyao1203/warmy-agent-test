from __future__ import annotations

from datetime import timedelta

from agenttest_api_runner.contracts import (
    ReportArtifact,
    ResultCallbackConfig,
    RunCaseResult,
    RunCaseTask,
    RunResult,
    RunTask,
)
from agenttest_api_runner.workflow import (
    ACTIVITY_RETRY_POLICY,
    ACTIVITY_TIMEOUT,
    RunWorkflow,
    aggregate_results,
    callback_task_for,
    normalize_run_task,
)


def test_workflow_activity_policy_is_bounded() -> None:
    assert ACTIVITY_TIMEOUT == timedelta(minutes=5)
    assert ACTIVITY_RETRY_POLICY.maximum_attempts == 3


def test_aggregate_distinguishes_failure_error_and_cancelled() -> None:
    assert aggregate_results(["passed", "failed"]) == "failed"
    assert aggregate_results(["passed", "error"]) == "error"
    assert aggregate_results(["passed", "cancelled"]) == "cancelled"
    assert aggregate_results(["passed", "passed"]) == "passed"


def test_workflow_contract_supports_one_hundred_cases_without_database_payloads() -> None:
    task = RunTask(
        run_id="run-1",
        idempotency_key="release-42",
        cases=[
            RunCaseTask(
                run_case_id=f"case-{index}",
                input={"message": str(index)},
                assertions=[],
            )
            for index in range(100)
        ],
        agent_config={"url": "https://agent.example/run", "mode": "sync"},
    )

    assert len(task.cases) == 100
    assert not hasattr(task, "database_url")
    assert getattr(RunWorkflow, "__temporal_workflow_definition", None) is not None


def test_workflow_builds_internal_callback_task_without_database_access() -> None:
    task = RunTask(
        run_id="run-1",
        idempotency_key="release-42",
        cases=[],
        agent_config={"url": "https://agent.example/run", "mode": "sync"},
        callback=ResultCallbackConfig(
            base_url="https://control.example",
            internal_token="secret-token",
            project_id="project-1",
        ),
    )
    result = RunResult(
        run_id="run-1",
        status="passed",
        cases=[RunCaseResult(run_case_id="case-1", status="passed")],
        reports=[
            ReportArtifact(
                name="run-result.json",
                content_type="application/json",
                content="{}",
            )
        ],
    )

    callback_task = callback_task_for(task, result)

    assert callback_task is not None
    assert callback_task.base_url == "https://control.example"
    assert callback_task.project_id == "project-1"
    assert callback_task.result is result
    assert callback_task.result.reports[0].name == "run-result.json"
    assert not hasattr(callback_task, "database_url")


def test_workflow_normalizes_json_payload_from_control_plane() -> None:
    task = normalize_run_task(
        {
            "run_id": "run-1",
            "idempotency_key": "release-42",
            "agent_config": {"url": "https://agent.example/run"},
            "cases": [
                {
                    "run_case_id": "case-1",
                    "input": {"message": "hello"},
                    "assertions": [{"type": "contains", "value": "hello"}],
                }
            ],
            "callback": {
                "base_url": "https://control.example",
                "internal_token": "secret-token",
                "project_id": "project-1",
            },
        }
    )

    assert task.run_id == "run-1"
    assert task.cases[0].input == {"message": "hello"}
    assert task.callback is not None
    assert task.callback.project_id == "project-1"
