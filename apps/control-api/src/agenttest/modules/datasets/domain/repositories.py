"""Dataset domain repository protocols."""

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


class DatasetVersionRepository(Protocol):
    async def get_by_id(self, version_id: DatasetVersionId) -> DatasetVersion | None: ...

    async def list_by_dataset(self, dataset_id: DatasetId) -> list[DatasetVersion]: ...

    async def get_next_version_number(self, dataset_id: DatasetId) -> int: ...

    async def add(self, version: DatasetVersion) -> None: ...

    async def save(self, version: DatasetVersion) -> None: ...


class TestCaseRepository(Protocol):
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
