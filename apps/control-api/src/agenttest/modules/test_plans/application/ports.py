"""TestPlan 应用层的出站端口。"""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class ProjectAccessPort(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...
