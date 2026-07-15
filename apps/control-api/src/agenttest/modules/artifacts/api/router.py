"""Artifact HTTP adapter with bounded, project-scoped transfers."""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import cast
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.datastructures import UploadFile

from agenttest.modules.artifacts.application.service import (
    ArtifactHashMismatch,
    ArtifactNotFound,
    ArtifactRunNotFound,
    ArtifactService,
    ArtifactTooLarge,
)
from agenttest.modules.artifacts.domain.models import Artifact, ArtifactId, UploadSource
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.problem_details import ProblemDetails


@dataclass(frozen=True, slots=True)
class ArtifactApiDependencies:
    service: ArtifactService
    actor: Callable[[Request], Awaitable[User]]
    csrf: Callable[[Request], None]
    project_access: Callable[[User, UUID, bool], Awaitable[None]]
    internal_token: str


def create_artifact_router(dependencies: ArtifactApiDependencies) -> APIRouter:
    router = APIRouter(tags=["artifacts"])

    async def authorize(
        request: Request,
        project_id: UUID,
        *,
        write: bool,
        csrf: bool = False,
    ) -> User | JSONResponse:
        try:
            actor = await dependencies.actor(request)
        except InvalidSessionError:
            return problem_response(401, "Authentication required", "Unauthorized")
        if csrf:
            try:
                dependencies.csrf(request)
            except PermissionError:
                return problem_response(403, "Request rejected", "CSRF validation failed")
        try:
            await dependencies.project_access(actor, project_id, write)
        except ProjectNotFoundError:
            return problem_response(404, "Project not found", "Project not found")
        except PermissionError:
            return problem_response(403, "Project access denied", "Forbidden")
        return actor

    @router.post(
        "/projects/{project_id}/runs/{run_id}/artifacts",
        summary="上传产物",
        response_model=None,
    )
    async def upload_artifact(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ) -> dict[str, object] | JSONResponse:
        actor = await authorize(request, project_id, write=True, csrf=True)
        if isinstance(actor, JSONResponse):
            return actor
        upload = await uploaded_file(request)
        try:
            result = await dependencies.service.upload(
                project_id=project_id,
                run_id=run_id,
                source=cast(UploadSource, upload),
                filename=upload.filename or "artifact",
                content_type=upload.content_type or "application/octet-stream",
            )
        except ArtifactRunNotFound:
            return problem_response(404, "Run not found", "Run not found")
        except ArtifactTooLarge:
            return problem_response(413, "Artifact too large", "Upload limit exceeded")
        return artifact_response(result.artifact)

    @router.get(
        "/projects/{project_id}/runs/{run_id}/artifacts",
        summary="列出产物",
        response_model=None,
    )
    async def list_artifacts(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ) -> dict[str, object] | JSONResponse:
        actor = await authorize(request, project_id, write=False)
        if isinstance(actor, JSONResponse):
            return actor
        artifacts = await dependencies.service.list_for_run(
            project_id=project_id,
            run_id=run_id,
        )
        return {"items": [artifact_response(artifact) for artifact in artifacts]}

    @router.get(
        "/projects/{project_id}/artifacts/{artifact_id}/download",
        summary="下载产物",
        response_model=None,
    )
    async def download_artifact(
        request: Request,
        project_id: UUID,
        artifact_id: UUID,
    ) -> StreamingResponse | JSONResponse:
        actor = await authorize(request, project_id, write=False)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            download = await dependencies.service.download(
                project_id=project_id,
                artifact_id=ArtifactId(str(artifact_id)),
            )
        except ArtifactNotFound:
            return problem_response(404, "Artifact not found", "Artifact not found")
        artifact = download.artifact
        return StreamingResponse(
            download.chunks,
            media_type=artifact.content_type,
            headers={
                "Content-Disposition": (
                    "attachment; filename*=UTF-8''" + quote(artifact.filename, safe="")
                ),
                "Content-Length": str(artifact.size_bytes),
            },
        )

    @router.post(
        "/internal/projects/{project_id}/runs/{run_id}/artifacts",
        status_code=201,
        response_model=None,
    )
    async def upload_internal_artifact(
        request: Request,
        project_id: UUID,
        run_id: UUID,
        x_internal_token: str | None = Header(default=None),
    ) -> dict[str, object] | JSONResponse:
        supplied_token = x_internal_token or ""
        if not secrets.compare_digest(supplied_token, dependencies.internal_token):
            return problem_response(403, "Permission denied", "Permission denied")
        form = await request.form()
        upload = form.get("file")
        run_case_value = form.get("run_case_id")
        if not isinstance(upload, UploadFile) or not run_case_value:
            return problem_response(400, "Invalid upload", "Invalid artifact upload")
        try:
            run_case_id = UUID(str(run_case_value))
        except ValueError:
            return problem_response(400, "Invalid upload", "Invalid run case id")
        expected_sha256 = str(form.get("sha256") or "") or None
        try:
            result = await dependencies.service.upload(
                project_id=project_id,
                run_id=run_id,
                run_case_id=run_case_id,
                source=cast(UploadSource, upload),
                filename=upload.filename or "artifact",
                content_type=upload.content_type or "application/octet-stream",
                internal=True,
                expected_sha256=expected_sha256,
            )
        except ArtifactRunNotFound:
            return problem_response(404, "Run case not found", "Run case not found")
        except ArtifactTooLarge:
            return problem_response(413, "Artifact too large", "Upload limit exceeded")
        except ArtifactHashMismatch:
            return problem_response(422, "Artifact hash mismatch", "Artifact hash mismatch")
        response = artifact_response(result.artifact)
        response.update(
            storage_path=result.artifact.storage_path,
            sha256=result.sha256,
        )
        return response

    return router


async def uploaded_file(request: Request) -> UploadFile:
    upload = (await request.form()).get("file")
    if not isinstance(upload, UploadFile):
        raise HTTPException(status_code=400, detail="Missing upload file")
    return upload


def artifact_response(artifact: Artifact) -> dict[str, object]:
    return {
        "id": str(artifact.id),
        "filename": artifact.filename,
        "content_type": artifact.content_type,
        "size_bytes": artifact.size_bytes,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


def problem_response(status: int, title: str, detail: str) -> JSONResponse:
    problem = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
