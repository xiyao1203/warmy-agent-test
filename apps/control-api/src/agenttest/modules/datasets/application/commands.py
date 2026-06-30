"""Dataset 应用层命令和处理器。

定义数据集管理、版本创建/发布、用例增删改查的 Command 和 Handler。
每个 Handler 负责权限校验、领域操作、持久化和审计日志。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.datasets.application.ports import ProjectAccessPort
from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
    TestCase,
    TestCaseId,
)
from agenttest.modules.datasets.domain.repositories import (
    DatasetRepository,
    DatasetVersionRepository,
    TestCaseRepository,
)
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
    TestGroup,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId

# ── Commands ────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CreateDatasetCommand:
    project_id: ProjectId
    name: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateDatasetCommand:
    dataset_id: DatasetId
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CreateDatasetVersionCommand:
    dataset_id: DatasetId


@dataclass(frozen=True, slots=True)
class AddTestCaseCommand:
    dataset_version_id: DatasetVersionId
    name: str
    input: dict[str, object]
    execution_mode: ExecutionMode
    assertions: list[dict[str, object]] | None = None
    scorers: list[dict[str, object]] | None = None
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] | None = None
    tags: list[str] | None = None
    scenario: str | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = None
    test_group: TestGroup | None = None


@dataclass(frozen=True, slots=True)
class UpdateTestCaseCommand:
    case_id: TestCaseId
    name: str | None = None
    input: dict[str, object] | None = None
    execution_mode: ExecutionMode | None = None
    assertions: list[dict[str, object]] | None = None
    scorers: list[dict[str, object]] | None = None
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] | None = None
    tags: list[str] | None = None
    scenario: str | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = None
    test_group: TestGroup | None = None
    sort_order: int | None = None


@dataclass(frozen=True, slots=True)
class DeleteTestCaseCommand:
    case_id: TestCaseId


@dataclass(frozen=True, slots=True)
class PublishDatasetVersionCommand:
    version_id: DatasetVersionId


# ── Handlers ────────────────────────────────────────────────────────────────


class CreateDatasetHandler:
    """创建数据集的命令处理器。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._datasets = datasets
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: CreateDatasetCommand) -> Dataset:
        await self._project_access.ensure_editor(actor, command.project_id)
        dataset = Dataset.create(
            dataset_id=DatasetId.new(),
            project_id=command.project_id,
            name=command.name,
            created_by=actor.user_id,
            description=command.description,
        )
        await self._datasets.add(dataset)
        await _record(
            self._audit,
            actor=actor,
            action="datasets.created",
            project_id=command.project_id,
            object_type="dataset",
            object_id=dataset.dataset_id.value,
            changes={"name": {"after": dataset.name}},
        )
        return dataset


class UpdateDatasetHandler:
    """更新数据集名称或描述的命令处理器。支持部分更新。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._datasets = datasets
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: UpdateDatasetCommand) -> Dataset:
        dataset = await _required_dataset(self._datasets, command.dataset_id)
        await self._project_access.ensure_editor(actor, dataset.project_id)
        changes: dict[str, dict[str, str]] = {}
        if command.name is not None:
            before = dataset.name
            dataset.rename(command.name)
            changes["name"] = {"before": before, "after": dataset.name}
        if command.description is not None:
            before = dataset.description or ""
            dataset.update_description(command.description)
            changes["description"] = {"before": before, "after": dataset.description or ""}
        await self._datasets.save(dataset)
        await _record(
            self._audit,
            actor=actor,
            action="datasets.updated",
            project_id=dataset.project_id,
            object_type="dataset",
            object_id=dataset.dataset_id.value,
            changes=changes,
        )
        return dataset


class CreateDatasetVersionHandler:
    """创建数据集新版本的命令处理器。自动计算下一个版本号。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: CreateDatasetVersionCommand) -> DatasetVersion:
        dataset = await _required_dataset(self._datasets, command.dataset_id)
        await self._project_access.ensure_editor(actor, dataset.project_id)
        next_number = await self._versions.get_next_version_number(dataset.dataset_id)
        version = DatasetVersion.create_draft(
            version_id=DatasetVersionId.new(),
            dataset_id=dataset.dataset_id,
            version_number=next_number,
            created_by=actor.user_id,
        )
        await self._versions.add(version)
        await _record(
            self._audit,
            actor=actor,
            action="datasets.version.created",
            project_id=dataset.project_id,
            object_type="dataset_version",
            object_id=version.version_id.value,
            changes={"version_number": {"after": version.version_number}},
        )
        return version


