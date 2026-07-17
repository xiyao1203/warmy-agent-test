from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.commands import (
    CreateRunCommand,
    CreateRunHandler,
)
from agenttest.modules.runs.application.ports import (
    RunDefinition,
    RunDefinitionCase,
    RunIdempotencyConflict,
    RunIdempotencyKeyExists,
)
from agenttest.modules.runs.domain.entities import Run, RunCase
from agenttest.modules.test_plans.public import TestPlanVersionId as PlanVersionId


class Repository:
    def __init__(self, *, conflict_on_add: bool = False) -> None:
        self.run: Run | None = None
        self.cases: list[RunCase] = []
        self.conflict_on_add = conflict_on_add

    async def get_by_idempotency_key(self, project_id: ProjectId, key: str) -> Run | None:
        if self.run and self.run.project_id == project_id and self.run.idempotency_key == key:
            return self.run
        return None

    async def add(self, run: Run, cases: list[RunCase]) -> None:
        self.run = run
        self.cases = cases
        if self.conflict_on_add:
            raise RunIdempotencyKeyExists

    async def save(self, run: Run) -> None:
        self.run = run


class Source:
    def __init__(self) -> None:
        self.loads = 0

    async def load(
        self,
        project_id: ProjectId,
        version_id: PlanVersionId,
    ) -> RunDefinition:
        self.loads += 1
        return RunDefinition(
            project_id=project_id,
            test_plan_version_id=version_id,
            agent_version_id=uuid4(),
            dataset_version_id=uuid4(),
            config_snapshot={"timeout": 30},
            plugin_snapshot={"id": "generic-http"},
            cases=[
                RunDefinitionCase(
                    test_case_id=uuid4(),
                    name="hello",
                    input_snapshot={"message": "hello"},
                    assertion_snapshot=[],
                )
            ],
        )


class Access:
    async def ensure_editor(self, _actor: User, _project_id: ProjectId) -> None:
        return None


class Orchestrator:
    def __init__(self) -> None:
        self.started = 0

    async def ensure_available(self) -> None:
        return None

    async def start(self, _run: Run, _cases: list[RunCase]) -> str:
        self.started += 1
        return "workflow-1"


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("run-create@example.test"),
        display_name="Run Creator",
        role=SystemRole.DEVELOPER,
    )


def handler(
    repository: Repository,
) -> tuple[CreateRunHandler, Source, Orchestrator]:
    source = Source()
    orchestrator = Orchestrator()
    return (
        CreateRunHandler(
            runs=repository,
            source=source,
            project_access=Access(),
            orchestrator=orchestrator,
        ),
        source,
        orchestrator,
    )


@pytest.mark.asyncio
async def test_plan_run_idempotency_is_request_exact() -> None:
    repository = Repository()
    create, source, orchestrator = handler(repository)
    project_id = ProjectId.new()
    first_plan = PlanVersionId.new()

    first = await create.execute(
        actor(),
        CreateRunCommand(project_id, first_plan, "plan-exact"),
    )
    replay = await create.execute(
        actor(),
        CreateRunCommand(project_id, first_plan, "plan-exact"),
    )

    with pytest.raises(RunIdempotencyConflict):
        await create.execute(
            actor(),
            CreateRunCommand(project_id, PlanVersionId.new(), "plan-exact"),
        )

    assert first.created is True
    assert replay.created is False
    assert replay.run.run_id == first.run.run_id
    assert source.loads == 1
    assert orchestrator.started == 1


@pytest.mark.asyncio
async def test_plan_run_recovers_the_winner_of_a_concurrent_insert() -> None:
    repository = Repository(conflict_on_add=True)
    create, _, orchestrator = handler(repository)
    project_id = ProjectId.new()

    result = await create.execute(
        actor(),
        CreateRunCommand(project_id, PlanVersionId.new(), "plan-race"),
    )

    assert result.created is False
    assert repository.run is result.run
    assert orchestrator.started == 0
