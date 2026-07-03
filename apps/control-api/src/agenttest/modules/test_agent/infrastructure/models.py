from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
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
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="新对话")
    protocol_version: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class TestAgentTaskModel(Base):
    __tablename__ = "test_agent_tasks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_tasks_project_session",
        ),
        ForeignKeyConstraint(
            ["project_id", "parent_task_id"],
            ["test_agent_tasks.project_id", "test_agent_tasks.id"],
            ondelete="CASCADE",
            name="fk_test_agent_tasks_parent",
        ),
        UniqueConstraint("project_id", "id", name="uq_test_agent_tasks_project_id"),
        UniqueConstraint("project_id", "idempotency_key", name="uq_test_agent_tasks_idempotency"),
        Index("ix_test_agent_tasks_session_status", "project_id", "session_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    parent_task_id: Mapped[UUID | None] = mapped_column(nullable=True)
    child_agent: Mapped[str] = mapped_column(String(64), nullable=False)
    capability: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    input: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestAgentEventModel(Base):
    __tablename__ = "test_agent_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_events_project_session",
        ),
        ForeignKeyConstraint(
            ["project_id", "generation_id"],
            ["test_agent_chat_generations.project_id", "test_agent_chat_generations.id"],
            ondelete="CASCADE",
            name="fk_test_agent_events_project_generation",
        ),
        UniqueConstraint(
            "project_id", "session_id", "sequence", name="uq_test_agent_events_sequence"
        ),
        Index("ix_test_agent_events_session_sequence", "project_id", "session_id", "sequence"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    generation_id: Mapped[UUID | None] = mapped_column(nullable=True)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestAgentChatGenerationModel(Base):
    __tablename__ = "test_agent_chat_generations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_generations_project_session",
        ),
        UniqueConstraint("project_id", "id", name="uq_test_agent_generations_project_id"),
        Index(
            "ix_test_agent_generations_session_status",
            "project_id",
            "session_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    workflow_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    partial_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TestAgentConfirmationModel(Base):
    __tablename__ = "test_agent_confirmations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "task_id"],
            ["test_agent_tasks.project_id", "test_agent_tasks.id"],
            ondelete="CASCADE",
            name="fk_test_agent_confirmations_project_task",
        ),
        UniqueConstraint("project_id", "id", name="uq_test_agent_confirmations_project_id"),
        UniqueConstraint("project_id", "task_id", name="uq_test_agent_confirmations_task"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    task_id: Mapped[UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    preview: Mapped[dict] = mapped_column(JSON, nullable=False)
    decided_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestAgentArtifactLinkModel(Base):
    __tablename__ = "test_agent_artifact_links"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_artifacts_project_session",
        ),
        ForeignKeyConstraint(
            ["project_id", "task_id"],
            ["test_agent_tasks.project_id", "test_agent_tasks.id"],
            ondelete="CASCADE",
            name="fk_test_agent_artifacts_project_task",
        ),
        UniqueConstraint(
            "project_id",
            "task_id",
            "artifact_type",
            "artifact_id",
            "relation",
            name="uq_test_agent_artifact_relation",
        ),
        Index(
            "ix_test_agent_artifacts_reverse",
            "project_id",
            "artifact_type",
            "artifact_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    task_id: Mapped[UUID] = mapped_column(nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_id: Mapped[UUID] = mapped_column(nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TargetAgentChatSessionModel(Base):
    __tablename__ = "target_agent_chat_sessions"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_target_chat_sessions_project_id"),
        Index("ix_target_chat_sessions_project_updated", "project_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    agent_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_versions.id", ondelete="RESTRICT"), nullable=False
    )
    environment_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("environment_templates.id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TargetAgentChatTurnModel(Base):
    __tablename__ = "target_agent_chat_turns"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["target_agent_chat_sessions.project_id", "target_agent_chat_sessions.id"],
            ondelete="CASCADE",
            name="fk_target_chat_turns_project_session",
        ),
        UniqueConstraint(
            "project_id", "session_id", "sequence", name="uq_target_chat_turns_sequence"
        ),
        Index("ix_target_chat_turns_session_sequence", "project_id", "session_id", "sequence"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    input: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trace: Mapped[list | None] = mapped_column(JSON, nullable=True)
    scores: Mapped[list | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
