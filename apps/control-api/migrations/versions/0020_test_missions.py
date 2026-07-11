"""Add project-scoped conversational test missions.

Revision ID: 0020
Revises: 0019
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MISSION_STATUSES = (
    "'collecting', 'needs_input', 'discovering', 'ready_for_confirmation', "
    "'confirmed', 'provisioning', 'running', 'needs_attention', "
    "'completed', 'failed', 'cancelled'"
)
FACT_SOURCES = "'system_inferred', 'target_discovered', 'platform_resolved', 'user_provided'"


def upgrade() -> None:
    op.create_table(
        "test_missions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("active_revision_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_id", sa.String(length=255), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"status IN ({MISSION_STATUSES})", name="ck_test_missions_status"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_missions_project_session",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "id", name="uq_test_missions_project_id"),
    )
    op.create_index(
        "ix_test_missions_project_status_updated",
        "test_missions",
        ["project_id", "status", "updated_at"],
    )
    op.create_index(
        "ix_test_missions_project_session", "test_missions", ["project_id", "session_id"]
    )
    op.create_table(
        "test_mission_facts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.Uuid(), nullable=False),
        sa.Column("field_key", sa.String(length=100), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("sensitive", sa.Boolean(), nullable=False),
        sa.Column("fact_revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"source IN ({FACT_SOURCES})", name="ck_mission_facts_source"),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_mission_facts_confidence"
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_facts_project_mission",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "mission_id",
            "field_key",
            name="uq_mission_facts_project_mission_key",
        ),
    )
    op.create_index(
        "ix_mission_facts_project_mission",
        "test_mission_facts",
        ["project_id", "mission_id"],
    )
    op.create_table(
        "test_mission_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.Uuid(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("confirmed_by", sa.Uuid(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_revisions_project_mission",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "mission_id", "revision_number", name="uq_mission_revisions_number"
        ),
        sa.UniqueConstraint(
            "project_id", "mission_id", "content_hash", name="uq_mission_revisions_hash"
        ),
        sa.UniqueConstraint("project_id", "id", name="uq_mission_revisions_project_id"),
    )
    op.create_index(
        "ix_mission_revisions_project_mission",
        "test_mission_revisions",
        ["project_id", "mission_id"],
    )
    op.create_table(
        "test_mission_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.Uuid(), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("relation", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_assets_project_mission",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "mission_id",
            "asset_type",
            "asset_id",
            "relation",
            name="uq_mission_asset_relation",
        ),
    )
    op.create_index(
        "ix_mission_assets_reverse",
        "test_mission_assets",
        ["project_id", "asset_type", "asset_id"],
    )
    op.create_table(
        "test_mission_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "mission_id"],
            ["test_missions.project_id", "test_missions.id"],
            ondelete="CASCADE",
            name="fk_mission_events_project_mission",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "mission_id", "sequence", name="uq_mission_events_sequence"
        ),
    )
    op.create_index(
        "ix_mission_events_project_mission_sequence",
        "test_mission_events",
        ["project_id", "mission_id", "sequence"],
    )
    op.create_table(
        "test_mission_stage_receipts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "revision_id"],
            ["test_mission_revisions.project_id", "test_mission_revisions.id"],
            ondelete="CASCADE",
            name="fk_mission_receipts_project_revision",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "revision_id", "stage", name="uq_mission_receipts_revision_stage"
        ),
    )
    op.create_index(
        "ix_mission_receipts_project_revision",
        "test_mission_stage_receipts",
        ["project_id", "revision_id", "stage"],
    )


def downgrade() -> None:
    op.drop_index("ix_mission_receipts_project_revision", table_name="test_mission_stage_receipts")
    op.drop_table("test_mission_stage_receipts")
    op.drop_index("ix_mission_events_project_mission_sequence", table_name="test_mission_events")
    op.drop_table("test_mission_events")
    op.drop_index("ix_mission_assets_reverse", table_name="test_mission_assets")
    op.drop_table("test_mission_assets")
    op.drop_index("ix_mission_revisions_project_mission", table_name="test_mission_revisions")
    op.drop_table("test_mission_revisions")
    op.drop_index("ix_mission_facts_project_mission", table_name="test_mission_facts")
    op.drop_table("test_mission_facts")
    op.drop_index("ix_test_missions_project_session", table_name="test_missions")
    op.drop_index("ix_test_missions_project_status_updated", table_name="test_missions")
    op.drop_table("test_missions")
