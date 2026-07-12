from datetime import timedelta

import pytest
from agenttest_api_runner.postprocess_contracts import (
    PostprocessStageResponse,
    PostprocessWorkflowTask,
)
from agenttest_api_runner.postprocess_workflow import (
    POSTPROCESS_ACTIVITY_RETRY,
    POSTPROCESS_ACTIVITY_TIMEOUT,
    PostprocessStateMachine,
    RunPostprocessWorkflow,
    normalize_postprocess_task,
)


def test_postprocess_payload_is_secret_free_and_workflow_registered() -> None:
    task = normalize_postprocess_task(
        {
            "project_id": "project-1",
            "run_id": "run-1",
            "pipeline_version": "trust-loop-v1",
            "callback_base_url": "https://control.example",
        }
    )

    assert isinstance(task, PostprocessWorkflowTask)
    assert "token" not in repr(task).lower()
    assert "cookie" not in repr(task).lower()
    assert getattr(RunPostprocessWorkflow, "__temporal_workflow_definition", None) is not None


def test_state_machine_continues_warnings_and_stops_required_failure() -> None:
    machine = PostprocessStateMachine()

    assert machine.apply("classify", PostprocessStageResponse("completed")) == "advance"
    assert (
        machine.apply(
            "diagnose",
            PostprocessStageResponse("warning", warning_code="diagnostic_model_unavailable"),
        )
        == "advance"
    )
    assert machine.warning_codes == ["diagnostic_model_unavailable"]
    assert machine.apply("evaluate_gate", PostprocessStageResponse("failed")) == "finish"
    assert machine.status == "failed"


def test_postprocess_activity_policy_is_bounded() -> None:
    assert POSTPROCESS_ACTIVITY_TIMEOUT == timedelta(minutes=2)
    assert POSTPROCESS_ACTIVITY_RETRY.maximum_attempts == 3


def test_state_machine_resumes_after_previously_completed_stage() -> None:
    machine = PostprocessStateMachine(completed_stages=("classify", "diagnose"))

    assert machine.pending_stages() == (
        "reproduce",
        "calibrate",
        "evaluate_gate",
        "finalize",
    )
    assert machine.apply("reproduce", PostprocessStageResponse("completed")) == "advance"
    assert machine.completed_stages == ["classify", "diagnose", "reproduce"]


def test_state_machine_cancellation_is_terminal() -> None:
    machine = PostprocessStateMachine()

    machine.cancel()

    assert machine.status == "cancelled"
    assert machine.pending_stages() == ()


@pytest.mark.asyncio
async def test_postprocess_contract_allows_nested_outputs() -> None:
    from temporalio.converter import DataConverter

    response = PostprocessStageResponse(
        "completed",
        output={"items": [{"rules": [{"code": "security", "status": "block"}]}]},
    )
    payloads = await DataConverter.default.encode([response])
    decoded = await DataConverter.default.decode(payloads, [PostprocessStageResponse])
    assert decoded == [response]
