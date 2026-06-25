from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from agenttest.modules.audit.application.ports import AuditEntry


class AuditEntryResponse(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    action: str
    object_type: str
    object_id: UUID | None
    project_id: UUID | None
    changes: dict[str, Any]
    source_ip: str | None
    created_at: datetime

    @classmethod
    def from_entry(cls, entry: AuditEntry) -> "AuditEntryResponse":
        return cls(
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


class AuditListResponse(BaseModel):
    items: list[AuditEntryResponse]
