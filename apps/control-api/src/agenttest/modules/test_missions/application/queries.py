from __future__ import annotations

from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.test_missions.application.commands import MissionPreviewResult
from agenttest.modules.test_missions.application.ports import MissionRepository
from agenttest.modules.test_missions.application.preflight import MissionPreflight
from agenttest.modules.test_missions.domain.entities import TestMission


class GetMissionHandler:
    def __init__(self, repository: MissionRepository, preflight: MissionPreflight) -> None:
        self._repository = repository
        self._preflight = preflight

    async def execute(
        self, actor: User, project_id: UUID, mission_id: UUID
    ) -> tuple[TestMission, MissionPreviewResult]:
        del actor
        mission = await self._repository.get(project_id, mission_id)
        if mission is None:
            raise LookupError("Mission does not exist in project")
        preview = self._preflight.evaluate(mission)
        return mission, MissionPreviewResult(mission_id, preview, None, None)
