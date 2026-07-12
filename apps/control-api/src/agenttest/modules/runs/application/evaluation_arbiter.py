from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationSignal:
    passed: bool
    confidence: float
    calibrated: bool

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("evaluation confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class EvaluationDecision:
    status: str
    source: str
    confidence: float


class EvaluationArbiter:
    def decide(
        self,
        *,
        rule: EvaluationSignal | None,
        domain: EvaluationSignal | None,
        model: EvaluationSignal | None,
    ) -> EvaluationDecision:
        for source, signal in (("rule", rule), ("domain", domain)):
            if signal is not None and not signal.passed:
                return EvaluationDecision("failed", source, signal.confidence)
        if rule is not None and domain is not None and rule.passed and domain.passed:
            return EvaluationDecision(
                "passed", "rule+domain", min(rule.confidence, domain.confidence)
            )
        if model is not None:
            if not model.calibrated:
                return EvaluationDecision("needs_review", "model", model.confidence)
            return EvaluationDecision(
                "passed" if model.passed else "failed", "model", model.confidence
            )
        if rule is not None or domain is not None:
            signal = rule or domain
            assert signal is not None
            return EvaluationDecision(
                "passed" if signal.passed else "failed",
                "rule" if rule else "domain",
                signal.confidence,
            )
        return EvaluationDecision("needs_review", "none", 0.0)
