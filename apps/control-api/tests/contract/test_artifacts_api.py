from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID, uuid4

from agenttest.modules.artifacts.api.router import (
    ArtifactApiDependencies,
    create_artifact_router,
)
from agenttest.modules.artifacts.application.service import (
    ArtifactDownload,
    ArtifactRunNotFound,
    ArtifactTooLarge,
    ArtifactUploadResult,
)
from agenttest.modules.artifacts.domain.models import Artifact, ArtifactId
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

PROJECT_ID = uuid4()
RUN_ID = uuid4()
ARTIFACT_ID = ArtifactId(str(uuid4()))


def make_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("artifact-editor@example.com"),
        display_name="Artifact editor",
        role=SystemRole.DEVELOPER,
    )


@dataclass
class StubArtifactService:
    upload_error: Exception | None = None

    def __post_init__(self) -> None:
        self.uploaded_content = b""
        self.uploaded_filename = ""
        self.uploaded_internal = False

    async def upload(self, **kwargs: object) -> ArtifactUploadResult:
        if self.upload_error is not None:
            raise self.upload_error
        source = kwargs["source"]
        chunks: list[bytes] = []
        while chunk := await source.read(64 * 1024):  # type: ignore[union-attr]
            chunks.append(chunk)
        self.uploaded_content = b"".join(chunks)
        self.uploaded_filename = str(kwargs["filename"])
        self.uploaded_internal = bool(kwargs.get("internal", False))
        artifact = Artifact(
            id=ARTIFACT_ID,
            project_id=kwargs["project_id"],  # type: ignore[arg-type]
            run_id=kwargs["run_id"],  # type: ignore[arg-type]
            filename="report.txt",
            content_type="text/plain",
            size_bytes=len(self.uploaded_content),
            storage_path="objects/report",
        )
        return ArtifactUploadResult(artifact=artifact, sha256="expected-digest")

    async def list_for_run(self, **kwargs: object) -> list[Artifact]:
        del kwargs
        return []

    async def download(self, **kwargs: object) -> ArtifactDownload:
        del kwargs
        artifact = Artifact(
            id=ARTIFACT_ID,
            project_id=PROJECT_ID,
            run_id=RUN_ID,
            filename="report.txt",
            content_type="text/plain",
            size_bytes=11,
            storage_path="objects/report",
        )

        async def chunks() -> AsyncIterator[bytes]:
            yield b"hello "
            yield b"world"

        return ArtifactDownload(artifact=artifact, chunks=chunks())


def client_for(
    service: StubArtifactService,
    *,
    csrf_allowed: bool = True,
    project_allowed: bool = True,
) -> tuple[TestClient, list[tuple[UUID, bool]]]:
    actor = make_user()
    access_calls: list[tuple[UUID, bool]] = []

    async def resolve_actor(request: Request) -> User:
        del request
        return actor

    def check_csrf(request: Request) -> None:
        del request
        if not csrf_allowed:
            raise PermissionError("CSRF mismatch")

    async def check_project(user: User, project_id: UUID, write: bool) -> None:
        assert user is actor
        access_calls.append((project_id, write))
        if not project_allowed:
            raise PermissionError("Project access denied")

    app = FastAPI()
    app.include_router(
        create_artifact_router(
            ArtifactApiDependencies(
                service=service,  # type: ignore[arg-type]
                actor=resolve_actor,
                csrf=check_csrf,
                project_access=check_project,
                internal_token="test-internal-token",
            )
        ),
        prefix="/api/v1",
    )
    return TestClient(app, raise_server_exceptions=False), access_calls


def test_authenticated_upload_checks_write_access_and_streams_to_service() -> None:
    service = StubArtifactService()
    client, access_calls = client_for(service)

    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/runs/{RUN_ID}/artifacts",
        files={"file": ("../report.txt", b"hello world", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "report.txt"
    assert service.uploaded_content == b"hello world"
    assert service.uploaded_filename == "../report.txt"
    assert service.uploaded_internal is False
    assert access_calls == [(PROJECT_ID, True)]


def test_upload_rejects_csrf_before_project_or_content_access() -> None:
    service = StubArtifactService()
    client, access_calls = client_for(service, csrf_allowed=False)

    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/runs/{RUN_ID}/artifacts",
        files={"file": ("secret.txt", b"secret", "text/plain")},
    )

    assert response.status_code == 403
    assert access_calls == []
    assert service.uploaded_content == b""


def test_upload_rejects_cross_project_run_without_disclosing_it() -> None:
    service = StubArtifactService(upload_error=ArtifactRunNotFound())
    client, _ = client_for(service)

    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/runs/{RUN_ID}/artifacts",
        files={"file": ("secret.txt", b"secret", "text/plain")},
    )

    assert response.status_code == 404


def test_upload_limit_uses_rfc7807_response() -> None:
    service = StubArtifactService(upload_error=ArtifactTooLarge())
    client, _ = client_for(service)

    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/runs/{RUN_ID}/artifacts",
        files={"file": ("large.bin", b"too large", "application/octet-stream")},
    )

    assert response.status_code == 413
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 413


def test_internal_upload_rejects_invalid_token() -> None:
    service = StubArtifactService()
    client, _ = client_for(service)

    response = client.post(
        f"/api/v1/internal/projects/{PROJECT_ID}/runs/{RUN_ID}/artifacts",
        headers={"X-Internal-Token": "wrong-internal-token"},
        data={"run_case_id": str(uuid4())},
        files={"file": ("report.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 403
    assert service.uploaded_content == b""


def test_download_streams_chunks_and_uses_safe_content_disposition() -> None:
    service = StubArtifactService()
    client, access_calls = client_for(service)

    response = client.get(f"/api/v1/projects/{PROJECT_ID}/artifacts/{ARTIFACT_ID}/download")

    assert response.status_code == 200
    assert response.content == b"hello world"
    assert response.headers["content-disposition"] == ("attachment; filename*=UTF-8''report.txt")
    assert access_calls == [(PROJECT_ID, False)]
