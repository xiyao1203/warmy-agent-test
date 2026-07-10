"""Add project-scoped run case evidence and stage events.

Revision ID: 0018
Revises: 0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("run_cases") as batch_op:
        batch_op.add_column(
            sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'"))
        )
        batch_op.add_column(
            sa.Column(
                "quality_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
            )
        )
        batch_op.add_column(
            sa.Column(
                "security_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
            )
        )
    op.create_table(
        "run_case_stage_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("run_case_id", sa.Uuid(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_case_id"], ["run_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_run_case_stage_events_project_case",
        "run_case_stage_events",
        ["project_id", "run_case_id"],
    )
    op.create_index(
        "ix_run_case_stage_events_run_created",
        "run_case_stage_events",
        ["run_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_run_case_stage_events_run_created", table_name="run_case_stage_events")
    op.drop_index("ix_run_case_stage_events_project_case", table_name="run_case_stage_events")
    op.drop_table("run_case_stage_events")
    with op.batch_alter_table("run_cases") as batch_op:
        batch_op.drop_column("security_summary")
        batch_op.drop_column("quality_summary")
        batch_op.drop_column("evidence")
