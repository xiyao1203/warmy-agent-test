"""安全策略领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass
class SecurityPolicy:
    """安全策略实体。"""

    id: UUID
    project_id: UUID
    name: str
    max_steps: int = 20
    timeout_seconds: int = 300
    blocked_tools: list[str] = field(default_factory=list)
    require_confirmation: bool = True
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class SecurityPolicyCreate:
    """创建安全策略入参。"""

    name: str
    max_steps: int = 20
    timeout_seconds: int = 300
    blocked_tools: list[str] = field(default_factory=list)
    require_confirmation: bool = True
    enabled: bool = True


class SecurityPolicyRepository(Protocol):
    """安全策略仓库协议。"""

    async def save(self, policy: SecurityPolicy, *, project_id: UUID) -> None: ...
    async def get(self, policy_id: UUID, *, project_id: UUID) -> SecurityPolicy | None: ...
    async def get_default(self, *, project_id: UUID) -> SecurityPolicy | None: ...
    async def list_all(self, *, project_id: UUID) -> list[SecurityPolicy]: ...


class PolicyEngine:
    """安全策略执行引擎。

    根据项目安全策略验证操作是否合规。
    """

    def __init__(self, policy: SecurityPolicy | None = None) -> None:
        self._policy = policy

    def check_step_limit(self, current_step: int) -> bool:
        """检查步骤数是否超限。"""
        if not self._policy or not self._policy.enabled:
            return True
        return current_step <= self._policy.max_steps

    def check_timeout(self, elapsed_seconds: float) -> bool:
        """检查是否超时。"""
        if not self._policy or not self._policy.enabled:
            return True
        return elapsed_seconds <= self._policy.timeout_seconds

    def is_tool_blocked(self, tool_name: str) -> bool:
        """检查工具是否被禁止。"""
        if not self._policy or not self._policy.enabled:
            return False
        return tool_name in self._policy.blocked_tools

    def needs_confirmation(self, tool_name: str) -> bool:
        """检查操作是否需要确认。"""
        if not self._policy or not self._policy.enabled:
            return False
        if not self._policy.require_confirmation:
            return False
        return self.is_tool_blocked(tool_name)
