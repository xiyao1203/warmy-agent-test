from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.browser_profiles.public import (
    BrowserSessionSnapshotRef,
    snapshot_ref_from_plugin_snapshot,
)
from agenttest.modules.runs.infrastructure.persistence.models import RunCaseModel, RunModel
from agenttest.shared.infrastructure.database import session_scope


class SqlAlchemyBrowserSessionScopeReader:
    """Resolve a browser snapshot using Runs-owned persistence models."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def resolve(
        self, project_id: UUID, run_id: UUID, run_case_id: UUID
    ) -> BrowserSessionSnapshotRef | None:
        async with session_scope(self._session_factory) as session:
            snapshot = await session.scalar(
                select(RunModel.plugin_snapshot)
                .join(RunCaseModel, RunCaseModel.run_id == RunModel.id)
                .where(
                    RunModel.project_id == project_id,
                    RunModel.id == run_id,
                    RunModel.status == "running",
                    RunCaseModel.id == run_case_id,
                )
            )
        return (
            snapshot_ref_from_plugin_snapshot(dict(snapshot))
            if isinstance(snapshot, dict)
            else None
        )
