"""Scorer config validation and trial evaluation tests.

Covers Rule/Reference/Model discriminated configs and trial results.
"""

from __future__ import annotations

import pytest
from agenttest.modules.scorers.application.evaluate import TrialResult, evaluate_deterministic
from agenttest.modules.scorers.domain.config import (
    DeepEvalScorerConfig,
    ModelScorerConfig,
    ReferenceScorerConfig,
    RuleScorerConfig,
    parse_scorer_config,
)
from pydantic import ValidationError

# ── Config parsing ────────────────────────────────────────────────────────


def test_parse_rule_config_rejects_missing_expected() -> None:
    with pytest.raises(ValidationError):
        parse_scorer_config("rule", {"operator": "contains"})


def test_parse_rule_config_accepts_valid() -> None:
    config = parse_scorer_config("rule", {"operator": "contains", "expected": "hello"})
    assert isinstance(config, RuleScorerConfig)
    assert config.operator == "contains"
    assert config.expected == "hello"


def test_parse_reference_config_defaults_operator() -> None:
    config = parse_scorer_config("reference", {})
    assert isinstance(config, ReferenceScorerConfig)
    assert config.operator == "exact"


def test_parse_reference_config_rejects_invalid_operator() -> None:
    with pytest.raises(ValidationError):
        parse_scorer_config("reference", {"operator": "regex"})


def test_parse_model_config_rejects_empty_rubric() -> None:
    with pytest.raises(ValidationError):
        parse_scorer_config("model", {"rubric": ""})


def test_parse_model_config_accepts_valid_rubric() -> None:
    config = parse_scorer_config("model", {"rubric": "Score 1 if correct, 0 otherwise"})
    assert isinstance(config, ModelScorerConfig)
    assert config.rubric == "Score 1 if correct, 0 otherwise"


def test_parse_deepeval_config_accepts_tool_correctness() -> None:
    config = parse_scorer_config(
        "deepeval",
        {"metric": "tool_correctness", "expected_tools": ["create_image_node"]},
    )
    assert isinstance(config, DeepEvalScorerConfig)
    assert config.expected_tools == ["create_image_node"]


def test_parse_scorer_config_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="Unsupported scorer type"):
        parse_scorer_config("unknown", {})


def test_parse_rule_config_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        parse_scorer_config("rule", {"operator": "contains", "expected": "x", "extra": 1})


# ── Deterministic evaluation ──────────────────────────────────────────────


def test_rule_contains_evaluation_passes() -> None:
    config = parse_scorer_config("rule", {"operator": "contains", "expected": "hello"})
    result = evaluate_deterministic(config, output={"message": "hello world"}, reference=None)
    assert result.score == 1.0
    assert result.passed is True
    assert "passed" in result.explanation


def test_rule_contains_evaluation_fails() -> None:
    config = parse_scorer_config("rule", {"operator": "contains", "expected": "xyz"})
    result = evaluate_deterministic(config, output={"message": "hello world"}, reference=None)
    assert result.score == 0.0
    assert result.passed is False
    assert "failed" in result.explanation


def test_rule_exact_evaluation() -> None:
    config = parse_scorer_config("rule", {"operator": "exact", "expected": "hello"})
    passed = evaluate_deterministic(config, output="hello", reference=None)
    assert passed.score == 1.0
    failed = evaluate_deterministic(config, output="hello world", reference=None)
    assert failed.score == 0.0


def test_reference_evaluation_with_reference() -> None:
    config = parse_scorer_config("reference", {"operator": "contains"})
    result = evaluate_deterministic(config, output="hello world", reference="hello")
    assert result.score == 1.0
    assert result.passed is True


def test_reference_evaluation_requires_reference() -> None:
    config = parse_scorer_config("reference", {"operator": "exact"})
    with pytest.raises(ValueError, match="reference"):
        evaluate_deterministic(config, output={"value": "a"}, reference=None)


def test_model_scorer_rejected_by_deterministic_evaluator() -> None:
    config = parse_scorer_config("model", {"rubric": "Score if correct"})
    with pytest.raises(ValueError, match="Model scorer must be executed by ModelJudge"):
        evaluate_deterministic(config, output="any", reference=None)


# ── TrialResult ───────────────────────────────────────────────────────────


def test_trial_result_construction() -> None:
    r = TrialResult(score=0.75, passed=True, explanation="partial match", confidence=0.8)
    assert r.score == 0.75
    assert r.passed is True
    assert r.explanation == "partial match"
    assert r.confidence == 0.8


def test_trial_result_default_confidence() -> None:
    r = TrialResult(score=1.0, passed=True, explanation="ok")
    assert r.confidence == 1.0
