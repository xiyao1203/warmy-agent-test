from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GateMetrics:
    critical_success_rate: float
    quality_delta: float
    critical_security_findings: int
    novel_failure_clusters: int
    flake_rate: float
    evidence_completeness: float
    calibrated: bool
    latency_delta: float
    cost_delta: float


@dataclass(frozen=True, slots=True)
class JointGateRule:
    code: str
    status: str
    threshold: str
    actual: str
    reason: str
    evidence_refs: tuple[UUID, ...] = ()

    @property
    def blocking(self) -> bool:
        return self.status == "block"


@dataclass(frozen=True, slots=True)
class JointGateDecision:
    status: str
    rules: tuple[JointGateRule, ...]
    baseline_id: UUID | None = None


class JointGate:
    def evaluate(self, metrics: GateMetrics) -> JointGateDecision:
        rules = (
            _minimum("evidence_completeness", metrics.evidence_completeness, 1.0, block=True),
            _minimum("critical_success_rate", metrics.critical_success_rate, 1.0, block=True),
            _maximum("critical_security", metrics.critical_security_findings, 0, block=True),
            _minimum("quality_delta", metrics.quality_delta, -0.05, block=True),
            _maximum("flake_rate", metrics.flake_rate, 0.05, block=True),
            _maximum("latency_delta", metrics.latency_delta, 0.2, block=False),
            _maximum("cost_delta", metrics.cost_delta, 0.2, block=False),
            _maximum("novel_failure_clusters", metrics.novel_failure_clusters, 0, block=False),
            JointGateRule(
                code="evaluation_calibration",
                status="allow" if metrics.calibrated else "needs_review",
                threshold="calibrated=true",
                actual=f"calibrated={str(metrics.calibrated).lower()}",
                reason="Model evaluation must be calibrated before autonomous release",
            ),
        )
        if any(rule.status == "block" for rule in rules):
            status = "block"
        elif any(rule.status == "needs_review" for rule in rules):
            status = "needs_review"
        else:
            status = "allow"
        return JointGateDecision(status=status, rules=rules)


def _minimum(code: str, actual: float, threshold: float, *, block: bool) -> JointGateRule:
    passed = actual >= threshold
    return JointGateRule(
        code=code,
        status="allow" if passed else ("block" if block else "needs_review"),
        threshold=f">={threshold:g}",
        actual=f"{actual:g}",
        reason=f"{code} must be at least {threshold:g}",
    )


def _maximum(
    code: str, actual: float | int, threshold: float | int, *, block: bool
) -> JointGateRule:
    passed = actual <= threshold
    return JointGateRule(
        code=code,
        status="allow" if passed else ("block" if block else "needs_review"),
        threshold=f"<={threshold:g}",
        actual=f"{actual:g}",
        reason=f"{code} must not exceed {threshold:g}",
    )
