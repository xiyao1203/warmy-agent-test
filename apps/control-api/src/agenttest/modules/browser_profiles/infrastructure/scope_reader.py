from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.browser_profiles.application.leases import (
    BrowserSessionSnapshotRef,
)
from agenttest.modules.runs.infrastructure.persistence.models import RunCaseModel, RunModel
from agenttest.shared.infrastructure.database import session_scope


def snapshot_ref_from_plugin_snapshot(
    plugin_snapshot: dict,
) -> BrowserSessionSnapshotRef | None:
    value = plugin_snapshot.get("browser_profile_snapshot")
    if not isinstance(value, dict):
        return None
    try:
        profile_id = UUID(str(value.get("browser_profile_id") or ""))
        version = int(value.get("auth_state_version") or 0)
        sha256 = str(value.get("auth_state_sha256") or "")
    except (TypeError, ValueError):
        return None
    if version <= 0 or len(sha256) != 64:
        return None
    return BrowserSessionSnapshotRef(profile_id, version, sha256)


class SqlAlchemyBrowserSessionScopeReader:
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
