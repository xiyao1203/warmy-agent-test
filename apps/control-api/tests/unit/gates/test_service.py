from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.gates.application.service import GateService
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("gate-service@example.com"),
        display_name="Gate Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_list_checks_project_membership_before_repository() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock(), ensure_editor=AsyncMock())
    gates = SimpleNamespace(list_by_project=AsyncMock(return_value=[]))
    service = GateService(
        gates=gates,
        evidence=SimpleNamespace(),
        project_access=access,
    )
    project_id = uuid4()

    assert await service.list_gates(_actor(), project_id) == []
    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
    gates.list_by_project.assert_awaited_once_with(project_id)
