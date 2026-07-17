from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.scorers.application.service import ScorerService


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("scorer-service@example.com"),
        display_name="Scorer Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_list_checks_project_membership_and_supports_unversioned_adapter() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock(), ensure_editor=AsyncMock())
    scorers = SimpleNamespace(list_by_project=AsyncMock(return_value=([], 0)))
    service = ScorerService(
        scorers=scorers,
        project_access=access,
        publish_versions=False,
    )
    project_id = uuid4()

    page = await service.list(_actor(), project_id, limit=10, offset=0)

    assert page.items == [] and page.total == 0
    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
