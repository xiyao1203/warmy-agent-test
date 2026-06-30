from datetime import datetime
from uuid import UUID

from sqlalchemy import (
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


class TestPlanModel(Base):
    __tablename__ = "test_plans"
    __table_args__ = (
        Index("ix_test_plans_project_created_at", "project_id", text("created_at DESC")),
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


class TestPlanVersionModel(Base):
    __tablename__ = "test_plan_versions"
    __table_args__ = (
        UniqueConstraint("test_plan_id", "version_number", name="uq_test_plan_versions_number"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    test_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("test_plans.id", ondelete="CASCADE"),
    )
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    agent_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("agent_versions.id", ondelete="SET NULL"), nullable=True
    )
    dataset_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True
    )
    environment_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("environment_templates.id", ondelete="SET NULL"), nullable=True
    )
    config: Mapped[dict] = mapped_column(JSONB)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
