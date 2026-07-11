from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import (
    FactSource,
    MissionEvent,
    MissionFact,
    MissionRevision,
    MissionStatus,
)
from agenttest.modules.test_missions.infrastructure.models import (
    TestMissionAssetModel,
    TestMissionEventModel,
    TestMissionFactModel,
    TestMissionModel,
    TestMissionRevisionModel,
)


class MissionConcurrentUpdateError(RuntimeError):
    pass


class SqlAlchemyMissionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, mission: TestMission) -> None:
        async with self._session_factory() as session, session.begin():
            session.add(TestMissionModel(**_mission_values(mission)))
            session.add_all(_fact_models(mission))
            session.add_all(_revision_models(mission))

    async def get(self, project_id: UUID, mission_id: UUID) -> TestMission | None:
        async with self._session_factory() as session:
            model = await session.scalar(
                select(TestMissionModel).where(
                    TestMissionModel.project_id == project_id,
                    TestMissionModel.id == mission_id,
                )
            )
            if model is None:
                return None
            return await _load_mission(session, model)

    async def get_for_session(self, project_id: UUID, session_id: UUID) -> TestMission | None:
        async with self._session_factory() as session:
            model = await session.scalar(
                select(TestMissionModel)
                .where(
                    TestMissionModel.project_id == project_id,
                    TestMissionModel.session_id == session_id,
                )
                .order_by(TestMissionModel.updated_at.desc())
            )
            if model is None:
                return None
            return await _load_mission(session, model)

    async def save(self, mission: TestMission, *, expected_lock_version: int) -> None:
        values = _mission_values(mission)
        values.pop("id")
        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                update(TestMissionModel)
                .where(
                    TestMissionModel.project_id == mission.project_id,
                    TestMissionModel.id == mission.mission_id,
                    TestMissionModel.lock_version == expected_lock_version,
                )
                .values(**values)
            )
            if cast(CursorResult[Any], result).rowcount != 1:
                raise MissionConcurrentUpdateError("Mission was updated concurrently")
            await session.execute(
                delete(TestMissionFactModel).where(
                    TestMissionFactModel.project_id == mission.project_id,
                    TestMissionFactModel.mission_id == mission.mission_id,
                )
            )
            await session.execute(
                delete(TestMissionRevisionModel).where(
                    TestMissionRevisionModel.project_id == mission.project_id,
                    TestMissionRevisionModel.mission_id == mission.mission_id,
                )
            )
            session.add_all(_fact_models(mission))
            session.add_all(_revision_models(mission))

    async def append_event(
        self,
        project_id: UUID,
        mission_id: UUID,
        event_type: str,
        payload: dict[str, object],
    ) -> MissionEvent:
        now = datetime.now(UTC)
        async with self._session_factory() as session, session.begin():
            mission_exists = await session.scalar(
                select(TestMissionModel.id)
                .where(
                    TestMissionModel.project_id == project_id,
                    TestMissionModel.id == mission_id,
                )
                .with_for_update()
            )
            if mission_exists is None:
                raise LookupError("Mission does not exist in project")
            latest = await session.scalar(
                select(func.max(TestMissionEventModel.sequence)).where(
                    TestMissionEventModel.project_id == project_id,
                    TestMissionEventModel.mission_id == mission_id,
                )
            )
            event = MissionEvent(
                event_id=uuid4(),
                project_id=project_id,
                mission_id=mission_id,
                sequence=int(latest or 0) + 1,
                event_type=event_type,
                payload=dict(payload),
                created_at=now,
            )
            session.add(
                TestMissionEventModel(
                    id=event.event_id,
                    project_id=project_id,
                    mission_id=mission_id,
                    sequence=event.sequence,
                    event_type=event_type,
                    payload=event.payload,
                    created_at=now,
                )
            )
            return event

    async def list_events(
        self, project_id: UUID, mission_id: UUID, *, after: int = 0
    ) -> list[MissionEvent]:
        async with self._session_factory() as session:
            models = list(
                (
                    await session.scalars(
                        select(TestMissionEventModel)
                        .where(
                            TestMissionEventModel.project_id == project_id,
                            TestMissionEventModel.mission_id == mission_id,
                            TestMissionEventModel.sequence > after,
                        )
                        .order_by(TestMissionEventModel.sequence)
                    )
                ).all()
            )
        return [_event(model) for model in models]

    async def link_asset(
        self,
        project_id: UUID,
        mission_id: UUID,
        asset_type: str,
        asset_id: UUID,
        relation: str,
        *,
        stage: str | None = None,
    ) -> bool:
        async with self._session_factory() as session, session.begin():
            existing = await session.scalar(
                select(TestMissionAssetModel.id).where(
                    TestMissionAssetModel.project_id == project_id,
                    TestMissionAssetModel.mission_id == mission_id,
                    TestMissionAssetModel.asset_type == asset_type,
                    TestMissionAssetModel.asset_id == asset_id,
                    TestMissionAssetModel.relation == relation,
                )
            )
            if existing is not None:
                return False
            session.add(
                TestMissionAssetModel(
                    id=uuid4(),
                    project_id=project_id,
                    mission_id=mission_id,
                    asset_type=asset_type,
                    asset_id=asset_id,
                    relation=relation,
                    stage=stage,
                    created_at=datetime.now(UTC),
                )
            )
            return True


