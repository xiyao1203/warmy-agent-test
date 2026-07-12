"""Add the Run session identifier declared by the persistence model.

Revision ID: 0024
Revises: 0023
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("session_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "session_id")
