import pytest
from agenttest.modules.scorers.application.evaluate import evaluate_deterministic
from agenttest.modules.scorers.domain.config import parse_scorer_config
from pydantic import ValidationError


def test_rule_scorer_config_and_trial() -> None:
    config = parse_scorer_config("rule", {"operator": "contains", "expected": "hello"})
    result = evaluate_deterministic(config, output={"message": "hello world"}, reference=None)
    assert result.score == 1.0
    assert result.passed is True


def test_reference_scorer_requires_reference_at_trial_time() -> None:
    config = parse_scorer_config("reference", {"operator": "exact"})
    with pytest.raises(ValueError, match="reference"):
        evaluate_deterministic(config, output={"value": "a"}, reference=None)


def test_model_scorer_requires_real_rubric() -> None:
    with pytest.raises(ValidationError):
        parse_scorer_config("model", {"rubric": ""})
