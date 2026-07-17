from __future__ import annotations

import json
from uuid import uuid4

import pytest
from agenttest.modules.datasets.application.trial_runs import (
    CaseTrialRuntime,
    CreateCaseTrialRunCommand,
    CreateCaseTrialRunHandler,
)
from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
)
from agenttest.modules.datasets.domain.entities import (
    TestCase as DatasetCase,
)
from agenttest.modules.datasets.domain.entities import (
    TestCaseId as DatasetCaseId,
)
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
)
from agenttest.modules.datasets.domain.value_objects import (
    TestCaseTemplate as CaseTemplate,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.public import Run, RunCase, RunIdempotencyKeyExists, RunType


class ItemRepository:
    def __init__(self, item) -> None:
        self.item = item

    async def get_by_id(self, item_id):
        for name in ("dataset_id", "version_id", "case_id"):
            if getattr(self.item, name, None) == item_id:
                return self.item
        return None


class RunRepository:
    def __init__(self) -> None:
        self.runs: list[Run] = []
        self.cases: list[RunCase] = []

    async def get_by_idempotency_key(self, project_id: ProjectId, key: str) -> Run | None:
        return next(
            (
                run
                for run in self.runs
                if run.project_id == project_id and run.idempotency_key == key
            ),
            None,
        )

    async def add(self, run: Run, cases: list[RunCase]) -> None:
        self.runs.append(run)
        self.cases.extend(cases)

    async def save(self, run: Run) -> None:
        assert run in self.runs


class RacingRunRepository(RunRepository):
    def __init__(self) -> None:
        super().__init__()
        self.winner: Run | None = None
        self.winner_cases: list[RunCase] = []

    async def add(self, run: Run, cases: list[RunCase]) -> None:
        assert self.winner is not None
        self.runs.append(self.winner)
        self.cases.extend(self.winner_cases)
        raise RunIdempotencyKeyExists


class Access:
    def __init__(self, project_id: ProjectId) -> None:
        self.project_id = project_id

    async def ensure_editor(self, _actor: User, project_id: ProjectId) -> None:
        if project_id != self.project_id:
            raise PermissionError


class RuntimeSource:
    async def load(self, *, project_id, agent_version_id, environment_template_id):
        del project_id, environment_template_id
        return CaseTrialRuntime(
            agent_version_id=agent_version_id,
            config_snapshot={"concurrency": 1, "case_trial": True},
            plugin_snapshot={"id": "http", "agent_config": {"url": "https://agent.test"}},
        )


class Orchestrator:
    def __init__(self) -> None:
        self.started = 0

    async def ensure_available(self) -> None:
        return None

    async def start(self, _run: Run, _cases: list[RunCase]) -> str:
        self.started += 1
        return "workflow-trial"

    async def cancel(self, _run: Run) -> None:
        return None


def build_handler():
    actor = User.create(
        user_id=UserId.new(),
        email=Email("trial@example.com"),
        display_name="Trial Tester",
        role=SystemRole.TESTER,
    )
    project_id = ProjectId.new()
    dataset = Dataset.create(
        dataset_id=DatasetId.new(),
        project_id=project_id,
        name="Professional",
        created_by=actor.user_id,
    )
    version = DatasetVersion.create_draft(
        version_id=DatasetVersionId.new(),
        dataset_id=dataset.dataset_id,
        version_number=1,
        created_by=actor.user_id,
    )
    case = DatasetCase.create(
        case_id=DatasetCaseId.new(),
        dataset_version_id=version.version_id,
        case_key="PAY-TC-000001",
        name="拒绝越权",
        objective="验证隐私保护",
        template=CaseTemplate.STEP_BY_STEP,
        input={
            "message": "查询其他用户订单",
            "password": "input-password",
            "headers": {"Authorization": "Bearer input-token"},
            "apiKey": "camel-api-key",
            "accessToken": "camel-access-token",
            "clientSecret": "camel-client-secret",
            "token_usage": 42,
        },
        initial_state={"browser": {"cookie": "session=initial-secret"}},
        data_bindings=[
            {
                "name": "token",
                "source": "credential",
                "reference": "credential://user-a",
                "sensitive": True,
                "value": "plain-secret",
            }
        ],
        steps=[
            {
                "step_no": 1,
                "action": "发送查询",
                "test_data": {"api_key": "step-api-key"},
                "expected_result": "拒绝",
                "assertions": [],
                "artifact_requirements": [],
            }
        ],
        execution_mode=ExecutionMode.API,
        assertions=[{"type": "contains", "value": "拒绝"}],
        expected_outcome={"secret": "expected-secret"},
        security_policies=[{"type": "pii_redaction", "token": "policy-token"}],
        postconditions=["清理会话"],
        created_by=actor.user_id,
    )
    runs = RunRepository()
    orchestrator = Orchestrator()
    handler = CreateCaseTrialRunHandler(
        datasets=ItemRepository(dataset),
        versions=ItemRepository(version),
        cases=ItemRepository(case),
        runs=runs,
        project_access=Access(project_id),
        runtime_source=RuntimeSource(),
        orchestrator=orchestrator,
    )
    return actor, project_id, case, runs, orchestrator, handler


@pytest.mark.asyncio
async def test_case_trial_is_idempotent_and_uses_secret_free_snapshot() -> None:
    actor, project_id, case, runs, orchestrator, handler = build_handler()
    command = CreateCaseTrialRunCommand(
        project_id=project_id,
        case_id=case.case_id,
        agent_version_id=uuid4(),
        environment_template_id=uuid4(),
        idempotency_key="trial-1",
    )

    first = await handler.execute(actor, command)
    second = await handler.execute(actor, command)

    assert first.created is True
    assert second.created is False
    assert second.run.run_id == first.run.run_id
    assert first.run.run_type is RunType.CASE_TRIAL
    assert first.run.test_plan_version_id is None
    assert first.run.source_test_case_id == case.case_id.value
    assert orchestrator.started == 1
    snapshot = runs.cases[0].case_spec_snapshot
    assert snapshot["schema_version"] == "platform-test-case/v1"
    assert snapshot["case_key"] == "PAY-TC-000001"
    assert snapshot["steps"][0]["expected_result"] == "拒绝"
    serialized = json.dumps(snapshot)
    for secret in (
        "plain-secret",
        "input-password",
        "Bearer input-token",
        "session=initial-secret",
        "camel-api-key",
        "camel-access-token",
        "camel-client-secret",
        "step-api-key",
        "expected-secret",
        "policy-token",
    ):
        assert secret not in serialized
    assert snapshot["input"]["token_usage"] == 42
    assert runs.cases[0].input_snapshot == snapshot["input"]


@pytest.mark.asyncio
async def test_case_trial_rejects_cross_project_without_creating_run() -> None:
    actor, _, case, runs, _, handler = build_handler()

    with pytest.raises(LookupError):
        await handler.execute(
            actor,
            CreateCaseTrialRunCommand(
                project_id=ProjectId.new(),
                case_id=case.case_id,
                agent_version_id=uuid4(),
                environment_template_id=uuid4(),
                idempotency_key="foreign",
            ),
        )

    assert runs.runs == []


@pytest.mark.asyncio
async def test_case_trial_rejects_same_key_for_a_different_target_or_snapshot() -> None:
    actor, project_id, case, runs, orchestrator, handler = build_handler()
    agent_version_id = uuid4()
    environment_template_id = uuid4()
    command = CreateCaseTrialRunCommand(
        project_id=project_id,
        case_id=case.case_id,
        agent_version_id=agent_version_id,
        environment_template_id=environment_template_id,
        idempotency_key="request-exact",
    )
    await handler.execute(actor, command)

    with pytest.raises(ValueError, match="different trial request"):
        await handler.execute(
            actor,
            CreateCaseTrialRunCommand(
                project_id=project_id,
                case_id=case.case_id,
                agent_version_id=uuid4(),
                environment_template_id=environment_template_id,
                idempotency_key="request-exact",
            ),
        )

    case.input["message"] = "修改后的查询"
    with pytest.raises(ValueError, match="different trial request"):
        await handler.execute(actor, command)

    assert len(runs.runs) == 1
    assert orchestrator.started == 1


@pytest.mark.asyncio
async def test_case_trial_recovers_a_matching_concurrent_unique_conflict() -> None:
    actor, project_id, case, _runs, orchestrator, handler = build_handler()
    command = CreateCaseTrialRunCommand(
        project_id=project_id,
        case_id=case.case_id,
        agent_version_id=uuid4(),
        environment_template_id=uuid4(),
        idempotency_key="concurrent-trial",
    )
    normal_result = await handler.execute(actor, command)

    racing = RacingRunRepository()
    racing.winner = normal_result.run
    racing.winner_cases = []
    handler._runs = racing
    result = await handler.execute(actor, command)

    assert result.created is False
    assert result.run.run_id == normal_result.run.run_id
    assert orchestrator.started == 1
