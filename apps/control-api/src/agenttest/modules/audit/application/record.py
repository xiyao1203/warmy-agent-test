from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from agenttest.modules.audit.application.ports import AuditEntry, AuditSink
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "api_key",
    "cookie",
    "credential",
    "password",
    "secret",
    "token",
)


class AuditRecorder:
    def __init__(self, sink: AuditSink) -> None:
        self._sink = sink

    async def record(
        self,
        *,
        actor_user_id: UserId | None,
        action: str,
        object_type: str,
        object_id: UUID | None,
        project_id: ProjectId | None,
        changes: dict[str, Any],
        source_ip: str | None,
    ) -> None:
        await self._sink.append(
            AuditEntry(
                entry_id=uuid4(),
                actor_user_id=actor_user_id,
                action=action,
                object_type=object_type,
                object_id=object_id,
                project_id=project_id,
                changes=_redact_mapping(changes),
                source_ip=source_ip,
                created_at=datetime.now(UTC),
            )
        )


def _redact_mapping(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _redact_all(item) if _is_sensitive(key) else _redact_value(item)
        for key, item in value.items()
    }


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _redact_mapping(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def _redact_all(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_all(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_all(item) for item in value]
    return REDACTED


def _is_sensitive(key: str) -> bool:
    normalized = key.lower()
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)
