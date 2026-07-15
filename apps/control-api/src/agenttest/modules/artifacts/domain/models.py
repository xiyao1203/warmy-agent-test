"""Artifact 产物领域模型。"""

from __future__ import annotations

from collections.abc import AsyncIterator
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

    async def run_exists(
        self,
        *,
        project_id: UUID,
        run_id: UUID,
        run_case_id: UUID | None,
    ) -> bool: ...
    async def save(self, artifact: Artifact, *, project_id: UUID) -> None: ...
    async def get(self, artifact_id: ArtifactId, *, project_id: UUID) -> Artifact | None: ...
    async def list_by_run(self, run_id: UUID, *, project_id: UUID) -> list[Artifact]: ...


class UploadSource(Protocol):
    async def read(self, size: int) -> bytes: ...


class ArtifactStorage(Protocol):
    """产物文件存储协议。"""

    async def begin(self, *, filename: str) -> str: ...
    async def append(self, temporary_key: str, chunk: bytes) -> None: ...
    async def commit(self, temporary_key: str) -> str: ...
    async def abort(self, temporary_key: str) -> None: ...
    async def delete(self, storage_path: str) -> None: ...
    def iter_chunks(
        self,
        storage_path: str,
        chunk_size: int,
    ) -> AsyncIterator[bytes]: ...
