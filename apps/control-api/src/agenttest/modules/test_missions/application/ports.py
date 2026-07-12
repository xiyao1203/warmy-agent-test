from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import MissionEvent


class MissionRepository(Protocol):
    async def add(self, mission: TestMission) -> None: ...

    async def get(self, project_id: UUID, mission_id: UUID) -> TestMission | None: ...

    async def get_for_session(self, project_id: UUID, session_id: UUID) -> TestMission | None: ...

    async def save(self, mission: TestMission, *, expected_lock_version: int) -> None: ...

    async def append_event(
        self,
        project_id: UUID,
        mission_id: UUID,
        event_type: str,
        payload: dict[str, object],
    ) -> MissionEvent: ...

    async def list_events(
        self, project_id: UUID, mission_id: UUID, *, after: int = 0
    ) -> list[MissionEvent]: ...

    async def link_asset(
        self,
        project_id: UUID,
        mission_id: UUID,
        asset_type: str,
        asset_id: UUID,
        relation: str,
        *,
        stage: str | None = None,
    ) -> bool: ...

    async def list_assets(self, project_id: UUID, mission_id: UUID) -> list[dict[str, object]]: ...
