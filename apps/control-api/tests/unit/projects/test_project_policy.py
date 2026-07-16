from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.domain.entities import (
    Project,
    ProjectId,
    ProjectMemberRole,
)
from agenttest.modules.projects.domain.policies import (
    ProjectAccessDeniedError,
    ProjectAccessPolicy,
    ProjectNotFoundError,
)
from agenttest.modules.projects.infrastructure.persistence.repositories import _to_project


def create_user(role: SystemRole, email: str) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(email),
        display_name=email.split("@")[0],
        role=role,
    )


def create_project() -> Project:
    return Project.create(
        project_id=ProjectId(uuid4()),
        name="Project A",
        created_by=UserId.new(),
    )


def test_super_admin_can_access_any_project() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    project = create_project()

    ProjectAccessPolicy.ensure_can_view(admin, project)


def test_normal_user_can_access_only_assigned_project() -> None:
    user = create_user(SystemRole.DEVELOPER, "developer@example.com")
    assigned = create_project()
    other = create_project()
    assigned.add_member(user.user_id, ProjectMemberRole.DEVELOPER)

    ProjectAccessPolicy.ensure_can_view(user, assigned)
    with pytest.raises(ProjectNotFoundError):
        ProjectAccessPolicy.ensure_can_view(user, other)


def test_removed_member_immediately_loses_access() -> None:
    user = create_user(SystemRole.TESTER, "tester@example.com")
    project = create_project()
    project.add_member(user.user_id, ProjectMemberRole.TESTER)
    project.remove_member(user.user_id)

    with pytest.raises(ProjectNotFoundError):
        ProjectAccessPolicy.ensure_can_view(user, project)


def test_viewer_cannot_change_membership() -> None:
    viewer = create_user(SystemRole.VIEWER, "viewer@example.com")
    project = create_project()
    project.add_member(viewer.user_id, ProjectMemberRole.VIEWER)

    with pytest.raises(ProjectAccessDeniedError):
        ProjectAccessPolicy.ensure_can_manage_members(viewer, project)


def test_only_super_admin_can_manage_members_in_m1() -> None:
    developer = create_user(SystemRole.DEVELOPER, "developer@example.com")
    project = create_project()
    project.add_member(developer.user_id, ProjectMemberRole.DEVELOPER)

    with pytest.raises(ProjectAccessDeniedError):
        ProjectAccessPolicy.ensure_can_manage_members(developer, project)


def test_project_supports_rename_archive_and_member_role_changes() -> None:
    project = create_project()
    member_id = UserId.new()

    project.rename("Renamed Project")
    project.add_member(member_id, ProjectMemberRole.DEVELOPER)
    project.change_member_role(member_id, ProjectMemberRole.REVIEWER)
    project.archive()

    assert project.name == "Renamed Project"
    assert project.member_role(member_id) is ProjectMemberRole.REVIEWER
    assert project.is_archived is True


def test_project_normalizes_professional_metadata() -> None:
    lead_id = UserId.new()
    project = Project.create(
        project_id=ProjectId(uuid4()),
        name="Professional QA",
        key="qa-team",
        description="  Agent regression program  ",
        lead_user_id=lead_id,
        created_by=UserId.new(),
    )

    assert project.key == "QA-TEAM"
    assert project.description == "Agent regression program"
    assert project.lead_user_id == lead_id
    assert project.created_at == project.updated_at


def test_project_rejects_invalid_key() -> None:
    with pytest.raises(ValueError, match="Project key"):
        Project.create(
            project_id=ProjectId(uuid4()),
            name="Invalid",
            key="1",
            created_by=UserId.new(),
        )


def test_project_repository_mapper_preserves_professional_metadata() -> None:
    now = datetime.now(UTC)
    creator = uuid4()
    lead = uuid4()
    project = _to_project(
        SimpleNamespace(
            id=uuid4(),
            key="QA-CORE",
            name="QA",
            description="Professional tests",
            lead_user_id=lead,
            created_by=creator,
            updated_by=creator,
            created_at=now,
            updated_at=now,
            archived_at=None,
        ),
        [],
    )

    assert project.key == "QA-CORE"
    assert project.description == "Professional tests"
    assert project.lead_user_id == UserId(lead)
    assert project.created_at == now
