from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import MissionFact


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    capabilities: tuple[str, ...]
    api_available: bool
    browser_available: bool
    login_valid: bool
    inferred_scenarios: tuple[str, ...]
    untrusted_content: str = ""


class TargetDiscoveryProbe(Protocol):
    async def probe(
        self,
        *,
        project_id: UUID,
        target: object,
        access: object,
        read_only: bool,
    ) -> DiscoveryResult: ...


class MissionDiscovery:
    def __init__(self, probe: TargetDiscoveryProbe) -> None:
        self._probe = probe

    async def discover(self, mission: TestMission) -> DiscoveryResult:
        mission.begin_discovery()
        try:
            target_fact = mission.facts.get("target")
            access_fact = mission.facts.get("access")
            result = await self._probe.probe(
                project_id=mission.project_id,
                target=target_fact.value if target_fact else {},
                access=access_fact.value if access_fact else {},
                read_only=True,
            )
            safe_discovery = asdict(result)
            safe_discovery.pop("untrusted_content", None)
            mission.merge_fact(MissionFact.discovered("discovery", safe_discovery, confidence=0.95))
            if result.inferred_scenarios:
                mission.merge_fact(
                    MissionFact.inferred(
                        "scenario_hints", list(result.inferred_scenarios), confidence=0.75
                    )
                )
            return result
        finally:
            mission.finish_discovery()
