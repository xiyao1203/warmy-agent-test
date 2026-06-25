"""Unit tests for test plan domain entities and value objects."""

from __future__ import annotations

from uuid import uuid4

import pytest

from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_plans.domain.entities import (
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from agenttest.modules.test_plans.domain.value_objects import (
    TestPlanConfig,
    VersionStatus,
)


def _make_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("dev@example.com"),
        display_name="Dev",
        role=SystemRole.DEVELOPER,
    )


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


# ── TestPlanConfig ─────────────────────────────────────────────────────────


def test_config_defaults() -> None:
    cfg = TestPlanConfig()
    assert cfg.runs_per_case == 1
    assert cfg.concurrency == 1
    assert cfg.timeout == 300
    assert cfg.pass_threshold == 1.0
    assert cfg.cost_budget is None


def test_config_validates_runs_per_case() -> None:
    with pytest.raises(ValueError, match="runs_per_case must be >= 1"):
        TestPlanConfig(runs_per_case=0)


def test_config_validates_concurrency() -> None:
    with pytest.raises(ValueError, match="concurrency must be >= 1"):
        TestPlanConfig(concurrency=0)


def test_config_validates_timeout() -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        TestPlanConfig(timeout=0)


def test_config_validates_pass_threshold() -> None:
    with pytest.raises(ValueError, match="pass_threshold must be between 0 and 1"):
        TestPlanConfig(pass_threshold=1.5)

    with pytest.raises(ValueError, match="pass_threshold must be between 0 and 1"):
        TestPlanConfig(pass_threshold=-0.1)


def test_config_validates_cost_budget() -> None:
    with pytest.raises(ValueError, match="cost_budget must be non-negative"):
        TestPlanConfig(cost_budget=-1.0)


def test_config_roundtrip() -> None:
    cfg = TestPlanConfig(
        api_browser_ratio=0.5,
        runs_per_case=3,
        concurrency=2,
        timeout=600,
        retry_policy={"max_retries": 3},
        scorers=[{"name": "exact"}],
        pass_threshold=0.8,
        cost_budget=50.0,
    )
    data = cfg.to_dict()
    restored = TestPlanConfig.from_dict(data)
    assert restored.api_browser_ratio == 0.5
    assert restored.runs_per_case == 3
    assert restored.concurrency == 2
    assert restored.timeout == 600
    assert restored.retry_policy == {"max_retries": 3}
    assert restored.scorers == [{"name": "exact"}]
    assert restored.pass_threshold == 0.8
    assert restored.cost_budget == 50.0


# ── TestPlan ───────────────────────────────────────────────────────────────


def test_plan_requires_name() -> None:
    with pytest.raises(ValueError, match="Test plan name is required"):
        TestPlan.create(
            test_plan_id=TestPlanId(uuid4()),
            project_id=_make_project_id(),
            name="  ",
            created_by=_make_user().user_id,
        )


def test_plan_create_and_rename() -> None:
    plan = TestPlan.create(
        test_plan_id=TestPlanId(uuid4()),
        project_id=_make_project_id(),
        name="My Plan",
        created_by=_make_user().user_id,
    )
    assert plan.name == "My Plan"
    plan.rename("Updated Plan")
    assert plan.name == "Updated Plan"


# ── TestPlanVersion ────────────────────────────────────────────────────────


def test_version_starts_draft() -> None:
    version = TestPlanVersion.create_draft(
        version_id=TestPlanVersionId(uuid4()),
        test_plan_id=TestPlanId(uuid4()),
        version_number=1,
        config=TestPlanConfig(),
        created_by=_make_user().user_id,
    )
    assert version.is_editable is True
    assert version.status is VersionStatus.DRAFT


def test_version_publish() -> None:
    version = TestPlanVersion.create_draft(
        version_id=TestPlanVersionId(uuid4()),
        test_plan_id=TestPlanId(uuid4()),
        version_number=1,
        config=TestPlanConfig(),
        created_by=_make_user().user_id,
    )
    version.publish()
    assert version.is_published is True
    assert version.is_editable is False

    with pytest.raises(ValueError, match="already published"):
        version.publish()


def test_version_update_config() -> None:
    version = TestPlanVersion.create_draft(
        version_id=TestPlanVersionId(uuid4()),
        test_plan_id=TestPlanId(uuid4()),
        version_number=1,
        config=TestPlanConfig(timeout=100),
        created_by=_make_user().user_id,
    )
    new_cfg = TestPlanConfig(timeout=200)
    version.update_config(new_cfg)
    assert version.config.timeout == 200


def test_cannot_update_published_version() -> None:
    version = TestPlanVersion.create_draft(
        version_id=TestPlanVersionId(uuid4()),
        test_plan_id=TestPlanId(uuid4()),
        version_number=1,
        config=TestPlanConfig(),
        created_by=_make_user().user_id,
    )
    version.publish()
    with pytest.raises(ValueError, match="Cannot modify a published version"):
        version.update_config(TestPlanConfig(timeout=999))
