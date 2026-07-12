from agenttest.modules.gates.application.joint_gate import GateMetrics, JointGate


def passing_metrics(**overrides: object) -> GateMetrics:
    values: dict[str, object] = {
        "critical_success_rate": 1.0,
        "quality_delta": 0.0,
        "critical_security_findings": 0,
        "novel_failure_clusters": 0,
        "flake_rate": 0.0,
        "evidence_completeness": 1.0,
        "calibrated": True,
        "latency_delta": 0.0,
        "cost_delta": 0.0,
    }
    values.update(overrides)
    return GateMetrics(**values)  # type: ignore[arg-type]


def test_high_quality_cannot_offset_critical_security_finding() -> None:
    decision = JointGate().evaluate(
        passing_metrics(quality_delta=0.5, critical_security_findings=1)
    )
    assert decision.status == "block"
    assert "critical_security" in {rule.code for rule in decision.rules if rule.blocking}


def test_incomplete_evidence_blocks_release() -> None:
    decision = JointGate().evaluate(passing_metrics(evidence_completeness=0.99))
    assert decision.status == "block"
    assert decision.rules[0].evidence_refs == ()


def test_uncalibrated_evaluation_requires_review_when_hard_gates_pass() -> None:
    decision = JointGate().evaluate(passing_metrics(calibrated=False))
    assert decision.status == "needs_review"


def test_all_rules_explain_threshold_and_actual_value() -> None:
    decision = JointGate().evaluate(passing_metrics())
    assert decision.status == "allow"
    assert all(rule.threshold and rule.actual for rule in decision.rules)
