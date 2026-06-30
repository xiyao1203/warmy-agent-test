"""TestPlan 领域实体。

定义测试计划相关的聚合根和实体：
- TestPlan：项目下的测试计划聚合根。
- TestPlanVersion：测试计划版本，关联特定 Agent/Dataset/Environment 版本。

遵循不可变版本策略：发布后不可修改，编辑必须创建新版本。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.agents.public import AgentVersionId
from agenttest.modules.datasets.public import DatasetVersionId
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_plans.domain.value_objects import TestPlanConfig, VersionStatus


@dataclass(frozen=True, slots=True)
class TestPlanId:
    """测试计划聚合根的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> TestPlanId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class TestPlanVersionId:
    """测试计划版本实体的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> TestPlanVersionId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class EnvironmentTemplateId:
    """环境模板实体的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> EnvironmentTemplateId:
        return cls(uuid4())


@dataclass(slots=True)
class TestPlan:
    """项目下的测试计划聚合根。

    测试计划定义了一组测试执行的配置，包括关联的 Agent、
    数据集和环境模板版本，以及并发、超时、阈值等运行参数。
    """

    test_plan_id: TestPlanId
    project_id: ProjectId
    name: str
    created_by: UserId
    updated_by: UserId
    created_at: datetime
    updated_at: datetime
    description: str | None = None

    @classmethod
    def create(
        cls,
        *,
        test_plan_id: TestPlanId,
        project_id: ProjectId,
        name: str,
        created_by: UserId,
        description: str | None = None,
    ) -> TestPlan:
        """创建新的测试计划。

        Raises:
            ValueError: name 为空。
        """
        normalized = name.strip()
        if not normalized:
            raise ValueError("Test plan name is required")
        now = datetime.now(UTC)
        return cls(
            test_plan_id=test_plan_id,
            project_id=project_id,
            name=normalized,
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
        )

    def rename(self, name: str) -> None:
        """修改测试计划名称。"""
        normalized = name.strip()
        if not normalized:
            raise ValueError("Test plan name is required")
        self.name = normalized
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str | None) -> None:
        """更新测试计划描述。"""
        self.description = description
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class TestPlanVersion:
    """测试计划的版本实体。

    版本关联特定的 Agent、Dataset 和 Environment 版本，
    确保测试执行的可复现性。发布后不可修改。

    Attributes:
        version_id: 版本唯一标识。
        test_plan_id: 所属测试计划 ID。
        version_number: 版本号，从 1 开始自增。
        status: 版本状态（draft / published）。
        config: 运行配置（并发、超时、阈值等）。
        agent_version_id: 关联的 Agent 已发布版本 ID。
        dataset_version_id: 关联的数据集已发布版本 ID。
        environment_template_id: 关联的环境模板 ID。
        published_at: 发布时间。
    """

    version_id: TestPlanVersionId
    test_plan_id: TestPlanId
    version_number: int
    status: VersionStatus
    config: TestPlanConfig
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    agent_version_id: AgentVersionId | None = None
    dataset_version_id: DatasetVersionId | None = None
    environment_template_id: EnvironmentTemplateId | None = None
    published_at: datetime | None = None

    @classmethod
    def create_draft(
        cls,
        *,
        version_id: TestPlanVersionId,
        test_plan_id: TestPlanId,
        version_number: int,
        config: TestPlanConfig,
        created_by: UserId,
        agent_version_id: AgentVersionId | None = None,
        dataset_version_id: DatasetVersionId | None = None,
        environment_template_id: EnvironmentTemplateId | None = None,
    ) -> TestPlanVersion:
        """创建新的草稿版本。

        Raises:
            ValueError: version_number < 1。
        """
        if version_number < 1:
            raise ValueError("version_number must be >= 1")
        now = datetime.now(UTC)
        return cls(
            version_id=version_id,
            test_plan_id=test_plan_id,
            version_number=version_number,
            status=VersionStatus.DRAFT,
            config=config,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            agent_version_id=agent_version_id,
            dataset_version_id=dataset_version_id,
            environment_template_id=environment_template_id,
            published_at=None,
        )

    @property
    def is_editable(self) -> bool:
        """仅草稿版本可编辑。"""
        return self.status is VersionStatus.DRAFT

    @property
    def is_published(self) -> bool:
        """版本是否已发布。"""
        return self.status is VersionStatus.PUBLISHED

    def publish(self) -> None:
        """发布草稿版本，发布后不可修改。

        Raises:
            ValueError: 版本已发布。
        """
        if self.status is VersionStatus.PUBLISHED:
            raise ValueError("Version is already published")
        self.status = VersionStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.updated_at = self.published_at

    def update_config(self, config: TestPlanConfig) -> None:
        """更新草稿版本的运行配置。仅草稿可调用。"""
        if not self.is_editable:
            raise ValueError("Cannot modify a published version")
        self.config = config
        self.updated_at = datetime.now(UTC)

    def update_references(
        self,
        *,
        agent_version_id: AgentVersionId | None = None,
        dataset_version_id: DatasetVersionId | None = None,
        environment_template_id: EnvironmentTemplateId | None = None,
    ) -> None:
        """更新草稿版本关联的 Agent/Dataset/Environment 引用。仅草稿可调用。"""
        if not self.is_editable:
            raise ValueError("Cannot modify a published version")
        if agent_version_id is not None:
            self.agent_version_id = agent_version_id
        if dataset_version_id is not None:
            self.dataset_version_id = dataset_version_id
        if environment_template_id is not None:
            self.environment_template_id = environment_template_id
        self.updated_at = datetime.now(UTC)
