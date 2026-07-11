from uuid import uuid4

import pytest
from agenttest.modules.identity.infrastructure.persistence.models import UserModel
from agenttest.modules.projects.infrastructure.persistence.models import ProjectModel
from agenttest.modules.test_agent.infrastructure.models import (
    TestAgentSessionModel as AgentSessionModel,
)
from agenttest.modules.test_missions.domain.entities import TestMission as Mission
from agenttest.modules.test_missions.domain.value_objects import MissionFact
from agenttest.modules.test_missions.infrastructure.models import (
    TestMissionAssetModel as MissionAssetModel,
)
from agenttest.modules.test_missions.infrastructure.models import (
    TestMissionEventModel as MissionEventModel,
)
from agenttest.modules.test_missions.infrastructure.models import (
    TestMissionFactModel as MissionFactModel,
)
from agenttest.modules.test_missions.infrastructure.models import (
    TestMissionModel as MissionModel,
)
from agenttest.modules.test_missions.infrastructure.models import (
    TestMissionRevisionModel as MissionRevisionModel,
)
from agenttest.modules.test_missions.infrastructure.models import (
    TestMissionStageReceiptModel as MissionStageReceiptModel,
)
from agenttest.modules.test_missions.infrastructure.repositories import (
    MissionConcurrentUpdateError,
    SqlAlchemyMissionRepository,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


async def _repository():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: MissionModel.metadata.create_all(
                sync_connection,
                tables=[
                    UserModel.__table__,
                    ProjectModel.__table__,
                    AgentSessionModel.__table__,
                    MissionModel.__table__,
                    MissionFactModel.__table__,
                    MissionRevisionModel.__table__,
                    MissionAssetModel.__table__,
                    MissionEventModel.__table__,
                    MissionStageReceiptModel.__table__,
                ],
            )
        )
    return engine, SqlAlchemyMissionRepository(async_sessionmaker(engine, expire_on_commit=False))


@pytest.mark.asyncio
async def test_repository_round_trip_is_project_and_session_scoped() -> None:
    engine, repository = await _repository()
    project_id = uuid4()
    session_id = uuid4()
    mission = Mission.create(
        project_id=project_id,
        session_id=session_id,
        created_by=uuid4(),
    )
    mission.merge_fact(MissionFact.user("target", {"url": "https://agent.example"}))

    await repository.add(mission)

    restored = await repository.get(project_id, mission.mission_id)
    foreign = await repository.get(uuid4(), mission.mission_id)
    by_session = await repository.get_for_session(project_id, session_id)

    assert restored is not None
    assert restored.facts["target"].value == {"url": "https://agent.example"}
    assert foreign is None
    assert by_session is not None and by_session.mission_id == mission.mission_id
    await engine.dispose()


@pytest.mark.asyncio
async def test_repository_stage_receipt_is_unique_per_revision_stage() -> None:
    from datetime import UTC, datetime

    from agenttest.modules.test_missions.application.stages import StageReceipt

    engine, repository = await _repository()
    mission = Mission.create(project_id=uuid4(), session_id=uuid4(), created_by=uuid4())
    for fact in (
        MissionFact.user("target", {"url": "https://agent.example"}),
        MissionFact.user("access", {"strategy": "none"}),
        MissionFact.user("test_goal", "验证问答"),
        MissionFact.user("safety_scope", "read_only"),
    ):
        mission.merge_fact(fact)
    revision = mission.confirm(confirmed_by=uuid4())
    await repository.add(mission)
    receipt = StageReceipt(
        receipt_id=uuid4(),
        project_id=mission.project_id,
        revision_id=revision.revision_id,
        stage="provision",
        status="completed",
        output={"test_plan_version_id": str(uuid4())},
        created_at=datetime.now(UTC),
    )

    await repository.save_stage_receipt(receipt)
    restored = await repository.get_stage_receipt(
        mission.project_id, revision.revision_id, "provision"
    )

    assert restored == receipt
    await engine.dispose()


@pytest.mark.asyncio
async def test_repository_saves_revision_and_rejects_stale_lock_version() -> None:
    engine, repository = await _repository()
    mission = Mission.create(
        project_id=uuid4(),
        session_id=uuid4(),
        created_by=uuid4(),
    )
    for fact in (
        MissionFact.user("target", {"url": "https://agent.example"}),
        MissionFact.user("access", {"strategy": "none"}),
        MissionFact.user("test_goal", "验证问答"),
        MissionFact.user("safety_scope", "read_only"),
    ):
        mission.merge_fact(fact)
    await repository.add(mission)
    expected_lock = mission.lock_version
    revision = mission.confirm(confirmed_by=uuid4())

    await repository.save(mission, expected_lock_version=expected_lock)

    restored = await repository.get(mission.project_id, mission.mission_id)
    assert restored is not None
    assert restored.revisions[0].content_hash == revision.content_hash
    with pytest.raises(MissionConcurrentUpdateError):
        await repository.save(mission, expected_lock_version=expected_lock)
    await engine.dispose()


@pytest.mark.asyncio
async def test_repository_appends_ordered_events_and_idempotent_asset_links() -> None:
    engine, repository = await _repository()
    mission = Mission.create(project_id=uuid4(), session_id=uuid4(), created_by=uuid4())
    await repository.add(mission)

    first = await repository.append_event(
        mission.project_id, mission.mission_id, "mission.created", {"safe": True}
    )
    second = await repository.append_event(
        mission.project_id, mission.mission_id, "mission.updated", {"safe": True}
    )
    asset_id = uuid4()
    assert await repository.link_asset(
        mission.project_id, mission.mission_id, "dataset_version", asset_id, "created"
    )
    assert not await repository.link_asset(
        mission.project_id, mission.mission_id, "dataset_version", asset_id, "created"
    )

    events = await repository.list_events(
        mission.project_id, mission.mission_id, after=first.sequence
    )
    assert first.sequence == 1
    assert second.sequence == 2
    assert [event.event_type for event in events] == ["mission.updated"]
    await engine.dispose()
