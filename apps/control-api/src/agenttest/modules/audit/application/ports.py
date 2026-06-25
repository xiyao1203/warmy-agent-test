from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


@dataclass(frozen=True, slots=True)
class AuditEntry:
    entry_id: UUID
    actor_user_id: UserId | None
    action: str
    object_type: str
    object_id: UUID | None
    project_id: ProjectId | None
    changes: dict[str, Any]
    source_ip: str | None
    created_at: datetime


class AuditSink(Protocol):
    async def append(self, entry: AuditEntry) -> None: ...


class AuditReader(Protocol):
    async def list_global(self, *, limit: int) -> list[AuditEntry]: ...

    async def list_project(
        self,
        *,
        project_id: ProjectId,
        limit: int,
    ) -> list[AuditEntry]: ...
