"""Add test assets schema: agents, datasets, test cases, test plans, environments."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- agents ---
    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("agent_type", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.CheckConstraint(
            "agent_type IN ('generic_http', 'canvas')",
            name="ck_agents_agent_type",
        ),
    )
    op.create_index(
        "ix_agents_project_created_at",
        "agents",
        [sa.text("project_id"), sa.text("created_at DESC")],
    )

    # --- agent_versions ---
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_agent_versions_status",
        ),
        sa.UniqueConstraint("agent_id", "version_number", name="uq_agent_versions_number"),
    )

    # --- environment_templates (before test_plan_versions for FK) ---
    op.create_table(
        "environment_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_type", sa.String(32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint(
            "template_type IN ('blank', 'preset')",
            name="ck_environment_templates_type",
        ),
        sa.UniqueConstraint("project_id", "name", name="uq_environment_templates_project_name"),
    )
    op.create_index(
        "ix_environment_templates_project",
        "environment_templates",
        [sa.text("project_id"), sa.text("created_at DESC")],
    )

    # --- datasets ---
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index(
        "ix_datasets_project_created_at",
        "datasets",
        [sa.text("project_id"), sa.text("created_at DESC")],
    )

    # --- dataset_versions ---
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_dataset_versions_status",
        ),
        sa.UniqueConstraint("dataset_id", "version_number", name="uq_dataset_versions_number"),
    )

    # --- test_cases ---
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("initial_state", sa.JSON(), nullable=True),
        sa.Column("execution_mode", sa.String(32), nullable=False),
        sa.Column("expected_outcome", sa.JSON(), nullable=True),
        sa.Column("assertions", sa.JSON(), nullable=False),
        sa.Column("scorers", sa.JSON(), nullable=False),
        sa.Column("security_policies", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("scenario", sa.String(200), nullable=True),
        sa.Column("priority", sa.String(32), nullable=True),
        sa.Column("risk_level", sa.String(32), nullable=True),
        sa.Column("difficulty", sa.String(32), nullable=True),
        sa.Column("test_group", sa.String(32), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"], ["dataset_versions.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "execution_mode IN ('api', 'browser')",
            name="ck_test_cases_execution_mode",
        ),
    )
    op.create_index(
        "ix_test_cases_version_sort",
        "test_cases",
        ["dataset_version_id", "sort_order"],
    )

    # --- test_plans ---
    op.create_table(
        "test_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index(
        "ix_test_plans_project_created_at",
        "test_plans",
        [sa.text("project_id"), sa.text("created_at DESC")],
    )

    # --- test_plan_versions ---
    op.create_table(
        "test_plan_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("test_plan_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("agent_version_id", sa.Uuid(), nullable=True),
        sa.Column("dataset_version_id", sa.Uuid(), nullable=True),
        sa.Column("environment_template_id", sa.Uuid(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["test_plan_id"], ["test_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_version_id"], ["agent_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["environment_template_id"], ["environment_templates.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_test_plan_versions_status",
        ),
        sa.UniqueConstraint(
            "test_plan_id", "version_number", name="uq_test_plan_versions_number"
        ),
    )


def downgrade() -> None:
    op.drop_table("test_plan_versions")
    op.drop_table("test_plans")
    op.drop_index("ix_test_cases_version_sort", table_name="test_cases")
    op.drop_table("test_cases")
    op.drop_table("dataset_versions")
    op.drop_index("ix_datasets_project_created_at", table_name="datasets")
    op.drop_table("datasets")
    op.drop_index("ix_environment_templates_project", table_name="environment_templates")
    op.drop_table("environment_templates")
    op.drop_table("agent_versions")
    op.drop_index("ix_agents_project_created_at", table_name="agents")
    op.drop_table("agents")
