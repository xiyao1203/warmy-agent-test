from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from agenttest.modules.agents.domain.value_objects import AgentConfig
from agenttest.modules.browser_profiles.application.publication import (
    BrowserProfilePublicationValidator,
)
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


class Repository:
    def __init__(self, item: BrowserProfile | None):
        self.item = item

    async def get(self, project_id: UUID, profile_id: UUID):
        item = self.item
        return item if item and item.project_id == project_id and item.id == profile_id else None


def config(profile_id: UUID | None) -> AgentConfig:
    return AgentConfig(
        api_url="https://app.tapnow.ai",
        target_config={
            "login": {"strategy": "browser_profile"},
            "browser_profile_id": str(profile_id) if profile_id else "",
        },
    )


@pytest.mark.asyncio
async def test_publication_requires_same_project_ready_profile() -> None:
    project_id = uuid4()
    item = BrowserProfile.create(
        project_id=project_id,
        name="TapNow",
        target_domain="app.tapnow.ai",
        created_by=uuid4(),
        now=datetime.now(UTC),
    )
    validator = BrowserProfilePublicationValidator(Repository(item))

    with pytest.raises(ValueError, match="登录态"):
        await validator.validate(project_id, config(item.id))

    item.store_auth_state(
        envelope="v1.cipher",
        sha256="d" * 64,
        saved_at=datetime.now(UTC),
    )
    await validator.validate(project_id, config(item.id))
    with pytest.raises(ValueError, match="浏览器实例"):
        await validator.validate(uuid4(), config(item.id))


@pytest.mark.asyncio
async def test_publication_requires_profile_id_but_ignores_other_login_strategies() -> None:
    validator = BrowserProfilePublicationValidator(Repository(None))

    with pytest.raises(ValueError, match="选择浏览器实例"):
        await validator.validate(uuid4(), config(None))
    await validator.validate(
        uuid4(),
        AgentConfig(
            api_url="https://app.tapnow.ai",
            target_config={"login": {"strategy": "none"}},
        ),
    )
