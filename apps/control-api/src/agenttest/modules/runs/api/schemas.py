from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from agenttest.modules.runs.domain.entities import Run, RunCase


class CreateRunRequest(BaseModel):
    test_plan_version_id: UUID


class RunResponse(BaseModel):
    id: UUID
    project_id: UUID
    test_plan_version_id: UUID
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
            test_plan_version_id=run.test_plan_version_id.value,
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
        )


class RunCaseListResponse(BaseModel):
    items: list[RunCaseResponse]


class ApplyRunCaseResultRequest(BaseModel):
    run_case_id: UUID
    status: str
    output: dict[str, object] | None = None
    trace: list[dict[str, object]] = []
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None


class ApplyRunResultRequest(BaseModel):
    cases: list[ApplyRunCaseResultRequest]
