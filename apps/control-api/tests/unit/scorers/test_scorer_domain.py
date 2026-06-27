"""Unit tests for Scorer domain entities and value objects."""

from __future__ import annotations

from uuid import uuid4

import pytest

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId
from agenttest.modules.scorers.domain.value_objects import ScorerResult, ScorerType


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


# ── Scorer 实体 ───────────────────────────────────────────────────────────


def test_scorer_create_defaults() -> None:
    s = Scorer.create(
        scorer_id=ScorerId.new(),
        project_id=_make_project_id(),
        name="Exact Match",
        scorer_type=ScorerType.RULE,
    )
    assert s.name == "Exact Match"
    assert s.scorer_type is ScorerType.RULE
    assert s.weight == 1.0
    assert s.threshold == 0.8
    assert s.enabled is True
    assert s.config_json == {}


def test_scorer_requires_name() -> None:
    with pytest.raises(ValueError, match="Scorer name is required"):
        Scorer.create(
            scorer_id=ScorerId.new(),
            project_id=_make_project_id(),
            name="  ",
            scorer_type=ScorerType.RULE,
        )


def test_scorer_validates_weight() -> None:
    with pytest.raises(ValueError, match="weight must be between 0 and 10"):
        Scorer.create(
            scorer_id=ScorerId.new(),
            project_id=_make_project_id(),
            name="Test",
            scorer_type=ScorerType.MODEL,
            weight=11.0,
        )


def test_scorer_validates_threshold() -> None:
    with pytest.raises(ValueError, match="threshold must be between 0 and 1"):
        Scorer.create(
            scorer_id=ScorerId.new(),
            project_id=_make_project_id(),
            name="Test",
            scorer_type=ScorerType.MODEL,
            threshold=1.5,
        )


def test_scorer_rename() -> None:
    s = Scorer.create(
        scorer_id=ScorerId.new(),
        project_id=_make_project_id(),
        name="Old Name",
        scorer_type=ScorerType.RULE,
    )
    s.rename("New Name")
    assert s.name == "New Name"


def test_scorer_update_weight() -> None:
    s = Scorer.create(
        scorer_id=ScorerId.new(),
        project_id=_make_project_id(),
        name="Test",
        scorer_type=ScorerType.RULE,
    )
    s.update_weight(5.0)
    assert s.weight == 5.0


def test_scorer_toggle() -> None:
    s = Scorer.create(
        scorer_id=ScorerId.new(),
        project_id=_make_project_id(),
        name="Test",
        scorer_type=ScorerType.RULE,
    )
    assert s.enabled is True
    s.toggle()
    assert s.enabled is False
    s.toggle()
    assert s.enabled is True


def test_scorer_evaluate_score() -> None:
    s = Scorer.create(
        scorer_id=ScorerId.new(),
        project_id=_make_project_id(),
        name="Test",
        scorer_type=ScorerType.RULE,
        threshold=0.7,
    )
    assert s.evaluate_score(0.8) is True
    assert s.evaluate_score(0.7) is True
    assert s.evaluate_score(0.69) is False


# ── ScorerType ────────────────────────────────────────────────────────────


def test_scorer_type_values() -> None:
    assert ScorerType.RULE == "rule"
    assert ScorerType.MODEL == "model"
    assert ScorerType.REFERENCE == "reference"


# ── ScorerResult ──────────────────────────────────────────────────────────


def test_scorer_result_roundtrip() -> None:
    r = ScorerResult(
        score=0.85,
        passed=True,
        explanation="Exact match found",
        evidence="Output matches expected",
        confidence=0.95,
        scorer_version="1.0",
    )
    data = r.to_dict()
    restored = ScorerResult.from_dict(data)
    assert restored.score == 0.85
    assert restored.passed is True
    assert restored.explanation == "Exact match found"
    assert restored.evidence == "Output matches expected"
    assert restored.confidence == 0.95
    assert restored.scorer_version == "1.0"
