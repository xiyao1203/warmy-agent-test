"""验证实验对比与人工审核的领域模型和数据契约。

覆盖：
- Experiment 实体创建与状态生命周期
- ReviewTask 自动收集触发与审核流程
- 实验对比统计值对象
- 实验和审核的项目隔离约束
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.experiments.domain.entities import (
    CaseComparison,
    Experiment,
    ExperimentId,
    ExperimentStatus,
    ExperimentSummary,
)
from agenttest.modules.experiments.infrastructure.persistence.models import (
    ExperimentModel,
)
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reviews.domain.entities import (
    ReviewStatus,
    ReviewTask,
    ReviewTaskId,
)
from agenttest.modules.reviews.infrastructure.persistence.models import (
    ReviewTaskModel,
)

# ── Experiment 实体测试 ────────────────────────────────────────────────


def test_experiment_create_requires_name() -> None:
    """空名称拒绝创建实验。"""
    with pytest.raises(ValueError, match="name"):
        Experiment.create(
            experiment_id=ExperimentId.new(),
            project_id=ProjectId.new(),
            name="",
            run_a_id=uuid4(),
            run_b_id=uuid4(),
        )


def test_experiment_create_rejects_same_run() -> None:
    """实验不允许对比同一 Run。"""
    run_id = uuid4()
    with pytest.raises(ValueError, match="different"):
        Experiment.create(
            experiment_id=ExperimentId.new(),
            project_id=ProjectId.new(),
            name="same-run test",
            run_a_id=run_id,
            run_b_id=run_id,
        )


def test_experiment_starts_as_pending() -> None:
    """新创建的实验状态为 pending。"""
    exp = Experiment.create(
        experiment_id=ExperimentId.new(),
        project_id=ProjectId.new(),
        name="A/B test",
        run_a_id=uuid4(),
        run_b_id=uuid4(),
    )

    assert exp.status is ExperimentStatus.PENDING
    assert exp.result_json == {}


def test_experiment_complete_stores_result_and_sets_completed() -> None:
    """实验完成后保存结果并标记为 completed。"""
    exp = Experiment.create(
        experiment_id=ExperimentId.new(),
        project_id=ProjectId.new(),
        name="A/B test",
        run_a_id=uuid4(),
        run_b_id=uuid4(),
    )
    result = {"improved": 5, "degraded": 2, "unchanged": 10}

    exp.complete(result)

    assert exp.status is ExperimentStatus.COMPLETED
    assert exp.result_json == result


def test_experiment_fail_stores_error() -> None:
    """实验失败时保存错误信息。"""
    exp = Experiment.create(
        experiment_id=ExperimentId.new(),
        project_id=ProjectId.new(),
        name="A/B test",
        run_a_id=uuid4(),
        run_b_id=uuid4(),
    )

    exp.fail("Run A not found")

    assert exp.status is ExperimentStatus.FAILED
    assert exp.result_json == {"error": "Run A not found"}


# ── ExperimentSummary 统计测试 ─────────────────────────────────────────


def test_experiment_summary_to_dict_rounds_values() -> None:
    """ExperimentSummary.to_dict 正确处理浮点精度。"""
    summary = ExperimentSummary(
        total_cases=10,
        improved=3,
        degraded=2,
        unchanged=5,
        avg_duration_delta_ms=15.12345,
        p50_duration_delta_ms=10.1,
        p95_duration_delta_ms=25.678,
        avg_score_delta=0.0123456,
        variance_score_delta=0.0012345,
    )

    result = summary.to_dict()
    assert result["total_cases"] == 10
    assert result["avg_duration_delta_ms"] == 15.12
    assert result["p95_duration_delta_ms"] == 25.68
    assert result["avg_score_delta"] == 0.0123


# ── CaseComparison 值对象测试 ──────────────────────────────────────────


def test_case_comparison_default_no_change() -> None:
    """默认用例对比分类为 no_change。"""
    comparison = CaseComparison(
        test_case_id="case-1",
        status_a="passed",
        status_b="passed",
        status_changed=False,
    )
    assert comparison.category == "no_change"
    assert comparison.duration_delta_ms == 0
    assert comparison.score_delta is None


# ── ReviewTask 实体测试 ──────────────────────────────────────────────


def test_review_task_create_requires_valid_confidence() -> None:
    """置信度必须在 0-1 之间。"""
    with pytest.raises(ValueError, match="between 0 and 1"):
        ReviewTask.create(
            task_id=ReviewTaskId.new(),
            project_id=ProjectId.new(),
            run_case_id=uuid4(),
            confidence=1.5,
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        ReviewTask.create(
            task_id=ReviewTaskId.new(),
            project_id=ProjectId.new(),
            run_case_id=uuid4(),
            confidence=-0.1,
        )


def test_review_task_approve_sets_score_and_status() -> None:
    """审批通过后设置评分和审核人。"""
    reviewer_id = uuid4()
    task = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=ProjectId.new(),
        run_case_id=uuid4(),
        confidence=0.6,
    )

    task.approve(reviewer_id, score=0.85, opinion="looks good")

    assert task.status is ReviewStatus.APPROVED
    assert task.score == 0.85
    assert task.reviewer_id == reviewer_id
    assert task.opinion == "looks good"
    assert task.reviewed_at is not None


def test_review_task_reject_sets_zero_score() -> None:
    """审批拒绝后评分自动为 0。"""
    reviewer_id = uuid4()
    task = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=ProjectId.new(),
        run_case_id=uuid4(),
        confidence=0.4,
    )

    task.reject(reviewer_id, opinion="incorrect output")

    assert task.status is ReviewStatus.REJECTED
    assert task.score == 0.0
    assert task.reviewed_at is not None


def test_review_task_cannot_review_non_pending() -> None:
    """非 pending 状态不可重复审核。"""
    reviewer_id = uuid4()
    task = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=ProjectId.new(),
        run_case_id=uuid4(),
        confidence=0.5,
    )
    task.approve(reviewer_id, score=0.9)

    with pytest.raises(ValueError, match="(?i)only pending"):
        task.approve(reviewer_id, score=0.5)


def test_review_task_skip_marks_as_skipped() -> None:
    """跳过审核标记为 skipped。"""
    task = ReviewTask.create(
        task_id=ReviewTaskId.new(),
        project_id=ProjectId.new(),
        run_case_id=uuid4(),
        confidence=0.3,
    )

    task.skip()

    assert task.status is ReviewStatus.SKIPPED


# ── 持久化模型约束测试 ────────────────────────────────────────────────


def test_experiment_model_has_project_foreign_key() -> None:
    """实验表强制项目外键。"""
    fk_columns = {fk.parent.name for fk in ExperimentModel.__table__.foreign_keys}
    assert "project_id" in fk_columns


def test_review_task_model_has_project_foreign_key() -> None:
    """审核任务表强制项目外键。"""
    fk_columns = {fk.parent.name for fk in ReviewTaskModel.__table__.foreign_keys}
    assert "project_id" in fk_columns
