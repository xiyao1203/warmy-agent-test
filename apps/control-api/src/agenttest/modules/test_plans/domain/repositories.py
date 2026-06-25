"""TestPlan domain repository protocols."""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_plans.domain.entities import (
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)


class TestPlanRepository(Protocol):
    async def get_by_id(self, test_plan_id: TestPlanId) -> TestPlan | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[TestPlan], str | None]: ...

    async def add(self, test_plan: TestPlan) -> None: ...

    async def save(self, test_plan: TestPlan) -> None: ...


class TestPlanVersionRepository(Protocol):
    async def get_by_id(self, version_id: TestPlanVersionId) -> TestPlanVersion | None: ...

    async def list_by_test_plan(self, test_plan_id: TestPlanId) -> list[TestPlanVersion]: ...

    async def get_next_version_number(self, test_plan_id: TestPlanId) -> int: ...

    async def add(self, version: TestPlanVersion) -> None: ...

    async def save(self, version: TestPlanVersion) -> None: ...
