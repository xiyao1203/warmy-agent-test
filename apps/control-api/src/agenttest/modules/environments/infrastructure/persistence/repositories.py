"""Environment 仓库的 SQLAlchemy 实现。"""

from __future__ import annotations

from base64 import b64decode, b64encode
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.modules.environments.infrastructure.persistence.models import (
    EnvironmentTemplateModel,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyEnvironmentTemplateRepository:
    """环境模板的 SQLAlchemy 仓库实现。"""
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, template_id: EnvironmentTemplateId) -> EnvironmentTemplate | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(EnvironmentTemplateModel, template_id.value)
        return _to_template(model) if model else None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[EnvironmentTemplate], str | None]:
        statement = (
            select(EnvironmentTemplateModel)
            .where(EnvironmentTemplateModel.project_id == project_id.value)
            .order_by(EnvironmentTemplateModel.created_at.desc())
            .limit(limit + 1)
        )
        if cursor is not None:
            cursor_ts = _decode_cursor(cursor)
            statement = statement.where(EnvironmentTemplateModel.created_at < cursor_ts)
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        has_more = len(models) > limit
        if has_more:
            models = models[:limit]
        next_cursor = _encode_cursor(models[-1].created_at) if has_more and models else None
        return [_to_template(m) for m in models], next_cursor

    async def add(self, template: EnvironmentTemplate) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                EnvironmentTemplateModel(
                    id=template.template_id.value,
                    project_id=template.project_id.value,
                    name=template.name,
                    description=template.description,
                    template_type=template.template_type.value,
                    config=template.config,
                    created_at=template.created_at,
                    updated_at=template.updated_at,
                    created_by=template.created_by.value,
                )
            )

    async def save(self, template: EnvironmentTemplate) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(EnvironmentTemplateModel)
                .where(EnvironmentTemplateModel.id == template.template_id.value)
                .values(
                    name=template.name,
                    description=template.description,
                    config=template.config,
                    updated_at=template.updated_at,
                )
            )

    async def delete(self, template_id: EnvironmentTemplateId) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                delete(EnvironmentTemplateModel).where(
                    EnvironmentTemplateModel.id == template_id.value
                )
            )


# ── Mappers ─────────────────────────────────────────────────────────────────


def _to_template(model: EnvironmentTemplateModel) -> EnvironmentTemplate:
    """ORM 模型 → 领域实体映射。"""
    return EnvironmentTemplate(
        template_id=EnvironmentTemplateId(model.id),
        project_id=ProjectId(model.project_id),
        name=model.name,
        template_type=TemplateType(model.template_type),
        config=model.config,
        created_by=UserId(model.created_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description,
    )


# ── Cursor helpers ──────────────────────────────────────────────────────────


def _encode_cursor(ts: datetime) -> str:
    return b64encode(ts.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(b64decode(cursor.encode()).decode())
