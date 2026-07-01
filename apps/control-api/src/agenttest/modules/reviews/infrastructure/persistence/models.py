"""ReviewTask SQLAlchemy 模型。"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base


class ReviewTaskModel(Base):
    __tablename__ = "review_tasks"
    __table_args__ = (
        Index("ix_review_tasks_project_status", "project_id", "status"),
        Index("ix_review_tasks_run_case", "run_case_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_case_id: Mapped[UUID] = mapped_column(ForeignKey("run_cases.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reviewer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    opinion: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReviewPolicyModel(Base):
    __tablename__ = "review_policies"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_review_policies_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    config: Mapped[dict] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
