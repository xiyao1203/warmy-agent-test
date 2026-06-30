"""Scorer 仓库的 SQLAlchemy 实现。"""

from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId
from agenttest.modules.scorers.domain.value_objects import ScorerType
from agenttest.modules.scorers.infrastructure.persistence.models import ScorerModel
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyScorerRepository:
    """评分器的 SQLAlchemy 仓库实现。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, scorer_id: ScorerId) -> Scorer | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(ScorerModel, scorer_id.value)
        return _to_scorer(model) if model else None

    async def get_by_id_and_project(
        self, scorer_id: ScorerId, project_id: ProjectId
    ) -> Scorer | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(ScorerModel, scorer_id.value)
            if model and model.project_id != project_id.value:
                return None
            return _to_scorer(model) if model else None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Scorer], int]:
        async with session_scope(self._session_factory) as session:
            count_stmt = (
                select(func.count())
                .select_from(ScorerModel)
                .where(ScorerModel.project_id == project_id.value)
            )
            total = (await session.execute(count_stmt)).scalar() or 0

            stmt = (
                select(ScorerModel)
                .where(ScorerModel.project_id == project_id.value)
                .order_by(ScorerModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = list((await session.scalars(stmt)).all())
        return [_to_scorer(m) for m in models], total

    async def add(self, scorer: Scorer) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                ScorerModel(
                    id=scorer.scorer_id.value,
                    project_id=scorer.project_id.value,
                    name=scorer.name,
                    scorer_type=scorer.scorer_type.value,
                    weight=scorer.weight,
                    threshold=scorer.threshold,
                    config_json=scorer.config_json,
                    description=scorer.description,
                    enabled=scorer.enabled,
                    created_at=scorer.created_at,
                    updated_at=scorer.updated_at,
                )
            )

    async def save(self, scorer: Scorer) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(ScorerModel)
                .where(ScorerModel.id == scorer.scorer_id.value)
                .values(
                    name=scorer.name,
                    scorer_type=scorer.scorer_type.value,
                    weight=scorer.weight,
                    threshold=scorer.threshold,
                    config_json=scorer.config_json,
                    description=scorer.description,
                    enabled=scorer.enabled,
                    updated_at=scorer.updated_at,
                )
            )

    async def delete(self, scorer_id: ScorerId) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(delete(ScorerModel).where(ScorerModel.id == scorer_id.value))


def _to_scorer(model: ScorerModel) -> Scorer:
    return Scorer(
        scorer_id=ScorerId(model.id),
        project_id=ProjectId(model.project_id),
        name=model.name,
        scorer_type=ScorerType(model.scorer_type),
        weight=model.weight,
        threshold=model.threshold,
        config_json=model.config_json,
        description=model.description,
        enabled=model.enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
