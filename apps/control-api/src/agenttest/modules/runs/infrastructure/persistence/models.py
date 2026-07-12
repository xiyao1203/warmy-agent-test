from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base

RUN_STATUSES = "'queued', 'running', 'passed', 'failed', 'error', 'cancelled'"


class RunModel(Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "idempotency_key",
            name="uq_runs_project_idempotency_key",
        ),
        CheckConstraint(f"status IN ({RUN_STATUSES})", name="ck_runs_status"),
        Index("ix_runs_project_status_created", "project_id", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_plan_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("test_plan_versions.id"),
        nullable=False,
    )
    agent_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_versions.id"),
        nullable=False,
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_versions.id"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    config_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    plugin_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancelled_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunCaseModel(Base):
    __tablename__ = "run_cases"
    __table_args__ = (
        CheckConstraint(f"status IN ({RUN_STATUSES})", name="ck_run_cases_status"),
        Index("ix_run_cases_run_status", "run_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_case_id: Mapped[UUID] = mapped_column(ForeignKey("test_cases.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    execution_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="api", server_default="api"
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    assertion_snapshot: Mapped[list] = mapped_column(JSON, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON)
    trace: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error_type: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    quality_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    security_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    outcomes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunCaseStageEventModel(Base):
    __tablename__ = "run_case_stage_events"
    __table_args__ = (
        Index("ix_run_case_stage_events_project_case", "project_id", "run_case_id"),
        Index("ix_run_case_stage_events_run_created", "run_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    run_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("run_cases.id", ondelete="CASCADE"), nullable=False
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunEventModel(Base):
    __tablename__ = "run_events"
    __table_args__ = (
        UniqueConstraint("run_id", "sequence", name="uq_run_events_sequence"),
        Index("ix_run_events_run_sequence", "run_id", "sequence"),
        Index("ix_run_events_parent", "parent_event_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    parent_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("run_events.id", ondelete="SET NULL"), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost: Mapped[float | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunEvaluationModel(Base):
    __tablename__ = "run_evaluations"
    __table_args__ = (
        UniqueConstraint("project_id", "run_id", name="uq_run_evaluations_project_run"),
        UniqueConstraint("project_id", "id", name="uq_run_evaluations_project_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32))
    aggregate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_rate: Mapped[float] = mapped_column(Float)
    total_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_usage: Mapped[dict] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScoreModel(Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint(
            "evaluation_id", "run_case_id", "scorer_version_id", name="uq_scores_source"
        ),
        Index("ix_scores_project_case", "project_id", "run_case_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("run_evaluations.id", ondelete="CASCADE")
    )
    run_case_id: Mapped[UUID] = mapped_column(ForeignKey("run_cases.id", ondelete="CASCADE"))
    scorer_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("scorer_versions.id"), nullable=True
    )
    score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
