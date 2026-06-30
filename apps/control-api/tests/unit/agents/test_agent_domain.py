"""Unit tests for agent domain entities and value objects."""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.agents.domain.entities import (
    Agent,
    AgentId,
    AgentVersion,
    AgentVersionId,
)
from agenttest.modules.agents.domain.value_objects import (
    AgentConfig,
    AgentType,
    VersionStatus,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId

# ── Helpers ────────────────────────────────────────────────────────────────


def _make_user(role: SystemRole = SystemRole.DEVELOPER) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("dev@example.com"),
        display_name="Dev",
        role=role,
    )


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


def _make_agent_id() -> AgentId:
    return AgentId(uuid4())


def _make_version_id() -> AgentVersionId:
    return AgentVersionId(uuid4())


def _make_config(api_url: str = "https://api.example.com/v1") -> AgentConfig:
    return AgentConfig(api_url=api_url)


# ── AgentConfig ─────────────────────────────────────────────────────────────


def test_config_requires_api_url() -> None:
    with pytest.raises(ValueError, match="api_url is required"):
        AgentConfig(api_url="")

    with pytest.raises(ValueError, match="api_url must be a valid URL"):
        AgentConfig(api_url="not-a-url")


def test_config_validates_timeout_positive() -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        AgentConfig(api_url="https://api.example.com", timeout=0)

    with pytest.raises(ValueError, match="timeout must be positive"):
        AgentConfig(api_url="https://api.example.com", timeout=-5)


def test_config_validates_max_steps_positive() -> None:
    with pytest.raises(ValueError, match="max_steps must be positive"):
        AgentConfig(api_url="https://api.example.com", max_steps=0)


def test_config_validates_cost_limit_non_negative() -> None:
    with pytest.raises(ValueError, match="cost_limit must be non-negative"):
        AgentConfig(api_url="https://api.example.com", cost_limit=-1.0)

    # zero is allowed
    cfg = AgentConfig(api_url="https://api.example.com", cost_limit=0)
    assert cfg.cost_limit == 0


def test_config_roundtrip() -> None:
    original = AgentConfig(
        api_url="https://api.example.com/v1",
        code_version="1.2.3",
        git_commit="abc123",
        model="gpt-4",
        model_params={"temperature": 0.7},
        system_prompt="You are helpful.",
        tools=[{"name": "search", "description": "Search the web"}],
        timeout=60,
        max_steps=10,
        cost_limit=5.0,
    )
    data = original.to_dict()
    restored = AgentConfig.from_dict(data)
    assert restored.api_url == original.api_url
    assert restored.code_version == original.code_version
    assert restored.git_commit == original.git_commit
    assert restored.model == original.model
    assert restored.model_params == original.model_params
    assert restored.system_prompt == original.system_prompt
    assert restored.tools == original.tools
    assert restored.timeout == original.timeout
    assert restored.max_steps == original.max_steps
    assert restored.cost_limit == original.cost_limit


def test_config_defaults() -> None:
    cfg = AgentConfig(api_url="https://api.example.com")
    assert cfg.timeout == 30
    assert cfg.model_params == {}
    assert cfg.tools == []
    assert cfg.max_steps is None
    assert cfg.cost_limit is None


# ── Agent ───────────────────────────────────────────────────────────────────


def test_agent_create_requires_name() -> None:
    with pytest.raises(ValueError, match="Agent name is required"):
        Agent.create(
            agent_id=_make_agent_id(),
            project_id=_make_project_id(),
            name="  ",
            agent_type=AgentType.GENERIC_HTTP,
            created_by=_make_user().user_id,
        )


def test_agent_belongs_to_project() -> None:
    project_id = _make_project_id()
    agent = Agent.create(
        agent_id=_make_agent_id(),
        project_id=project_id,
        name="My Agent",
        agent_type=AgentType.GENERIC_HTTP,
        created_by=_make_user().user_id,
    )
    assert agent.project_id == project_id
    assert agent.name == "My Agent"
    assert agent.agent_type is AgentType.GENERIC_HTTP


def test_agent_rename() -> None:
    agent = Agent.create(
        agent_id=_make_agent_id(),
        project_id=_make_project_id(),
        name="Old Name",
        agent_type=AgentType.CANVAS,
        created_by=_make_user().user_id,
    )
    agent.rename("New Name")
    assert agent.name == "New Name"


