from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.commands import (
    CancelMissionHandler,
    ConfirmMissionHandler,
    DiscoverMissionHandler,
    PreviewMissionHandler,
    ResumeMissionHandler,
    UpsertMissionHandler,
)
from agenttest.modules.test_missions.application.discovery import DiscoveryResult, MissionDiscovery
from agenttest.modules.test_missions.application.intake import MissionIntake
from agenttest.modules.test_missions.application.preflight import MissionPreflight
from agenttest.modules.test_missions.domain.value_objects import MissionEvent


class Repository:
    def __init__(self) -> None:
        self.items = {}
        self.events = []

    async def add(self, mission):
        self.items[mission.mission_id] = mission

    async def get(self, project_id, mission_id):
        item = self.items.get(mission_id)
        return item if item and item.project_id == project_id else None

    async def get_for_session(self, project_id, session_id):
        return next(
            (
                item
                for item in self.items.values()
                if item.project_id == project_id and item.session_id == session_id
            ),
            None,
        )

    async def save(self, mission, *, expected_lock_version):
        stored = self.items.get(mission.mission_id)
        if stored is None or expected_lock_version >= mission.lock_version:
            raise RuntimeError("stale")
        self.items[mission.mission_id] = mission

    async def append_event(self, project_id, mission_id, event_type, payload):
        event = MissionEvent(
            event_id=uuid4(),
            project_id=project_id,
            mission_id=mission_id,
            sequence=len(self.events) + 1,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        self.events.append(event)
        return event

    async def list_assets(self, project_id, mission_id):
        del project_id, mission_id
        return []


class Runtime:
    def __init__(self) -> None:
        self.started = []
        self.cancelled = []
        self.resumed = []

    async def start(self, mission, revision, idempotency_key):
        self.started.append((mission.mission_id, revision.revision_id, idempotency_key))
        return f"test-mission-{mission.mission_id}-{revision.revision_number}"

    async def cancel(self, workflow_id):
        self.cancelled.append(workflow_id)

    async def resume(self, workflow_id):
        self.resumed.append(workflow_id)


class Probe:
    async def probe(self, *, project_id, target, access, read_only):
        assert read_only is True
        return DiscoveryResult(
            capabilities=("chat",),
            api_available=False,
            browser_available=True,
            login_valid=True,
            inferred_scenarios=("真实聊天",),
        )


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("mission@example.com"),
        display_name="Mission User",
        role=SystemRole.DEVELOPER,
    )


async def ready_mission(repository: Repository):
    handler = UpsertMissionHandler(repository, MissionIntake())
    return await handler.execute(
        actor(),
        ProjectId.new(),
        session_id=uuid4(),
        values={
            "target_url": "https://agent.example",
            "access_strategy": "none",
            "test_goal": "验证多轮客服问答",
            "safety_scope": "read_only",
        },
    )


@pytest.mark.asyncio
async def test_upsert_builds_one_ready_mission_per_session() -> None:
    repository = Repository()
    project_id = ProjectId.new()
    session_id = uuid4()
    handler = UpsertMissionHandler(repository, MissionIntake())

    first = await handler.execute(
        actor(), project_id, session_id=session_id, values={"target_url": "https://agent.example"}
    )
    second = await handler.execute(
        actor(), project_id, session_id=session_id, values={"test_goal": "验证问答"}
    )

    assert first.mission_id == second.mission_id
    assert second.facts["test_goal"].value == "验证问答"


@pytest.mark.asyncio
async def test_confirm_rejects_stale_hash_and_starts_runtime_once() -> None:
    repository = Repository()
    mission = await ready_mission(repository)
    preview = await PreviewMissionHandler(repository, MissionPreflight()).execute(
        actor(), mission.project_id, mission.mission_id
    )
    runtime = Runtime()
    handler = ConfirmMissionHandler(repository, MissionPreflight(), runtime)

    with pytest.raises(ValueError, match="preview has changed"):
        await handler.execute(
            actor(),
            mission.project_id,
            mission.mission_id,
            revision_hash="0" * 64,
            idempotency_key="confirm-1",
        )

    first = await handler.execute(
        actor(),
        mission.project_id,
        mission.mission_id,
        revision_hash=preview.revision_hash,
        idempotency_key="confirm-1",
    )
    second = await handler.execute(
        actor(),
        mission.project_id,
        mission.mission_id,
        revision_hash=preview.revision_hash,
        idempotency_key="confirm-1",
    )

    assert first.revision.revision_id == second.revision.revision_id
    assert len(runtime.started) == 1
    assert [event.event_type for event in repository.events[-2:]] == [
        "mission.confirmed",
        "mission.started",
    ]


@pytest.mark.asyncio
async def test_discover_handler_persists_safe_target_observations() -> None:
    repository = Repository()
    mission = await ready_mission(repository)

    result = await DiscoverMissionHandler(
        repository, MissionDiscovery(Probe())
    ).execute(actor(), mission.project_id, mission.mission_id)

    assert result.login_valid is True
    assert mission.facts["discovery"].value["capabilities"] == ("chat",)
    assert repository.events[-1].event_type == "mission.discovered"


@pytest.mark.asyncio
async def test_cancel_and_resume_control_existing_temporal_workflow() -> None:
    repository = Repository()
    mission = await ready_mission(repository)
    runtime = Runtime()
    preview = await PreviewMissionHandler(repository, MissionPreflight()).execute(
        actor(), mission.project_id, mission.mission_id
    )
    await ConfirmMissionHandler(repository, MissionPreflight(), runtime).execute(
        actor(),
        mission.project_id,
        mission.mission_id,
        revision_hash=preview.revision_hash,
        idempotency_key="control-1",
    )
    mission.mark_running()
    mission.mark_needs_attention("auth_expired")

    resumed = await ResumeMissionHandler(repository, runtime).execute(
        actor(), mission.project_id, mission.mission_id
    )
    assert resumed.status.value == "running"
    cancelled = await CancelMissionHandler(repository, runtime).execute(
        actor(), mission.project_id, mission.mission_id
    )

    assert cancelled.status.value == "cancelled"
    assert runtime.resumed == [mission.workflow_id]
    assert runtime.cancelled == [mission.workflow_id]
