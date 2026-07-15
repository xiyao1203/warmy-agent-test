"""Enforce Artifact and Run project consistency.

Revision ID: 0025
Revises: 0024
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("artifacts") as batch_op:
        batch_op.create_foreign_key(
            "fk_artifacts_project_run",
            "runs",
            ["project_id", "run_id"],
            ["project_id", "id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("artifacts") as batch_op:
        batch_op.drop_constraint("fk_artifacts_project_run", type_="foreignkey")
