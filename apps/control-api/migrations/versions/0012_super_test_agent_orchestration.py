"""super test agent orchestration

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-30 23:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "test_agent_sessions",
        sa.Column("title", sa.String(200), nullable=False, server_default="新对话"),
    )
    op.add_column(
        "test_agent_sessions",
        sa.Column("protocol_version", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "test_agent_sessions",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "test_agent_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("parent_task_id", sa.Uuid(), nullable=True),
        sa.Column("child_agent", sa.String(64), nullable=False),
        sa.Column("capability", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_tasks_project_session",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "parent_task_id"],
            ["test_agent_tasks.project_id", "test_agent_tasks.id"],
            ondelete="CASCADE",
            name="fk_test_agent_tasks_parent",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "id", name="uq_test_agent_tasks_project_id"),
        sa.UniqueConstraint(
            "project_id", "idempotency_key", name="uq_test_agent_tasks_idempotency"
        ),
    )
    op.create_index(
        "ix_test_agent_tasks_session_status",
        "test_agent_tasks",
        ["project_id", "session_id", "status"],
    )

    op.create_table(
        "test_agent_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_events_project_session",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "session_id", "sequence", name="uq_test_agent_events_sequence"
        ),
    )
    op.create_index(
        "ix_test_agent_events_session_sequence",
        "test_agent_events",
        ["project_id", "session_id", "sequence"],
    )

    op.create_table(
        "test_agent_confirmations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("preview", sa.JSON(), nullable=False),
        sa.Column("decided_by", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "task_id"],
            ["test_agent_tasks.project_id", "test_agent_tasks.id"],
            ondelete="CASCADE",
            name="fk_test_agent_confirmations_project_task",
        ),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "id", name="uq_test_agent_confirmations_project_id"
        ),
        sa.UniqueConstraint(
            "project_id", "task_id", name="uq_test_agent_confirmations_task"
        ),
    )

    op.create_table(
        "test_agent_artifact_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("relation", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_artifacts_project_session",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "task_id"],
            ["test_agent_tasks.project_id", "test_agent_tasks.id"],
            ondelete="CASCADE",
            name="fk_test_agent_artifacts_project_task",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "task_id",
            "artifact_type",
            "artifact_id",
            "relation",
            name="uq_test_agent_artifact_relation",
        ),
    )
    op.create_index(
        "ix_test_agent_artifacts_reverse",
        "test_agent_artifact_links",
        ["project_id", "artifact_type", "artifact_id"],
    )

    op.create_table(
        "target_agent_chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("agent_version_id", sa.Uuid(), nullable=False),
        sa.Column("environment_template_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["agent_version_id"], ["agent_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["environment_template_id"],
            ["environment_templates.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "id", name="uq_target_chat_sessions_project_id"
        ),
    )
    op.create_index(
        "ix_target_chat_sessions_project_updated",
        "target_agent_chat_sessions",
        ["project_id", "updated_at"],
    )

    op.create_table(
        "target_agent_chat_turns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("trace", sa.JSON(), nullable=True),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("token_usage", sa.JSON(), nullable=True),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["target_agent_chat_sessions.project_id", "target_agent_chat_sessions.id"],
            ondelete="CASCADE",
            name="fk_target_chat_turns_project_session",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "session_id", "sequence", name="uq_target_chat_turns_sequence"
        ),
    )
    op.create_index(
        "ix_target_chat_turns_session_sequence",
        "target_agent_chat_turns",
        ["project_id", "session_id", "sequence"],
    )


def downgrade() -> None:
    op.drop_index("ix_target_chat_turns_session_sequence", table_name="target_agent_chat_turns")
    op.drop_table("target_agent_chat_turns")
    op.drop_index(
        "ix_target_chat_sessions_project_updated", table_name="target_agent_chat_sessions"
    )
    op.drop_table("target_agent_chat_sessions")
    op.drop_index("ix_test_agent_artifacts_reverse", table_name="test_agent_artifact_links")
    op.drop_table("test_agent_artifact_links")
    op.drop_table("test_agent_confirmations")
    op.drop_index("ix_test_agent_events_session_sequence", table_name="test_agent_events")
    op.drop_table("test_agent_events")
    op.drop_index("ix_test_agent_tasks_session_status", table_name="test_agent_tasks")
    op.drop_table("test_agent_tasks")
    op.drop_column("test_agent_sessions", "archived_at")
    op.drop_column("test_agent_sessions", "protocol_version")
    op.drop_column("test_agent_sessions", "title")
