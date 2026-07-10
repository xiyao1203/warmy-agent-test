from uuid import uuid4

from agenttest.modules.gates.application.evaluate import GateEvidence, evaluate_evidence
from agenttest.modules.gates.domain.entities import ReleaseGate


def test_release_gate_uses_server_evidence_and_blocks_pending_reviews() -> None:
    gate = ReleaseGate.create(
        project_id=uuid4(),
        name="production",
        success_rate_threshold=0.8,
        security_threshold=0.9,
        cost_limit=2.0,
    )

    decision = evaluate_evidence(
        gate,
        GateEvidence(
            run_id=uuid4(),
            pass_rate=0.75,
            critical_passed=True,
            total_cost=1.0,
            security_score=0.95,
            pending_reviews=1,
        ),
    )

    assert decision.passed is False
    assert any("通过率" in item for item in decision.failures)
    assert any("人工审核" in item for item in decision.failures)


def test_release_gate_rejects_incomplete_run_evidence() -> None:
    gate = ReleaseGate.create(project_id=uuid4(), name="production")

    decision = evaluate_evidence(
        gate,
        GateEvidence(
            run_id=uuid4(),
            pass_rate=None,
            critical_passed=False,
            total_cost=None,
            security_score=None,
            pending_reviews=0,
        ),
    )

    assert decision.passed is False
    assert "执行尚未产生可用评测" in decision.failures


def test_release_gate_blocks_high_security_findings() -> None:
    gate = ReleaseGate.create(project_id=uuid4(), name="production")

    decision = evaluate_evidence(
        gate,
        GateEvidence(
            run_id=uuid4(),
            pass_rate=1.0,
            critical_passed=True,
            total_cost=0.1,
            security_score=1.0,
            pending_reviews=0,
            blocking_findings=1,
        ),
    )

    assert decision.passed is False
    assert any("高危安全发现" in item for item in decision.failures)
