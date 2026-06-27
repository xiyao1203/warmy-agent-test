"""Unit tests for ReleaseGate domain entity."""

from __future__ import annotations

from uuid import uuid4

import pytest

from agenttest.modules.gates.domain.entities import (
    GateResult,
    ReleaseGate,
    ReleaseGateId,
)


def test_gate_create_defaults() -> None:
    g = ReleaseGate.create(project_id=uuid4(), name="CI Gate")
    assert g.name == "CI Gate"
    assert g.success_rate_threshold == 0.8
    assert g.security_threshold == 0.8
    assert g.cost_limit is None
    assert g.critical_cases == []
    assert g.enabled is True


def test_gate_requires_name() -> None:
    with pytest.raises(ValueError, match="Gate name is required"):
        ReleaseGate.create(project_id=uuid4(), name="  ")


def test_gate_validates_threshold() -> None:
    with pytest.raises(
        ValueError, match="success_rate_threshold must be between 0 and 1"
    ):
        ReleaseGate.create(project_id=uuid4(), name="Test", success_rate_threshold=1.5)


def test_gate_validates_security_threshold() -> None:
    with pytest.raises(
        ValueError, match="security_threshold must be between 0 and 1"
    ):
        ReleaseGate.create(project_id=uuid4(), name="Test", security_threshold=-0.1)


def test_gate_validates_cost_limit() -> None:
    with pytest.raises(ValueError, match="cost_limit must be non-negative"):
        ReleaseGate.create(project_id=uuid4(), name="Test", cost_limit=-1.0)


def test_gate_evaluate_pass() -> None:
    g = ReleaseGate.create(
        project_id=uuid4(),
        name="CI Gate",
        success_rate_threshold=0.8,
        critical_cases=["case-1"],
        cost_limit=100.0,
        security_threshold=0.7,
    )
    result = g.evaluate(
        actual_pass_rate=0.9,
        critical_passed=True,
        actual_cost=50.0,
        security_score=0.8,
    )
    assert result.passed is True
    assert result.failures == []


def test_gate_evaluate_fail_low_pass_rate() -> None:
    g = ReleaseGate.create(
        project_id=uuid4(), name="Gate", success_rate_threshold=0.8,
    )
    result = g.evaluate(actual_pass_rate=0.5, critical_passed=True)
    assert result.passed is False
    assert any("通过率" in f for f in result.failures)


def test_gate_evaluate_fail_critical() -> None:
    g = ReleaseGate.create(project_id=uuid4(), name="Gate")
    result = g.evaluate(actual_pass_rate=1.0, critical_passed=False)
    assert result.passed is False
    assert any("关键用例" in f for f in result.failures)


def test_gate_evaluate_fail_cost() -> None:
    g = ReleaseGate.create(
        project_id=uuid4(), name="Gate", cost_limit=50.0,
    )
    result = g.evaluate(
        actual_pass_rate=1.0, critical_passed=True, actual_cost=80.0,
    )
    assert result.passed is False
    assert any("成本" in f for f in result.failures)


def test_gate_evaluate_fail_security() -> None:
    g = ReleaseGate.create(
        project_id=uuid4(), name="Gate", security_threshold=0.8,
    )
    result = g.evaluate(
        actual_pass_rate=1.0, critical_passed=True, security_score=0.5,
    )
    assert result.passed is False
    assert any("安全评分" in f for f in result.failures)


def test_gate_toggle() -> None:
    g = ReleaseGate.create(project_id=uuid4(), name="Gate")
    assert g.enabled is True
    g.toggle()
    assert g.enabled is False


def test_gate_result_to_dict() -> None:
    from datetime import UTC, datetime

    r = GateResult(passed=True, failures=[], evaluated_at=datetime.now(UTC))
    d = r.to_dict()
    assert d["passed"] is True
    assert d["failures"] == []
