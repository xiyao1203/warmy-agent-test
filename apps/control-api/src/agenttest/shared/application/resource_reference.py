"""Safe cross-module resource references for list summaries and Agent results."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResourceType(StrEnum):
    USER = "user"
    PROJECT = "project"
    AGENT = "agent"
    AGENT_VERSION = "agent_version"
    DATASET = "dataset"
    DATASET_VERSION = "dataset_version"
    TEST_CASE = "test_case"
    TEST_PLAN = "test_plan"
    TEST_PLAN_VERSION = "test_plan_version"
    RUN = "run"
    ENVIRONMENT = "environment"
    ENVIRONMENT_VERSION = "environment_version"
    SCORER = "scorer"
    EXPERIMENT = "experiment"
    SECURITY_SCAN = "security_scan"
    SECURITY_PROFILE = "security_profile"
    REVIEW = "review"
    RELEASE_GATE = "release_gate"


class ResourceReference(BaseModel):
    """An internal reference whose href is created only from an allowlisted type."""

    model_config = ConfigDict(frozen=True)

    resource_type: ResourceType
    id: UUID
    key: str | None = None
    name: str
    version: int | str | None = None
    status: str | None = None
    href: str | None

    @classmethod
    def build(
        cls,
        *,
        resource_type: ResourceType,
        resource_id: UUID,
        project_id: UUID,
        name: str,
        key: str | None = None,
        version: int | str | None = None,
        status: str | None = None,
        parent_id: UUID | None = None,
    ) -> ResourceReference:
        return cls(
            resource_type=resource_type,
            id=resource_id,
            key=key,
            name=name,
            version=version,
            status=status,
            href=_safe_href(resource_type, project_id, resource_id, parent_id),
        )


def _safe_href(
    resource_type: ResourceType,
    project_id: UUID,
    resource_id: UUID,
    parent_id: UUID | None,
) -> str | None:
    project = f"/projects/{project_id}"
    routes: dict[ResourceType, str | None] = {
        ResourceType.USER: None,
        ResourceType.PROJECT: f"{project}/overview",
        ResourceType.AGENT: f"{project}/agents/{resource_id}",
        ResourceType.AGENT_VERSION: (
            f"{project}/agents/{parent_id}" if parent_id is not None else f"{project}/agents"
        ),
        ResourceType.DATASET: f"{project}/datasets/{resource_id}",
        ResourceType.DATASET_VERSION: (
            f"{project}/datasets/{parent_id}" if parent_id is not None else f"{project}/datasets"
        ),
        ResourceType.TEST_CASE: f"{project}/datasets",
        ResourceType.TEST_PLAN: f"{project}/test-plans/{resource_id}",
        ResourceType.TEST_PLAN_VERSION: (
            f"{project}/test-plans/{parent_id}"
            if parent_id is not None
            else f"{project}/test-plans"
        ),
        ResourceType.RUN: f"{project}/runs/{resource_id}",
        ResourceType.ENVIRONMENT: f"{project}/environments",
        ResourceType.ENVIRONMENT_VERSION: f"{project}/environments",
        ResourceType.SCORER: f"{project}/scorers",
        ResourceType.EXPERIMENT: f"{project}/experiments",
        ResourceType.SECURITY_SCAN: f"{project}/security",
        ResourceType.SECURITY_PROFILE: f"{project}/security",
        ResourceType.REVIEW: f"{project}/reviews",
        ResourceType.RELEASE_GATE: f"{project}/gates",
    }
    return routes[resource_type]
