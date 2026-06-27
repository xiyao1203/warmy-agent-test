"""ReleaseGate 仓库 SQLAlchemy 实现。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.gates.domain.entities import (
    ReleaseGate,
    ReleaseGateId,
)
from agenttest.modules.gates.infrastructure.persistence.models import (
    ReleaseGateModel,
)


class SqlAlchemyReleaseGateRepository:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def get_by_id_and_project(
        self, gate_id: ReleaseGateId, project_id: UUID,
    ) -> ReleaseGate | None:
        async with self._session_factory() as session:
            row = await session.get(ReleaseGateModel, gate_id.value)
            if row is None or row.project_id != project_id:
                return None
            return _to_entity(row)

    async def list_by_project(
        self, project_id: UUID, *, limit: int = 50,
    ) -> list[ReleaseGate]:
        async with self._session_factory() as session:
            stmt = (
                select(ReleaseGateModel)
                .where(ReleaseGateModel.project_id == project_id)
                .order_by(ReleaseGateModel.created_at.desc())
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_entity(r) for r in rows]

    async def add(self, gate: ReleaseGate) -> None:
        async with self._session_factory() as session:
            session.add(_to_model(gate))
            await session.commit()

    async def save(self, gate: ReleaseGate) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    "UPDATE release_gates SET name=:n, "
                    "success_rate_threshold=:srt, critical_cases=:cc, "
                    "cost_limit=:cl, security_threshold=:st, enabled=:e, "
                    "updated_at=:u WHERE id=:id"
                ),
                {
                    "id": gate.gate_id.value,
                    "n": gate.name,
                    "srt": gate.success_rate_threshold,
                    "cc": gate.critical_cases,
                    "cl": gate.cost_limit,
                    "st": gate.security_threshold,
                    "e": gate.enabled,
                    "u": gate.updated_at,
                },
            )
            await session.commit()

    async def delete(self, gate_id: ReleaseGateId) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text("DELETE FROM release_gates WHERE id=:id"),
                {"id": gate_id.value},
            )
            await session.commit()


def _to_model(g: ReleaseGate) -> ReleaseGateModel:
    return ReleaseGateModel(
        id=g.gate_id.value,
        project_id=g.project_id,
        name=g.name,
        success_rate_threshold=g.success_rate_threshold,
        critical_cases=g.critical_cases,
        cost_limit=g.cost_limit,
        security_threshold=g.security_threshold,
        enabled=g.enabled,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


def _to_entity(row: ReleaseGateModel) -> ReleaseGate:
    return ReleaseGate(
        gate_id=ReleaseGateId(row.id),
        project_id=row.project_id,
        name=row.name,
        success_rate_threshold=row.success_rate_threshold,
        critical_cases=list(row.critical_cases)
        if isinstance(row.critical_cases, list)
        else [],
        cost_limit=row.cost_limit,
        security_threshold=row.security_threshold,
        enabled=row.enabled,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
