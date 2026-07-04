"""Unit tests for test plan asset graph config fields.

Covers:
- TestPlanConfig typed asset IDs (scorer_ids, security_profile_ids, etc.)
- observation_only flag and roundtrip
- update_references behaviour
- Version immutability after publish
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.agents.public import AgentVersionId
from agenttest.modules.datasets.public import DatasetVersionId
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.test_plans.domain.entities import (
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from agenttest.modules.test_plans.domain.value_objects import TestPlanConfig


def _make_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("dev@example.com"),
        display_name="Dev",
        role=SystemRole.DEVELOPER,
    )


def _make_draft_version(**kwargs: object) -> TestPlanVersion:
    config = TestPlanConfig(**kwargs)
    return TestPlanVersion.create_draft(
        version_id=TestPlanVersionId(uuid4()),
        test_plan_id=TestPlanId(uuid4()),
        version_number=1,
        config=config,
        created_by=_make_user().user_id,
    )


# ── Observation-only ──────────────────────────────────────────────────────


def test_observation_only_disabled_by_default() -> None:
    cfg = TestPlanConfig()
    assert cfg.observation_only is False


def test_observation_only_config_roundtrip() -> None:
    cfg = TestPlanConfig(observation_only=True)
    assert cfg.observation_only is True
    data = cfg.to_dict()
    assert data["observation_only"] is True
    restored = TestPlanConfig.from_dict(data)
    assert restored.observation_only is True


# ── Scorer IDs ────────────────────────────────────────────────────────────


def test_scorer_ids_default_empty() -> None:
    cfg = TestPlanConfig()
    assert cfg.scorer_ids == []


def test_scorer_ids_preserved() -> None:
    cfg = TestPlanConfig(scorer_ids=["scorer-1", "scorer-2"])
    assert cfg.scorer_ids == ["scorer-1", "scorer-2"]
    data = cfg.to_dict()
    assert data["scorer_ids"] == ["scorer-1", "scorer-2"]
    restored = TestPlanConfig.from_dict(data)
    assert restored.scorer_ids == ["scorer-1", "scorer-2"]


# ── Security profile IDs ──────────────────────────────────────────────────


def test_security_profile_ids_default_empty() -> None:
    cfg = TestPlanConfig()
    assert cfg.security_profile_ids == []


def test_security_profile_ids_preserved() -> None:
    cfg = TestPlanConfig(security_profile_ids=["sec-1"])
    assert cfg.security_profile_ids == ["sec-1"]
    data = cfg.to_dict()
    assert data["security_profile_ids"] == ["sec-1"]


# ── Review policy and release gate IDs ────────────────────────────────────


def test_review_policy_id_default_none() -> None:
    cfg = TestPlanConfig()
    assert cfg.review_policy_id is None


def test_review_policy_id_roundtrip() -> None:
    cfg = TestPlanConfig(review_policy_id="review-abc")
    assert cfg.review_policy_id == "review-abc"
    data = cfg.to_dict()
    assert data["review_policy_id"] == "review-abc"
    restored = TestPlanConfig.from_dict(data)
    assert restored.review_policy_id == "review-abc"


def test_release_gate_id_default_none() -> None:
    cfg = TestPlanConfig()
    assert cfg.release_gate_id is None


def test_release_gate_id_roundtrip() -> None:
    cfg = TestPlanConfig(release_gate_id="gate-xyz")
    assert cfg.release_gate_id == "gate-xyz"
    data = cfg.to_dict()
    assert data["release_gate_id"] == "gate-xyz"


# ── Version update_references ─────────────────────────────────────────────


def test_update_references_partial() -> None:
    """update_references only changes provided fields."""
    version = _make_draft_version()
    agent_id = AgentVersionId(uuid4())
    version.update_references(agent_version_id=agent_id)
    assert version.agent_version_id == agent_id
    assert version.dataset_version_id is None


def test_update_references_all_fields() -> None:
    """update_references can set all three references at once."""
    version = _make_draft_version()
    agent_id = AgentVersionId(uuid4())
    dataset_id = DatasetVersionId(uuid4())
    from agenttest.modules.test_plans.domain.entities import EnvironmentTemplateId

    env_id = EnvironmentTemplateId(uuid4())
    version.update_references(
        agent_version_id=agent_id,
        dataset_version_id=dataset_id,
        environment_template_id=env_id,
    )
    assert version.agent_version_id == agent_id
    assert version.dataset_version_id == dataset_id
    assert version.environment_template_id == env_id


def test_cannot_update_published_version_references() -> None:
    """Published versions reject reference updates."""
    version = _make_draft_version()
    version.publish()
    with pytest.raises(ValueError, match="Cannot modify a published version"):
        version.update_references(agent_version_id=AgentVersionId(uuid4()))


def test_cannot_update_published_version_config() -> None:
    """Published versions reject config updates."""
    version = _make_draft_version()
    version.publish()
    with pytest.raises(ValueError, match="Cannot modify a published version"):
        version.update_config(TestPlanConfig(timeout=999))


# ── Config with all asset IDs ─────────────────────────────────────────────


def test_config_full_asset_graph_roundtrip() -> None:
    """All typed asset IDs survive serialization roundtrip."""
    cfg = TestPlanConfig(
        scorer_ids=["s1", "s2"],
        security_profile_ids=["sec-1"],
        review_policy_id="rev-1",
        release_gate_id="gate-1",
        observation_only=False,
        baseline_run_id="run-baseline",
    )
    data = cfg.to_dict()
    restored = TestPlanConfig.from_dict(data)
    assert restored.scorer_ids == ["s1", "s2"]
    assert restored.security_profile_ids == ["sec-1"]
    assert restored.review_policy_id == "rev-1"
    assert restored.release_gate_id == "gate-1"
    assert restored.observation_only is False
    assert restored.baseline_run_id == "run-baseline"
