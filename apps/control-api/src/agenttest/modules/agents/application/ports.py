"""Outbound ports for the agents application layer."""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class ProjectAccessPort(Protocol):
    """Port for verifying project membership and edit permissions.

    Implementations are provided by the bootstrap layer, which has access
    to the projects module infrastructure.
    """

    async def ensure_member(self, actor: User, project_id: ProjectId) -> None:
        """Ensure the actor is a member of the project.

        Raises ``ProjectNotFoundError`` if the actor is not a member.
        """
        ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None:
        """Ensure the actor can edit test assets (developer/tester or super_admin).

        Raises ``ProjectNotFoundError`` if not a member.
        Raises ``PermissionError`` if a member but lacks edit rights.
        """
        ...
