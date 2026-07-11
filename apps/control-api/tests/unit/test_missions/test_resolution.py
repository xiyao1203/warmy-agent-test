from uuid import UUID, uuid4

import pytest
from agenttest.modules.test_missions.application.resolution import (
    PlatformAssetResolver,
    ResolvedTarget,
)
from agenttest.modules.test_missions.application.url_policy import UnsafeTargetUrlError
from agenttest.modules.test_missions.domain.entities import TestMission as Mission
from agenttest.modules.test_missions.domain.value_objects import FactSource, MissionFact


class Catalog:
    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        self.version_id = uuid4()

    async def find_target(self, project_id: UUID, target_url: str):
        if project_id != self.project_id:
            return None
        return ResolvedTarget(
            agent_version_id=self.version_id,
            target_url=target_url,
            api_available=True,
        )


class AddressResolver:
    def __init__(self, addresses: tuple[str, ...]) -> None:
        self.addresses = addresses

    async def resolve(self, host: str) -> tuple[str, ...]:
        del host
        return self.addresses


@pytest.mark.asyncio
async def test_resolver_uses_only_same_project_assets() -> None:
    project_id = uuid4()
    catalog = Catalog(project_id)
    mission = Mission.create(project_id=project_id, session_id=uuid4(), created_by=uuid4())
    mission.merge_fact(MissionFact.user("target", {"url": "https://agent.example"}))

    result = await PlatformAssetResolver(
        catalog, address_resolver=AddressResolver(("93.184.216.34",))
    ).resolve(mission)

    assert result.target is not None
    assert result.target.agent_version_id == catalog.version_id
    assert mission.facts["agent_version_id"].source is FactSource.PLATFORM_RESOLVED


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/",
        "https://user:password@agent.example",
    ],
)
@pytest.mark.asyncio
async def test_resolver_rejects_unsafe_target_urls(url: str) -> None:
    mission = Mission.create(project_id=uuid4(), session_id=uuid4(), created_by=uuid4())
    mission.merge_fact(MissionFact.user("target", {"url": url}))

    with pytest.raises(UnsafeTargetUrlError):
        await PlatformAssetResolver(
            Catalog(mission.project_id),
            address_resolver=AddressResolver(("93.184.216.34",)),
        ).resolve(mission)


@pytest.mark.asyncio
async def test_resolver_rejects_hostname_that_resolves_to_private_address() -> None:
    mission = Mission.create(project_id=uuid4(), session_id=uuid4(), created_by=uuid4())
    mission.merge_fact(MissionFact.user("target", {"url": "https://metadata.internal/agent"}))

    with pytest.raises(UnsafeTargetUrlError):
        await PlatformAssetResolver(
            Catalog(mission.project_id),
            address_resolver=AddressResolver(("169.254.169.254",)),
        ).resolve(mission)
