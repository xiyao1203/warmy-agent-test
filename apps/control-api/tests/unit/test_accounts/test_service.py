from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_accounts.application.service import (
    TestAccountService as AccountService,
)


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("account-service@example.com"),
        display_name="Account Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_list_checks_project_membership_before_repository() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock(), ensure_editor=AsyncMock())
    accounts = SimpleNamespace(list_by_project=AsyncMock(return_value=[]))
    service = AccountService(accounts=accounts, project_access=access)
    project_id = uuid4()

    assert await service.list(_actor(), project_id) == []
    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
    accounts.list_by_project.assert_awaited_once_with(project_id)