def test_agent_rename_rejects_empty() -> None:
    agent = Agent.create(
        agent_id=_make_agent_id(),
        project_id=_make_project_id(),
        name="Old Name",
        agent_type=AgentType.CANVAS,
        created_by=_make_user().user_id,
    )
    with pytest.raises(ValueError, match="Agent name is required"):
        agent.rename("")


def test_agent_update_description() -> None:
    agent = Agent.create(
        agent_id=_make_agent_id(),
        project_id=_make_project_id(),
        name="Test Agent",
        agent_type=AgentType.GENERIC_HTTP,
        created_by=_make_user().user_id,
    )
    agent.update_description("A new description")
    assert agent.description == "A new description"


# ── AgentVersion ────────────────────────────────────────────────────────────


def test_version_starts_as_draft() -> None:
    version = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=1,
        config=_make_config(),
        created_by=_make_user().user_id,
    )
    assert version.status is VersionStatus.DRAFT
    assert version.is_editable is True
    assert version.is_published is False
    assert version.published_at is None


def test_version_number_must_be_positive() -> None:
    with pytest.raises(ValueError, match="version_number must be >= 1"):
        AgentVersion.create_draft(
            version_id=_make_version_id(),
            agent_id=_make_agent_id(),
            version_number=0,
            config=_make_config(),
            created_by=_make_user().user_id,
        )


def test_publish_transitions_to_published() -> None:
    version = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=1,
        config=_make_config(),
        created_by=_make_user().user_id,
    )
    version.publish()
    assert version.status is VersionStatus.PUBLISHED
    assert version.is_published is True
    assert version.is_editable is False
    assert version.published_at is not None


def test_publish_already_published_raises() -> None:
    version = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=1,
        config=_make_config(),
        created_by=_make_user().user_id,
    )
    version.publish()
    with pytest.raises(ValueError, match="already published"):
        version.publish()


def test_cannot_modify_published_version() -> None:
    version = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=1,
        config=_make_config(),
        created_by=_make_user().user_id,
    )
    version.publish()
    with pytest.raises(ValueError, match="Cannot modify a published version"):
        version.update_config(_make_config(api_url="https://new.example.com"))


def test_update_draft_config() -> None:
    version = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=1,
        config=_make_config(),
        created_by=_make_user().user_id,
    )
    new_config = AgentConfig(api_url="https://updated.example.com", timeout=120)
    version.update_config(new_config)
    assert version.config.api_url == "https://updated.example.com"
    assert version.config.timeout == 120


def test_create_new_version_from_published() -> None:
    source = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=1,
        config=AgentConfig(api_url="https://source.example.com", timeout=90),
        created_by=_make_user().user_id,
    )
    source.publish()

    new_version = AgentVersion.create_new_version_from(
        version_id=_make_version_id(),
        source=source,
        new_version_number=2,
    )
    assert new_version.status is VersionStatus.DRAFT
    assert new_version.version_number == 2
    assert new_version.agent_id == source.agent_id
    assert new_version.config.api_url == "https://source.example.com"
    assert new_version.config.timeout == 90


def test_create_new_version_from_draft_raises() -> None:
    source = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=1,
        config=_make_config(),
        created_by=_make_user().user_id,
    )
    with pytest.raises(ValueError, match="Can only create a new version from a published version"):
        AgentVersion.create_new_version_from(
            version_id=_make_version_id(),
            source=source,
            new_version_number=2,
        )


def test_agent_version_ref() -> None:
    from agenttest.modules.agents.public import AgentVersionRef

    version = AgentVersion.create_draft(
        version_id=_make_version_id(),
        agent_id=_make_agent_id(),
        version_number=3,
        config=_make_config(),
        created_by=_make_user().user_id,
    )
    ref = AgentVersionRef.from_version(version)
    assert ref.agent_version_id == version.version_id
    assert ref.agent_id == version.agent_id
    assert ref.version_number == 3


# ── AgentType ───────────────────────────────────────────────────────────────


def test_agent_type_values() -> None:
    assert AgentType.GENERIC_HTTP == "generic_http"
    assert AgentType.CANVAS == "canvas"


def test_version_status_values() -> None:
    assert VersionStatus.DRAFT == "draft"
    assert VersionStatus.PUBLISHED == "published"
