from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.domain.entities import (
    AgentConfirmation,
    AgentEvent,
    AgentTask,
    ArtifactLink,
    ChatSession,
    ChatSessionId,
)


class ChatSessionRepository(Protocol):
    async def list_by_project(
        self, project_id: ProjectId, *, include_archived: bool = False
    ) -> list[ChatSession]: ...

    async def get(
        self,
        project_id: ProjectId,
        session_id: ChatSessionId,
    ) -> ChatSession | None: ...

    async def save(self, session: ChatSession) -> None: ...


class OrchestrationRepository(Protocol):
    async def add_task(self, task: AgentTask) -> None: ...
    async def get_task(self, project_id: ProjectId, task_id: UUID) -> AgentTask | None: ...
    async def save_task(self, task: AgentTask) -> None: ...
    async def add_confirmation(self, confirmation: AgentConfirmation) -> None: ...
    async def get_confirmation(
        self, project_id: ProjectId, confirmation_id: UUID
    ) -> AgentConfirmation | None: ...
    async def save_confirmation(self, confirmation: AgentConfirmation) -> None: ...
    async def append_event(
        self,
        project_id: ProjectId,
        session_id: ChatSessionId,
        event_type: str,
        payload: dict[str, object],
    ) -> AgentEvent: ...
    async def list_events(
        self, project_id: ProjectId, session_id: ChatSessionId, *, after: int = 0
    ) -> list[AgentEvent]: ...
    async def add_artifact_link(self, link: ArtifactLink) -> None: ...
    async def list_artifact_links(
        self, project_id: ProjectId, session_id: ChatSessionId
    ) -> list[ArtifactLink]: ...
