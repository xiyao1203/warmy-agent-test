from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base


class RunPostprocessJobModel(Base):
    __tablename__ = "run_postprocess_jobs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "run_id"],
            ["runs.project_id", "runs.id"],
            ondelete="CASCADE",
            name="fk_run_postprocess_jobs_project_run",
        ),
        UniqueConstraint(
            "project_id",
            "run_id",
            "pipeline_version",
            name="uq_run_postprocess_jobs_project_run_pipeline",
        ),
        UniqueConstraint("project_id", "id", name="uq_run_postprocess_jobs_project_id"),
        Index(
            "ix_run_postprocess_jobs_project_status_updated",
            "project_id",
            "status",
            "updated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    run_id: Mapped[UUID] = mapped_column(nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(32))
    workflow_id: Mapped[str | None] = mapped_column(String(255))
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    warning_codes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunPostprocessStageResultModel(Base):
    __tablename__ = "run_postprocess_stage_results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "job_id"],
            ["run_postprocess_jobs.project_id", "run_postprocess_jobs.id"],
            ondelete="CASCADE",
            name="fk_run_postprocess_stage_results_project_job",
        ),
        UniqueConstraint(
            "project_id", "job_id", "stage", name="uq_run_postprocess_stage_results_job_stage"
        ),
        Index(
            "ix_run_postprocess_stage_results_project_job",
            "project_id",
            "job_id",
            "completed_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    job_id: Mapped[UUID] = mapped_column(nullable=False)
    run_id: Mapped[UUID] = mapped_column(nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    output: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    warning_code: Mapped[str | None] = mapped_column(String(100))
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunDiagnosticModel(Base):
    __tablename__ = "run_diagnostics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "run_id"],
            ["runs.project_id", "runs.id"],
            ondelete="CASCADE",
            name="fk_run_diagnostics_project_run",
        ),
        UniqueConstraint(
            "project_id",
            "run_case_id",
            "pipeline_version",
            name="uq_run_diagnostics_project_case_pipeline",
        ),
        Index("ix_run_diagnostics_project_run", "project_id", "run_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    run_id: Mapped[UUID] = mapped_column(nullable=False)
    run_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("run_cases.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_class: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    summary: Mapped[str | None] = mapped_column(Text)
    counterevidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    verification_steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    model_adapter_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunRegressionCandidateModel(Base):
    __tablename__ = "run_regression_candidates"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "run_id"],
            ["runs.project_id", "runs.id"],
            ondelete="CASCADE",
            name="fk_run_regression_candidates_project_run",
        ),
        UniqueConstraint(
            "project_id",
            "fingerprint",
            "pipeline_version",
            name="uq_run_regression_candidates_project_fingerprint_pipeline",
        ),
        Index(
            "ix_run_regression_candidates_project_status",
            "project_id",
            "status",
            "updated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    run_id: Mapped[UUID] = mapped_column(nullable=False)
    run_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("run_cases.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_reference: Mapped[dict] = mapped_column(JSON, nullable=False)
    minimized_input: Mapped[dict | None] = mapped_column(JSON)
    reproduction_run_case_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    reproduction_count: Mapped[int] = mapped_column(Integer, nullable=False)
    target_dataset_version_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunCalibrationModel(Base):
    __tablename__ = "run_calibrations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "run_id"],
            ["runs.project_id", "runs.id"],
            ondelete="CASCADE",
            name="fk_run_calibrations_project_run",
        ),
        UniqueConstraint(
            "project_id",
            "run_id",
            "pipeline_version",
            name="uq_run_calibrations_project_run_pipeline",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    run_id: Mapped[UUID] = mapped_column(nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sample_set_version: Mapped[str | None] = mapped_column(String(100))
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    arbitration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evaluator_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunJointGateDecisionModel(Base):
    __tablename__ = "run_joint_gate_decisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "run_id"],
            ["runs.project_id", "runs.id"],
            ondelete="CASCADE",
            name="fk_run_joint_gate_decisions_project_run",
        ),
        UniqueConstraint(
            "project_id",
            "run_id",
            "pipeline_version",
            name="uq_run_joint_gate_decisions_project_run_pipeline",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    run_id: Mapped[UUID] = mapped_column(nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline_run_id: Mapped[UUID | None] = mapped_column(nullable=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    rules: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    input_facts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
