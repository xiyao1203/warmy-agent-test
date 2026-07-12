from datetime import timedelta

import pytest
from agenttest_api_runner.mission_contracts import (
    MissionStageResponse,
    MissionWorkflowTask,
)
from agenttest_api_runner.mission_workflow import (
    MISSION_ACTIVITY_RETRY,
    MISSION_ACTIVITY_TIMEOUT,
    MissionStateMachine,
    normalize_mission_task,
)
from agenttest_api_runner.mission_workflow import (
    TestMissionWorkflow as MissionWorkflow,
)
from temporalio.converter import DataConverter


def test_mission_payload_is_secret_free_and_workflow_is_registered() -> None:
    task = normalize_mission_task(
        {
            "project_id": "project-1",
            "mission_id": "mission-1",
            "revision_id": "revision-1",
            "revision_hash": "a" * 64,
            "callback_base_url": "https://control.example",
        }
    )

    assert isinstance(task, MissionWorkflowTask)
    assert not hasattr(task, "internal_token")
    assert "cookie" not in repr(task).lower()
    assert getattr(MissionWorkflow, "__temporal_workflow_definition", None) is not None


def test_state_machine_pauses_resumes_and_distinguishes_terminal_outcomes() -> None:
    machine = MissionStateMachine()

    assert machine.apply("provision", MissionStageResponse("completed")) == "advance"
    assert machine.apply("await_run", MissionStageResponse("running")) == "poll"
    assert (
        machine.apply(
            "await_run", MissionStageResponse("needs_attention", error_type="auth_expired")
        )
        == "pause"
    )
    assert machine.status == "needs_attention"
    machine.resume()
    assert machine.status == "running"
    assert (
        machine.apply(
            "await_run", MissionStageResponse("failed", error_type="target_product_error")
        )
        == "finish"
    )
    assert machine.status == "failed"
    assert machine.error_type == "target_product_error"


def test_mission_activity_policy_is_bounded() -> None:
    assert MISSION_ACTIVITY_TIMEOUT == timedelta(minutes=2)
    assert MISSION_ACTIVITY_RETRY.maximum_attempts == 3


def test_resume_increments_attempt_forwarded_to_stage_activity() -> None:
    workflow = MissionWorkflow()

    assert workflow.resume_attempt == 0


@pytest.mark.asyncio
async def test_temporal_stage_response_allows_nested_platform_output() -> None:
    response = MissionStageResponse(
        "completed",
        output={
            "agent_version_id": "version-1",
            "artifacts": [
                {"type": "agent_version", "id": "version-1", "metadata": {"reused": False}}
            ],
        },
    )

    payloads = await DataConverter.default.encode([response])
    decoded = await DataConverter.default.decode(payloads, [MissionStageResponse])

    assert decoded[0] == response
