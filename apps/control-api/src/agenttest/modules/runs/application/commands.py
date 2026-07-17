from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.run_postprocessing.public import RunPostprocessCreator
from agenttest.modules.runs.application.ports import (
    ProjectAccessPort,
    ReviewCollectorPort,
    RunIdempotencyConflict,
    RunIdempotencyKeyExists,
    RunOrchestrator,
    RunRepository,
    RunSourcePort,
)
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.evidence import (
    ExecutionOutcome,
    QualityDecision,
    RunCaseEvidence,
    SecurityDecision,
)
from agenttest.modules.runs.domain.outcomes import Outcome, RunCaseOutcomes
from agenttest.modules.runs.domain.value_objects import RunCaseStatus, RunStatus, RunType
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
    evidence: dict[str, object] | None = None


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
        request_fingerprint = _plan_run_request_fingerprint(command)
        existing = await self._runs.get_by_idempotency_key(command.project_id, key)
        if existing is not None:
            return _reuse_exact_plan_run(existing, command, request_fingerprint)
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
            config_snapshot={
                **definition.config_snapshot,
                "plan_run_request_fingerprint": request_fingerprint,
            },
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
                case_spec_snapshot=item.case_spec_snapshot,
                execution_mode=item.execution_mode,
            )
            for item in definition.cases
        ]
        try:
            await self._runs.add(run, cases)
        except RunIdempotencyKeyExists:
            winner = await self._runs.get_by_idempotency_key(command.project_id, key)
            if winner is None:
                raise RuntimeError(
                    "Run idempotency conflict was not visible after transaction rollback"
                ) from None
            return _reuse_exact_plan_run(winner, command, request_fingerprint)
        workflow_id = await self._orchestrator.start(run, cases)
        run.start(workflow_id)
        await self._runs.save(run)
        return CreateRunResult(run=run, created=True)


def _plan_run_request_fingerprint(command: CreateRunCommand) -> str:
    canonical = json.dumps(
        {
            "run_type": RunType.PLAN.value,
            "project_id": str(command.project_id.value),
            "test_plan_version_id": str(command.test_plan_version_id.value),
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return sha256(canonical).hexdigest()


def _reuse_exact_plan_run(
    existing: Run,
    command: CreateRunCommand,
    request_fingerprint: str,
) -> CreateRunResult:
    stored_fingerprint = existing.config_snapshot.get("plan_run_request_fingerprint")
    legacy_exact_match = (
        stored_fingerprint is None
        and existing.run_type is RunType.PLAN
        and existing.test_plan_version_id == command.test_plan_version_id
    )
    if not legacy_exact_match and (
        existing.run_type is not RunType.PLAN
        or existing.test_plan_version_id != command.test_plan_version_id
        or stored_fingerprint != request_fingerprint
    ):
        raise RunIdempotencyConflict(
            "Idempotency-Key is already used by a different plan run request"
        )
    return CreateRunResult(run=existing, created=False)


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
        postprocess: RunPostprocessCreator | None = None,
    ) -> None:
        self._runs = runs
        self._review_collector = review_collector
        self._postprocess = postprocess

    async def execute(self, command: ApplyRunResultCommand) -> Run:
        run = await self._runs.get_by_id(command.project_id, command.run_id)
        if run is None:
            raise RunNotFoundError
        if run.status.is_terminal:
            await self._ensure_postprocess(run)
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
            evidence = RunCaseEvidence.from_payload(result.evidence or {})
            case.evidence = evidence.to_dict()
            case.quality_summary = {"decision": evidence.quality_decision.value}
            case.security_summary = {"decision": evidence.security_decision.value}
            case.outcomes = _project_outcomes(
                case,
                result.status,
                evidence,
                error_type=result.error_type,
            )
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
        await self._ensure_postprocess(run)
        if self._review_collector is not None:
            await self._review_collector.collect(run.project_id, run.run_id)
        return run

    async def _ensure_postprocess(self, run: Run) -> None:
        if self._postprocess is not None and run.status is not RunStatus.CANCELLED:
            await self._postprocess.ensure_created(run.project_id.value, run.run_id.value)


def _count(cases: list[RunCase], status: RunCaseStatus) -> int:
    return sum(1 for case in cases if case.status is status)


def _project_outcomes(
    case: RunCase,
    status: RunCaseStatus,
    evidence: RunCaseEvidence,
    *,
    error_type: str | None,
) -> RunCaseOutcomes:
    evidence_ids = (uuid5(NAMESPACE_URL, f"agenttest:run-case-evidence:{case.run_case_id.value}"),)
    execution = (
        Outcome.passed(evidence_ids=evidence_ids)
        if evidence.execution_outcome is ExecutionOutcome.SUCCESS
        else Outcome.error(
            "execution_cancelled"
            if evidence.execution_outcome is ExecutionOutcome.CANCELLED
            else error_type or "execution_error",
            evidence_ids=evidence_ids,
        )
    )
    assertion = (
        Outcome.passed(evidence_ids=evidence_ids)
        if status is RunCaseStatus.PASSED
        else Outcome.failed("assertion_mismatch", evidence_ids=evidence_ids)
    )
    quality = {
        QualityDecision.PASS: lambda: Outcome.passed(evidence_ids=evidence_ids),
        QualityDecision.FAIL: lambda: Outcome.failed("quality_failed", evidence_ids=evidence_ids),
        QualityDecision.REVIEW_REQUIRED: lambda: Outcome.needs_review(
            "quality_review_required", evidence_ids=evidence_ids
        ),
    }[evidence.quality_decision]()
    security = (
        Outcome.passed(evidence_ids=evidence_ids)
        if evidence.security_decision is SecurityDecision.CLEAR
        else Outcome.failed(
            "security_blocked"
            if evidence.security_decision is SecurityDecision.BLOCKED
            else "security_finding",
            evidence_ids=evidence_ids,
        )
    )
    return RunCaseOutcomes(execution, assertion, quality, security)


def _default_error_type(status: RunCaseStatus) -> str:
    if status is RunCaseStatus.CANCELLED:
        return "CancelledError"
    if status is RunCaseStatus.ERROR:
        return "PlatformError"
    return "AssertionError"
