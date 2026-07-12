from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutePostprocessStageRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=300)
    workflow_id: str = Field(min_length=1, max_length=255)
    attempt: int = Field(default=1, ge=1, le=100)


class PostprocessStageResponse(BaseModel):
    status: str
    output: dict[str, object]
    warning_code: str | None = None


class TrustLoopResponse(BaseModel):
    job_id: UUID | None
    project_id: UUID
    run_id: UUID
    pipeline_version: str
    status: str
    current_stage: str | None
    classifications: list[dict[str, object]]
    diagnostics: dict[str, object]
    regressions: list[dict[str, object]]
    calibration: dict[str, object]
    joint_gate: dict[str, object] | None
    warning_codes: list[str]
    error_type: str | None
    created_at: datetime | None
    updated_at: datetime | None
    completed_at: datetime | None


class DiagnosticResponse(BaseModel):
    id: UUID
    run_case_id: UUID
    pipeline_version: str
    status: str
    failure_class: str
    confidence: float
    evidence_ids: list[str]
    summary: str | None
    counterevidence: list[str]
    verification_steps: list[str]
    created_at: datetime
    updated_at: datetime


class DiagnosticListResponse(BaseModel):
    items: list[DiagnosticResponse]
    total: int
    limit: int
    offset: int


class RegressionCandidateResponse(BaseModel):
    id: UUID
    run_case_id: UUID
    pipeline_version: str
    fingerprint: str
    status: str
    input_reference: dict[str, object]
    minimized_input: dict[str, object] | None
    reproduction_run_case_ids: list[str]
    reproduction_count: int
    target_dataset_version_id: UUID | None
    created_at: datetime
    updated_at: datetime


class RegressionCandidateListResponse(BaseModel):
    items: list[RegressionCandidateResponse]
    total: int
    limit: int
    offset: int


class CalibrationResponse(BaseModel):
    id: UUID | None
    pipeline_version: str
    status: str
    sample_set_version: str | None
    metrics: dict[str, object]
    arbitration: dict[str, object]
    evaluator_version: str | None
    created_at: datetime | None
    updated_at: datetime | None


class JointGateDecisionResponse(BaseModel):
    id: UUID | None
    pipeline_version: str
    status: str
    baseline_run_id: UUID | None
    decision: str | None
    rules: list[dict[str, object]]
    input_facts: dict[str, object]
    explanation: str | None
    created_at: datetime | None
