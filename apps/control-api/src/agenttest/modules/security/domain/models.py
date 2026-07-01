"""安全策略领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4


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


# ── Security Scan ─────────────────────────────────────────────────────────


class ScanStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingCategory(StrEnum):
    INJECTION = "injection"
    LEAK = "leak"
    JAILBREAK = "jailbreak"
    OTHER = "other"


@dataclass(slots=True)
class SecurityScan:
    """安全扫描实体。"""

    scan_id: UUID
    project_id: UUID
    status: ScanStatus
    scan_type: str
    findings: list[dict[str, object]]
    summary: dict[str, object]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    run_id: UUID | None = None
    agent_version_id: UUID | None = None
    environment_version_id: UUID | None = None
    security_profile_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID,
        scan_type: str = "full",
        run_id: UUID | None = None,
        agent_version_id: UUID | None = None,
        environment_version_id: UUID | None = None,
        security_profile_id: UUID | None = None,
    ) -> SecurityScan:
        now = datetime.now(UTC)
        return cls(
            scan_id=uuid4(),
            project_id=project_id,
            status=ScanStatus.PENDING,
            scan_type=scan_type,
            findings=[],
            summary={},
            created_at=now,
            updated_at=now,
            run_id=run_id,
            agent_version_id=agent_version_id,
            environment_version_id=environment_version_id,
            security_profile_id=security_profile_id,
        )

    def complete(self, findings: list[dict[str, object]]) -> None:
        self.findings = findings
        counts: dict[str, int] = {}
        for f in findings:
            cat = str(f.get("category", "other"))
            counts[cat] = counts.get(cat, 0) + 1
        self.summary = dict(counts)
        numeric_scores: list[float] = []
        for item in findings:
            raw_score = item.get("score")
            if isinstance(raw_score, int | float):
                numeric_scores.append(float(raw_score))
        self.summary["score"] = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 1.0
        self.status = ScanStatus.COMPLETED
        now = datetime.now(UTC)
        self.completed_at = now
        self.updated_at = now

    def fail(self, error: str) -> None:
        self.status = ScanStatus.FAILED
        self.summary = {"error": 1}
        self.updated_at = datetime.now(UTC)
