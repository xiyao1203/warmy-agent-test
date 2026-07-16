from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.modules.runs.domain.entities import Run, RunCase


class CreateRunRequest(BaseModel):
    test_plan_version_id: UUID


class RunResponse(BaseModel):
    id: UUID
    project_id: UUID
    test_plan_version_id: UUID | None
    run_type: str
    source_test_case_id: UUID | None
    status: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    error_cases: int
    cancelled_cases: int
    workflow_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, run: Run) -> RunResponse:
        return cls(
            id=run.run_id.value,
            project_id=run.project_id.value,
            test_plan_version_id=(
                run.test_plan_version_id.value if run.test_plan_version_id else None
            ),
            run_type=run.run_type.value,
            source_test_case_id=run.source_test_case_id,
            status=run.status.value,
            total_cases=run.total_cases,
            passed_cases=run.passed_cases,
            failed_cases=run.failed_cases,
            error_cases=run.error_cases,
            cancelled_cases=run.cancelled_cases,
            workflow_id=run.workflow_id,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )


class RunListResponse(BaseModel):
    items: list[RunResponse]


class RunCaseResponse(BaseModel):
    id: UUID
    test_case_id: UUID
    name: str
    status: str
    output: dict[str, object] | None
    trace: list[dict[str, object]]
    error_type: str | None
    error_message: str | None
    duration_ms: int | None
    evidence: dict[str, object]
    quality_summary: dict[str, object]
    security_summary: dict[str, object]
    outcomes: dict[str, object]
    case_spec_snapshot: dict[str, object]

    @classmethod
    def from_domain(cls, case: RunCase) -> RunCaseResponse:
        return cls(
            id=case.run_case_id.value,
            test_case_id=case.test_case_id,
            name=case.name,
            status=case.status.value,
            output=case.output,
            trace=case.trace,
            error_type=case.error_type,
            error_message=case.error_message,
            duration_ms=case.duration_ms,
            evidence=case.evidence,
            quality_summary=case.quality_summary,
            security_summary=case.security_summary,
            outcomes=case.outcomes.to_dict(),
            case_spec_snapshot=case.case_spec_snapshot,
        )


class RunCaseListResponse(BaseModel):
    items: list[RunCaseResponse]


class ApplyRunCaseScoreRequest(BaseModel):
    scorer_version_id: str
    scorer_type: str
    score: float
    passed: bool
    explanation: str = ""
    confidence: float = 1.0


class ApplyRunCaseResultRequest(BaseModel):
    run_case_id: UUID
    status: str
    output: dict[str, object] | None = None
    trace: list[dict[str, object]] = Field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    scores: list[ApplyRunCaseScoreRequest] = Field(default_factory=list)
    evidence: dict[str, object] = Field(default_factory=dict)


class ApplyRunResultRequest(BaseModel):
    cases: list[ApplyRunCaseResultRequest]
