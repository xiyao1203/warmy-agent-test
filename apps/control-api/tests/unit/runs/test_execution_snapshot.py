from uuid import uuid4

import pytest
from agenttest.modules.agents.public import AgentInvocationConfig
from agenttest.modules.environments.public import EnvironmentRuntimeSnapshot
from agenttest.modules.runs.application.execution_snapshot import (
    CaseExecutionSnapshot,
    EvaluationPolicySnapshot,
    PlatformTestCaseSnapshotV1,
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


def test_professional_case_snapshot_rejects_embedded_credential_value() -> None:
    payload = {
        "schema_version": "platform-test-case/v1",
        "case_key": "PAY-TC-000001",
        "objective": "验证隐私保护",
        "input": {"message": "hello"},
        "data_bindings": [
            {
                "name": "token",
                "source": "credential",
                "reference": "credential://user-a",
                "value": "plain-secret",
            }
        ],
        "execution_mode": "api",
    }

    with pytest.raises(ValidationError, match="must not contain values"):
        PlatformTestCaseSnapshotV1.model_validate(payload)


def test_case_trial_snapshot_requires_source_case() -> None:
    payload = make_snapshot().model_dump(mode="json")
    payload["run_type"] = "case_trial"
    payload["test_plan_version_id"] = None

    with pytest.raises(ValidationError, match="source_test_case_id"):
        RunExecutionSnapshot.model_validate(payload)
