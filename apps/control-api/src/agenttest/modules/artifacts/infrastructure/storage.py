"""文件系统产物存储。"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4


class FileSystemArtifactStorage:
    """本地文件系统产物存储。"""

    def __init__(self, base_path: Path) -> None:
        self._base = base_path.resolve()

    async def begin(self, *, filename: str) -> str:
        temporary_key = f"tmp/{uuid4().hex}.upload"
        path = self._resolve(temporary_key)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.touch, mode=0o600, exist_ok=False)
        return temporary_key

    async def append(self, temporary_key: str, chunk: bytes) -> None:
        path = self._resolve(temporary_key)
        await asyncio.to_thread(_append_bytes, path, chunk)

    async def commit(self, temporary_key: str) -> str:
        temporary_path = self._resolve(temporary_key)
        digest = await asyncio.to_thread(_sha256, temporary_path)
        storage_path = f"objects/{digest[:2]}/{digest[2:4]}/{digest}"
        final_path = self._resolve(storage_path)
        await asyncio.to_thread(final_path.parent.mkdir, parents=True, exist_ok=True)
        if final_path.exists():
            await asyncio.to_thread(temporary_path.unlink)
        else:
            await asyncio.to_thread(temporary_path.replace, final_path)
        return storage_path

    async def abort(self, temporary_key: str) -> None:
        await self.delete(temporary_key)

    async def iter_chunks(
        self,
        storage_path: str,
        chunk_size: int,
    ) -> AsyncIterator[bytes]:
        path = self._resolve(storage_path)
        handle = await asyncio.to_thread(path.open, "rb")
        try:
            while chunk := await asyncio.to_thread(handle.read, chunk_size):
                yield chunk
        finally:
            await asyncio.to_thread(handle.close)

    async def delete(self, storage_path: str) -> None:
        path = self._resolve(storage_path)
        if path.exists():
            await asyncio.to_thread(path.unlink)

    def _resolve(self, storage_path: str) -> Path:
        candidate = (self._base / storage_path).resolve()
        try:
            candidate.relative_to(self._base)
        except ValueError as error:
            raise ValueError("path is outside artifact storage") from error
        return candidate


def _append_bytes(path: Path, chunk: bytes) -> None:
    with path.open("ab") as handle:
        handle.write(chunk)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
