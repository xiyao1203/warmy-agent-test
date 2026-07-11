"""Add project-scoped browser profiles and encrypted auth state.

Revision ID: 0019
Revises: 0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "browser_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("target_domain", sa.String(length=500), nullable=False),
        sa.Column("user_data_dir", sa.String(length=1000), nullable=False),
        sa.Column("cdp_port", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("auth_state_status", sa.String(length=32), nullable=False),
        sa.Column("auth_state_envelope", sa.Text(), nullable=True),
        sa.Column("auth_state_sha256", sa.String(length=64), nullable=True),
        sa.Column("auth_state_version", sa.Integer(), nullable=False),
        sa.Column("auth_state_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by_run_case_id", sa.Uuid(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('stopped', 'starting', 'running', 'error')",
            name="ck_browser_profiles_status",
        ),
        sa.CheckConstraint(
            "auth_state_status IN ('missing', 'ready', 'expired', 'error')",
            name="ck_browser_profiles_auth_state_status",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["locked_by_run_case_id"], ["run_cases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "name", name="uq_browser_profiles_project_name"),
    )
    op.create_index(
        "ix_browser_profiles_project_updated",
        "browser_profiles",
        ["project_id", "updated_at"],
    )
    op.create_index(
        "ix_browser_profiles_project_status",
        "browser_profiles",
        ["project_id", "auth_state_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_browser_profiles_project_status", table_name="browser_profiles")
    op.drop_index("ix_browser_profiles_project_updated", table_name="browser_profiles")
    op.drop_table("browser_profiles")
