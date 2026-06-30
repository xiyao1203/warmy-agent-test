"""Dataset 应用层查询处理器。

定义数据集、版本和测试用例的只读查询 Handler。
所有查询校验用户对目标项目的成员资格。
"""

from __future__ import annotations

from agenttest.modules.datasets.application.commands import (
    _required_dataset,
    _required_version,
)
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
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class ListDatasetsHandler:
    """查询项目下数据集列表，支持游标分页。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._datasets = datasets
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Dataset], str | None]:
        await self._project_access.ensure_member(actor, project_id)
        return await self._datasets.list_by_project(project_id, limit=limit, cursor=cursor)


class GetDatasetHandler:
    """查询单个数据集详情。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._datasets = datasets
        self._project_access = project_access

    async def execute(self, actor: User, dataset_id: DatasetId) -> Dataset:
        dataset = await _required_dataset(self._datasets, dataset_id)
        await self._project_access.ensure_member(actor, dataset.project_id)
        return dataset


class ListDatasetVersionsHandler:
    """查询数据集的所有版本（按版本号倒序）。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._project_access = project_access

    async def execute(self, actor: User, dataset_id: DatasetId) -> list[DatasetVersion]:
        dataset = await _required_dataset(self._datasets, dataset_id)
        await self._project_access.ensure_member(actor, dataset.project_id)
        return await self._versions.list_by_dataset(dataset.dataset_id)


class GetDatasetVersionHandler:
    """查询单个数据集版本详情。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        version_id: DatasetVersionId,
    ) -> DatasetVersion:
        version = await _required_version(self._versions, version_id)
        dataset = await _required_dataset(self._datasets, version.dataset_id)
        await self._project_access.ensure_member(actor, dataset.project_id)
        return version


class ListTestCasesHandler:
    """查询数据集版本下的测试用例列表，支持游标分页。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        cases: TestCaseRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._cases = cases
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        dataset_version_id: DatasetVersionId,
        *,
        limit: int = 200,
        cursor: str | None = None,
    ) -> tuple[list[TestCase], str | None]:
        version = await _required_version(self._versions, dataset_version_id)
        dataset = await _required_dataset(self._datasets, version.dataset_id)
        await self._project_access.ensure_member(actor, dataset.project_id)
        return await self._cases.list_by_version(dataset_version_id, limit=limit, cursor=cursor)


class GetTestCaseHandler:
    """查询单个测试用例详情。"""

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        cases: TestCaseRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._cases = cases
        self._project_access = project_access

    async def execute(self, actor: User, case_id: TestCaseId) -> TestCase:
        from agenttest.modules.datasets.application.commands import (
            _required_case,
        )

        case = await _required_case(self._cases, case_id)
        version = await _required_version(self._versions, case.dataset_version_id)
        dataset = await _required_dataset(self._datasets, version.dataset_id)
        await self._project_access.ensure_member(actor, dataset.project_id)
        return case
