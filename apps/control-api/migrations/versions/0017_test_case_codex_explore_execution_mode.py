"""Allow codex_explore test case execution mode.

Revision ID: 0017
Revises: 0016
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("test_cases") as batch_op:
        batch_op.drop_constraint("ck_test_cases_execution_mode", type_="check")
        batch_op.create_check_constraint(
            "ck_test_cases_execution_mode",
            "execution_mode IN ('api', 'browser', 'codex_explore')",
        )


def downgrade() -> None:
    with op.batch_alter_table("test_cases") as batch_op:
        batch_op.drop_constraint("ck_test_cases_execution_mode", type_="check")
        batch_op.create_check_constraint(
            "ck_test_cases_execution_mode",
            "execution_mode IN ('api', 'browser')",
        )
