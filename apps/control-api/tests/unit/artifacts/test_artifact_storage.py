from __future__ import annotations

from pathlib import Path

import pytest
from agenttest.modules.artifacts.infrastructure.storage import FileSystemArtifactStorage


@pytest.mark.asyncio
async def test_storage_promotes_temporary_upload_and_streams_chunks(tmp_path: Path) -> None:
    storage = FileSystemArtifactStorage(tmp_path)

    temporary_key = await storage.begin(filename="evidence.bin")
    await storage.append(temporary_key, b"abc")
    await storage.append(temporary_key, b"def")
    storage_path = await storage.commit(temporary_key)

    assert not (tmp_path / temporary_key).exists()
    assert (tmp_path / storage_path).read_bytes() == b"abcdef"
    chunks = [chunk async for chunk in storage.iter_chunks(storage_path, 2)]
    assert chunks == [b"ab", b"cd", b"ef"]


@pytest.mark.asyncio
async def test_storage_abort_removes_temporary_upload(tmp_path: Path) -> None:
    storage = FileSystemArtifactStorage(tmp_path)
    temporary_key = await storage.begin(filename="evidence.bin")
    await storage.append(temporary_key, b"partial")

    await storage.abort(temporary_key)

    assert not (tmp_path / temporary_key).exists()


@pytest.mark.asyncio
async def test_storage_rejects_paths_outside_root(tmp_path: Path) -> None:
    storage = FileSystemArtifactStorage(tmp_path)

    with pytest.raises(ValueError, match="outside artifact storage"):
        await storage.delete("../../outside.txt")
