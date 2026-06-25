"""Dataset domain entities."""

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
    value: UUID

    @classmethod
    def new(cls) -> DatasetId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class DatasetVersionId:
    value: UUID

    @classmethod
    def new(cls) -> DatasetVersionId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class TestCaseId:
    value: UUID

    @classmethod
    def new(cls) -> TestCaseId:
        return cls(uuid4())


@dataclass(slots=True)
class Dataset:
    """Root entity representing a test dataset under a project."""

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
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Dataset name is required")
        self.name = normalized_name
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str | None) -> None:
        self.description = description
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class DatasetVersion:
    """An immutable-once-published version of a dataset."""

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
        return self.status is VersionStatus.DRAFT

    @property
    def is_published(self) -> bool:
        return self.status is VersionStatus.PUBLISHED

    def publish(self) -> None:
        if self.status is VersionStatus.PUBLISHED:
            raise ValueError("Version is already published")
        self.status = VersionStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.updated_at = self.published_at


@dataclass(slots=True)
class TestCase:
    """A single test case belonging to a dataset version."""

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
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Test case name is required")
        if not input:
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
