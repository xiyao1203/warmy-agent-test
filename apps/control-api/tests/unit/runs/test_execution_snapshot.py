from uuid import uuid4

import pytest
from agenttest.modules.agents.domain.invocation import AgentInvocationConfig
from agenttest.modules.environments.domain.runtime import EnvironmentRuntimeSnapshot
from agenttest.modules.runs.application.execution_snapshot import (
    CaseExecutionSnapshot,
    EvaluationPolicySnapshot,
    RunExecutionSnapshot,
)
from pydantic import ValidationError


def make_snapshot() -> RunExecutionSnapshot:
    return RunExecutionSnapshot(
        schema_version=1,
        project_id=uuid4(),
        run_id=uuid4(),
        test_plan_version_id=uuid4(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        agent=AgentInvocationConfig(
            endpoint_url="https://agent.example/run",
            response_path="output",
        ),
        environment=EnvironmentRuntimeSnapshot(),
        cases=[
            CaseExecutionSnapshot(
                run_case_id=uuid4(),
                test_case_id=uuid4(),
                name="greets user",
                input={"message": "hello"},
                assertions=[{"type": "contains", "value": "hello"}],
            )
        ],
        evaluation_policy=EvaluationPolicySnapshot(observation_only=True),
    )


def test_run_snapshot_round_trip_keeps_typed_runtime_assets() -> None:
    snapshot = make_snapshot()

    restored = RunExecutionSnapshot.model_validate(snapshot.model_dump(mode="json"))

    assert restored == snapshot
    assert restored.agent.endpoint_url.unicode_string() == "https://agent.example/run"
    assert restored.cases[0].assertions[0]["type"] == "contains"


@pytest.mark.parametrize("field", ["agent", "cases", "evaluation_policy"])
def test_run_snapshot_rejects_missing_required_execution_asset(field: str) -> None:
    payload = make_snapshot().model_dump(mode="json")
    payload.pop(field)

    with pytest.raises(ValidationError):
        RunExecutionSnapshot.model_validate(payload)


def test_run_snapshot_rejects_empty_cases() -> None:
    payload = make_snapshot().model_dump(mode="json")
    payload["cases"] = []

    with pytest.raises(ValidationError):
        RunExecutionSnapshot.model_validate(payload)
