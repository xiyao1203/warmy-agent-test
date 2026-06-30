"""Dataset 领域仓库接口。

定义 DatasetRepository、DatasetVersionRepository 和 TestCaseRepository
的抽象协议，由基础设施层实现。
"""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
    TestCase,
    TestCaseId,
)
from agenttest.modules.projects.public import ProjectId


class DatasetRepository(Protocol):
    """数据集聚合根的持久化仓库接口。"""

    async def get_by_id(self, dataset_id: DatasetId) -> Dataset | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Dataset], str | None]: ...

    async def add(self, dataset: Dataset) -> None: ...

    async def save(self, dataset: Dataset) -> None: ...

    async def delete(self, dataset_id: DatasetId) -> None: ...


class DatasetVersionRepository(Protocol):
    """数据集版本的持久化仓库接口。"""

    async def get_by_id(self, version_id: DatasetVersionId) -> DatasetVersion | None: ...

    async def list_by_dataset(self, dataset_id: DatasetId) -> list[DatasetVersion]: ...

    async def get_next_version_number(self, dataset_id: DatasetId) -> int: ...

    async def add(self, version: DatasetVersion) -> None: ...

    async def save(self, version: DatasetVersion) -> None: ...


class TestCaseRepository(Protocol):
    """测试用例的持久化仓库接口。"""

    async def get_by_id(self, case_id: TestCaseId) -> TestCase | None: ...

    async def list_by_version(
        self,
        dataset_version_id: DatasetVersionId,
        *,
        limit: int = 200,
        cursor: str | None = None,
    ) -> tuple[list[TestCase], str | None]: ...

    async def add(self, case: TestCase) -> None: ...

    async def save(self, case: TestCase) -> None: ...

    async def delete(self, case_id: TestCaseId) -> None: ...

    async def get_max_sort_order(self, dataset_version_id: DatasetVersionId) -> int: ...

    async def count_by_version(self, dataset_version_id: DatasetVersionId) -> int: ...
