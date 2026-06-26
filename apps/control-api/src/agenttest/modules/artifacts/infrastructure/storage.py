"""文件系统产物存储。"""

from __future__ import annotations

import hashlib
from pathlib import Path


class FileSystemArtifactStorage:
    """本地文件系统产物存储。"""

    def __init__(self, base_path: Path) -> None:
        self._base = base_path

    async def store(self, *, filename: str, content: bytes) -> str:
        """保存文件，按日期 + 哈希分目录。"""
        h = hashlib.sha256(content).hexdigest()[:12]
        dir_path = self._base / h[:2] / h[2:4]
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / f"{h}_{filename}"
        file_path.write_bytes(content)
        return str(file_path.relative_to(self._base))

    async def retrieve(self, storage_path: str) -> bytes:
        return (self._base / storage_path).read_bytes()

    async def delete(self, storage_path: str) -> None:
        path = self._base / storage_path
        if path.exists():
            path.unlink()
