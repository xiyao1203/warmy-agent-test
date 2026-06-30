from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.ports import (
    ChatSessionRepository,
    OrchestrationRepository,
)
from agenttest.modules.test_agent.domain.entities import (
    AgentConfirmation,
    AgentEvent,
    AgentTask,
    ArtifactLink,
    ChatMessage,
    ChatSession,
    ChatSessionId,
    ConfirmationStatus,
    RiskLevel,
    SessionStatus,
    TaskStatus,
)
from agenttest.modules.test_agent.infrastructure.models import (
    TestAgentArtifactLinkModel,
    TestAgentConfirmationModel,
    TestAgentEventModel,
    TestAgentMessageModel,
    TestAgentSessionModel,
    TestAgentTaskModel,
)
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyChatSessionRepository(ChatSessionRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_by_project(
        self, project_id: ProjectId, *, include_archived: bool = False
    ) -> list[ChatSession]:
        statement = select(TestAgentSessionModel).where(
            TestAgentSessionModel.project_id == project_id.value
        )
        if not include_archived:
            statement = statement.where(TestAgentSessionModel.archived_at.is_(None))
        statement = statement.order_by(TestAgentSessionModel.updated_at.desc())
        async with session_scope(self._session_factory) as database:
            models = list((await database.scalars(statement)).all())
        sessions: list[ChatSession] = []
        for model in models:
            restored = await self.get(project_id, ChatSessionId(model.id))
            if restored is not None:
                sessions.append(restored)
        return sessions

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
            title=model.title,
            protocol_version=model.protocol_version,
            archived_at=model.archived_at,
        )

    async def save(self, session: ChatSession) -> None:
        async with transaction_scope(self._session_factory) as database:
            model = await database.get(TestAgentSessionModel, session.session_id.value)
            if model is None:
                model = TestAgentSessionModel(
                    id=session.session_id.value,
                    project_id=session.project_id,
                    status=session.status.value,
                    title=session.title,
                    protocol_version=session.protocol_version,
                    archived_at=session.archived_at,
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
                model.title = session.title
                model.protocol_version = session.protocol_version
                model.archived_at = session.archived_at
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


class SqlAlchemyOrchestrationRepository(OrchestrationRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add_task(self, task: AgentTask) -> None:
        async with transaction_scope(self._session_factory) as database:
            database.add(_task_to_model(task))

    async def get_task(self, project_id: ProjectId, task_id: UUID) -> AgentTask | None:
        statement = select(TestAgentTaskModel).where(
            TestAgentTaskModel.project_id == project_id.value,
            TestAgentTaskModel.id == task_id,
        )
        async with session_scope(self._session_factory) as database:
            model = await database.scalar(statement)
        return _task_to_domain(model) if model is not None else None

    async def save_task(self, task: AgentTask) -> None:
        async with transaction_scope(self._session_factory) as database:
            await database.execute(
                update(TestAgentTaskModel)
                .where(
                    TestAgentTaskModel.project_id == task.project_id,
                    TestAgentTaskModel.id == task.task_id,
                )
                .values(
                    status=task.status.value,
                    output=task.output,
                    error=task.error,
                    updated_at=task.updated_at,
                )
            )

    async def add_confirmation(self, confirmation: AgentConfirmation) -> None:
        async with transaction_scope(self._session_factory) as database:
            database.add(
                TestAgentConfirmationModel(
                    id=confirmation.confirmation_id,
                    project_id=confirmation.project_id,
                    task_id=confirmation.task_id,
                    status=confirmation.status.value,
                    preview=confirmation.preview,
                    decided_by=confirmation.decided_by,
                    decided_at=confirmation.decided_at,
                    created_at=confirmation.created_at,
                )
            )

    async def get_confirmation(
        self, project_id: ProjectId, confirmation_id: UUID
    ) -> AgentConfirmation | None:
        statement = select(TestAgentConfirmationModel).where(
            TestAgentConfirmationModel.project_id == project_id.value,
            TestAgentConfirmationModel.id == confirmation_id,
        )
        async with session_scope(self._session_factory) as database:
            model = await database.scalar(statement)
        if model is None:
            return None
        return AgentConfirmation(
            confirmation_id=model.id,
            project_id=model.project_id,
            task_id=model.task_id,
            status=ConfirmationStatus(model.status),
            preview=dict(model.preview),
            decided_by=model.decided_by,
            decided_at=model.decided_at,
            created_at=model.created_at,
        )

    async def save_confirmation(self, confirmation: AgentConfirmation) -> None:
        async with transaction_scope(self._session_factory) as database:
            await database.execute(
                update(TestAgentConfirmationModel)
                .where(
                    TestAgentConfirmationModel.project_id == confirmation.project_id,
                    TestAgentConfirmationModel.id == confirmation.confirmation_id,
                )
                .values(
                    status=confirmation.status.value,
                    decided_by=confirmation.decided_by,
                    decided_at=confirmation.decided_at,
                )
            )

    async def append_event(
        self,
        project_id: ProjectId,
        session_id: ChatSessionId,
        event_type: str,
        payload: dict[str, object],
    ) -> AgentEvent:
        async with transaction_scope(self._session_factory) as database:
            locked = await database.scalar(
                select(TestAgentSessionModel)
                .where(
                    TestAgentSessionModel.project_id == project_id.value,
                    TestAgentSessionModel.id == session_id.value,
                )
                .with_for_update()
            )
            if locked is None:
                raise ValueError("Session does not exist in project")
            current = await database.scalar(
                select(func.max(TestAgentEventModel.sequence)).where(
                    TestAgentEventModel.project_id == project_id.value,
                    TestAgentEventModel.session_id == session_id.value,
                )
            )
            event = AgentEvent(
                event_id=uuid4(),
                project_id=project_id.value,
                session_id=session_id.value,
                sequence=int(current or 0) + 1,
                event_type=event_type,
                payload=payload,
                created_at=datetime.now(UTC),
            )
            database.add(
                TestAgentEventModel(
                    id=event.event_id,
                    project_id=event.project_id,
                    session_id=event.session_id,
                    sequence=event.sequence,
                    event_type=event.event_type,
                    payload=event.payload,
                    created_at=event.created_at,
                )
            )
        return event

    async def list_events(
        self, project_id: ProjectId, session_id: ChatSessionId, *, after: int = 0
    ) -> list[AgentEvent]:
        statement = (
            select(TestAgentEventModel)
            .where(
                TestAgentEventModel.project_id == project_id.value,
                TestAgentEventModel.session_id == session_id.value,
                TestAgentEventModel.sequence > after,
            )
            .order_by(TestAgentEventModel.sequence)
        )
        async with session_scope(self._session_factory) as database:
            models = list((await database.scalars(statement)).all())
        return [
            AgentEvent(
                event_id=model.id,
                project_id=model.project_id,
                session_id=model.session_id,
                sequence=model.sequence,
                event_type=model.event_type,
                payload=dict(model.payload),
                created_at=model.created_at,
            )
            for model in models
        ]

    async def add_artifact_link(self, link: ArtifactLink) -> None:
        async with transaction_scope(self._session_factory) as database:
            database.add(
                TestAgentArtifactLinkModel(
                    id=link.link_id,
                    project_id=link.project_id,
                    session_id=link.session_id,
                    task_id=link.task_id,
                    artifact_type=link.artifact_type,
                    artifact_id=link.artifact_id,
                    relation=link.relation,
                    created_at=link.created_at,
                )
            )

    async def list_artifact_links(
        self, project_id: ProjectId, session_id: ChatSessionId
    ) -> list[ArtifactLink]:
        statement = (
            select(TestAgentArtifactLinkModel)
            .where(
                TestAgentArtifactLinkModel.project_id == project_id.value,
                TestAgentArtifactLinkModel.session_id == session_id.value,
            )
            .order_by(TestAgentArtifactLinkModel.created_at)
        )
        async with session_scope(self._session_factory) as database:
            models = list((await database.scalars(statement)).all())
        return [
            ArtifactLink(
                link_id=model.id,
                project_id=model.project_id,
                session_id=model.session_id,
                task_id=model.task_id,
                artifact_type=model.artifact_type,
                artifact_id=model.artifact_id,
                relation=model.relation,
                created_at=model.created_at,
            )
            for model in models
        ]


def _task_to_model(task: AgentTask) -> TestAgentTaskModel:
    return TestAgentTaskModel(
        id=task.task_id,
        project_id=task.project_id,
        session_id=task.session_id,
        parent_task_id=task.parent_task_id,
        child_agent=task.child_agent,
        capability=task.capability,
        status=task.status.value,
        risk_level=task.risk_level.value,
        idempotency_key=task.idempotency_key,
        input=task.input,
        output=task.output,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _task_to_domain(model: TestAgentTaskModel) -> AgentTask:
    return AgentTask(
        task_id=model.id,
        project_id=model.project_id,
        session_id=model.session_id,
        parent_task_id=model.parent_task_id,
        child_agent=model.child_agent,
        capability=model.capability,
        status=TaskStatus(model.status),
        risk_level=RiskLevel(model.risk_level),
        idempotency_key=model.idempotency_key,
        input=dict(model.input),
        output=dict(model.output) if model.output is not None else None,
        error=dict(model.error) if model.error is not None else None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
