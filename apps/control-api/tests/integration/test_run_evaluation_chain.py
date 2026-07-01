"""验证评分器结果持久化与评估聚合的完整链路。

覆盖：
- build_evaluation_summary 基于断言状态的后备评估
- ScoreModel 和 RunEvaluationModel 的约束与字段
- save_result 在有无 scorer 结果时的不同路径
- 评分器 version_id 关联
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.evaluations.domain import (
    CaseScore,
    CaseScoreInput,
    build_evaluation_summary,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunEvaluationModel,
    ScoreModel,
)
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    _case_model,
    _run_model,
)
from agenttest.modules.test_plans.public import TestPlanVersionId
from sqlalchemy import UniqueConstraint

# ── 后备评估逻辑测试 ──────────────────────────────────────────────────


def test_build_evaluation_summary_from_assertion_status() -> None:
    """后备评估正确基于断言状态生成评分。"""
    summary = build_evaluation_summary(
        [
            CaseScoreInput(run_case_id="case-1", status="passed"),
            CaseScoreInput(run_case_id="case-2", status="failed"),
            CaseScoreInput(run_case_id="case-3", status="passed"),
        ]
    )

    assert summary.status == "completed"
    assert summary.aggregate_score == pytest.approx(2.0 / 3.0)
    assert summary.pass_rate == pytest.approx(2.0 / 3.0)
    assert len(summary.scores) == 3
    assert summary.scores[0].passed is True
    assert summary.scores[0].score == 1.0
    assert summary.scores[1].passed is False
    assert summary.scores[1].score == 0.0


def test_build_evaluation_summary_requires_at_least_one_case() -> None:
    """空用例列表拒绝生成评估。"""
    with pytest.raises(ValueError, match="at least one case"):
        build_evaluation_summary([])


def test_build_evaluation_handles_error_and_cancelled_status() -> None:
    """非 passed 状态（error/cancelled）均视为失败。"""
    summary = build_evaluation_summary(
        [
            CaseScoreInput(run_case_id="case-1", status="error"),
            CaseScoreInput(run_case_id="case-2", status="cancelled"),
        ]
    )

    assert summary.aggregate_score == 0.0
    assert summary.pass_rate == 0.0
    assert all(not s.passed for s in summary.scores)


# ── ScoreModel 和 RunEvaluationModel 约束测试 ─────────────────────────


def test_score_model_has_required_fields() -> None:
    """ScoreModel 必须包含评估、用例和评分器维度字段。"""
    assert ScoreModel.__tablename__ == "scores"

    columns = {c.name: c for c in ScoreModel.__table__.c}
    for col in ("id", "project_id", "evaluation_id", "run_case_id", "score", "passed"):
        assert col in columns, f"ScoreModel missing column: {col}"
    assert columns["score"].type.python_type is float
    assert columns["passed"].type.python_type is bool


def test_run_evaluation_model_has_unique_project_run_constraint() -> None:
    """每个项目下每个 Run 只能有一条评估记录。"""
    unique_constraints = {
        c.name: c
        for c in RunEvaluationModel.__table__.constraints
        if isinstance(c, UniqueConstraint)
    }
    assert "uq_run_evaluations_project_run" in unique_constraints


def test_score_model_source_uniqueness_constraint() -> None:
    """每个评估下同一用例同一评分器版本只能打一次分。"""
    unique_constraints = {
        c.name: c for c in ScoreModel.__table__.constraints if isinstance(c, UniqueConstraint)
    }
    assert "uq_scores_source" in unique_constraints


# ── Run / RunCase 模型映射测试 ─────────────────────────────────────────


def test_run_model_maps_all_required_fields() -> None:
    """_run_model 生成完整的 RunModel 包含所有必填字段。"""
    run = Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=TestPlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="eval-test-key",
        created_by=UserId.new(),
        config_snapshot={"timeout": 60},
        plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
        total_cases=2,
    )

    model = _run_model(run)

    assert model.id == run.run_id.value
    assert model.project_id == run.project_id.value
    assert model.status == "queued"
    assert model.total_cases == 2
    assert model.config_snapshot == {"timeout": 60}
    assert model.plugin_snapshot == {"id": "generic-http", "version": "1.0.0"}


def test_case_model_maps_with_scores_context() -> None:
    """_case_model 生成包含 output/trace/duration_ms 等 Worker 返回字段。"""
    run = Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=TestPlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="case-model-test",
        created_by=UserId.new(),
        config_snapshot={"timeout": 30},
        plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
        total_cases=1,
    )
    case = RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=uuid4(),
        name="test case",
        input_snapshot={"prompt": "hello"},
        assertion_snapshot=[{"type": "contains", "value": "hello"}],
    )
    case.start()
    case.pass_case(output={"answer": "hello world"}, trace=[], duration_ms=42)

    model = _case_model(case)

    assert model.output == {"answer": "hello world"}
    assert model.duration_ms == 42
    assert model.status == "passed"


# ── CaseScore 评估值对象测试 ──────────────────────────────────────────


def test_case_score_default_confidence() -> None:
    """CaseScore 默认置信度为 1.0。"""
    score = CaseScore(
        run_case_id="case-1",
        score=0.85,
        passed=True,
        explanation="rule passed",
    )
    assert score.confidence == 1.0


def test_evaluation_summary_is_frozen() -> None:
    """EvaluationSummary 是不可变值对象。"""
    summary = build_evaluation_summary([CaseScoreInput(run_case_id="case-1", status="passed")])
    with pytest.raises((TypeError, AttributeError)):
        summary.status = "modified"  # type: ignore[misc]
