"""Experiment 仓库 SQLAlchemy 实现。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.experiments.domain.entities import (
    Experiment,
    ExperimentId,
    ExperimentStatus,
)
from agenttest.modules.experiments.infrastructure.persistence.models import (
    ExperimentModel,
)
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyExperimentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, exp_id: ExperimentId) -> Experiment | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(ExperimentModel, exp_id.value)
        return _to_experiment(model) if model else None

    async def get_by_id_and_project(
        self, exp_id: ExperimentId, project_id: ProjectId,
    ) -> Experiment | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(ExperimentModel, exp_id.value)
            if model and model.project_id != project_id.value:
                return None
            return _to_experiment(model) if model else None

    async def list_by_project(
        self, project_id: ProjectId, *, limit: int = 50, offset: int = 0,
    ) -> list[Experiment]:
        stmt = (
            select(ExperimentModel)
            .where(ExperimentModel.project_id == project_id.value)
            .order_by(ExperimentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(stmt)).all())
        return [_to_experiment(m) for m in models]

    async def add(self, experiment: Experiment) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(_to_model(experiment))

    async def save(self, experiment: Experiment) -> None:
        async with transaction_scope(self._session_factory) as session:
            model = await session.get(ExperimentModel, experiment.experiment_id.value)
            if model:
                model.name = experiment.name
                model.status = experiment.status.value
                model.result_json = experiment.result_json
                model.description = experiment.description
                model.updated_at = experiment.updated_at


def _to_model(e: Experiment) -> ExperimentModel:
    return ExperimentModel(
        id=e.experiment_id.value,
        project_id=e.project_id.value,
        name=e.name,
        run_a_id=e.run_a_id,
        run_b_id=e.run_b_id,
        status=e.status.value,
        result_json=e.result_json,
        description=e.description,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


def _to_experiment(m: ExperimentModel) -> Experiment:
    return Experiment(
        experiment_id=ExperimentId(m.id),
        project_id=ProjectId(m.project_id),
        name=m.name,
        run_a_id=m.run_a_id,
        run_b_id=m.run_b_id,
        status=ExperimentStatus(m.status),
        result_json=m.result_json,
        description=m.description,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )
