from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_plans.application.dry_run import (
    DryRunService,
    DryRunVersionNotFound,
)


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("dry-run-service@example.com"),
        display_name="Dry Run Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_missing_version_is_checked_inside_project_scope() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock(), ensure_editor=AsyncMock())
    reader = SimpleNamespace(get_dry_run_model=AsyncMock(return_value=None))
    service = DryRunService(reader=reader, project_access=access)
    project_id = uuid4()

    with pytest.raises(DryRunVersionNotFound):
        await service.execute(_actor(), project_id, uuid4(), uuid4())

    access.ensure_editor.assert_awaited_once_with(ANY, ProjectId(project_id))
