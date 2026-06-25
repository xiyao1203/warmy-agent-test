"""TestPlan 应用层命令和处理器。

定义测试计划的创建、更新、版本管理和发布操作的 Command 和 Handler。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from agenttest.modules.agents.public import AgentVersionId
from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.datasets.public import DatasetVersionId
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_plans.application.ports import ProjectAccessPort
from agenttest.modules.test_plans.domain.entities import (
    EnvironmentTemplateId,
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from agenttest.modules.test_plans.domain.repositories import (
    TestPlanRepository,
    TestPlanVersionRepository,
)
from agenttest.modules.test_plans.domain.value_objects import TestPlanConfig

# ── Commands ────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CreateTestPlanCommand:
    project_id: ProjectId
    name: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateTestPlanCommand:
    test_plan_id: TestPlanId
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CreateTestPlanVersionCommand:
    test_plan_id: TestPlanId
    config: TestPlanConfig
    agent_version_id: AgentVersionId | None = None
    dataset_version_id: DatasetVersionId | None = None
    environment_template_id: EnvironmentTemplateId | None = None


@dataclass(frozen=True, slots=True)
class UpdateTestPlanVersionCommand:
    version_id: TestPlanVersionId
    config: TestPlanConfig | None = None
    agent_version_id: AgentVersionId | None = None
    dataset_version_id: DatasetVersionId | None = None
    environment_template_id: EnvironmentTemplateId | None = None


@dataclass(frozen=True, slots=True)
class PublishTestPlanVersionCommand:
    version_id: TestPlanVersionId


# ── Handlers ────────────────────────────────────────────────────────────────


class CreateTestPlanHandler:
    """创建测试计划的命令处理器。"""
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._test_plans = test_plans
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: CreateTestPlanCommand) -> TestPlan:
        await self._project_access.ensure_editor(actor, command.project_id)
        plan = TestPlan.create(
            test_plan_id=TestPlanId.new(),
            project_id=command.project_id,
            name=command.name,
            created_by=actor.user_id,
            description=command.description,
        )
        await self._test_plans.add(plan)
        await _record(
            self._audit,
            actor=actor,
            action="test_plans.created",
            project_id=command.project_id,
            object_type="test_plan",
            object_id=plan.test_plan_id.value,
            changes={"name": {"after": plan.name}},
        )
        return plan


class UpdateTestPlanHandler:
    """更新测试计划的命令处理器。支持部分更新。"""
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._test_plans = test_plans
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: UpdateTestPlanCommand) -> TestPlan:
        plan = await _required_plan(self._test_plans, command.test_plan_id)
        await self._project_access.ensure_editor(actor, plan.project_id)
        changes: dict[str, dict[str, str]] = {}
        if command.name is not None:
            before = plan.name
            plan.rename(command.name)
            changes["name"] = {"before": before, "after": plan.name}
        if command.description is not None:
            before = plan.description or ""
            plan.update_description(command.description)
            changes["description"] = {"before": before, "after": plan.description or ""}
        await self._test_plans.save(plan)
        await _record(
            self._audit,
            actor=actor,
            action="test_plans.updated",
            project_id=plan.project_id,
            object_type="test_plan",
            object_id=plan.test_plan_id.value,
            changes=changes,
        )
        return plan


class CreateTestPlanVersionHandler:
    """创建测试计划新版本的命令处理器。可关联 Agent/Dataset/Environment。"""
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        versions: TestPlanVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._test_plans = test_plans
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: CreateTestPlanVersionCommand) -> TestPlanVersion:
        plan = await _required_plan(self._test_plans, command.test_plan_id)
        await self._project_access.ensure_editor(actor, plan.project_id)
        next_number = await self._versions.get_next_version_number(plan.test_plan_id)
        version = TestPlanVersion.create_draft(
            version_id=TestPlanVersionId.new(),
            test_plan_id=plan.test_plan_id,
            version_number=next_number,
            config=command.config,
            created_by=actor.user_id,
            agent_version_id=command.agent_version_id,
            dataset_version_id=command.dataset_version_id,
            environment_template_id=command.environment_template_id,
        )
        await self._versions.add(version)
        await _record(
            self._audit,
            actor=actor,
            action="test_plans.version.created",
            project_id=plan.project_id,
            object_type="test_plan_version",
            object_id=version.version_id.value,
            changes={"version_number": {"after": version.version_number}},
        )
        return version


class UpdateTestPlanVersionHandler:
    """更新测试计划版本的命令处理器。仅草稿版本可编辑。"""
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        versions: TestPlanVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._test_plans = test_plans
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: UpdateTestPlanVersionCommand) -> TestPlanVersion:
        version = await _required_version(self._versions, command.version_id)
        plan = await _required_plan(self._test_plans, version.test_plan_id)
        await self._project_access.ensure_editor(actor, plan.project_id)
        if command.config is not None:
            version.update_config(command.config)
        if (
            command.agent_version_id is not None
            or command.dataset_version_id is not None
            or command.environment_template_id is not None
        ):
            version.update_references(
                agent_version_id=command.agent_version_id,
                dataset_version_id=command.dataset_version_id,
                environment_template_id=command.environment_template_id,
            )
        await self._versions.save(version)
        return version


class PublishTestPlanVersionHandler:
    """发布测试计划版本的命令处理器。"""
    def __init__(
        self,
        *,
        test_plans: TestPlanRepository,
        versions: TestPlanVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._test_plans = test_plans
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: PublishTestPlanVersionCommand) -> TestPlanVersion:
        version = await _required_version(self._versions, command.version_id)
        plan = await _required_plan(self._test_plans, version.test_plan_id)
        await self._project_access.ensure_editor(actor, plan.project_id)
        version.publish()
        await self._versions.save(version)
        await _record(
            self._audit,
            actor=actor,
            action="test_plans.version.published",
            project_id=plan.project_id,
            object_type="test_plan_version",
            object_id=version.version_id.value,
            changes={
                "status": {"after": "published"},
                "version_number": {"after": version.version_number},
            },
        )
        return version


# ── Helpers ─────────────────────────────────────────────────────────────────


async def _required_plan(repo: TestPlanRepository, plan_id: TestPlanId) -> TestPlan:
    plan = await repo.get_by_id(plan_id)
    if plan is None:
        raise TestPlanNotFoundError(plan_id)
    return plan


async def _required_version(
    repo: TestPlanVersionRepository, version_id: TestPlanVersionId
) -> TestPlanVersion:
    version = await repo.get_by_id(version_id)
    if version is None:
        raise TestPlanVersionNotFoundError(version_id)
    return version


async def _record(
    audit: AuditWriter | None,
    *,
    actor: User,
    action: str,
    project_id: ProjectId,
    object_type: str,
    object_id: object,
    changes: Mapping[str, object] | None = None,
) -> None:
    if audit is not None:
        await audit.record(
            actor_user_id=actor.user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,  # type: ignore[arg-type]
            project_id=project_id,
            changes=dict(changes) if changes else {},
            source_ip=None,
        )


# ── Errors ──────────────────────────────────────────────────────────────────


class TestPlanNotFoundError(Exception):
    """测试计划不存在的领域异常。"""
    def __init__(self, plan_id: TestPlanId) -> None:
        self.plan_id = plan_id
        super().__init__(f"Test plan {plan_id.value} not found")


class TestPlanVersionNotFoundError(Exception):
    """测试计划版本不存在的领域异常。"""
    def __init__(self, version_id: TestPlanVersionId) -> None:
        self.version_id = version_id
        super().__init__(f"Test plan version {version_id.value} not found")
