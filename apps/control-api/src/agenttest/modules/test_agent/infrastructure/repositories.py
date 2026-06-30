from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.ports import ChatSessionRepository
from agenttest.modules.test_agent.domain.entities import (
    ChatMessage,
    ChatSession,
    ChatSessionId,
    SessionStatus,
)
from agenttest.modules.test_agent.infrastructure.models import (
    TestAgentMessageModel,
    TestAgentSessionModel,
)
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyChatSessionRepository(ChatSessionRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(
        self,
        project_id: ProjectId,
        session_id: ChatSessionId,
    ) -> ChatSession | None:
        statement = select(TestAgentSessionModel).where(
            TestAgentSessionModel.project_id == project_id.value,
            TestAgentSessionModel.id == session_id.value,
        )
        messages_statement = (
            select(TestAgentMessageModel)
            .where(
                TestAgentMessageModel.project_id == project_id.value,
                TestAgentMessageModel.session_id == session_id.value,
            )
            .order_by(TestAgentMessageModel.sequence)
        )
        async with session_scope(self._session_factory) as database:
            model = await database.scalar(statement)
            if model is None:
                return None
            messages = list((await database.scalars(messages_statement)).all())
        return ChatSession(
            session_id=ChatSessionId(model.id),
            project_id=model.project_id,
            created_by=model.created_by,
            messages=[
                ChatMessage(
                    message_id=message.id,
                    sequence=message.sequence,
                    role=message.role,
                    content=message.content,
                    timestamp=message.created_at,
                )
                for message in messages
            ],
            plan_draft=dict(model.plan_draft),
            status=SessionStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save(self, session: ChatSession) -> None:
        async with transaction_scope(self._session_factory) as database:
            model = await database.get(TestAgentSessionModel, session.session_id.value)
            if model is None:
                model = TestAgentSessionModel(
                    id=session.session_id.value,
                    project_id=session.project_id,
                    status=session.status.value,
                    plan_draft=session.plan_draft,
                    created_by=session.created_by,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                )
                database.add(model)
                # Flush to ensure session exists before adding messages
                await database.flush()
            else:
                if model.project_id != session.project_id:
                    raise ValueError("Session project cannot change")
                model.status = session.status.value
                model.plan_draft = session.plan_draft
                model.updated_at = session.updated_at
                await database.execute(
                    delete(TestAgentMessageModel).where(
                        TestAgentMessageModel.project_id == session.project_id,
                        TestAgentMessageModel.session_id == session.session_id.value,
                    )
                )
            database.add_all(
                [
                    TestAgentMessageModel(
                        id=message.message_id,
                        project_id=session.project_id,
                        session_id=session.session_id.value,
                        sequence=message.sequence,
                        role=message.role,
                        content=message.content,
                        created_at=message.timestamp,
                    )
                    for message in session.messages
                ]
            )
