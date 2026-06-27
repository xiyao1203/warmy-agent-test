"""Unit tests for environment template domain entities."""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId


def _make_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("dev@example.com"),
        display_name="Dev",
        role=SystemRole.DEVELOPER,
    )


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


def test_template_requires_name() -> None:
    with pytest.raises(ValueError, match="Environment template name is required"):
        EnvironmentTemplate.create(
            template_id=EnvironmentTemplateId(uuid4()),
            project_id=_make_project_id(),
            name="  ",
            template_type=TemplateType.BLANK,
            created_by=_make_user().user_id,
        )


def test_template_create_blank() -> None:
    tpl = EnvironmentTemplate.create(
        template_id=EnvironmentTemplateId(uuid4()),
        project_id=_make_project_id(),
        name="Blank Env",
        template_type=TemplateType.BLANK,
        created_by=_make_user().user_id,
    )
    assert tpl.name == "Blank Env"
    assert tpl.template_type is TemplateType.BLANK
    assert tpl.config == {}


def test_template_create_preset() -> None:
    config = {"initial_state": {"key": "val"}, "mock_services": ["auth"]}
    tpl = EnvironmentTemplate.create(
        template_id=EnvironmentTemplateId(uuid4()),
        project_id=_make_project_id(),
        name="Preset Env",
        template_type=TemplateType.PRESET,
        created_by=_make_user().user_id,
        config=config,
        description="A preset environment",
    )
    assert tpl.template_type is TemplateType.PRESET
    assert tpl.config == config
    assert tpl.description == "A preset environment"


def test_template_rename() -> None:
    tpl = EnvironmentTemplate.create(
        template_id=EnvironmentTemplateId(uuid4()),
        project_id=_make_project_id(),
        name="Old",
        template_type=TemplateType.BLANK,
        created_by=_make_user().user_id,
    )
    tpl.rename("New")
    assert tpl.name == "New"


def test_template_update_config() -> None:
    tpl = EnvironmentTemplate.create(
        template_id=EnvironmentTemplateId(uuid4()),
        project_id=_make_project_id(),
        name="Test",
        template_type=TemplateType.PRESET,
        created_by=_make_user().user_id,
    )
    tpl.update_config({"updated": True})
    assert tpl.config == {"updated": True}
