"""验证发布门禁评估的领域模型和数据契约。

覆盖：
- ReleaseGate 实体创建与门禁评估逻辑
- GateResult 值对象
- 门禁的各种失败条件（通过率、关键用例、成本、安全）
- ReleaseGate 模型约束
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.gates.domain.entities import (
    GateResult,
    ReleaseGate,
)
from agenttest.modules.gates.infrastructure.persistence.models import (
    ReleaseDecisionModel,
    ReleaseGateModel,
)

# ── ReleaseGate 实体测试 ──────────────────────────────────────────────


def test_release_gate_create_requires_name() -> None:
    """空名称拒绝创建门禁。"""
    with pytest.raises(ValueError, match="name"):
        ReleaseGate.create(
            project_id=uuid4(),
            name="",
        )


def test_release_gate_create_validates_thresholds() -> None:
    """门禁阈值必须在 0-1 之间。"""
    with pytest.raises(ValueError, match="between 0 and 1"):
        ReleaseGate.create(
            project_id=uuid4(),
            name="invalid gate",
            success_rate_threshold=1.5,
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        ReleaseGate.create(
            project_id=uuid4(),
            name="invalid gate",
            security_threshold=-0.5,
        )


def test_release_gate_create_rejects_negative_cost() -> None:
    """成本限额不可为负。"""
    with pytest.raises(ValueError, match="non-negative"):
        ReleaseGate.create(
            project_id=uuid4(),
            name="invalid cost",
            cost_limit=-100.0,
        )


def test_release_gate_defaults() -> None:
    """门禁创建使用合理的默认值。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="default gate",
    )

    assert gate.success_rate_threshold == 0.8
    assert gate.security_threshold == 0.8
    assert gate.critical_cases == []
    assert gate.cost_limit is None
    assert gate.enabled is True


# ── GateResult 评估测试 ───────────────────────────────────────────────


def test_gate_evaluate_all_passed() -> None:
    """所有指标达标时门禁通过。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="strict gate",
        success_rate_threshold=0.85,
        security_threshold=0.7,
    )

    result = gate.evaluate(
        actual_pass_rate=0.9,
        critical_passed=True,
        security_score=0.85,
    )

    assert result.passed is True
    assert result.failures == []


def test_gate_evaluate_fails_on_low_pass_rate() -> None:
    """通过率低于阈值时门禁失败。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="pass rate gate",
        success_rate_threshold=0.85,
    )

    result = gate.evaluate(
        actual_pass_rate=0.7,
        critical_passed=True,
    )

    assert result.passed is False
    assert any("通过率" in f for f in result.failures)


def test_gate_evaluate_fails_on_critical_cases() -> None:
    """关键用例未通过时门禁失败。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="critical gate",
        critical_cases=["case-1", "case-2"],
    )

    result = gate.evaluate(
        actual_pass_rate=0.95,
        critical_passed=False,
    )

    assert result.passed is False
    assert any("关键用例" in f for f in result.failures)


def test_gate_evaluate_fails_on_cost_limit() -> None:
    """成本超出限额时门禁失败。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="cost gate",
        cost_limit=10.0,
    )

    result = gate.evaluate(
        actual_pass_rate=0.95,
        critical_passed=True,
        actual_cost=25.0,
    )

    assert result.passed is False
    assert any("成本" in f or "cost" in f.lower() for f in result.failures)


def test_gate_evaluate_cost_within_limit_passes() -> None:
    """成本在限额内时不影响通过。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="budget gate",
        cost_limit=100.0,
    )

    result = gate.evaluate(
        actual_pass_rate=0.95,
        critical_passed=True,
        actual_cost=50.0,
    )

    assert result.passed is True


def test_gate_evaluate_fails_on_low_security_score() -> None:
    """安全评分低于阈值时门禁失败。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="security gate",
        security_threshold=0.8,
    )

    result = gate.evaluate(
        actual_pass_rate=0.9,
        critical_passed=True,
        security_score=0.5,
    )

    assert result.passed is False
    assert any("安全评分" in f for f in result.failures)


def test_gate_evaluate_multiple_failures() -> None:
    """多个条件不满足时同时报告所有失败原因。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="multi gate",
        success_rate_threshold=0.9,
        security_threshold=0.8,
        cost_limit=5.0,
    )

    result = gate.evaluate(
        actual_pass_rate=0.6,
        critical_passed=False,
        actual_cost=20.0,
        security_score=0.3,
    )

    assert result.passed is False
    assert len(result.failures) >= 3  # pass rate + critical + cost + security


# ── GateResult 值对象测试 ─────────────────────────────────────────────


def test_gate_result_to_dict_includes_timestamp() -> None:
    """GateResult 序列化包含 ISO 时间戳。"""
    result = GateResult(
        passed=True,
        failures=[],
        evaluated_at=datetime.now(UTC),
    )

    d = result.to_dict()
    assert d["passed"] is True
    assert d["failures"] == []
    assert "evaluated_at" in d


# ── ReleaseGate 开关测试 ─────────────────────────────────────────────


def test_release_gate_toggle() -> None:
    """toggle 切换门禁启用状态。"""
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="toggle gate",
    )
    assert gate.enabled is True

    gate.toggle()
    assert gate.enabled is False

    gate.toggle()
    assert gate.enabled is True


# ── 持久化模型约束测试 ───────────────────────────────────────────────


def test_release_gate_model_has_project_foreign_key() -> None:
    """门禁表强制项目外键。"""
    fk_columns = {fk.parent.name for fk in ReleaseGateModel.__table__.foreign_keys}
    assert "project_id" in fk_columns


def test_release_decision_model_has_project_and_run_fks() -> None:
    """发布决策表关联项目和运行。"""
    fk_columns = {fk.parent.name for fk in ReleaseDecisionModel.__table__.foreign_keys}
    assert "project_id" in fk_columns
    assert "run_id" in fk_columns
