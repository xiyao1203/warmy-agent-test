"""Deterministic scorer activities executed inside the API Runner Worker.

Model scorers are NOT evaluated here—they must be submitted to Model Runner
as a separate Activity or via the Control API callback chain.
"""

from __future__ import annotations

from dataclasses import dataclass

from temporalio import activity


@dataclass(frozen=True, slots=True)
class ScoreTask:
    run_case_id: str
    scorer_version_id: str
    scorer_type: str
    config: dict[str, object]
    output: dict[str, object]
    reference: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ScoreResult:
    scorer_version_id: str
    scorer_type: str
    score: float
    passed: bool
    explanation: str
    confidence: float = 1.0


@activity.defn
async def evaluate_deterministic_scorer(task: ScoreTask) -> ScoreResult:
    """Evaluate a single Rule or Reference scorer against case output.

    Model scorers MUST be routed to Model Runner separately.
    """
    activity.heartbeat({"run_case_id": task.run_case_id, "phase": "score"})
    if task.scorer_type == "rule":
        return _evaluate_rule(task)
    if task.scorer_type == "reference":
        return _evaluate_reference(task)
    raise ValueError(f"Deterministic scorer cannot evaluate type: {task.scorer_type}")


def evaluate_scorers_sync(
    scorer_configs: list[dict[str, object]],
    output: dict[str, object],
    *,
    reference: dict[str, object] | None = None,
) -> list[ScoreResult]:
    """Synchronous helper for running all deterministic scorers at once."""
    results: list[ScoreResult] = []
    for cfg in scorer_configs:
        scorer_type = str(cfg.get("scorer_type", ""))
        if scorer_type not in {"rule", "reference"}:
            continue
        raw_config = cfg.get("config", {})
        config = dict(raw_config) if isinstance(raw_config, dict) else {}
        task = ScoreTask(
            run_case_id="",
            scorer_version_id=str(cfg.get("scorer_version_id", "")),
            scorer_type=scorer_type,
            config=config,
            output=output,
            reference=reference,
        )
        if scorer_type == "rule":
            results.append(_evaluate_rule(task))
        elif scorer_type == "reference":
            results.append(_evaluate_reference(task))
    return results


def _evaluate_rule(task: ScoreTask) -> ScoreResult:
    operator = task.config.get("operator", "contains")
    expected = task.config.get("expected")
    rendered = str(task.output)
    if operator == "exact":
        passed = task.output == expected
    else:
        passed = str(expected) in rendered
    return ScoreResult(
        scorer_version_id=task.scorer_version_id,
        scorer_type="rule",
        score=1.0 if passed else 0.0,
        passed=passed,
        explanation=f"rule {operator} {'passed' if passed else 'failed'}",
    )


def _evaluate_reference(task: ScoreTask) -> ScoreResult:
    if task.reference is None:
        return ScoreResult(
            scorer_version_id=task.scorer_version_id,
            scorer_type="reference",
            score=0.0,
            passed=False,
            explanation="reference scorer requires reference output",
        )
    operator = task.config.get("operator", "exact")
    if operator == "exact":
        passed = task.output == task.reference
    else:
        passed = str(task.reference) in str(task.output)
    return ScoreResult(
        scorer_version_id=task.scorer_version_id,
        scorer_type="reference",
        score=1.0 if passed else 0.0,
        passed=passed,
        explanation=f"reference {operator} {'passed' if passed else 'failed'}",
    )
