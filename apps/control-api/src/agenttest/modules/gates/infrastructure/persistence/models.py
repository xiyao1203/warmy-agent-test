"""ReleaseGate SQLAlchemy 模型。"""

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
)
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base


class ReleaseGateModel(Base):
    __tablename__ = "release_gates"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    success_rate_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.8,
    )
    critical_cases: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cost_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    security_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.8,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class ReleaseDecisionModel(Base):
    __tablename__ = "release_decisions"
    __table_args__ = (
        Index("ix_release_decisions_project_run", "project_id", "run_id", "created_at"),
        Index(
            "ix_release_decisions_project_gate_created",
            "project_id",
            "gate_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    gate_id: Mapped[UUID] = mapped_column(ForeignKey("release_gates.id"))
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"))
    experiment_id: Mapped[UUID | None] = mapped_column(ForeignKey("experiments.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    facts: Mapped[dict] = mapped_column(JSON)
    failures: Mapped[list] = mapped_column(JSON)
    evidence: Mapped[dict] = mapped_column(JSON)
    evaluated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
