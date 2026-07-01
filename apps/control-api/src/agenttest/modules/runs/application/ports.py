from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.domain.entities import Run, RunCase, RunId
from agenttest.modules.test_plans.public import TestPlanVersionId


@dataclass(frozen=True, slots=True)
class RunDefinitionCase:
    test_case_id: UUID
    name: str
    input_snapshot: dict[str, object]
    assertion_snapshot: list[dict[str, object]]
    execution_mode: str = "api"


@dataclass(frozen=True, slots=True)
class RunDefinition:
    project_id: ProjectId
    test_plan_version_id: TestPlanVersionId
    agent_version_id: UUID
    dataset_version_id: UUID
    config_snapshot: dict[str, object]
    plugin_snapshot: dict[str, object]
    cases: list[RunDefinitionCase]


class ProjectAccessPort(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class RunSourcePort(Protocol):
    async def load(
        self,
        project_id: ProjectId,
        version_id: TestPlanVersionId,
    ) -> RunDefinition: ...


class RunRepository(Protocol):
    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None: ...

    async def get_by_idempotency_key(
        self,
        project_id: ProjectId,
        key: str,
    ) -> Run | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
    ) -> list[Run]: ...

    async def add(self, run: Run, cases: list[RunCase]) -> None: ...

    async def save(self, run: Run) -> None: ...

    async def save_result(
        self,
        run: Run,
        cases: list[RunCase],
        scores: dict[str, list[dict[str, object]]] | None = None,
    ) -> None: ...

    async def list_cases(
        self,
        project_id: ProjectId,
        run_id: RunId,
    ) -> list[RunCase]: ...


class ReviewCollectorPort(Protocol):
    async def collect(self, project_id: ProjectId, run_id: RunId) -> None: ...


class RunOrchestrator(Protocol):
    async def ensure_available(self) -> None: ...

    async def start(self, run: Run, cases: list[RunCase]) -> str: ...

    async def cancel(self, run: Run) -> None: ...


class RunRuntimeUnavailableError(RuntimeError):
    """The configured execution runtime cannot accept Run workflows."""
