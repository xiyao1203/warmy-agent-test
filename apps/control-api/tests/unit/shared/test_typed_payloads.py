from pathlib import Path
from uuid import uuid4

import pytest
from agenttest.modules.reviews.domain.auto_collector import AutoCollector
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    _parse_float,
    _parse_optional_uuid,
    _parse_required_uuid,
)
from agenttest.modules.test_plans.domain.value_objects import TestPlanConfig


@pytest.mark.parametrize(
    "payload",
    [
        {"confidence": "high"},
        {"is_high_risk": "yes"},
        {"has_security_findings": 1},
        {"scores": []},
        {"scores": {"judge": "excellent"}},
    ],
)
def test_review_payload_rejects_wrong_business_types(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="review result"):
        AutoCollector().should_collect(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"retry_policy": []},
        {"scorers": {}},
        {"release_gate": []},
        {"scorer_ids": {}},
    ],
)
def test_test_plan_config_rejects_wrong_container_types(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="test plan config"):
        TestPlanConfig.from_dict(payload)


def test_run_score_parsers_reject_wrong_types() -> None:
    with pytest.raises(ValueError, match="score"):
        _parse_float({"unexpected": True}, field="score", default=0.0)
    with pytest.raises(ValueError, match="run_case_id"):
        _parse_required_uuid([], field="run_case_id")
    with pytest.raises(ValueError, match="scorer_version_id"):
        _parse_optional_uuid({}, field="scorer_version_id")


def test_run_score_parsers_keep_valid_values() -> None:
    value = uuid4()

    assert _parse_float("0.75", field="score", default=0.0) == 0.75
    assert _parse_required_uuid(str(value), field="run_case_id") == value
    assert _parse_optional_uuid(None, field="scorer_version_id") is None


def test_touched_business_boundaries_have_no_type_ignores() -> None:
    paths = [
        Path("apps/control-api/src/agenttest/modules/reviews/domain/auto_collector.py"),
        Path(
            "apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py"
        ),
        Path("apps/control-api/src/agenttest/modules/test_plans/domain/value_objects.py"),
    ]

    violations = [
        f"{path}:{line_number}"
        for path in paths
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if "type: ignore" in line
    ]

    assert violations == []
