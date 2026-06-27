"""Experiment 领域实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from agenttest.modules.projects.public import ProjectId


class ExperimentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ExperimentId:
    value: UUID

    @classmethod
    def new(cls) -> ExperimentId:
        return cls(uuid4())


@dataclass(slots=True)
class Experiment:
    """实验对比实体。

    记录两个运行之间的 A/B 对比实验。

    Attributes:
        experiment_id: 实验唯一标识。
        project_id: 所属项目 ID。
        name: 实验名称。
        run_a_id: 运行 A ID。
        run_b_id: 运行 B ID。
        status: 实验状态。
        result_json: 对比结果（JSON）。
        created_at: 创建时间。
        updated_at: 更新时间。
        description: 可选描述。
    """
    experiment_id: ExperimentId
    project_id: ProjectId
    name: str
    run_a_id: UUID
    run_b_id: UUID
    status: ExperimentStatus
    result_json: dict[str, object]
    created_at: datetime
    updated_at: datetime
    description: str | None = None

    @classmethod
    def create(
        cls,
        *,
        experiment_id: ExperimentId,
        project_id: ProjectId,
        name: str,
        run_a_id: UUID,
        run_b_id: UUID,
        description: str | None = None,
    ) -> Experiment:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Experiment name is required")
        if run_a_id == run_b_id:
            raise ValueError("run_a_id and run_b_id must be different")
        now = datetime.now(UTC)
        return cls(
            experiment_id=experiment_id,
            project_id=project_id,
            name=normalized,
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            status=ExperimentStatus.PENDING,
            result_json={},
            created_at=now,
            updated_at=now,
            description=description,
        )

    def complete(self, result_json: dict[str, object]) -> None:
        self.result_json = result_json
        self.status = ExperimentStatus.COMPLETED
        self.updated_at = datetime.now(UTC)

    def fail(self, error: str) -> None:
        self.result_json = {"error": error}
        self.status = ExperimentStatus.FAILED
        self.updated_at = datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class CaseComparison:
    """单用例对比结果值对象。"""
    test_case_id: str
    status_a: str | None
    status_b: str | None
    status_changed: bool
    duration_delta_ms: int = 0
    score_delta: float | None = None
    category: str = "no_change"  # "improved" | "degraded" | "no_change"


@dataclass(frozen=True, slots=True)
class ExperimentSummary:
    """实验对比统计摘要值对象。"""
    total_cases: int = 0
    improved: int = 0
    degraded: int = 0
    unchanged: int = 0
    avg_duration_delta_ms: float = 0.0
    p50_duration_delta_ms: float = 0.0
    p95_duration_delta_ms: float = 0.0
    avg_score_delta: float = 0.0
    variance_score_delta: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "total_cases": self.total_cases,
            "improved": self.improved,
            "degraded": self.degraded,
            "unchanged": self.unchanged,
            "avg_duration_delta_ms": round(self.avg_duration_delta_ms, 2),
            "p50_duration_delta_ms": round(self.p50_duration_delta_ms, 2),
            "p95_duration_delta_ms": round(self.p95_duration_delta_ms, 2),
            "avg_score_delta": round(self.avg_score_delta, 4),
            "variance_score_delta": round(self.variance_score_delta, 4),
        }
