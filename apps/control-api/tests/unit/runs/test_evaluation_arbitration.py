from agenttest.modules.runs.application.evaluation_arbiter import (
    EvaluationArbiter,
    EvaluationSignal,
)


def test_uncalibrated_model_failure_requires_review() -> None:
    decision = EvaluationArbiter().decide(
        rule=None,
        domain=None,
        model=EvaluationSignal(passed=False, confidence=0.9, calibrated=False),
    )
    assert decision.status == "needs_review"


def test_hard_rule_failure_has_precedence_over_model_pass() -> None:
    decision = EvaluationArbiter().decide(
        rule=EvaluationSignal(passed=False, confidence=1.0, calibrated=True),
        domain=None,
        model=EvaluationSignal(passed=True, confidence=0.99, calibrated=True),
    )
    assert decision.status == "failed"
    assert decision.source == "rule"
