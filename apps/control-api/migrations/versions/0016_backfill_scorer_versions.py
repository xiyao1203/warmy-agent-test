"""Backfill executable scorer versions.

Revision ID: 0016
Revises: 0015
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from alembic import context, op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    scorer_versions = sa.table(
        "scorer_versions",
        sa.column("id", sa.Uuid()),
        sa.column("project_id", sa.Uuid()),
        sa.column("scorer_id", sa.Uuid()),
        sa.column("version_number", sa.Integer()),
        sa.column("status", sa.String()),
        sa.column("config", sa.JSON()),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("created_by", sa.Uuid()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    scorers = bind.execute(
        sa.text(
            """
            SELECT s.id, s.project_id, s.config_json, s.created_at, s.updated_at
            FROM scorers s
            WHERE NOT EXISTS (
                SELECT 1 FROM scorer_versions sv WHERE sv.scorer_id = s.id
            )
            """
        )
    ).mappings()
    for scorer in scorers:
        created_by = bind.execute(
            sa.text(
                """
                SELECT user_id FROM project_members
                WHERE project_id = :project_id
                ORDER BY created_at
                LIMIT 1
                """
            ),
            {"project_id": scorer["project_id"]},
        ).scalar()
        if created_by is None:
            created_by = bind.execute(
                sa.text("SELECT created_by FROM projects WHERE id = :project_id"),
                {"project_id": scorer["project_id"]},
            ).scalar()
        if created_by is None:
            continue

        now = datetime.now(UTC)
        config_json = scorer["config_json"] or {}
        if isinstance(config_json, str):
            config_json = json.loads(config_json)

        bind.execute(
            scorer_versions.insert().values(
                id=uuid4(),
                project_id=_uuid(scorer["project_id"]),
                scorer_id=_uuid(scorer["id"]),
                version_number=1,
                status="published",
                config=config_json,
                published_at=now,
                created_by=_uuid(created_by),
                created_at=_datetime(scorer["created_at"]) or now,
                updated_at=_datetime(scorer["updated_at"]) or now,
            )
        )


def downgrade() -> None:
    op.execute("DELETE FROM scorer_versions WHERE version_number = 1 AND status = 'published'")


def _uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
