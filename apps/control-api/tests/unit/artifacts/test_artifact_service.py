from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from agenttest.modules.artifacts.application.service import (
    ArtifactHashMismatch,
    ArtifactNotFound,
    ArtifactRunNotFound,
    ArtifactService,
    ArtifactTooLarge,
    sanitize_filename,
)
from agenttest.modules.artifacts.domain.models import Artifact, ArtifactId


class CountingUpload:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = iter(chunks)
        self.read_calls = 0

    async def read(self, size: int) -> bytes:
        self.read_calls += 1
        return next(self._chunks, b"")


class CancelledUpload:
    async def read(self, size: int) -> bytes:
        del size
        raise BaseException("upload cancelled")


class FakeArtifactRepository:
    def __init__(self, *, run_exists: bool = True, save_error: Exception | None = None) -> None:
        self._run_exists = run_exists
        self._save_error = save_error
        self.saved: list[Artifact] = []

    async def run_exists(
        self,
        *,
        project_id: UUID,
        run_id: UUID,
        run_case_id: UUID | None,
    ) -> bool:
        return self._run_exists

    async def save(self, artifact: Artifact, *, project_id: UUID) -> None:
        if self._save_error is not None:
            raise self._save_error
        self.saved.append(artifact)

    async def get(self, artifact_id: ArtifactId, *, project_id: UUID) -> Artifact | None:
        return next((item for item in self.saved if item.id == artifact_id), None)

    async def list_by_run(self, run_id: UUID, *, project_id: UUID) -> list[Artifact]:
        return [
            item for item in self.saved if item.run_id == run_id and item.project_id == project_id
        ]


class FakeArtifactStorage:
    def __init__(self) -> None:
        self.temporary_key = "tmp/upload"
        self.final_key = "objects/evidence.bin"
        self.appended: list[bytes] = []
        self.aborted: list[str] = []
        self.deleted: list[str] = []

    async def begin(self, *, filename: str) -> str:
        return self.temporary_key

    async def append(self, temporary_key: str, chunk: bytes) -> None:
        assert temporary_key == self.temporary_key
        self.appended.append(chunk)

    async def commit(self, temporary_key: str) -> str:
        assert temporary_key == self.temporary_key
        return self.final_key

    async def abort(self, temporary_key: str) -> None:
        self.aborted.append(temporary_key)

    async def delete(self, storage_path: str) -> None:
        self.deleted.append(storage_path)

    async def iter_chunks(
        self,
        storage_path: str,
        chunk_size: int,
    ) -> AsyncIterator[bytes]:
        yield b"stored"


PROJECT_ID = uuid4()
RUN_ID = uuid4()


def make_service(
    repository: FakeArtifactRepository,
    storage: FakeArtifactStorage,
    *,
    user_limit_bytes: int = 64,
) -> ArtifactService:
    return ArtifactService(
        repository=repository,
        storage=storage,
        user_limit_bytes=user_limit_bytes,
        internal_limit_bytes=256,
    )


@pytest.mark.asyncio
async def test_upload_rejects_cross_project_run_before_reading_content() -> None:
    source = CountingUpload([b"secret"])
    storage = FakeArtifactStorage()
    service = make_service(FakeArtifactRepository(run_exists=False), storage)

    with pytest.raises(ArtifactRunNotFound):
        await service.upload(
            project_id=PROJECT_ID,
            run_id=RUN_ID,
            source=source,
            filename="evidence.png",
            content_type="image/png",
        )

    assert source.read_calls == 0
    assert storage.appended == []


@pytest.mark.asyncio
async def test_upload_stops_at_limit_and_aborts_temporary_object() -> None:
    source = CountingUpload([b"1234", b"56"])
    storage = FakeArtifactStorage()
    service = make_service(FakeArtifactRepository(), storage, user_limit_bytes=5)

    with pytest.raises(ArtifactTooLarge):
        await service.upload(
            project_id=PROJECT_ID,
            run_id=RUN_ID,
            source=source,
            filename="evidence.bin",
            content_type="application/octet-stream",
        )

    assert source.read_calls == 2
    assert storage.appended == [b"1234"]
    assert storage.aborted == [storage.temporary_key]


@pytest.mark.asyncio
async def test_upload_cancellation_aborts_temporary_object() -> None:
    storage = FakeArtifactStorage()
    service = make_service(FakeArtifactRepository(), storage)

    with pytest.raises(BaseException, match="upload cancelled"):
        await service.upload(
            project_id=PROJECT_ID,
            run_id=RUN_ID,
            source=CancelledUpload(),
            filename="evidence.bin",
            content_type="application/octet-stream",
        )

    assert storage.aborted == [storage.temporary_key]


def test_sanitize_filename_removes_paths_controls_and_empty_names() -> None:
    assert sanitize_filename("../../report.png") == "report.png"
    assert sanitize_filename("folder\\trace.json") == "trace.json"
    assert sanitize_filename("bad\x00name.txt") == "badname.txt"
    assert sanitize_filename("../") == "artifact"


@pytest.mark.asyncio
async def test_repository_failure_deletes_promoted_object() -> None:
    storage = FakeArtifactStorage()
    service = make_service(
        FakeArtifactRepository(save_error=RuntimeError("database failed")),
        storage,
    )

    with pytest.raises(RuntimeError, match="database failed"):
        await service.upload(
            project_id=PROJECT_ID,
            run_id=RUN_ID,
            source=CountingUpload([b"evidence"]),
            filename="evidence.bin",
            content_type="application/octet-stream",
        )

    assert storage.deleted == [storage.final_key]


@pytest.mark.asyncio
async def test_internal_upload_rejects_hash_mismatch_before_promotion() -> None:
    repository = FakeArtifactRepository()
    storage = FakeArtifactStorage()
    service = make_service(repository, storage)

    with pytest.raises(ArtifactHashMismatch):
        await service.upload(
            project_id=PROJECT_ID,
            run_id=RUN_ID,
            source=CountingUpload([b"evidence"]),
            filename="evidence.bin",
            content_type="application/octet-stream",
            internal=True,
            expected_sha256="0" * 64,
        )

    assert repository.saved == []
    assert storage.aborted == [storage.temporary_key]


@pytest.mark.asyncio
async def test_download_returns_storage_iterator_without_materializing_content() -> None:
    repository = FakeArtifactRepository()
    artifact = Artifact(
        id=ArtifactId(str(uuid4())),
        project_id=PROJECT_ID,
        run_id=RUN_ID,
        filename="evidence.bin",
        content_type="application/octet-stream",
        size_bytes=6,
        storage_path="objects/evidence.bin",
    )
    repository.saved.append(artifact)
    service = make_service(repository, FakeArtifactStorage())

    download = await service.download(
        project_id=PROJECT_ID,
        artifact_id=artifact.id,
    )

    assert download.artifact is artifact
    assert [chunk async for chunk in download.chunks] == [b"stored"]


@pytest.mark.asyncio
async def test_download_hides_artifacts_outside_project() -> None:
    service = make_service(FakeArtifactRepository(), FakeArtifactStorage())

    with pytest.raises(ArtifactNotFound):
        await service.download(
            project_id=PROJECT_ID,
            artifact_id=ArtifactId(str(uuid4())),
        )
