from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from agenttest.modules.browser_profiles.application.auth_state import BrowserAuthStateService
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class BrowserProfileRepository(Protocol):
    async def list(self, project_id: UUID) -> list[BrowserProfile]: ...

    async def get(self, project_id: UUID, profile_id: UUID) -> BrowserProfile | None: ...

    async def add(self, item: BrowserProfile) -> None: ...

    async def save(self, item: BrowserProfile) -> None: ...

    async def delete(self, project_id: UUID, profile_id: UUID) -> bool: ...


class BrowserProfileRuntime(Protocol):
    def profile_dir(self, profile_id: UUID) -> str: ...

    async def start(self, profile: BrowserProfile, login_url: str) -> None: ...

    async def stop(self, profile_id: UUID) -> None: ...

    async def export_storage_state(self, profile: BrowserProfile) -> dict[str, Any]: ...

    async def verify(self, profile: BrowserProfile, storage_state: dict[str, Any]) -> bool: ...


class ProjectAccessPort(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class BrowserProfileNotFound(Exception):
    pass


class DuplicateBrowserProfile(Exception):
    pass


class BrowserProfileAuthStateMissing(Exception):
    pass


class BrowserProfileOperationError(Exception):
    pass


class BrowserProfileService:
    def __init__(
        self,
        *,
        repository: BrowserProfileRepository,
        runtime: BrowserProfileRuntime,
        auth_state: BrowserAuthStateService,
        project_access: ProjectAccessPort,
    ) -> None:
        self._repository = repository
        self._runtime = runtime
        self._auth_state = auth_state
        self._project_access = project_access

    async def list(self, actor: User, project_id: UUID) -> list[BrowserProfile]:
        await self._project_access.ensure_member(actor, ProjectId(project_id))
        return await self._repository.list(project_id)

    async def create(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str,
        target_domain: str,
    ) -> BrowserProfile:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        item = BrowserProfile.create(
            project_id=project_id,
            name=name,
            target_domain=target_domain,
            created_by=actor.user_id.value,
            now=datetime.now(UTC),
        )
        item.user_data_dir = self._runtime.profile_dir(item.id)
        await self._repository.add(item)
        return item

    async def get(self, actor: User, project_id: UUID, profile_id: UUID) -> BrowserProfile:
        await self._project_access.ensure_member(actor, ProjectId(project_id))
        return await self._profile(project_id, profile_id)

    async def update(
        self,
        actor: User,
        project_id: UUID,
        profile_id: UUID,
        *,
        name: str | None,
        target_domain: str | None,
    ) -> BrowserProfile:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        item = await self._profile(project_id, profile_id)
        if name is not None:
            item.name = name.strip()
        if target_domain is not None:
            item.target_domain = target_domain.strip()
        item.updated_at = datetime.now(UTC)
        await self._repository.save(item)
        return item

    async def start(
        self,
        actor: User,
        project_id: UUID,
        profile_id: UUID,
        *,
        login_url: str,
    ) -> BrowserProfile:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        item = await self._profile(project_id, profile_id)
        try:
            await self._runtime.start(item, login_url)
            item.status = "running"
            item.updated_at = datetime.now(UTC)
            await self._repository.save(item)
        except Exception as error:
            item.status = "error"
            item.cdp_endpoint = ""
            item.updated_at = datetime.now(UTC)
            await self._repository.save(item)
            raise BrowserProfileOperationError(str(error)) from error
        return item

    async def complete_login(
        self,
        actor: User,
        project_id: UUID,
        profile_id: UUID,
        *,
        stop_after_save: bool,
    ) -> BrowserProfile:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        item = await self._profile(project_id, profile_id)
        try:
            storage_state = await self._runtime.export_storage_state(item)
            snapshot = self._auth_state.seal(
                project_id=project_id,
                profile_id=profile_id,
                target_domain=item.target_domain,
                storage_state=storage_state,
            )
            item.store_auth_state(
                envelope=snapshot.envelope,
                sha256=snapshot.sha256,
                saved_at=datetime.now(UTC),
            )
            await self._repository.save(item)
            if stop_after_save:
                await self._runtime.stop(profile_id)
                item.status = "stopped"
                item.cdp_endpoint = ""
                item.updated_at = datetime.now(UTC)
                await self._repository.save(item)
        except Exception as error:
            item.auth_state_status = "error"
            item.updated_at = datetime.now(UTC)
            await self._repository.save(item)
            raise BrowserProfileOperationError(str(error)) from error
        return item

    async def verify(self, actor: User, project_id: UUID, profile_id: UUID) -> BrowserProfile:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        item = await self._profile(project_id, profile_id)
        if not item.auth_state_envelope:
            raise BrowserProfileAuthStateMissing
        try:
            storage_state = self._auth_state.open(project_id, profile_id, item.auth_state_envelope)
            verified_at = datetime.now(UTC)
            if await self._runtime.verify(item, storage_state):
                item.mark_auth_ready(verified_at)
            else:
                item.auth_state_status = "expired"
                item.last_verified_at = verified_at
                item.updated_at = verified_at
            await self._repository.save(item)
        except Exception as error:
            item.auth_state_status = "error"
            item.updated_at = datetime.now(UTC)
            await self._repository.save(item)
            raise BrowserProfileOperationError(str(error)) from error
        return item

    async def stop(self, actor: User, project_id: UUID, profile_id: UUID) -> BrowserProfile:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        item = await self._profile(project_id, profile_id)
        await self._runtime.stop(profile_id)
        item.status = "stopped"
        item.cdp_endpoint = ""
        item.updated_at = datetime.now(UTC)
        await self._repository.save(item)
        return item

    async def delete(self, actor: User, project_id: UUID, profile_id: UUID) -> None:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        await self._profile(project_id, profile_id)
        await self._runtime.stop(profile_id)
        if not await self._repository.delete(project_id, profile_id):
            raise BrowserProfileNotFound

    async def _profile(self, project_id: UUID, profile_id: UUID) -> BrowserProfile:
        item = await self._repository.get(project_id, profile_id)
        if item is None:
            raise BrowserProfileNotFound
        return item
