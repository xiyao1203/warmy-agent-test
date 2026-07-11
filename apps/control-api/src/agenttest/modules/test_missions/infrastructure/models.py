from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base

MISSION_STATUSES = (
    "'collecting', 'needs_input', 'discovering', 'ready_for_confirmation', "
    "'confirmed', 'provisioning', 'running', 'needs_attention', "
    "'completed', 'failed', 'cancelled'"
)
FACT_SOURCES = "'system_inferred', 'target_discovered', 'platform_resolved', 'user_provided'"


class TestMissionModel(Base):
    __tablename__ = "test_missions"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_test_missions_project_id"),
        ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_missions_project_session",
        ),
        CheckConstraint(f"status IN ({MISSION_STATUSES})", name="ck_test_missions_status"),
        Index("ix_test_missions_project_status_updated", "project_id", "status", "updated_at"),
        Index("ix_test_missions_project_session", "project_id", "session_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[UUID] = mapped_column(nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    active_revision_id: Mapped[UUID | None] = mapped_column(nullable=True)
    lock_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TestMissionFactModel(Base):
    __tablename__ = "test_mission_facts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_facts_project_mission",
        ),
        UniqueConstraint(
            "project_id",
            "mission_id",
            "field_key",
            name="uq_mission_facts_project_mission_key",
        ),
        CheckConstraint(f"source IN ({FACT_SOURCES})", name="ck_mission_facts_source"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_mission_facts_confidence"),
        Index("ix_mission_facts_project_mission", "project_id", "mission_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    mission_id: Mapped[UUID] = mapped_column(nullable=False)
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_json: Mapped[object] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    verified: Mapped[bool] = mapped_column(nullable=False)
    sensitive: Mapped[bool] = mapped_column(nullable=False)
    fact_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestMissionRevisionModel(Base):
    __tablename__ = "test_mission_revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_revisions_project_mission",
        ),
        UniqueConstraint(
            "project_id",
            "mission_id",
            "revision_number",
            name="uq_mission_revisions_number",
        ),
        UniqueConstraint(
            "project_id", "mission_id", "content_hash", name="uq_mission_revisions_hash"
        ),
        Index("ix_mission_revisions_project_mission", "project_id", "mission_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    mission_id: Mapped[UUID] = mapped_column(nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    confirmed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestMissionAssetModel(Base):
    __tablename__ = "test_mission_assets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_assets_project_mission",
        ),
        UniqueConstraint(
            "project_id",
            "mission_id",
            "asset_type",
            "asset_id",
            "relation",
            name="uq_mission_asset_relation",
        ),
        Index("ix_mission_assets_reverse", "project_id", "asset_type", "asset_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    mission_id: Mapped[UUID] = mapped_column(nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_id: Mapped[UUID] = mapped_column(nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TestMissionEventModel(Base):
    __tablename__ = "test_mission_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_events_project_mission",
        ),
        UniqueConstraint("project_id", "mission_id", "sequence", name="uq_mission_events_sequence"),
        Index(
            "ix_mission_events_project_mission_sequence",
            "project_id",
            "mission_id",
            "sequence",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(nullable=False)
    mission_id: Mapped[UUID] = mapped_column(nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
