"""ReviewTask 领域实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from agenttest.modules.projects.public import ProjectId


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class ReviewTaskId:
    value: UUID

    @classmethod
    def new(cls) -> ReviewTaskId:
        return cls(uuid4())


@dataclass(slots=True)
class ReviewTask:
    """人工审核任务实体。

    低置信度的运行用例自动入队等待人工审核评分。

    Attributes:
        task_id: 任务唯一标识。
        project_id: 所属项目 ID。
        run_case_id: 关联的运行用例 ID。
        status: 审核状态。
        reviewer_id: 审核人 ID（审核完成后填入）。
        score: 人工评分（0.0-1.0）。
        opinion: 审核意见。
        rubric_scores: 多维评分（JSON）。
        confidence: 原始置信度（触发入队的置信度）。
        created_at: 创建时间。
        updated_at: 更新时间。
        reviewed_at: 审核完成时间。
    """

    task_id: ReviewTaskId
    project_id: ProjectId
    run_case_id: UUID
    status: ReviewStatus
    confidence: float
    created_at: datetime
    updated_at: datetime
    reviewer_id: UUID | None = None
    score: float | None = None
    opinion: str | None = None
    rubric_scores: dict[str, float] | None = None
    reviewed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        task_id: ReviewTaskId,
        project_id: ProjectId,
        run_case_id: UUID,
        confidence: float,
    ) -> ReviewTask:
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("confidence must be between 0 and 1")
        now = datetime.now(UTC)
        return cls(
            task_id=task_id,
            project_id=project_id,
            run_case_id=run_case_id,
            status=ReviewStatus.PENDING,
            confidence=confidence,
            created_at=now,
            updated_at=now,
        )

    def approve(
        self,
        reviewer_id: UUID,
        score: float,
        opinion: str | None = None,
        rubric_scores: dict[str, float] | None = None,
    ) -> None:
        if self.status is not ReviewStatus.PENDING:
            raise ValueError("Only pending tasks can be reviewed")
        if not (0.0 <= score <= 1.0):
            raise ValueError("score must be between 0 and 1")
        now = datetime.now(UTC)
        self.status = ReviewStatus.APPROVED
        self.reviewer_id = reviewer_id
        self.score = score
        self.opinion = opinion
        self.rubric_scores = rubric_scores
        self.reviewed_at = now
        self.updated_at = now

    def reject(
        self,
        reviewer_id: UUID,
        opinion: str | None = None,
    ) -> None:
        if self.status is not ReviewStatus.PENDING:
            raise ValueError("Only pending tasks can be reviewed")
        now = datetime.now(UTC)
        self.status = ReviewStatus.REJECTED
        self.reviewer_id = reviewer_id
        self.score = 0.0
        self.opinion = opinion
        self.reviewed_at = now
        self.updated_at = now

    def skip(self) -> None:
        if self.status is not ReviewStatus.PENDING:
            raise ValueError("Only pending tasks can be skipped")
        self.status = ReviewStatus.SKIPPED
        self.updated_at = datetime.now(UTC)
