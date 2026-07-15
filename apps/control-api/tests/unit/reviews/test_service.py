from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reviews.application.service import ReviewService


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("review-service@example.com"),
        display_name="Review Service",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_stats_checks_project_membership_before_repository() -> None:
    access = SimpleNamespace(ensure_member=AsyncMock(), ensure_editor=AsyncMock())
    reviews = SimpleNamespace(get_stats=AsyncMock(return_value={"pending": 2}))
    service = ReviewService(reviews=reviews, project_access=access)
    project_id = uuid4()

    assert await service.stats(_actor(), project_id) == {"pending": 2}
    access.ensure_member.assert_awaited_once_with(ANY, ProjectId(project_id))
    reviews.get_stats.assert_awaited_once_with(ProjectId(project_id))
