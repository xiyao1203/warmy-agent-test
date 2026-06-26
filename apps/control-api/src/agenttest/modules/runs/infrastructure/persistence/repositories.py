from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.value_objects import RunCaseStatus, RunStatus
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunCaseModel,
    RunModel,
)
from agenttest.modules.test_plans.public import TestPlanVersionId
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyRunRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None:
        statement = select(RunModel).where(
            RunModel.id == run_id.value,
            RunModel.project_id == project_id.value,
        )
        async with session_scope(self._session_factory) as session:
            model = await session.scalar(statement)
        return _to_run(model) if model else None

    async def get_by_idempotency_key(
        self,
        project_id: ProjectId,
        key: str,
    ) -> Run | None:
        statement = select(RunModel).where(
            RunModel.project_id == project_id.value,
            RunModel.idempotency_key == key,
        )
        async with session_scope(self._session_factory) as session:
            model = await session.scalar(statement)
        return _to_run(model) if model else None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
    ) -> list[Run]:
        statement = (
            select(RunModel)
            .where(RunModel.project_id == project_id.value)
            .order_by(RunModel.created_at.desc())
            .limit(limit)
        )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        return [_to_run(model) for model in models]

    async def add(self, run: Run, cases: list[RunCase]) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(_run_model(run))
            session.add_all([_case_model(case) for case in cases])

    async def save(self, run: Run) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(RunModel)
                .where(
                    RunModel.id == run.run_id.value,
                    RunModel.project_id == run.project_id.value,
                )
                .values(
                    status=run.status.value,
                    workflow_id=run.workflow_id,
                    passed_cases=run.passed_cases,
                    failed_cases=run.failed_cases,
                    error_cases=run.error_cases,
                    cancelled_cases=run.cancelled_cases,
                    updated_at=run.updated_at,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                )
            )

    async def save_result(self, run: Run, cases: list[RunCase]) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(RunModel)
                .where(
                    RunModel.id == run.run_id.value,
                    RunModel.project_id == run.project_id.value,
                )
                .values(
                    status=run.status.value,
                    workflow_id=run.workflow_id,
                    passed_cases=run.passed_cases,
                    failed_cases=run.failed_cases,
                    error_cases=run.error_cases,
                    cancelled_cases=run.cancelled_cases,
                    updated_at=run.updated_at,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                )
            )
            for case in cases:
                await session.execute(
                    update(RunCaseModel)
                    .where(
                        RunCaseModel.id == case.run_case_id.value,
                        RunCaseModel.run_id == run.run_id.value,
                    )
                    .values(
                        status=case.status.value,
                        output=case.output,
                        trace=case.trace,
                        error_type=case.error_type,
                        error_message=case.error_message,
                        duration_ms=case.duration_ms,
                        updated_at=case.updated_at,
                        started_at=case.started_at,
                        completed_at=case.completed_at,
                    )
                )

    async def list_cases(self, run_id: RunId) -> list[RunCase]:
        statement = (
            select(RunCaseModel)
            .where(RunCaseModel.run_id == run_id.value)
            .order_by(RunCaseModel.created_at)
        )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        return [_to_case(model) for model in models]


def _run_model(run: Run) -> RunModel:
    return RunModel(
        id=run.run_id.value,
        project_id=run.project_id.value,
        test_plan_version_id=run.test_plan_version_id.value,
        agent_version_id=run.agent_version_id,
        dataset_version_id=run.dataset_version_id,
        idempotency_key=run.idempotency_key,
        status=run.status.value,
        config_snapshot=run.config_snapshot,
        plugin_snapshot=run.plugin_snapshot,
        total_cases=run.total_cases,
        passed_cases=run.passed_cases,
        failed_cases=run.failed_cases,
        error_cases=run.error_cases,
        cancelled_cases=run.cancelled_cases,
        workflow_id=run.workflow_id,
        created_by=run.created_by.value,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


def _case_model(case: RunCase) -> RunCaseModel:
    return RunCaseModel(
        id=case.run_case_id.value,
        run_id=case.run_id.value,
        test_case_id=case.test_case_id,
        name=case.name,
        status=case.status.value,
        input_snapshot=case.input_snapshot,
        assertion_snapshot=case.assertion_snapshot,
        output=case.output,
        trace=case.trace,
        error_type=case.error_type,
        error_message=case.error_message,
        duration_ms=case.duration_ms,
        created_at=case.created_at,
        updated_at=case.updated_at,
        started_at=case.started_at,
        completed_at=case.completed_at,
    )


def _to_run(model: RunModel) -> Run:
    return Run(
        run_id=RunId(model.id),
        project_id=ProjectId(model.project_id),
        test_plan_version_id=TestPlanVersionId(model.test_plan_version_id),
        agent_version_id=model.agent_version_id,
        dataset_version_id=model.dataset_version_id,
        idempotency_key=model.idempotency_key,
        created_by=UserId(model.created_by),
        config_snapshot=dict(model.config_snapshot),
        plugin_snapshot=dict(model.plugin_snapshot),
        total_cases=model.total_cases,
        status=RunStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        passed_cases=model.passed_cases,
        failed_cases=model.failed_cases,
        error_cases=model.error_cases,
        cancelled_cases=model.cancelled_cases,
        workflow_id=model.workflow_id,
    )


def _to_case(model: RunCaseModel) -> RunCase:
    return RunCase(
        run_case_id=RunCaseId(model.id),
        run_id=RunId(model.run_id),
        test_case_id=model.test_case_id,
        name=model.name,
        input_snapshot=dict(model.input_snapshot),
        assertion_snapshot=list(model.assertion_snapshot),
        status=RunCaseStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        output=dict(model.output) if model.output else None,
        trace=list(model.trace),
        error_type=model.error_type,
        error_message=model.error_message,
        duration_ms=model.duration_ms,
    )