class AddTestCaseHandler:
    """向数据集版本添加测试用例的命令处理器。仅草稿版本可添加。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        cases: TestCaseRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._cases = cases
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: AddTestCaseCommand) -> TestCase:
        version = await _required_version(self._versions, command.dataset_version_id)
        if not version.is_editable:
            raise DatasetVersionNotEditableError(version.version_id)
        dataset = await _required_dataset(self._datasets, version.dataset_id)
        await self._project_access.ensure_editor(actor, dataset.project_id)
        max_order = await self._cases.get_max_sort_order(version.version_id)
        case = TestCase.create(
            case_id=TestCaseId.new(),
            dataset_version_id=version.version_id,
            name=command.name,
            input=command.input,
            execution_mode=command.execution_mode,
            assertions=command.assertions,
            scorers=command.scorers,
            initial_state=command.initial_state,
            expected_outcome=command.expected_outcome,
            security_policies=command.security_policies,
            tags=command.tags,
            scenario=command.scenario,
            priority=command.priority,
            risk_level=command.risk_level,
            difficulty=command.difficulty,
            test_group=command.test_group,
            sort_order=max_order + 1,
        )
        await self._cases.add(case)
        await _record(
            self._audit,
            actor=actor,
            action="datasets.test_case.created",
            project_id=dataset.project_id,
            object_type="test_case",
            object_id=case.case_id.value,
            changes={"name": {"after": case.name}},
        )
        return case


class UpdateTestCaseHandler:
    """更新测试用例的命令处理器。仅草稿版本内的用例可编辑。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        cases: TestCaseRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._cases = cases
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: UpdateTestCaseCommand) -> TestCase:
        case = await _required_case(self._cases, command.case_id)
        version = await _required_version(self._versions, case.dataset_version_id)
        if not version.is_editable:
            raise DatasetVersionNotEditableError(version.version_id)
        dataset = await _required_dataset(self._datasets, version.dataset_id)
        await self._project_access.ensure_editor(actor, dataset.project_id)
        case.update(
            name=command.name,
            input=command.input,
            execution_mode=command.execution_mode,
            assertions=command.assertions,
            scorers=command.scorers,
            initial_state=command.initial_state,
            expected_outcome=command.expected_outcome,
            security_policies=command.security_policies,
            tags=command.tags,
            scenario=command.scenario,
            priority=command.priority,
            risk_level=command.risk_level,
            difficulty=command.difficulty,
            test_group=command.test_group,
            sort_order=command.sort_order,
        )
        await self._cases.save(case)
        return case


class DeleteTestCaseHandler:
    """删除测试用例的命令处理器。仅草稿版本内的用例可删除。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        cases: TestCaseRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._cases = cases
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: DeleteTestCaseCommand) -> None:
        case = await _required_case(self._cases, command.case_id)
        version = await _required_version(self._versions, case.dataset_version_id)
        if not version.is_editable:
            raise DatasetVersionNotEditableError(version.version_id)
        dataset = await _required_dataset(self._datasets, version.dataset_id)
        await self._project_access.ensure_editor(actor, dataset.project_id)
        await self._cases.delete(case.case_id)
        await _record(
            self._audit,
            actor=actor,
            action="datasets.test_case.deleted",
            project_id=dataset.project_id,
            object_type="test_case",
            object_id=case.case_id.value,
            changes={},
        )


class PublishDatasetVersionHandler:
    """发布数据集版本的命令处理器。发布后版本及用例不可修改。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: PublishDatasetVersionCommand) -> DatasetVersion:
        version = await _required_version(self._versions, command.version_id)
        dataset = await _required_dataset(self._datasets, version.dataset_id)
        await self._project_access.ensure_editor(actor, dataset.project_id)
        version.publish()
        await self._versions.save(version)
        await _record(
            self._audit,
            actor=actor,
            action="datasets.version.published",
            project_id=dataset.project_id,
            object_type="dataset_version",
            object_id=version.version_id.value,
            changes={
                "status": {"after": "published"},
                "version_number": {"after": version.version_number},
            },
        )
        return version


# ── Helpers ─────────────────────────────────────────────────────────────────


async def _required_dataset(datasets: DatasetRepository, dataset_id: DatasetId) -> Dataset:
    dataset = await datasets.get_by_id(dataset_id)
    if dataset is None:
        raise DatasetNotFoundError(dataset_id)
    return dataset


async def _required_version(
    versions: DatasetVersionRepository, version_id: DatasetVersionId
) -> DatasetVersion:
    version = await versions.get_by_id(version_id)
    if version is None:
        raise DatasetVersionNotFoundError(version_id)
    return version


async def _required_case(cases: TestCaseRepository, case_id: TestCaseId) -> TestCase:
    case = await cases.get_by_id(case_id)
    if case is None:
        raise TestCaseNotFoundError(case_id)
    return case


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


class DatasetNotFoundError(Exception):
    """数据集不存在的领域异常。"""

    def __init__(self, dataset_id: DatasetId) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"Dataset {dataset_id.value} not found")


class DatasetVersionNotFoundError(Exception):
    """数据集版本不存在的领域异常。"""

    def __init__(self, version_id: DatasetVersionId) -> None:
        self.version_id = version_id
        super().__init__(f"Dataset version {version_id.value} not found")


class DatasetVersionNotEditableError(Exception):
    """尝试修改已发布版本的领域异常。"""

    def __init__(self, version_id: DatasetVersionId) -> None:
        self.version_id = version_id
        super().__init__(f"Dataset version {version_id.value} is not editable")


class TestCaseNotFoundError(Exception):
    """测试用例不存在的领域异常。"""

    def __init__(self, case_id: TestCaseId) -> None:
        self.case_id = case_id
        super().__init__(f"Test case {case_id.value} not found")
