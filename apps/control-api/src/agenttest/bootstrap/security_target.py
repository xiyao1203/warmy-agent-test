from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.agents.infrastructure.persistence.models import AgentModel, AgentVersionModel
from agenttest.modules.agents.public import invocation_from_stored_config


class SqlAlchemySecurityTargetResolver:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def endpoint_for(self, project_id: UUID, agent_version_id: UUID) -> str | None:
        statement = (
            select(AgentVersionModel)
            .join(AgentModel, AgentModel.id == AgentVersionModel.agent_id)
            .where(
                AgentVersionModel.id == agent_version_id,
                AgentVersionModel.status == "published",
                AgentModel.project_id == project_id,
            )
        )
        async with self._session_factory() as session:
            version = await session.scalar(statement)
        if version is None:
            return None
        return invocation_from_stored_config(dict(version.config)).endpoint_url.unicode_string()
