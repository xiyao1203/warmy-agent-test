from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CaseScoreInput:
    run_case_id: str
    status: str


@dataclass(frozen=True, slots=True)
class CaseScore:
    run_case_id: str
    score: float
    passed: bool
    explanation: str
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    status: str
    aggregate_score: float
    pass_rate: float
    scores: list[CaseScore]


def build_evaluation_summary(cases: list[CaseScoreInput]) -> EvaluationSummary:
    if not cases:
        raise ValueError("Evaluation requires at least one case")
    scores = [
        CaseScore(
            run_case_id=item.run_case_id,
            score=1.0 if item.status == "passed" else 0.0,
            passed=item.status == "passed",
            explanation=f"Run case completed with status: {item.status}",
        )
        for item in cases
    ]
    aggregate = sum(item.score for item in scores) / len(scores)
    return EvaluationSummary(
        status="completed",
        aggregate_score=aggregate,
        pass_rate=aggregate,
        scores=scores,
    )
