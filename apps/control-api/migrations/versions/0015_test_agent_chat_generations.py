"""Add recoverable Test Agent chat generations.

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "test_agent_chat_generations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.String(200), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("partial_content", sa.Text(), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id", "session_id"],
            ["test_agent_sessions.project_id", "test_agent_sessions.id"],
            name="fk_test_agent_generations_project_session",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "id", name="uq_test_agent_generations_project_id"),
    )
    op.create_index(
        "ix_test_agent_generations_session_status",
        "test_agent_chat_generations",
        ["project_id", "session_id", "status"],
    )
    with op.batch_alter_table("test_agent_events") as batch_op:
        batch_op.add_column(sa.Column("generation_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_test_agent_events_project_generation",
            "test_agent_chat_generations",
            ["project_id", "generation_id"],
            ["project_id", "id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(
            "ix_test_agent_events_generation",
            ["project_id", "generation_id", "sequence"],
        )


def downgrade() -> None:
    with op.batch_alter_table("test_agent_events") as batch_op:
        batch_op.drop_index("ix_test_agent_events_generation")
        batch_op.drop_constraint("fk_test_agent_events_project_generation", type_="foreignkey")
        batch_op.drop_column("generation_id")
    op.drop_index(
        "ix_test_agent_generations_session_status",
        table_name="test_agent_chat_generations",
    )
    op.drop_table("test_agent_chat_generations")
