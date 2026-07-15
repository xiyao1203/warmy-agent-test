from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.experiments.application.service import ExperimentService
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("experiment-service@example.com"),
        display_name="Experiment Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_list_checks_project_membership_before_repository() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock(), ensure_editor=AsyncMock())
    experiments = SimpleNamespace(list_by_project=AsyncMock(return_value=[]))
    service = ExperimentService(
        experiments=experiments,
        runs=SimpleNamespace(),
        project_access=access,
    )
    project_id = uuid4()

    assert await service.list(_actor(), project_id, 20, 0) == []
    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
    experiments.list_by_project.assert_awaited_once()