def _mission_values(mission: TestMission) -> dict[str, object]:
    return {
        "id": mission.mission_id,
        "project_id": mission.project_id,
        "session_id": mission.session_id,
        "created_by": mission.created_by,
        "status": mission.status.value,
        "active_revision_id": mission.active_revision_id,
        "workflow_id": mission.workflow_id,
        "lock_version": mission.lock_version,
        "created_at": mission.created_at,
        "updated_at": mission.updated_at,
        "completed_at": mission.completed_at,
    }


def _fact_models(mission: TestMission) -> list[TestMissionFactModel]:
    return [
        TestMissionFactModel(
            id=uuid4(),
            project_id=mission.project_id,
            mission_id=mission.mission_id,
            field_key=fact.key,
            value_json=fact.value,
            source=fact.source.value,
            confidence=fact.confidence,
            verified=fact.verified,
            sensitive=fact.sensitive,
            fact_revision=mission.lock_version,
            created_at=mission.created_at,
            updated_at=mission.updated_at,
        )
        for fact in mission.facts.values()
    ]


def _revision_models(mission: TestMission) -> list[TestMissionRevisionModel]:
    return [
        TestMissionRevisionModel(
            id=revision.revision_id,
            project_id=revision.project_id,
            mission_id=revision.mission_id,
            revision_number=revision.revision_number,
            snapshot_json=revision.snapshot,
            content_hash=revision.content_hash,
            confirmed_by=revision.confirmed_by,
            confirmed_at=revision.confirmed_at,
        )
        for revision in mission.revisions
    ]


async def _load_mission(session: AsyncSession, model: TestMissionModel) -> TestMission:
    facts = list(
        (
            await session.scalars(
                select(TestMissionFactModel).where(
                    TestMissionFactModel.project_id == model.project_id,
                    TestMissionFactModel.mission_id == model.id,
                )
            )
        ).all()
    )
    revisions = list(
        (
            await session.scalars(
                select(TestMissionRevisionModel)
                .where(
                    TestMissionRevisionModel.project_id == model.project_id,
                    TestMissionRevisionModel.mission_id == model.id,
                )
                .order_by(TestMissionRevisionModel.revision_number)
            )
        ).all()
    )
    return TestMission(
        mission_id=model.id,
        project_id=model.project_id,
        session_id=model.session_id,
        created_by=model.created_by,
        status=MissionStatus(model.status),
        facts={
            fact.field_key: MissionFact(
                key=fact.field_key,
                value=fact.value_json,
                source=FactSource(fact.source),
                confidence=fact.confidence,
                verified=fact.verified,
                sensitive=fact.sensitive,
            )
            for fact in facts
        },
        revisions=[
            MissionRevision(
                revision_id=revision.id,
                project_id=revision.project_id,
                mission_id=revision.mission_id,
                revision_number=revision.revision_number,
                snapshot=revision.snapshot_json,
                content_hash=revision.content_hash,
                confirmed_by=revision.confirmed_by,
                confirmed_at=_utc(revision.confirmed_at),
            )
            for revision in revisions
        ],
        active_revision_id=model.active_revision_id,
        workflow_id=model.workflow_id,
        lock_version=model.lock_version,
        created_at=_utc(model.created_at),
        updated_at=_utc(model.updated_at),
        completed_at=_utc(model.completed_at) if model.completed_at else None,
    )


def _event(model: TestMissionEventModel) -> MissionEvent:
    return MissionEvent(
        event_id=model.id,
        project_id=model.project_id,
        mission_id=model.mission_id,
        sequence=model.sequence,
        event_type=model.event_type,
        payload=model.payload,
        created_at=_utc(model.created_at),
    )


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
