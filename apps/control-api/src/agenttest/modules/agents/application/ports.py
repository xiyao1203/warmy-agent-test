"""Agent 应用层的出站端口（Port）。

定义项目访问权限检查接口，由启动层提供实现。
"""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class ProjectAccessPort(Protocol):
    """项目成员资格和编辑权限检查端口。

    实现由 bootstrap 层提供，注入 projects 模块的基础设施。
    """

    async def ensure_member(self, actor: User, project_id: ProjectId) -> None:
        """校验 Actor 是项目成员，否则抛出 ProjectNotFoundError。"""
        ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None:
        """校验 Actor 有编辑权限（developer/tester 或 super_admin）。

        Raises:
            ProjectNotFoundError: 非项目成员。
            PermissionError: 是成员但无编辑权限。
        """
        ...
