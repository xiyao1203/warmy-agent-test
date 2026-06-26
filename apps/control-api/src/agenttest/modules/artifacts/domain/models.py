"""Artifact 产物领域模型。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


class ArtifactId(UUID):
    """产物 ID。"""
    pass


@dataclass
class Artifact:
    """运行产物实体。"""

    id: ArtifactId
    project_id: UUID
    run_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    created_at: datetime | None = None


@dataclass
class ArtifactCreate:
    """创建产物的输入。"""

    run_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str


class ArtifactRepository(Protocol):
    """产物仓库协议。"""

    async def save(self, artifact: Artifact, *, project_id: UUID) -> None: ...
    async def get(self, artifact_id: ArtifactId, *, project_id: UUID) -> Artifact | None: ...
    async def list_by_run(self, run_id: UUID, *, project_id: UUID) -> list[Artifact]: ...


class ArtifactStorage(Protocol):
    """产物文件存储协议。"""

    async def store(self, *, filename: str, content: bytes) -> str:
        """保存文件，返回 storage_path。"""
        ...

    async def retrieve(self, storage_path: str) -> bytes:
        """读取文件内容。"""
        ...

    async def delete(self, storage_path: str) -> None:
        """删除存储的文件。"""
        ...
