from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
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


class TestAgentSessionModel(Base):
    __tablename__ = "test_agent_sessions"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_test_agent_sessions_project_id"),
        Index("ix_test_agent_sessions_project_updated", "project_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_draft: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestAgentMessageModel(Base):
    __tablename__ = "test_agent_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_messages_project_session",
        ),
        UniqueConstraint(
            "project_id",
            "session_id",
            "sequence",
            name="uq_test_agent_messages_sequence",
        ),
        Index(
            "ix_test_agent_messages_project_session_sequence",
            "project_id",
            "session_id",
            "sequence",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
