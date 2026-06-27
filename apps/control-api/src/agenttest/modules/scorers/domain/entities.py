"""Scorer 领域实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.scorers.domain.value_objects import ScorerType


@dataclass(frozen=True, slots=True)
class ScorerId:
    """评分器唯一标识。"""
    value: UUID

    @classmethod
    def new(cls) -> ScorerId:
        return cls(uuid4())


@dataclass(slots=True)
class Scorer:
    """评分器实体。

    定义项目下的评分器，支持规则、模型和参考三种类型。

    Attributes:
        scorer_id: 评分器唯一标识。
        project_id: 所属项目 ID。
        name: 评分器名称。
        scorer_type: 评分器类型。
        weight: 权重（0.0-10.0），用于加权平均。
        threshold: 通过阈值（0.0-1.0）。
        config_json: 额外配置。
        created_at: 创建时间。
        updated_at: 更新时间。
        description: 可选描述。
        enabled: 是否启用。
    """
    scorer_id: ScorerId
    project_id: ProjectId
    name: str
    scorer_type: ScorerType
    weight: float
    threshold: float
    config_json: dict[str, object]
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    enabled: bool = True

    @classmethod
    def create(
        cls,
        *,
        scorer_id: ScorerId,
        project_id: ProjectId,
        name: str,
        scorer_type: ScorerType,
        weight: float = 1.0,
        threshold: float = 0.8,
        config_json: dict[str, object] | None = None,
        description: str | None = None,
    ) -> Scorer:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Scorer name is required")
        if not (0.0 <= weight <= 10.0):
            raise ValueError("weight must be between 0 and 10")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be between 0 and 1")
        now = datetime.now(UTC)
        return cls(
            scorer_id=scorer_id,
            project_id=project_id,
            name=normalized,
            scorer_type=scorer_type,
            weight=weight,
            threshold=threshold,
            config_json=config_json or {},
            created_at=now,
            updated_at=now,
            description=description,
        )

    def rename(self, name: str) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Scorer name is required")
        self.name = normalized
        self.updated_at = datetime.now(UTC)

    def update_weight(self, weight: float) -> None:
        if not (0.0 <= weight <= 10.0):
            raise ValueError("weight must be between 0 and 10")
        self.weight = weight
        self.updated_at = datetime.now(UTC)

    def update_threshold(self, threshold: float) -> None:
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold
        self.updated_at = datetime.now(UTC)

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self.updated_at = datetime.now(UTC)

    def evaluate_score(self, score: float) -> bool:
        """根据阈值判断是否通过。"""
        return score >= self.threshold
