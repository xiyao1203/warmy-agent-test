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
    _codex_model,
    _codex_model_provider,
    _target_browser_profile_id,
    _target_url,
    aggregate_results,
    callback_task_for,
    execution_activity_options,
    normalize_run_task,
)


def test_workflow_activity_policy_is_bounded() -> None:
    assert ACTIVITY_TIMEOUT == timedelta(minutes=5)
    assert ACTIVITY_RETRY_POLICY.maximum_attempts == 3


def test_execution_policy_controls_timeout_and_retries_with_safe_bounds() -> None:
    timeout, retry = execution_activity_options(
        {"timeout": 12, "max_retries": 4, "retry_policy": {"backoff_coefficient": 1.5}}
    )

    assert timeout == timedelta(seconds=12)
    assert retry.maximum_attempts == 5
    assert retry.backoff_coefficient == 1.5


def test_execution_policy_rejects_invalid_runtime_values() -> None:
    timeout, retry = execution_activity_options(
        {"timeout": -1, "max_retries": 100, "retry_policy": {"backoff_coefficient": 0}}
    )

    assert timeout == timedelta(seconds=1)
    assert retry.maximum_attempts == 11
    assert retry.backoff_coefficient == 1.0


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


def test_workflow_normalizes_codex_browser_execution_mode() -> None:
    task = normalize_run_task(
        {
            "run_id": "run-codex",
            "idempotency_key": "codex-1",
            "agent_config": {"canvas_url": "about:blank"},
            "cases": [
                {
                    "run_case_id": "case-codex",
                    "input": {
                        "url": "about:blank",
                        "test_intent": "确认页面可访问",
                        "timeout": 90,
                    },
                    "assertions": [],
                    "execution_mode": "codex_explore",
                }
            ],
        }
    )

    assert task.cases[0].execution_mode == "codex_explore"
    assert task.cases[0].input["test_intent"] == "确认页面可访问"


def test_target_config_supplies_default_url_and_browser_profile() -> None:
    agent_config = {
        "endpoint_url": "https://fallback.example/run",
        "target_config": {
            "browser_profile_id": "profile-from-agent",
            "entry_url": "https://app.tapnow.ai/canvas/demo",
        },
    }

    assert _target_url({}, agent_config) == "https://app.tapnow.ai/canvas/demo"
    assert (
        _target_browser_profile_id({}, {}, agent_config)
        == "profile-from-agent"
    )
    assert _target_url({"url": "https://case.example"}, agent_config) == "https://case.example"
    assert (
        _target_browser_profile_id(
            {"browser_profile_id": "profile-from-case"},
            {"browser_profile_id": "profile-from-plan"},
            agent_config,
        )
        == "profile-from-case"
    )


def test_codex_model_defaults_to_execution_policy() -> None:
    policy = {
        "codex_model": "gpt-5.5",
        "codex_model_provider": "openai-compatible",
    }

    assert _codex_model({}, policy) == "gpt-5.5"
    assert _codex_model_provider({}, policy) == "openai-compatible"


def test_codex_model_case_input_overrides_execution_policy() -> None:
    case_input = {
        "model": "local-browser-model",
        "model_provider": "ollama",
    }
    policy = {
        "codex_model": "gpt-5.5",
        "codex_model_provider": "openai-compatible",
    }

    assert _codex_model(case_input, policy) == "local-browser-model"
    assert _codex_model_provider(case_input, policy) == "ollama"
