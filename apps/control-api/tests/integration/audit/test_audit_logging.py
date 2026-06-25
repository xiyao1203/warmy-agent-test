from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.audit.application.ports import AuditEntry
from agenttest.modules.audit.application.record import AuditRecorder
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


class FakeAuditSink:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


@pytest.mark.asyncio
async def test_audit_recorder_redacts_secret_changes() -> None:
    sink = FakeAuditSink()
    recorder = AuditRecorder(sink)

    await recorder.record(
        actor_user_id=UserId.new(),
        action="identity.user.reset_password",
        object_type="user",
        object_id=uuid4(),
        project_id=None,
        changes={
            "display_name": {"before": "Old", "after": "New"},
            "password": {"before": "old-secret", "after": "new-secret"},
            "session_token": {"after": "raw-token"},
            "cookie": {"after": "session=value"},
        },
        source_ip="127.0.0.1",
    )

    entry = sink.entries[0]
    assert entry.changes["display_name"] == {"before": "Old", "after": "New"}
    assert entry.changes["password"] == {"before": "[REDACTED]", "after": "[REDACTED]"}
    assert entry.changes["session_token"] == {"after": "[REDACTED]"}
    assert entry.changes["cookie"] == {"after": "[REDACTED]"}


@pytest.mark.asyncio
async def test_audit_entry_keeps_actor_object_project_and_source_ip() -> None:
    sink = FakeAuditSink()
    recorder = AuditRecorder(sink)
    actor_id = UserId.new()
    object_id = uuid4()
    project_id = ProjectId.new()

    await recorder.record(
        actor_user_id=actor_id,
        action="projects.member.add",
        object_type="project_member",
        object_id=object_id,
        project_id=project_id,
        changes={"role": {"after": "tester"}},
        source_ip="192.0.2.10",
    )

    entry = sink.entries[0]
    assert entry.actor_user_id == actor_id
    assert entry.object_id == object_id
    assert entry.project_id == project_id
    assert entry.source_ip == "192.0.2.10"
