"""add environment_template_id to test_accounts

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_accounts",
        sa.Column("environment_template_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_test_accounts_env_tpl",
        "test_accounts",
        "environment_templates",
        ["environment_template_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_test_accounts_env_tpl", "test_accounts", type_="foreignkey")
    op.drop_column("test_accounts", "environment_template_id")
