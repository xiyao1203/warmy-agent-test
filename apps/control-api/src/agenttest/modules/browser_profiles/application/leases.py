from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.browser_profiles.application.auth_state import BrowserAuthStateService
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


@dataclass(frozen=True, slots=True)
class BrowserSessionSnapshotRef:
    browser_profile_id: UUID
    auth_state_version: int
    auth_state_sha256: str


@dataclass(frozen=True, slots=True)
class RedeemedBrowserSession:
    storage_state: dict
    auth_state_version: int


class BrowserProfileLeaseRepository(Protocol):
    async def get(self, project_id: UUID, profile_id: UUID) -> BrowserProfile | None: ...


class BrowserSessionScopeReader(Protocol):
    async def resolve(
        self, project_id: UUID, run_id: UUID, run_case_id: UUID
    ) -> BrowserSessionSnapshotRef | None: ...


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


class BrowserSessionLeaseService:
    def __init__(
        self,
        *,
        repository: BrowserProfileLeaseRepository,
        auth_state: BrowserAuthStateService,
        scope_reader: BrowserSessionScopeReader,
    ) -> None:
        self._repository = repository
        self._auth_state = auth_state
        self._scope_reader = scope_reader

    async def redeem(
        self,
        *,
        project_id: UUID,
        run_id: UUID,
        run_case_id: UUID,
        browser_profile_id: UUID,
    ) -> RedeemedBrowserSession:
        ref = await self._scope_reader.resolve(project_id, run_id, run_case_id)
        if ref is None or ref.browser_profile_id != browser_profile_id:
            raise PermissionError("浏览器实例不在当前运行快照中")
        profile = await self._repository.get(project_id, browser_profile_id)
        if profile is None:
            raise PermissionError("浏览器实例不存在")
        if profile.auth_state_status != "ready" or not profile.auth_state_envelope:
            raise RuntimeError("浏览器登录态已过期或不可用")
        if (
            profile.auth_state_version != ref.auth_state_version
            or profile.auth_state_sha256 != ref.auth_state_sha256
        ):
            raise RuntimeError("浏览器登录态版本与不可变运行快照不一致")
        return RedeemedBrowserSession(
            storage_state=self._auth_state.open(
                project_id, browser_profile_id, profile.auth_state_envelope
            ),
            auth_state_version=profile.auth_state_version,
        )
