from __future__ import annotations

from typing import Protocol

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.domain.entities import ChatSession, ChatSessionId


class ChatSessionRepository(Protocol):
    async def get(
        self,
        project_id: ProjectId,
        session_id: ChatSessionId,
    ) -> ChatSession | None: ...

    async def save(self, session: ChatSession) -> None: ...
