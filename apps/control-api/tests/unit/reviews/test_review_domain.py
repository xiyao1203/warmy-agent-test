"""Unit tests for ReviewTask domain entity."""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reviews.domain.entities import (
    ReviewStatus,
    ReviewTask,
    ReviewTaskId,
)


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


def test_review_task_create() -> None:
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    assert t.status is ReviewStatus.PENDING
    assert t.confidence == 0.3
    assert t.score is None
    assert t.reviewer_id is None


def test_review_task_validates_confidence() -> None:
    with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
        ReviewTask.create(
            task_id=ReviewTaskId.new(),
            project_id=_make_project_id(),
            run_case_id=uuid4(),
            confidence=1.5,
        )


def test_review_task_approve() -> None:
    reviewer = uuid4()
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    t.approve(reviewer, score=0.9, opinion="Looks good")
    assert t.status is ReviewStatus.APPROVED
    assert t.score == 0.9
    assert t.reviewer_id == reviewer
    assert t.opinion == "Looks good"
    assert t.reviewed_at is not None


def test_review_task_approve_with_rubric() -> None:
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    rubric = {"accuracy": 0.9, "completeness": 0.8, "relevance": 0.85}
    t.approve(uuid4(), score=0.85, rubric_scores=rubric)
    assert t.rubric_scores == rubric


def test_review_task_approve_validates_score() -> None:
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    with pytest.raises(ValueError, match="score must be between 0 and 1"):
        t.approve(uuid4(), score=1.5)


def test_review_task_reject() -> None:
    reviewer = uuid4()
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    t.reject(reviewer, opinion="Incorrect output")
    assert t.status is ReviewStatus.REJECTED
    assert t.score == 0.0
    assert t.opinion == "Incorrect output"


def test_review_task_skip() -> None:
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    t.skip()
    assert t.status is ReviewStatus.SKIPPED


def test_review_task_cannot_review_twice() -> None:
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    t.approve(uuid4(), score=0.9)
    with pytest.raises(ValueError, match="Only pending tasks can be reviewed"):
        t.approve(uuid4(), score=0.8)


def test_review_task_cannot_skip_after_review() -> None:
    t = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=_make_project_id(),
        run_case_id=uuid4(),
        confidence=0.3,
    )
    t.approve(uuid4(), score=0.9)
    with pytest.raises(ValueError, match="Only pending tasks can be skipped"):
        t.skip()


def test_review_status_values() -> None:
    assert ReviewStatus.PENDING == "pending"
    assert ReviewStatus.APPROVED == "approved"
    assert ReviewStatus.REJECTED == "rejected"
    assert ReviewStatus.SKIPPED == "skipped"
