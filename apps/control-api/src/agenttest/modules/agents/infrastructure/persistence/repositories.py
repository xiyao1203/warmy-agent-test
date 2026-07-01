"""Agent 仓库的 SQLAlchemy 实现。

提供 SqlAlchemyAgentRepository 和 SqlAlchemyAgentVersionRepository，
实现领域层定义的仓库接口。
"""

from __future__ import annotations

from base64 import b64decode, b64encode
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.agents.domain.entities import (
    Agent,
    AgentId,
    AgentVersion,
    AgentVersionId,
)
from agenttest.modules.agents.domain.invocation import invocation_from_stored_config
from agenttest.modules.agents.domain.value_objects import (
    AgentConfig,
    AgentType,
    VersionStatus,
)
from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyAgentRepository:
    """Agent 聚合根的 SQLAlchemy 仓库实现。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, agent_id: AgentId) -> Agent | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(AgentModel, agent_id.value)
        return _to_agent(model) if model else None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Agent], str | None]:
        statement = (
            select(AgentModel)
            .where(AgentModel.project_id == project_id.value)
            .order_by(AgentModel.created_at.desc())
            .limit(limit + 1)
        )
        if cursor is not None:
            cursor_ts = _decode_cursor(cursor)
            statement = statement.where(AgentModel.created_at < cursor_ts)
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        has_more = len(models) > limit
        if has_more:
            models = models[:limit]
        next_cursor = _encode_cursor(models[-1].created_at) if has_more and models else None
        agents = [_to_agent(m) for m in models]
        return agents, next_cursor

    async def add(self, agent: Agent) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                AgentModel(
                    id=agent.agent_id.value,
                    project_id=agent.project_id.value,
                    name=agent.name,
                    description=agent.description,
                    agent_type=agent.agent_type.value,
                    created_at=agent.created_at,
                    updated_at=agent.updated_at,
                    created_by=agent.created_by.value,
                    updated_by=agent.updated_by.value,
                )
            )

    async def save(self, agent: Agent) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(AgentModel)
                .where(AgentModel.id == agent.agent_id.value)
                .values(
                    name=agent.name,
                    description=agent.description,
                    updated_at=agent.updated_at,
                    updated_by=agent.updated_by.value,
                )
            )

    async def delete(self, agent_id: AgentId) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(delete(AgentModel).where(AgentModel.id == agent_id.value))


class SqlAlchemyAgentVersionRepository:
    """Agent 版本的 SQLAlchemy 仓库实现。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, version_id: AgentVersionId) -> AgentVersion | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(AgentVersionModel, version_id.value)
        return _to_version(model) if model else None

    async def list_by_agent(self, agent_id: AgentId) -> list[AgentVersion]:
        statement = (
            select(AgentVersionModel)
            .where(AgentVersionModel.agent_id == agent_id.value)
            .order_by(AgentVersionModel.version_number.desc())
        )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        return [_to_version(m) for m in models]

    async def get_next_version_number(self, agent_id: AgentId) -> int:
        statement = select(func.max(AgentVersionModel.version_number)).where(
            AgentVersionModel.agent_id == agent_id.value
        )
        async with session_scope(self._session_factory) as session:
            result = await session.scalar(statement)
        return (result or 0) + 1

    async def add(self, version: AgentVersion) -> None:
        invocation = invocation_from_stored_config(version.config.to_dict()).model_dump(mode="json")
        async with transaction_scope(self._session_factory) as session:
            session.add(
                AgentVersionModel(
                    id=version.version_id.value,
                    agent_id=version.agent_id.value,
                    version_number=version.version_number,
                    status=version.status.value,
                    config=version.config.to_dict(),
                    schema_version=1,
                    invocation_config=invocation,
                    readiness_status="ready",
                    published_at=version.published_at,
                    created_at=version.created_at,
                    updated_at=version.updated_at,
                    created_by=version.created_by.value,
                )
            )

    async def save(self, version: AgentVersion) -> None:
        invocation = invocation_from_stored_config(version.config.to_dict()).model_dump(mode="json")
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(AgentVersionModel)
                .where(AgentVersionModel.id == version.version_id.value)
                .values(
                    status=version.status.value,
                    config=version.config.to_dict(),
                    schema_version=1,
                    invocation_config=invocation,
                    readiness_status="ready",
                    published_at=version.published_at,
                    updated_at=version.updated_at,
                )
            )


# ── Mappers ───────────────────────────────────────────────────────────────────


def _to_agent(model: AgentModel) -> Agent:
    """将 ORM 模型映射为领域实体。"""
    return Agent(
        agent_id=AgentId(model.id),
        project_id=ProjectId(model.project_id),
        name=model.name,
        agent_type=AgentType(model.agent_type),
        created_by=UserId(model.created_by),
        updated_by=UserId(model.updated_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description,
    )


def _to_version(model: AgentVersionModel) -> AgentVersion:
    """将 ORM 模型映射为领域实体。"""
    return AgentVersion(
        version_id=AgentVersionId(model.id),
        agent_id=AgentId(model.agent_id),
        version_number=model.version_number,
        status=VersionStatus(model.status),
        config=AgentConfig.from_dict(model.config),
        created_by=UserId(model.created_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        published_at=model.published_at,
    )


# ── Cursor helpers ────────────────────────────────────────────────────────────


def _encode_cursor(ts: datetime) -> str:
    """将时间戳编码为游标字符串。"""
    return b64encode(ts.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    """将游标字符串解码为时间戳。"""
    return datetime.fromisoformat(b64decode(cursor.encode()).decode())
