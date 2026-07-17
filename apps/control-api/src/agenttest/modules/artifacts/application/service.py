from __future__ import annotations

import hashlib
import secrets
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from agenttest.modules.artifacts.domain.models import (
    Artifact,
    ArtifactId,
    ArtifactRepository,
    ArtifactStorage,
    UploadSource,
)

UPLOAD_CHUNK_SIZE = 64 * 1024


class ArtifactRunNotFound(Exception):
    """The requested Run or RunCase is outside the project scope."""


class ArtifactTooLarge(Exception):
    """The uploaded payload exceeds the configured byte limit."""


class ArtifactNotFound(Exception):
    """The Artifact is unavailable within the requested project."""


class ArtifactHashMismatch(Exception):
    """The uploaded payload does not match the caller-provided digest."""


@dataclass(frozen=True, slots=True)
class ArtifactUploadResult:
    artifact: Artifact
    sha256: str


@dataclass(frozen=True, slots=True)
class ArtifactDownload:
    artifact: Artifact
    chunks: AsyncIterator[bytes]


class ArtifactService:
    def __init__(
        self,
        *,
        repository: ArtifactRepository,
        storage: ArtifactStorage,
        user_limit_bytes: int,
        internal_limit_bytes: int,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._user_limit_bytes = user_limit_bytes
        self._internal_limit_bytes = internal_limit_bytes

    async def upload(
        self,
        *,
        project_id: UUID,
        run_id: UUID,
        source: UploadSource,
        filename: str,
        content_type: str,
        run_case_id: UUID | None = None,
        internal: bool = False,
        expected_sha256: str | None = None,
    ) -> ArtifactUploadResult:
        if not await self._repository.run_exists(
            project_id=project_id,
            run_id=run_id,
            run_case_id=run_case_id,
        ):
            raise ArtifactRunNotFound

        safe_filename = sanitize_filename(filename)
        temporary_key = await self._storage.begin(filename=safe_filename)
        promoted_key: str | None = None
        size_bytes = 0
        digest = hashlib.sha256()
        limit = self._internal_limit_bytes if internal else self._user_limit_bytes

        try:
            while chunk := await source.read(UPLOAD_CHUNK_SIZE):
                size_bytes += len(chunk)
                if size_bytes > limit:
                    raise ArtifactTooLarge
                digest.update(chunk)
                await self._storage.append(temporary_key, chunk)

            actual_sha256 = digest.hexdigest()
            if expected_sha256 and not secrets.compare_digest(
                expected_sha256.lower(), actual_sha256
            ):
                raise ArtifactHashMismatch

            promoted_key = await self._storage.commit(temporary_key)
            artifact = Artifact(
                id=ArtifactId(str(uuid4())),
                project_id=project_id,
                run_id=run_id,
                filename=safe_filename,
                content_type=content_type,
                size_bytes=size_bytes,
                storage_path=promoted_key,
            )
            try:
                await self._repository.save(artifact, project_id=project_id)
            except BaseException:
                await self._storage.delete(promoted_key)
                raise
            return ArtifactUploadResult(artifact=artifact, sha256=actual_sha256)
        except BaseException:
            if promoted_key is None:
                await self._storage.abort(temporary_key)
            raise

    async def list_for_run(self, *, project_id: UUID, run_id: UUID) -> list[Artifact]:
        return await self._repository.list_by_run(run_id, project_id=project_id)

    async def download(
        self,
        *,
        project_id: UUID,
        artifact_id: ArtifactId,
    ) -> ArtifactDownload:
        artifact = await self._repository.get(artifact_id, project_id=project_id)
        if artifact is None:
            raise ArtifactNotFound
        return ArtifactDownload(
            artifact=artifact,
            chunks=self._storage.iter_chunks(artifact.storage_path, UPLOAD_CHUNK_SIZE),
        )


def sanitize_filename(filename: str) -> str:
    basename = PurePosixPath(filename.replace("\\", "/")).name
    cleaned = "".join(character for character in basename if 31 < ord(character) != 127)
    cleaned = cleaned.strip().strip(".")
    return cleaned[:255] or "artifact"
