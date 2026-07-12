from uuid import uuid4

import pytest
from agenttest.modules.test_missions.domain.entities import TestMission as Mission
from agenttest.modules.test_missions.domain.value_objects import MissionFact
from agenttest.modules.test_missions.infrastructure.temporal_orchestrator import (
    TemporalMissionOrchestrator,
)


class Client:
    def __init__(self) -> None:
        self.started = []

    async def start_workflow(self, name, payload, *, id, task_queue):
        self.started.append((name, payload, id, task_queue))


@pytest.mark.asyncio
async def test_temporal_payload_contains_revision_references_but_no_secret() -> None:
    mission = Mission.create(project_id=uuid4(), session_id=uuid4(), created_by=uuid4())
    for fact in (
        MissionFact.user("target", {"url": "https://agent.example"}),
        MissionFact.user("access", {"strategy": "none"}),
        MissionFact.user("test_goal", "验证问答"),
        MissionFact.user("safety_scope", "read_only"),
    ):
        mission.merge_fact(fact)
    revision = mission.confirm(confirmed_by=uuid4())
    client = Client()
    runtime = TemporalMissionOrchestrator(
        client=client,
        task_queue="agenttest-api-runner",
        callback_base_url="https://control.example",
    )

    workflow_id = await runtime.start(mission, revision, "confirm-once")

    assert workflow_id == f"test-mission-{mission.mission_id}-1"
    payload = client.started[0][1]
    assert payload["revision_hash"] == revision.content_hash
    assert "token" not in repr(payload).lower()
    assert "facts" not in payload
