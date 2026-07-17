"""Create persisted regression cases from failed RunCases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.datasets.application.commands import AddTestCaseCommand
from agenttest.modules.datasets.domain.entities import DatasetVersionId, TestCase, TestCaseId
from agenttest.modules.datasets.domain.repositories import TestCaseRepository
from agenttest.modules.datasets.domain.value_objects import (
    Priority,
    RiskLevel,
    TestCaseSource,
    TestCaseType,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.public import Run, RunCase, RunCaseStatus, RunId


class RunLookup(Protocol):
    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None: ...

    async def list_cases(
        self,
        project_id: ProjectId,
        run_id: RunId,
    ) -> list[RunCase]: ...


class AddCase(Protocol):
    async def execute(self, actor: User, command: AddTestCaseCommand) -> TestCase: ...


class SourceRunNotFoundError(Exception):
    """The source run does not exist in the requested project."""


@dataclass(frozen=True, slots=True)
class GenerateFromRunCommand:
    run_id: UUID
    dataset_version_id: UUID
    priority: Priority = Priority.P1
    risk_level: RiskLevel = RiskLevel.MEDIUM


@dataclass(frozen=True, slots=True)
class GenerateFromRunResult:
    generated_cases: list[TestCase]
    total_failed: int
    skipped_existing: int


class GenerateCasesFromFailedRunHandler:
    def __init__(
        self,
        *,
        runs: RunLookup,
        cases: TestCaseRepository,
        add_case: AddCase,
    ) -> None:
        self._runs = runs
        self._cases = cases
        self._add_case = add_case

    async def execute(
        self,
        *,
        actor: User,
        project_id: ProjectId,
        command: GenerateFromRunCommand,
    ) -> GenerateFromRunResult:
        run_id = RunId(command.run_id)
        run = await self._runs.get_by_id(project_id, run_id)
        if run is None:
            raise SourceRunNotFoundError
        failed = [
            case
            for case in await self._runs.list_cases(project_id, run_id)
            if case.status in {RunCaseStatus.FAILED, RunCaseStatus.ERROR}
        ]
        version_id = DatasetVersionId(command.dataset_version_id)
        existing, _ = await self._cases.list_by_version(version_id, limit=200)
        existing_tags = {tag for case in existing for tag in case.tags}
        generated: list[TestCase] = []
        skipped = 0
        for failed_case in failed:
            source_tag = f"generated-from-run-case:{failed_case.run_case_id.value}"
            if source_tag in existing_tags:
                skipped += 1
                continue
            source = await self._cases.get_by_id(TestCaseId(failed_case.test_case_id))
            if source is None:
                raise ValueError("Source test case no longer exists")
            assertions = (
                failed_case.assertion_snapshot
                or source.assertions
                or [{"type": "execution_status", "value": "passed"}]
            )
            diagnosis = failed_case.error_message or failed_case.error_type or failed_case.name
            created = await self._add_case.execute(
                actor,
                AddTestCaseCommand(
                    dataset_version_id=version_id,
                    name=f"回归：{failed_case.name}",
                    objective=f"回归失败：{diagnosis}",
                    template=source.template,
                    case_type=TestCaseType.REGRESSION,
                    automation_status=source.automation_status,
                    source=TestCaseSource.RUN_REGRESSION,
                    source_ref=str(run_id.value),
                    component=source.component,
                    requirement_refs=source.requirement_refs,
                    owner_id=source.owner_id,
                    preconditions=source.preconditions,
                    input=failed_case.input_snapshot,
                    data_bindings=source.data_bindings,
                    steps=source.steps,
                    execution_mode=source.execution_mode,
                    assertions=assertions,
                    scorers=source.scorers,
                    initial_state=source.initial_state,
                    expected_outcome=source.expected_outcome,
                    security_policies=source.security_policies,
                    artifact_requirements=source.artifact_requirements,
                    postconditions=source.postconditions,
                    estimated_duration_seconds=source.estimated_duration_seconds,
                    timeout_seconds=source.timeout_seconds,
                    retry_count=source.retry_count,
                    custom_fields=source.custom_fields,
                    tags=[
                        *source.tags,
                        f"generated-from-run:{run_id.value}",
                        source_tag,
                    ],
                    scenario=source.scenario,
                    priority=command.priority,
                    risk_level=command.risk_level,
                    difficulty=source.difficulty,
                    test_group=source.test_group,
                ),
            )
            generated.append(created)
            existing_tags.add(source_tag)
        return GenerateFromRunResult(
            generated_cases=generated,
            total_failed=len(failed),
            skipped_existing=skipped,
        )
