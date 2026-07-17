from __future__ import annotations

from dataclasses import dataclass

from agenttest.modules.scorers.application.config import (
    DeepEvalScorerConfig,
    ModelScorerConfig,
    ReferenceScorerConfig,
    RuleScorerConfig,
    ScorerConfig,
)


@dataclass(frozen=True, slots=True)
class TrialResult:
    score: float
    passed: bool
    explanation: str
    confidence: float = 1.0


def evaluate_deterministic(
    config: ScorerConfig,
    *,
    output: object,
    reference: object | None,
) -> TrialResult:
    if isinstance(config, ModelScorerConfig):
        raise ValueError("Model scorer must be executed by ModelJudge")
    if isinstance(config, DeepEvalScorerConfig):
        raise ValueError("DeepEval scorer must be executed by its runtime adapter")
    expected = config.expected if isinstance(config, RuleScorerConfig) else reference
    if isinstance(config, ReferenceScorerConfig) and reference is None:
        raise ValueError("reference is required")
    operator = config.operator
    passed = output == expected if operator == "exact" else str(expected) in str(output)
    return TrialResult(
        score=1.0 if passed else 0.0,
        passed=passed,
        explanation=f"{operator} comparison {'passed' if passed else 'failed'}",
    )
