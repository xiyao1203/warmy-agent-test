from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agenttest.modules.gates.domain.entities import GateResult, ReleaseGate


@dataclass(frozen=True, slots=True)
class GateEvidence:
    run_id: UUID
    pass_rate: float | None
    critical_passed: bool
    total_cost: float | None
    security_score: float | None
    pending_reviews: int
    blocking_findings: int = 0


def evaluate_evidence(gate: ReleaseGate, evidence: GateEvidence) -> GateResult:
    if evidence.pass_rate is None:
        result = gate.evaluate(
            actual_pass_rate=0,
            critical_passed=evidence.critical_passed,
            actual_cost=evidence.total_cost,
            security_score=evidence.security_score,
        )
        result.failures.insert(0, "执行尚未产生可用评测")
    else:
        result = gate.evaluate(
            actual_pass_rate=evidence.pass_rate,
            critical_passed=evidence.critical_passed,
            actual_cost=evidence.total_cost,
            security_score=evidence.security_score,
        )
    if evidence.security_score is None:
        result.failures.append("尚未产生安全测试证据")
    if evidence.pending_reviews > 0:
        result.failures.append(f"仍有 {evidence.pending_reviews} 项人工审核待完成")
    if evidence.blocking_findings > 0:
        result.failures.append(f"存在 {evidence.blocking_findings} 项高危安全发现")
    if result.failures and result.passed:
        return GateResult(
            passed=False,
            failures=result.failures,
            evaluated_at=result.evaluated_at,
        )
    return GateResult(
        passed=not result.failures,
        failures=result.failures,
        evaluated_at=result.evaluated_at,
    )
