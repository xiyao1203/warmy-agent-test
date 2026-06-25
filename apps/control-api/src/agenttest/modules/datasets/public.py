"""Stable public interface for the datasets module.

Other modules must only import from this file when referencing datasets.
"""

from __future__ import annotations

from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
    TestCase,
    TestCaseId,
)
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
    TestGroup,
    VersionStatus,
)

__all__ = [
    "Dataset",
    "DatasetId",
    "DatasetVersion",
    "DatasetVersionId",
    "DatasetVersionRef",
    "ExecutionMode",
    "Priority",
    "RiskLevel",
    "TestCase",
    "TestCaseId",
    "TestGroup",
    "VersionStatus",
]


class DatasetVersionRef:
    """已发布数据集版本的轻量引用。

    供其他模块引用数据集版本时使用，避免加载完整实体。
    """

    __slots__ = ("dataset_version_id", "dataset_id", "version_number")

    def __init__(
        self,
        dataset_version_id: DatasetVersionId,
        dataset_id: DatasetId,
        version_number: int,
    ) -> None:
        self.dataset_version_id = dataset_version_id
        self.dataset_id = dataset_id
        self.version_number = version_number

    @classmethod
    def from_version(cls, version: DatasetVersion) -> DatasetVersionRef:
        """从完整 DatasetVersion 实体创建引用。"""
        return cls(version.version_id, version.dataset_id, version.version_number)
