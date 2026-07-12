from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit
from uuid import UUID

from agenttest.modules.test_missions.application.url_policy import (
    HostAddressResolver,
    SystemHostAddressResolver,
    TargetUrlPolicy,
)
from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import MissionFact


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    agent_version_id: UUID
    target_url: str
    api_available: bool


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    target: ResolvedTarget | None


class MissionPlatformCatalog(Protocol):
    async def find_target(self, project_id: UUID, target_url: str) -> ResolvedTarget | None: ...


class PlatformAssetResolver:
    def __init__(
        self,
        catalog: MissionPlatformCatalog,
        url_policy: TargetUrlPolicy | None = None,
        address_resolver: HostAddressResolver | None = None,
    ) -> None:
        self._catalog = catalog
        self._url_policy = url_policy or TargetUrlPolicy()
        self._address_resolver = address_resolver or SystemHostAddressResolver()

    async def resolve(self, mission: TestMission) -> ResolutionResult:
        target_fact = mission.facts.get("target")
        target = target_fact.value if target_fact else None
        if not isinstance(target, dict):
            return ResolutionResult(None)
        raw_url = target.get("url")
        if not isinstance(raw_url, str):
            return ResolutionResult(None)
        target_url = self._url_policy.validate(raw_url)
        host = urlsplit(target_url).hostname
        if host is None:
            return ResolutionResult(None)
        addresses = await self._address_resolver.resolve(host)
        target_url = self._url_policy.validate(target_url, addresses)
        resolved = await self._catalog.find_target(mission.project_id, target_url)
        if resolved is not None:
            mission.merge_fact(
                MissionFact.platform("agent_version_id", str(resolved.agent_version_id))
            )
            mission.merge_fact(MissionFact.platform("api_available", resolved.api_available))
        return ResolutionResult(resolved)
