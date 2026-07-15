from __future__ import annotations

from collections.abc import Callable
from typing import Literal, Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.security.adapters import ScannerUnavailableError
from agenttest.modules.security.adapters.promptfoo_adapter import PromptfooOutputError
from agenttest.modules.security.domain.models import ScanStatus, SecurityScan
from agenttest.modules.security.domain.targets import validate_agent_endpoint


class SecurityScanRepository(Protocol):
    async def add(self, scan: SecurityScan) -> None: ...

    async def get_by_id_and_project(
        self, scan_id: UUID, project_id: UUID
    ) -> SecurityScan | None: ...

    async def list_by_project(self, project_id: UUID, *, limit: int = 50) -> list[SecurityScan]: ...

    async def save(self, scan: SecurityScan) -> None: ...


class SecurityTargetResolver(Protocol):
    async def endpoint_for(self, project_id: UUID, agent_version_id: UUID) -> str | None: ...


class SecurityScanner(Protocol):
    async def run_scan(self, *, agent_endpoint: str, scan_type: str) -> list[dict[str, object]]: ...


class ProjectAccessPort(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class SecurityScanNotFound(Exception):
    pass


class InvalidSecurityTarget(Exception):
    pass


class SecurityScanService:
    def __init__(
        self,
        *,
        scans: SecurityScanRepository,
        targets: SecurityTargetResolver,
        scanner_factory: Callable[[], SecurityScanner],
        project_access: ProjectAccessPort,
        allow_private_network: bool,
    ) -> None:
        self._scans = scans
        self._targets = targets
        self._scanner_factory = scanner_factory
        self._project_access = project_access
        self._allow_private_network = allow_private_network

    async def list(self, actor: User, project_id: UUID, *, limit: int) -> list[SecurityScan]:
        await self._project_access.ensure_member(actor, ProjectId(project_id))
        return await self._scans.list_by_project(project_id, limit=limit)

    async def trigger(
        self,
        actor: User,
        project_id: UUID,
        *,
        agent_version_id: UUID,
        run_id: UUID | None,
        environment_version_id: UUID | None,
        security_profile_id: UUID | None,
        scan_type: Literal["full", "quick"],
    ) -> SecurityScan:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        endpoint = await self._targets.endpoint_for(project_id, agent_version_id)
        if endpoint is None:
            raise InvalidSecurityTarget
        scan = SecurityScan.create(
            project_id=project_id,
            scan_type=scan_type,
            run_id=run_id,
            agent_version_id=agent_version_id,
            environment_version_id=environment_version_id,
            security_profile_id=security_profile_id,
        )
        await self._scans.add(scan)
        scan.status = ScanStatus.RUNNING
        await self._scans.save(scan)
        try:
            validate_agent_endpoint(endpoint, allow_private_network=self._allow_private_network)
            scan.complete(
                await self._scanner_factory().run_scan(agent_endpoint=endpoint, scan_type=scan_type)
            )
        except (
            ScannerUnavailableError,
            PromptfooOutputError,
            RuntimeError,
            ValueError,
        ) as error:
            scan.fail(str(error))
        await self._scans.save(scan)
        return scan

    async def get(self, actor: User, project_id: UUID, scan_id: UUID) -> SecurityScan:
        await self._project_access.ensure_member(actor, ProjectId(project_id))
        scan = await self._scans.get_by_id_and_project(scan_id, project_id)
        if scan is None:
            raise SecurityScanNotFound
        return scan
