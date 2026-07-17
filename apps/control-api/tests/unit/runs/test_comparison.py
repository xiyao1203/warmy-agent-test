from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.comparison import (
    RunComparisonNotFound,
    RunComparisonService,
)


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("comparison-service@example.com"),
        display_name="Comparison Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_compare_scopes_run_lookup_to_project() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock())
    runs = SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    service = RunComparisonService(runs=runs, project_access=access)
    project_id = uuid4()

    with pytest.raises(RunComparisonNotFound):
        await service.compare(_actor(), project_id, uuid4(), uuid4())

    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
    first_project, _ = runs.get_by_id.await_args.args
    assert first_project == ProjectId(project_id)
