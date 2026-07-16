"""Stable public interface for project authorization."""

from typing import Protocol

from agenttest.modules.projects.domain.entities import (
    Project,
    ProjectId,
    ProjectMemberRole,
)
from agenttest.modules.projects.domain.policies import (
    ProjectAccessDeniedError,
    ProjectAccessPolicy,
    ProjectNotFoundError,
)


class ProjectAssetKeyAllocator(Protocol):
    async def allocate(
        self,
        project_id: ProjectId,
        resource_type: str,
        marker: str,
    ) -> str: ...


__all__ = [
    "Project",
    "ProjectAccessDeniedError",
    "ProjectAccessPolicy",
    "ProjectAssetKeyAllocator",
    "ProjectId",
    "ProjectMemberRole",
    "ProjectNotFoundError",
]
