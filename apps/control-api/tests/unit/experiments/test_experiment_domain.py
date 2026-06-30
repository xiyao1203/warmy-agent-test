"""Unit tests for Experiment domain entities."""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.experiments.domain.entities import (
    CaseComparison,
    Experiment,
    ExperimentId,
    ExperimentStatus,
    ExperimentSummary,
)
from agenttest.modules.projects.public import ProjectId


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


def test_experiment_create() -> None:
    run_a = uuid4()
    run_b = uuid4()
    e = Experiment.create(
        experiment_id=ExperimentId.new(),
        project_id=_make_project_id(),
        name="A/B Test 1",
        run_a_id=run_a,
        run_b_id=run_b,
    )
    assert e.name == "A/B Test 1"
    assert e.status is ExperimentStatus.PENDING
    assert e.run_a_id == run_a
    assert e.run_b_id == run_b
    assert e.result_json == {}


def test_experiment_requires_name() -> None:
    with pytest.raises(ValueError, match="Experiment name is required"):
        Experiment.create(
            experiment_id=ExperimentId.new(),
            project_id=_make_project_id(),
            name="  ",
            run_a_id=uuid4(),
            run_b_id=uuid4(),
        )


def test_experiment_requires_different_runs() -> None:
    same_id = uuid4()
    with pytest.raises(ValueError, match="must be different"):
        Experiment.create(
            experiment_id=ExperimentId.new(),
            project_id=_make_project_id(),
            name="Test",
            run_a_id=same_id,
            run_b_id=same_id,
        )


def test_experiment_complete() -> None:
    e = Experiment.create(
        experiment_id=ExperimentId.new(),
        project_id=_make_project_id(),
        name="Test",
        run_a_id=uuid4(),
        run_b_id=uuid4(),
    )
    result = {"summary": {"total": 10, "improved": 3}}
    e.complete(result)
    assert e.status is ExperimentStatus.COMPLETED
    assert e.result_json == result


def test_experiment_fail() -> None:
    e = Experiment.create(
        experiment_id=ExperimentId.new(),
        project_id=_make_project_id(),
        name="Test",
        run_a_id=uuid4(),
        run_b_id=uuid4(),
    )
    e.fail("Connection error")
    assert e.status is ExperimentStatus.FAILED
    assert e.result_json == {"error": "Connection error"}


def test_experiment_status_values() -> None:
    assert ExperimentStatus.PENDING == "pending"
    assert ExperimentStatus.RUNNING == "running"
    assert ExperimentStatus.COMPLETED == "completed"
    assert ExperimentStatus.FAILED == "failed"


def test_case_comparison_create() -> None:
    c = CaseComparison(
        test_case_id="case-1",
        status_a="passed",
        status_b="failed",
        status_changed=True,
        duration_delta_ms=500,
        category="degraded",
    )
    assert c.status_changed is True
    assert c.category == "degraded"


def test_experiment_summary_to_dict() -> None:
    s = ExperimentSummary(
        total_cases=10,
        improved=3,
        degraded=1,
        unchanged=6,
        avg_duration_delta_ms=-120.5,
        p50_duration_delta_ms=-100.0,
        p95_duration_delta_ms=-250.0,
        avg_score_delta=0.05,
        variance_score_delta=0.01,
    )
    d = s.to_dict()
    assert d["total_cases"] == 10
    assert d["improved"] == 3
    assert d["degraded"] == 1
    assert d["unchanged"] == 6
    assert d["avg_duration_delta_ms"] == -120.5
    assert d["avg_score_delta"] == 0.05
