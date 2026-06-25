"""TestPlan application query handlers."""

from __future__ import annotations

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_plans.application.commands import (
    _required_plan,
    _required_version,
)
from agenttest.modules.test_plans.application.ports import ProjectAccessPort
from agenttest.modules.test_plans.domain.entities import (
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from agenttest.modules.test_plans.domain.repositories import (
    TestPlanRepository,
    TestPlanVersionRepository,
)


class ListTestPlansHandler:
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._test_plans = test_plans
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[TestPlan], str | None]:
        await self._project_access.ensure_member(actor, project_id)
        return await self._test_plans.list_by_project(project_id, limit=limit, cursor=cursor)


class GetTestPlanHandler:
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._test_plans = test_plans
        self._project_access = project_access

    async def execute(self, actor: User, plan_id: TestPlanId) -> TestPlan:
        plan = await _required_plan(self._test_plans, plan_id)
        await self._project_access.ensure_member(actor, plan.project_id)
        return plan


class ListTestPlanVersionsHandler:
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        versions: TestPlanVersionRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._test_plans = test_plans
        self._versions = versions
        self._project_access = project_access

    async def execute(self, actor: User, plan_id: TestPlanId) -> list[TestPlanVersion]:
        plan = await _required_plan(self._test_plans, plan_id)
        await self._project_access.ensure_member(actor, plan.project_id)
        return await self._versions.list_by_test_plan(plan.test_plan_id)


class GetTestPlanVersionHandler:
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        versions: TestPlanVersionRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._test_plans = test_plans
        self._versions = versions
        self._project_access = project_access

    async def execute(self, actor: User, version_id: TestPlanVersionId) -> TestPlanVersion:
        version = await _required_version(self._versions, version_id)
        plan = await _required_plan(self._test_plans, version.test_plan_id)
        await self._project_access.ensure_member(actor, plan.project_id)
        return version
