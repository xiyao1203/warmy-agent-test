from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.audit.application.ports import AuditEntry
from agenttest.modules.audit.infrastructure.persistence.models import AuditLogModel
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


class SqlAlchemyAuditRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def append(self, entry: AuditEntry) -> None:
        async with self._session_factory.begin() as session:
            session.add(
                AuditLogModel(
                    id=entry.entry_id,
                    actor_user_id=(
                        entry.actor_user_id.value if entry.actor_user_id is not None else None
                    ),
                    action=entry.action,
                    object_type=entry.object_type,
                    object_id=entry.object_id,
                    project_id=entry.project_id.value if entry.project_id is not None else None,
                    changes=entry.changes,
                    source_ip=entry.source_ip,
                    created_at=entry.created_at,
                )
            )

    async def list_global(self, *, limit: int) -> list[AuditEntry]:
        statement = (
            select(AuditLogModel)
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
        )
        async with self._session_factory() as session:
            models = list((await session.scalars(statement)).all())
        return [_to_entry(model) for model in models]

    async def list_project(
        self,
        *,
        project_id: ProjectId,
        limit: int,
    ) -> list[AuditEntry]:
        statement = (
            select(AuditLogModel)
            .where(AuditLogModel.project_id == project_id.value)
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
        )
        async with self._session_factory() as session:
            models = list((await session.scalars(statement)).all())
        return [_to_entry(model) for model in models]


def _to_entry(model: AuditLogModel) -> AuditEntry:
    return AuditEntry(
        entry_id=model.id,
        actor_user_id=UserId(model.actor_user_id) if model.actor_user_id else None,
        action=model.action,
        object_type=model.object_type,
        object_id=model.object_id,
        project_id=ProjectId(model.project_id) if model.project_id else None,
        changes=model.changes,
        source_ip=model.source_ip,
        created_at=model.created_at,
    )
