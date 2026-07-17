from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.event_stream import RunProgressService


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("event-service@example.com"),
        display_name="Event Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_missing_run_is_scoped_and_returns_none() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock())
    runs = SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    service = RunProgressService(runs=runs, project_access=access)
    project_id = uuid4()

    assert await service.get(_actor(), project_id, uuid4()) is None
    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
