"""ReleaseGate 领域实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ReleaseGateId:
    value: UUID

    @classmethod
    def new(cls) -> ReleaseGateId:
        return cls(uuid4())


@dataclass(slots=True)
class ReleaseGate:
    """发布门禁实体。

    定义项目发布前必须满足的条件。

    Attributes:
        gate_id: 门禁唯一标识。
        project_id: 所属项目 ID。
        name: 门禁名称。
        success_rate_threshold: 通过率阈值（0.0-1.0）。
        critical_cases: 必须通过的关键用例 ID 列表。
        cost_limit: 成本上限（可选）。
        security_threshold: 安全评分阈值（0.0-1.0）。
        enabled: 是否启用。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    gate_id: ReleaseGateId
    project_id: UUID
    name: str
    success_rate_threshold: float
    critical_cases: list[str]
    cost_limit: float | None
    security_threshold: float
    enabled: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID,
        name: str,
        success_rate_threshold: float = 0.8,
        critical_cases: list[str] | None = None,
        cost_limit: float | None = None,
        security_threshold: float = 0.8,
    ) -> ReleaseGate:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Gate name is required")
        if not (0.0 <= success_rate_threshold <= 1.0):
            raise ValueError("success_rate_threshold must be between 0 and 1")
        if not (0.0 <= security_threshold <= 1.0):
            raise ValueError("security_threshold must be between 0 and 1")
        if cost_limit is not None and cost_limit < 0:
            raise ValueError("cost_limit must be non-negative")
        now = datetime.now(UTC)
        return cls(
            gate_id=ReleaseGateId.new(),
            project_id=project_id,
            name=normalized,
            success_rate_threshold=success_rate_threshold,
            critical_cases=critical_cases or [],
            cost_limit=cost_limit,
            security_threshold=security_threshold,
            enabled=True,
            created_at=now,
            updated_at=now,
        )

    def evaluate(
        self,
        *,
        actual_pass_rate: float,
        critical_passed: bool,
        actual_cost: float | None = None,
        security_score: float | None = None,
    ) -> GateResult:
        """评估门禁是否通过。"""
        failures: list[str] = []

        if actual_pass_rate < self.success_rate_threshold:
            failures.append(
                f"通过率 {actual_pass_rate:.1%} 低于阈值 {self.success_rate_threshold:.1%}"
            )

        if not critical_passed:
            failures.append("关键用例未全部通过")

        if (
            self.cost_limit is not None
            and actual_cost is not None
            and actual_cost > self.cost_limit
        ):
            failures.append(f"成本 {actual_cost:.2f} 超出限额 {self.cost_limit:.2f}")

        if security_score is not None and security_score < self.security_threshold:
            failures.append(f"安全评分 {security_score:.2f} 低于阈值 {self.security_threshold:.2f}")

        return GateResult(
            passed=len(failures) == 0,
            failures=failures,
            evaluated_at=datetime.now(UTC),
        )

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self.updated_at = datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class GateResult:
    """门禁评估结果值对象。"""

    passed: bool
    failures: list[str]
    evaluated_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "failures": self.failures,
            "evaluated_at": self.evaluated_at.isoformat(),
        }
