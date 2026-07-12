"""Align the PostgreSQL audit log schema with the ORM mapping.

Revision ID: 0023
Revises: 0022
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE audit.audit_logs SET SCHEMA public")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE SCHEMA IF NOT EXISTS audit")
        op.execute("ALTER TABLE public.audit_logs SET SCHEMA audit")
