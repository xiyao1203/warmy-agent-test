from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.ports import RunRuntimeUnavailableError
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.infrastructure.temporal_orchestrator import (
    RUN_WORKFLOW_NAME,
    TemporalRunOrchestrator,
)
from agenttest.modules.test_plans.public import TestPlanVersionId
from temporalio.service import RPCError, RPCStatusCode


class FakeWorkflowHandle:
    def __init__(self) -> None:
        self.signals: list[str] = []

    async def signal(self, name: str) -> None:
        self.signals.append(name)


class FakeTemporalClient:
    def __init__(self) -> None:
        self.started: list[dict[str, object]] = []
        self.handle = FakeWorkflowHandle()
        self.requested_workflow_id: str | None = None

    async def start_workflow(self, workflow: str, payload: dict[str, object], **kwargs):
        self.started.append({"workflow": workflow, "payload": payload, "kwargs": kwargs})
        return self.handle

    def get_workflow_handle(self, workflow_id: str) -> FakeWorkflowHandle:
        self.requested_workflow_id = workflow_id
        return self.handle


class CompletedWorkflowHandle:
    async def signal(self, _name: str) -> None:
        raise RPCError("workflow execution already completed", RPCStatusCode.NOT_FOUND, b"")


class CompletedWorkflowClient(FakeTemporalClient):
    def __init__(self) -> None:
        super().__init__()
        self.handle = CompletedWorkflowHandle()


def make_run() -> tuple[Run, list[RunCase]]:
    run = Run.create(
        run_id=RunId(uuid4()),
        project_id=ProjectId.new(),
        test_plan_version_id=TestPlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="temporal-start",
        created_by=UserId.new(),
        config_snapshot={
            "agent": {"url": "https://agent.example/run", "mode": "sync"},
        },
        plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
        total_cases=1,
    )
    case = RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=uuid4(),
        name="hello",
        input_snapshot={"message": "hello"},
        assertion_snapshot=[{"type": "contains", "value": "hello"}],
    )
    return run, [case]


def test_temporal_payload_uses_agent_snapshot_not_plan_configuration() -> None:
    run, cases = make_run()
    run.config_snapshot.clear()
    run.config_snapshot.update({"concurrency": 4, "retry": {"max_attempts": 2}})
    run.plugin_snapshot["agent_config"] = {
        "endpoint_url": "https://agent.example/run",
        "protocol": "sync_json",
        "response_path": "output",
        "timeout_seconds": 12,
    }
    run.plugin_snapshot["environment_config"] = {
        "variables": {"tenant": "staging"},
        "headers": {"x-tenant": "demo"},
    }

    from agenttest.modules.runs.infrastructure.temporal_orchestrator import _payload

    payload = _payload(run, cases, control_api_base_url=None, internal_api_token=None)

    assert payload["agent_config"] == run.plugin_snapshot["agent_config"]
    assert payload["environment"] == run.plugin_snapshot["environment_config"]
    assert payload["execution_policy"] == run.config_snapshot


@pytest.mark.asyncio
async def test_temporal_orchestrator_starts_run_workflow_with_snapshot_payload() -> None:
    run, cases = make_run()
    client = FakeTemporalClient()
    orchestrator = TemporalRunOrchestrator(
        client=client,
        control_api_base_url="https://control.example",
        internal_api_token="secret-token",
        task_queue="agenttest-api-runner",
    )

    workflow_id = await orchestrator.start(run, cases)

    assert workflow_id == f"run-{run.run_id.value}"
    assert client.started[0]["workflow"] == RUN_WORKFLOW_NAME
    payload = client.started[0]["payload"]
    assert payload["run_id"] == str(run.run_id.value)
    assert payload["idempotency_key"] == "temporal-start"
    assert payload["agent_config"] == {"url": "https://agent.example/run", "mode": "sync"}
    assert payload["agent_type"] == "generic_http"
    assert payload["cases"] == [
        {
            "run_case_id": str(cases[0].run_case_id.value),
            "input": {"message": "hello"},
            "assertions": [{"type": "contains", "value": "hello"}],
            "execution_mode": "api",
        }
    ]
    assert payload["callback"] == {
        "base_url": "https://control.example",
        "internal_token": "secret-token",
        "project_id": str(run.project_id.value),
    }
    assert client.started[0]["kwargs"]["id"] == workflow_id
    assert client.started[0]["kwargs"]["task_queue"] == "agenttest-api-runner"


@pytest.mark.asyncio
async def test_temporal_orchestrator_signals_cancel_when_workflow_exists() -> None:
    run, cases = make_run()
    client = FakeTemporalClient()
    orchestrator = TemporalRunOrchestrator(
        client=client,
        task_queue="agenttest-api-runner",
    )
    workflow_id = await orchestrator.start(run, cases)
    run.start(workflow_id)

    await orchestrator.cancel(run)

    assert client.requested_workflow_id == workflow_id
    assert client.handle.signals == ["cancel"]


@pytest.mark.asyncio
async def test_temporal_orchestrator_ignores_completed_workflow_on_cancel() -> None:
    run, cases = make_run()
    client = CompletedWorkflowClient()
    orchestrator = TemporalRunOrchestrator(
        client=client,
        task_queue="agenttest-api-runner",
    )
    workflow_id = await orchestrator.start(run, cases)
    run.start(workflow_id)

    await orchestrator.cancel(run)

    assert client.requested_workflow_id == workflow_id


@pytest.mark.asyncio
async def test_temporal_readiness_uses_stable_runtime_error() -> None:
    orchestrator = TemporalRunOrchestrator(task_queue="agenttest-api-runner")

    with pytest.raises(RunRuntimeUnavailableError, match="Run execution runtime"):
        await orchestrator.ensure_available()
