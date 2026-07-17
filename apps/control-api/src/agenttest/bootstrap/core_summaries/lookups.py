"""SQLAlchemy read-side projections for decision-ready core lists.

The reader lives in the composition layer because it joins several bounded contexts.
It never mutates business data and every method applies an explicit project scope.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.browser_profiles.infrastructure.models import BrowserProfileModel
from agenttest.modules.datasets.infrastructure.persistence.models import (
    DatasetModel,
    DatasetVersionModel,
    TestCaseModel,
)
from agenttest.modules.environments.infrastructure.persistence.models import (
    EnvironmentTemplateModel,
)
from agenttest.modules.identity.infrastructure.persistence.models import UserModel
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunModel,
)
from agenttest.modules.security.infrastructure.models import SecurityProfileModel
from agenttest.modules.test_plans.infrastructure.persistence.models import (
    TestPlanModel,
    TestPlanVersionModel,
)
from agenttest.shared.application.resource_reference import (
    ResourceReference,
    ResourceType,
)


async def _group_count(
    session: AsyncSession, model: Any, project_column: Any, ids: list[UUID]
) -> dict[UUID, int]:
    result = await session.execute(
        select(project_column, func.count(model.id))
        .where(project_column.in_(ids))
        .group_by(project_column)
    )
    return {project_id: int(count) for project_id, count in result}


async def _agent_version_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(AgentVersionModel, AgentModel)
        .join(AgentModel, AgentModel.id == AgentVersionModel.agent_id)
        .where(AgentModel.project_id == project_id, AgentVersionModel.id.in_(values))
    )
    return {
        version.id: ResourceReference.build(
            resource_type=ResourceType.AGENT_VERSION,
            resource_id=version.id,
            project_id=project_id,
            parent_id=agent.id,
            name=agent.name,
            version=version.version_number,
            status=version.status,
        )
        for version, agent in result
    }


async def _dataset_version_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(DatasetVersionModel, DatasetModel)
        .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
        .where(DatasetModel.project_id == project_id, DatasetVersionModel.id.in_(values))
    )
    return {
        version.id: ResourceReference.build(
            resource_type=ResourceType.DATASET_VERSION,
            resource_id=version.id,
            project_id=project_id,
            parent_id=dataset.id,
            name=dataset.name,
            version=version.version_number,
            status=version.status,
        )
        for version, dataset in result
    }


async def _plan_version_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(TestPlanVersionModel, TestPlanModel)
        .join(TestPlanModel, TestPlanModel.id == TestPlanVersionModel.test_plan_id)
        .where(TestPlanModel.project_id == project_id, TestPlanVersionModel.id.in_(values))
    )
    return {
        version.id: ResourceReference.build(
            resource_type=ResourceType.TEST_PLAN_VERSION,
            resource_id=version.id,
            project_id=project_id,
            parent_id=plan.id,
            name=plan.name,
            version=version.version_number,
            status=version.status,
        )
        for version, plan in result
    }


async def _environment_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(EnvironmentTemplateModel).where(
            EnvironmentTemplateModel.project_id == project_id,
            EnvironmentTemplateModel.id.in_(values),
        )
    )
    return {
        item.id: ResourceReference.build(
            resource_type=ResourceType.ENVIRONMENT,
            resource_id=item.id,
            project_id=project_id,
            name=item.name,
        )
        for item in result.scalars()
    }


async def _case_counts_for_versions(
    session: AsyncSession, ids: Iterable[UUID | None]
) -> dict[UUID, int]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(TestCaseModel.dataset_version_id, func.count(TestCaseModel.id))
        .where(TestCaseModel.dataset_version_id.in_(values))
        .group_by(TestCaseModel.dataset_version_id)
    )
    return {version_id: int(count) for version_id, count in result}


async def _case_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(TestCaseModel)
        .join(DatasetVersionModel, DatasetVersionModel.id == TestCaseModel.dataset_version_id)
        .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
        .where(DatasetModel.project_id == project_id, TestCaseModel.id.in_(values))
    )
    return {
        item.id: ResourceReference.build(
            resource_type=ResourceType.TEST_CASE,
            resource_id=item.id,
            project_id=project_id,
            name=item.name,
            key=item.case_key,
            status=item.case_status,
        )
        for item in result.scalars()
    }


async def _user_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(select(UserModel).where(UserModel.id.in_(values)))
    return {
        user.id: ResourceReference.build(
            resource_type=ResourceType.USER,
            resource_id=user.id,
            project_id=project_id,
            name=user.display_name,
            status=user.status,
        )
        for user in result.scalars()
    }


async def _browser_profile_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(BrowserProfileModel).where(
            BrowserProfileModel.project_id == project_id,
            BrowserProfileModel.id.in_(values),
        )
    )
    return {
        item.id: ResourceReference.build(
            resource_type=ResourceType.ENVIRONMENT,
            resource_id=item.id,
            project_id=project_id,
            name=item.name,
            status=item.auth_state_status,
        )
        for item in result.scalars()
    }


async def _run_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(RunModel).where(RunModel.project_id == project_id, RunModel.id.in_(values))
    )
    return {run.id: _run_ref(run) for run in result.scalars()}


async def _security_profile_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(SecurityProfileModel).where(
            SecurityProfileModel.project_id == project_id,
            SecurityProfileModel.id.in_(values),
        )
    )
    return {
        profile.id: ResourceReference.build(
            resource_type=ResourceType.SECURITY_PROFILE,
            resource_id=profile.id,
            project_id=project_id,
            name=profile.name,
            status=profile.status,
        )
        for profile in result.scalars()
    }


def _run_ref(run: RunModel) -> ResourceReference:
    return ResourceReference.build(
        resource_type=ResourceType.RUN,
        resource_id=run.id,
        project_id=run.project_id,
        name=f"RUN-{str(run.id).split('-')[0].upper()}",
        status=run.status,
    )


def _ids(values: Iterable[UUID | None]) -> list[UUID]:
    return list({value for value in values if value is not None})


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _string(value: object) -> str | None:
    return str(value) if value is not None and str(value) else None


def _integer(value: object, default: int) -> int:
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_integer(value: object) -> int | None:
    return _integer(value, 0) if value is not None else None


def _optional_float(value: object) -> float | None:
    if not isinstance(value, (str, int, float)):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _age_seconds(now: datetime, created_at: datetime) -> int:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return max(0, int((now - created_at).total_seconds()))


def _uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value:
        try:
            return UUID(value)
        except ValueError:
            return None
    return None
