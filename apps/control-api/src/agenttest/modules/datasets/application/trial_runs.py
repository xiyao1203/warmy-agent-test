"""Create an immutable, project-scoped single-case trial Run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.datasets.application.contracts import build_case_spec_snapshot
from agenttest.modules.datasets.application.ports import ProjectAccessPort
from agenttest.modules.datasets.domain.entities import TestCase, TestCaseId
from agenttest.modules.datasets.domain.repositories import (
    DatasetRepository,
    DatasetVersionRepository,
    TestCaseRepository,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.public import (
    Run,
    RunCase,
    RunCaseId,
    RunId,
    RunOrchestrator,
    RunRepository,
    RunType,
)


@dataclass(frozen=True, slots=True)
class CaseTrialRuntime:
    agent_version_id: UUID
    config_snapshot: dict[str, object]
    plugin_snapshot: dict[str, object]


class CaseTrialRuntimeSource(Protocol):
    async def load(
        self,
        *,
        project_id: ProjectId,
        agent_version_id: UUID,
        environment_template_id: UUID,
    ) -> CaseTrialRuntime: ...


@dataclass(frozen=True, slots=True)
class CreateCaseTrialRunCommand:
    project_id: ProjectId
    case_id: TestCaseId
    agent_version_id: UUID
    environment_template_id: UUID
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class CreateCaseTrialRunResult:
    run: Run
    created: bool


class CreateCaseTrialRunHandler:
    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        cases: TestCaseRepository,
        runs: RunRepository,
        project_access: ProjectAccessPort,
        runtime_source: CaseTrialRuntimeSource,
        orchestrator: RunOrchestrator,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._cases = cases
        self._runs = runs
        self._project_access = project_access
        self._runtime_source = runtime_source
        self._orchestrator = orchestrator

    async def execute(
        self,
        actor: User,
        command: CreateCaseTrialRunCommand,
    ) -> CreateCaseTrialRunResult:
        key = command.idempotency_key.strip()
        if not key:
            raise ValueError("Idempotency-Key is required")
        case, dataset_project_id = await self._resolve_case(command.case_id)
        if dataset_project_id != command.project_id:
            raise LookupError("Test case was not found")
        await self._project_access.ensure_editor(actor, command.project_id)

        existing = await self._runs.get_by_idempotency_key(command.project_id, key)
        if existing is not None:
            if (
                existing.run_type is not RunType.CASE_TRIAL
                or existing.source_test_case_id != case.case_id.value
            ):
                raise ValueError("Idempotency-Key is already used by another Run")
            return CreateCaseTrialRunResult(run=existing, created=False)

        issues = case.readiness_issues()
        if issues:
            raise ValueError(issues[0][2])
        runtime = await self._runtime_source.load(
            project_id=command.project_id,
            agent_version_id=command.agent_version_id,
            environment_template_id=command.environment_template_id,
        )
        await self._orchestrator.ensure_available()

        run = Run.create_case_trial(
            run_id=RunId.new(),
            project_id=command.project_id,
            source_test_case_id=case.case_id.value,
            agent_version_id=runtime.agent_version_id,
            dataset_version_id=case.dataset_version_id.value,
            idempotency_key=key,
            created_by=actor.user_id,
            config_snapshot=runtime.config_snapshot,
            plugin_snapshot=runtime.plugin_snapshot,
        )
        snapshot = build_case_spec_snapshot(case)
        run_case = RunCase.create(
            run_case_id=RunCaseId.new(),
            run_id=run.run_id,
            test_case_id=case.case_id.value,
            name=case.name,
            input_snapshot=case.input,
            assertion_snapshot=case.assertions,
            case_spec_snapshot=snapshot,
            execution_mode=case.execution_mode.value,
        )
        await self._runs.add(run, [run_case])
        workflow_id = await self._orchestrator.start(run, [run_case])
        run.start(workflow_id)
        await self._runs.save(run)
        return CreateCaseTrialRunResult(run=run, created=True)

    async def _resolve_case(self, case_id: TestCaseId) -> tuple[TestCase, ProjectId]:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise LookupError("Test case was not found")
        version = await self._versions.get_by_id(case.dataset_version_id)
        if version is None:
            raise LookupError("Dataset version was not found")
        dataset = await self._datasets.get_by_id(version.dataset_id)
        if dataset is None:
            raise LookupError("Dataset was not found")
        return case, dataset.project_id
