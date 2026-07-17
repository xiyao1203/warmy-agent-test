from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.bootstrap.core_summaries.assets import AssetSummaryQueries
from agenttest.bootstrap.core_summaries.execution import ExecutionSummaryQueries
from agenttest.bootstrap.core_summaries.quality import QualitySummaryQueries
from agenttest.shared.application.core_summaries import (
    AgentSummaryMetrics,
    DatasetSummaryMetrics,
    EnvironmentSummaryMetrics,
    ExperimentSummaryMetrics,
    GateSummaryMetrics,
    ProjectSummaryMetrics,
    ReviewSummaryMetrics,
    RunSummaryMetrics,
    ScorerSummaryMetrics,
    SecurityScanSummaryMetrics,
    TestPlanSummaryMetrics,
)


class SqlAlchemyCoreSummaryReader:
    """Stable read-side Facade over feature-grouped summary queries."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._assets = AssetSummaryQueries(session_factory)
        self._execution = ExecutionSummaryQueries(session_factory)
        self._quality = QualitySummaryQueries(session_factory)

    async def projects(self, ids: list[UUID]) -> dict[UUID, ProjectSummaryMetrics]:
        return await self._assets.projects(ids)

    async def agents(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, AgentSummaryMetrics]:
        return await self._assets.agents(project_id, ids)

    async def datasets(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, DatasetSummaryMetrics]:
        return await self._assets.datasets(project_id, ids)

    async def test_plans(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, TestPlanSummaryMetrics]:
        return await self._assets.test_plans(project_id, ids)

    async def runs(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, RunSummaryMetrics]:
        return await self._execution.runs(project_id, ids)

    async def environments(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, EnvironmentSummaryMetrics]:
        return await self._assets.environments(project_id, ids)

    async def scorers(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, ScorerSummaryMetrics]:
        return await self._quality.scorers(project_id, ids)

    async def experiments(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, ExperimentSummaryMetrics]:
        return await self._execution.experiments(project_id, ids)

    async def security_scans(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, SecurityScanSummaryMetrics]:
        return await self._quality.security_scans(project_id, ids)

    async def reviews(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, ReviewSummaryMetrics]:
        return await self._quality.reviews(project_id, ids)

    async def gates(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, GateSummaryMetrics]:
        return await self._quality.gates(project_id, ids)
