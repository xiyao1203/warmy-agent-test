"""persist test agent sessions

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-30 11:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "test_agent_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("plan_draft", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "id", name="uq_test_agent_sessions_project_id"),
    )
    op.create_index(
        "ix_test_agent_sessions_project_updated",
        "test_agent_sessions",
        ["project_id", sa.text("updated_at DESC")],
    )
    op.create_table(
        "test_agent_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            ondelete="CASCADE",
            name="fk_test_agent_messages_project_session",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "session_id",
            "sequence",
            name="uq_test_agent_messages_sequence",
        ),
    )
    op.create_index(
        "ix_test_agent_messages_project_session_sequence",
        "test_agent_messages",
        ["project_id", "session_id", "sequence"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_test_agent_messages_project_session_sequence",
        table_name="test_agent_messages",
    )
    op.drop_table("test_agent_messages")
    op.drop_index(
        "ix_test_agent_sessions_project_updated",
        table_name="test_agent_sessions",
    )
    op.drop_table("test_agent_sessions")
