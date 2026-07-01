"""Dataset 领域实体。

定义数据集相关的聚合根和实体：
- Dataset：项目下的数据集聚合根。
- DatasetVersion：数据集的版本，支持草稿/发布状态。
- TestCase：属于某个 DatasetVersion 的测试用例。

已发布版本不可修改，编辑必须创建新版本。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
    TestGroup,
    VersionStatus,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


@dataclass(frozen=True, slots=True)
class DatasetId:
    """数据集聚合根的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> DatasetId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class DatasetVersionId:
    """数据集版本实体的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> DatasetVersionId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class TestCaseId:
    """测试用例实体的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> TestCaseId:
        return cls(uuid4())


@dataclass(slots=True)
class Dataset:
    """项目下的测试数据集聚合根。

    数据集本身不包含具体测试用例——用例通过 DatasetVersion 管理，
    遵循不可变版本策略。

    Attributes:
        dataset_id: 数据集唯一标识。
        project_id: 所属项目 ID。
        name: 数据集名称。
        description: 可选的描述。
        created_by / updated_by: 创建和更新者。
        created_at / updated_at: 时间戳（UTC）。
    """

    dataset_id: DatasetId
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
        dataset_id: DatasetId,
        project_id: ProjectId,
        name: str,
        created_by: UserId,
        description: str | None = None,
    ) -> Dataset:
        """创建新的数据集。

        Raises:
            ValueError: name 为空或仅含空白字符。
        """
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Dataset name is required")
        now = datetime.now(UTC)
        return cls(
            dataset_id=dataset_id,
            project_id=project_id,
            name=normalized_name,
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
        )

    def rename(self, name: str) -> None:
        """修改数据集名称。"""
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Dataset name is required")
        self.name = normalized_name
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str | None) -> None:
        """更新数据集描述。"""
        self.description = description
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class DatasetVersion:
    """数据集的版本实体。

    版本遵循草稿→发布单向状态流转。发布后不可修改，
    编辑必须创建新草稿版本。

    Attributes:
        version_id: 版本唯一标识。
        dataset_id: 所属数据集 ID。
        version_number: 版本号，从 1 开始自增。
        status: 版本状态（draft / published）。
        published_at: 发布时间，仅已发布版本有值。
    """

    version_id: DatasetVersionId
    dataset_id: DatasetId
    version_number: int
    status: VersionStatus
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    @classmethod
    def create_draft(
        cls,
        *,
        version_id: DatasetVersionId,
        dataset_id: DatasetId,
        version_number: int,
        created_by: UserId,
    ) -> DatasetVersion:
        """创建新的草稿版本。

        Raises:
            ValueError: version_number < 1。
        """
        if version_number < 1:
            raise ValueError("version_number must be >= 1")
        now = datetime.now(UTC)
        return cls(
            version_id=version_id,
            dataset_id=dataset_id,
            version_number=version_number,
            status=VersionStatus.DRAFT,
            created_by=created_by,
            created_at=now,
            updated_at=now,
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
        """发布草稿版本。发布后不可修改。

        Raises:
            ValueError: 版本已经发布。
        """
        if self.status is VersionStatus.PUBLISHED:
            raise ValueError("Version is already published")
        self.status = VersionStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.updated_at = self.published_at


@dataclass(slots=True)
class TestCase:
    """测试用例实体，属于某个数据集版本。

    包含输入、期望输出、断言、评分器和安全策略等完整测试定义。
    支持 API 和浏览器两种执行模式。

    Attributes:
        case_id: 用例唯一标识。
        dataset_version_id: 所属数据集版本 ID。
        name: 用例名称。
        input: 输入数据（JSON）。
        execution_mode: 执行模式（api / browser）。
        assertions: 断言规则列表。
        scorers: 评分器配置列表。
        tags / priority / risk_level / test_group: 分类和标签。
        sort_order: 排序序号。
    """

    case_id: TestCaseId
    dataset_version_id: DatasetVersionId
    name: str
    input: dict[str, object]
    execution_mode: ExecutionMode
    assertions: list[dict[str, object]]
    scorers: list[dict[str, object]]
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    scenario: str | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = None
    test_group: TestGroup | None = None
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        case_id: TestCaseId,
        dataset_version_id: DatasetVersionId,
        name: str,
        input: dict[str, object],
        execution_mode: ExecutionMode,
        assertions: list[dict[str, object]] | None = None,
        scorers: list[dict[str, object]] | None = None,
        initial_state: dict[str, object] | None = None,
        expected_outcome: dict[str, object] | None = None,
        security_policies: list[dict[str, object]] | None = None,
        tags: list[str] | None = None,
        scenario: str | None = None,
        priority: Priority | None = None,
        risk_level: RiskLevel | None = None,
        difficulty: str | None = None,
        test_group: TestGroup | None = None,
        sort_order: int = 0,
    ) -> TestCase:
        """创建新的测试用例。

        Raises:
            ValueError: name 为空或 input 为空时抛出。
        """
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Test case name is required")
        if input is None:
            raise ValueError("Test case input is required")
        now = datetime.now(UTC)
        return cls(
            case_id=case_id,
            dataset_version_id=dataset_version_id,
            name=normalized_name,
            input=input,
            execution_mode=execution_mode,
            assertions=assertions or [],
            scorers=scorers or [],
            initial_state=initial_state,
            expected_outcome=expected_outcome,
            security_policies=security_policies or [],
            tags=tags or [],
            scenario=scenario,
            priority=priority,
            risk_level=risk_level,
            difficulty=difficulty,
            test_group=test_group,
            sort_order=sort_order,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        *,
        name: str | None = None,
        input: dict[str, object] | None = None,
        execution_mode: ExecutionMode | None = None,
        assertions: list[dict[str, object]] | None = None,
        scorers: list[dict[str, object]] | None = None,
        initial_state: dict[str, object] | None = None,
        expected_outcome: dict[str, object] | None = None,
        security_policies: list[dict[str, object]] | None = None,
        tags: list[str] | None = None,
        scenario: str | None = None,
        priority: Priority | None = None,
        risk_level: RiskLevel | None = None,
        difficulty: str | None = None,
        test_group: TestGroup | None = None,
        sort_order: int | None = None,
    ) -> None:
        """部分更新测试用例字段，仅更新传入的非 None 字段。"""
        if name is not None:
            normalized = name.strip()
            if not normalized:
                raise ValueError("Test case name is required")
            self.name = normalized
        if input is not None:
            if not input:
                raise ValueError("Test case input is required")
            self.input = input
        if execution_mode is not None:
            self.execution_mode = execution_mode
        if assertions is not None:
            self.assertions = assertions
        if scorers is not None:
            self.scorers = scorers
        if initial_state is not None:
            self.initial_state = initial_state
        if expected_outcome is not None:
            self.expected_outcome = expected_outcome
        if security_policies is not None:
            self.security_policies = security_policies
        if tags is not None:
            self.tags = tags
        if scenario is not None:
            self.scenario = scenario
        if priority is not None:
            self.priority = priority
        if risk_level is not None:
            self.risk_level = risk_level
        if difficulty is not None:
            self.difficulty = difficulty
        if test_group is not None:
            self.test_group = test_group
        if sort_order is not None:
            self.sort_order = sort_order
        self.updated_at = datetime.now(UTC)
