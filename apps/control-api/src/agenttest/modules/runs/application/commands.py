from __future__ import annotations

from dataclasses import dataclass

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.ports import (
    ProjectAccessPort,
    ReviewCollectorPort,
    RunOrchestrator,
    RunRepository,
    RunSourcePort,
)
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.value_objects import RunCaseStatus
from agenttest.modules.test_plans.public import TestPlanVersionId


@dataclass(frozen=True, slots=True)
class CreateRunCommand:
    project_id: ProjectId
    test_plan_version_id: TestPlanVersionId
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class CreateRunResult:
    run: Run
    created: bool


@dataclass(frozen=True, slots=True)
class ApplyRunCaseScore:
    scorer_version_id: str
    scorer_type: str
    score: float
    passed: bool
    explanation: str = ""
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class ApplyRunCaseResult:
    run_case_id: RunCaseId
    status: RunCaseStatus
    output: dict[str, object] | None = None
    trace: list[dict[str, object]] | None = None
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    scores: list[ApplyRunCaseScore] | None = None


@dataclass(frozen=True, slots=True)
class ApplyRunResultCommand:
    project_id: ProjectId
    run_id: RunId
    cases: list[ApplyRunCaseResult]


class RunNotFoundError(Exception):
    pass


class CreateRunHandler:
    def __init__(
        self,
        *,
        runs: RunRepository,
        source: RunSourcePort,
        project_access: ProjectAccessPort,
        orchestrator: RunOrchestrator,
    ) -> None:
        self._runs = runs
        self._source = source
        self._project_access = project_access
        self._orchestrator = orchestrator

    async def execute(self, actor: User, command: CreateRunCommand) -> CreateRunResult:
        await self._project_access.ensure_editor(actor, command.project_id)
        key = command.idempotency_key.strip()
        if not key:
            raise ValueError("Idempotency-Key is required")
        existing = await self._runs.get_by_idempotency_key(command.project_id, key)
        if existing is not None:
            return CreateRunResult(run=existing, created=False)
        await self._orchestrator.ensure_available()
        definition = await self._source.load(
            command.project_id,
            command.test_plan_version_id,
        )
        if not definition.cases:
            raise ValueError("Published test plan has no test cases")
        run = Run.create(
            run_id=RunId.new(),
            project_id=command.project_id,
            test_plan_version_id=definition.test_plan_version_id,
            agent_version_id=definition.agent_version_id,
            dataset_version_id=definition.dataset_version_id,
            idempotency_key=key,
            created_by=actor.user_id,
            config_snapshot=definition.config_snapshot,
            plugin_snapshot=definition.plugin_snapshot,
            total_cases=len(definition.cases),
        )
        cases = [
            RunCase.create(
                run_case_id=RunCaseId.new(),
                run_id=run.run_id,
                test_case_id=item.test_case_id,
                name=item.name,
                input_snapshot=item.input_snapshot,
                assertion_snapshot=item.assertion_snapshot,
            )
            for item in definition.cases
        ]
        await self._runs.add(run, cases)
        workflow_id = await self._orchestrator.start(run, cases)
        run.start(workflow_id)
        await self._runs.save(run)
        return CreateRunResult(run=run, created=True)


class CancelRunHandler:
    def __init__(
        self,
        *,
        runs: RunRepository,
        project_access: ProjectAccessPort,
        orchestrator: RunOrchestrator,
    ) -> None:
        self._runs = runs
        self._project_access = project_access
        self._orchestrator = orchestrator

    async def execute(self, actor: User, project_id: ProjectId, run_id: RunId) -> Run:
        await self._project_access.ensure_editor(actor, project_id)
        run = await self._runs.get_by_id(project_id, run_id)
        if run is None:
            raise RunNotFoundError
        await self._orchestrator.cancel(run)
        run.cancel()
        await self._runs.save(run)
        return run


class ApplyRunResultHandler:
    def __init__(
        self,
        *,
        runs: RunRepository,
        review_collector: ReviewCollectorPort | None = None,
    ) -> None:
        self._runs = runs
        self._review_collector = review_collector

    async def execute(self, command: ApplyRunResultCommand) -> Run:
        run = await self._runs.get_by_id(command.project_id, command.run_id)
        if run is None:
            raise RunNotFoundError
        if run.status.is_terminal:
            return run

        cases = await self._runs.list_cases(command.project_id, run.run_id)
        if len(command.cases) != run.total_cases:
            raise ValueError("Run result must include every run case")

        cases_by_id = {case.run_case_id: case for case in cases}
        score_map: dict[str, list[dict[str, object]]] = {}
        for result in command.cases:
            case = cases_by_id.get(result.run_case_id)
            if case is None:
                raise ValueError("Unknown run case in result")
            if case.status.is_terminal:
                continue
            if case.status is RunCaseStatus.QUEUED:
                case.start()
            if result.status is RunCaseStatus.PASSED:
                case.pass_case(
                    output=result.output or {},
                    trace=result.trace or [],
                    duration_ms=result.duration_ms or 0,
                )
                if result.scores:
                    score_map[str(case.run_case_id.value)] = [
                        {
                            "scorer_version_id": s.scorer_version_id,
                            "scorer_type": s.scorer_type,
                            "score": s.score,
                            "passed": s.passed,
                            "explanation": s.explanation,
                            "confidence": s.confidence,
                        }
                        for s in result.scores
                    ]
                continue
            case.fail(
                status=result.status,
                error_type=result.error_type or _default_error_type(result.status),
                error_message=result.error_message or result.status.value,
                trace=result.trace or [],
                duration_ms=result.duration_ms,
            )

        passed_cases = _count(cases, RunCaseStatus.PASSED)
        failed_cases = _count(cases, RunCaseStatus.FAILED)
        error_cases = _count(cases, RunCaseStatus.ERROR)
        cancelled_cases = _count(cases, RunCaseStatus.CANCELLED)
        run.complete(
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            error_cases=error_cases,
            cancelled_cases=cancelled_cases,
        )
        await self._runs.save_result(run, cases, score_map if score_map else None)
        if self._review_collector is not None:
            await self._review_collector.collect(run.project_id, run.run_id)
        return run


def _count(cases: list[RunCase], status: RunCaseStatus) -> int:
    return sum(1 for case in cases if case.status is status)


def _default_error_type(status: RunCaseStatus) -> str:
    if status is RunCaseStatus.CANCELLED:
        return "CancelledError"
    if status is RunCaseStatus.ERROR:
        return "PlatformError"
    return "AssertionError"
