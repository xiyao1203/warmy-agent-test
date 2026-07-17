from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base


class DatasetModel(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        Index("ix_datasets_project_created_at", "project_id", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class DatasetVersionModel(Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_number", name="uq_dataset_versions_number"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
    )
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class TestCaseModel(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('api', 'browser', 'codex_explore')",
            name="ck_test_cases_execution_mode",
        ),
        Index("ix_test_cases_version_sort", "dataset_version_id", "sort_order"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(500))
    case_key: Mapped[str] = mapped_column(String(40), unique=True)
    objective: Mapped[str] = mapped_column(Text)
    case_status: Mapped[str] = mapped_column(String(32))
    template: Mapped[str] = mapped_column(String(32))
    case_type: Mapped[str] = mapped_column(String(32))
    automation_status: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    source_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    component: Mapped[str | None] = mapped_column(String(200), nullable=True)
    requirement_refs: Mapped[list] = mapped_column(JSONB)
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    input: Mapped[dict] = mapped_column(JSONB)
    initial_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preconditions: Mapped[list] = mapped_column(JSONB)
    data_bindings: Mapped[list] = mapped_column(JSONB)
    steps: Mapped[list] = mapped_column(JSONB)
    execution_mode: Mapped[str] = mapped_column(String(32))
    expected_outcome: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    assertions: Mapped[list] = mapped_column(JSONB)
    scorers: Mapped[list] = mapped_column(JSONB)
    security_policies: Mapped[list] = mapped_column(JSONB)
    artifact_requirements: Mapped[list] = mapped_column(JSONB)
    postconditions: Mapped[list] = mapped_column(JSONB)
    estimated_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    custom_fields: Mapped[dict] = mapped_column(JSONB)
    tags: Mapped[list] = mapped_column(JSONB)
    scenario: Mapped[str | None] = mapped_column(String(200), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    test_group: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
