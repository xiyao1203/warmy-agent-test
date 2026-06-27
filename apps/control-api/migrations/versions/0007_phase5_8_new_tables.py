"""Phase 5-8 新表 + run_events 扩展。

- scorers 表（Phase 6 评分器）
- experiments 表（Phase 7 实验对比）
- review_tasks 表（Phase 8 人工审核）
- run_events 新增列（Phase 5 Trace）
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Phase 5: run_events 扩展列 ────────────────────────────────────────
    op.add_column(
        "run_events",
        sa.Column("parent_event_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_run_events_parent",
        "run_events",
        "run_events",
        ["parent_event_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_run_events_parent", "run_events", ["parent_event_id"],
    )
    op.add_column("run_events", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("run_events", sa.Column("token_count", sa.Integer(), nullable=True))
    op.add_column("run_events", sa.Column("cost", sa.Float(), nullable=True))
    op.add_column("run_events", sa.Column("metadata", sa.JSON(), nullable=True))

    # ── Phase 6: scorers 表 ───────────────────────────────────────────────
    op.create_table(
        "scorers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("scorer_type", sa.String(32), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("threshold", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_scorers_project_enabled", "scorers", ["project_id", "enabled"],
    )

    # ── Phase 7: experiments 表 ───────────────────────────────────────────
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "run_a_id",
            sa.Uuid(),
            sa.ForeignKey("runs.id"),
            nullable=False,
        ),
        sa.Column(
            "run_b_id",
            sa.Uuid(),
            sa.ForeignKey("runs.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("result_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_experiments_project_status", "experiments", ["project_id", "status"],
    )

    # ── Phase 8: review_tasks 表 ──────────────────────────────────────────
    op.create_table(
        "review_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_case_id",
            sa.Uuid(),
            sa.ForeignKey("run_cases.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "reviewer_id",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("opinion", sa.Text(), nullable=True),
        sa.Column("rubric_scores", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_review_tasks_project_status", "review_tasks", ["project_id", "status"],
    )
    op.create_index(
        "ix_review_tasks_run_case", "review_tasks", ["run_case_id"],
    )


def downgrade() -> None:
    op.drop_table("review_tasks")
    op.drop_table("experiments")
    op.drop_table("scorers")
    op.drop_column("run_events", "metadata")
    op.drop_column("run_events", "cost")
    op.drop_column("run_events", "token_count")
    op.drop_column("run_events", "duration_ms")
    op.drop_index("ix_run_events_parent", table_name="run_events")
    op.drop_constraint("fk_run_events_parent", "run_events", type_="foreignkey")
    op.drop_column("run_events", "parent_event_id")
