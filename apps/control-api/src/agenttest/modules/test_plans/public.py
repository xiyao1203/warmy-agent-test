"""Stable public interface for the test_plans module."""

from __future__ import annotations

from agenttest.modules.environments.public import EnvironmentTemplateId
from agenttest.modules.test_plans.application.commands import (
    CreateTestPlanCommand,
    CreateTestPlanVersionCommand,
    PublishTestPlanVersionCommand,
)
from agenttest.modules.test_plans.domain.entities import (
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from agenttest.modules.test_plans.domain.value_objects import TestPlanConfig, VersionStatus

__all__ = [
    "TestPlan",
    "CreateTestPlanCommand",
    "CreateTestPlanVersionCommand",
    "EnvironmentTemplateId",
    "PublishTestPlanVersionCommand",
    "TestPlanConfig",
    "TestPlanId",
    "TestPlanVersion",
    "TestPlanVersionId",
    "TestPlanVersionRef",
    "VersionStatus",
]


class TestPlanVersionRef:
    """已发布测试计划版本的轻量引用。"""

    __slots__ = ("plan_version_id", "test_plan_id", "version_number")

    def __init__(
        self,
        plan_version_id: TestPlanVersionId,
        test_plan_id: TestPlanId,
        version_number: int,
    ) -> None:
        self.plan_version_id = plan_version_id
        self.test_plan_id = test_plan_id
        self.version_number = version_number

    @classmethod
    def from_version(cls, version: TestPlanVersion) -> TestPlanVersionRef:
        """从完整 TestPlanVersion 实体创建引用。"""
        return cls(version.version_id, version.test_plan_id, version.version_number)
