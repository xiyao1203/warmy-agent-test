from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.security.application.scan_service import SecurityScanService


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("security-service@example.com"),
        display_name="Security Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_list_checks_project_membership_before_repository() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock(), ensure_editor=AsyncMock())
    scans = SimpleNamespace(list_by_project=AsyncMock(return_value=[]))
    service = SecurityScanService(
        scans=scans,
        targets=SimpleNamespace(),
        scanner_factory=lambda: SimpleNamespace(),
        project_access=access,
        allow_private_network=False,
    )
    project_id = uuid4()

    assert await service.list(_actor(), project_id, limit=5) == []
    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
    scans.list_by_project.assert_awaited_once_with(project_id, limit=5)
