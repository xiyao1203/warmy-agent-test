"""Artifact API 路由。

提供产物上传、列表和下载端点。
所有端点受 current_user + csrf + project_id 隔离保护。
"""

from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from agenttest.modules.artifacts.domain.models import (
    Artifact,
    ArtifactId,
)
from agenttest.modules.artifacts.infrastructure.repositories import (
    SqlAlchemyArtifactRepository,
)
from agenttest.modules.artifacts.infrastructure.storage import (
    FileSystemArtifactStorage,
)


def create_artifact_router(
    storage: FileSystemArtifactStorage,
    session_factory,
    *,
    _actor,
    _check_csrf,
    _check_project,
    internal_token: str,
) -> APIRouter:
    router = APIRouter(tags=["artifacts"])

    @router.post(
        "/projects/{project_id}/runs/{run_id}/artifacts",
        summary="上传产物",
    )
    async def upload_artifact(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ):
        try:
            await _actor(request)
            _check_csrf(request)
            await _check_project(project_id)
        except Exception as exc:
            if "InvalidSession" in type(exc).__name__:
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"detail": "Unauthorized"},
                )
            if "PermissionError" in str(exc) or "CSRF" in str(exc):
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"detail": "Forbidden"},
                )
            if "ProjectNotFound" in type(exc).__name__:
                return JSONResponse(
                    status_code=HTTP_404_NOT_FOUND,
                    content={"detail": "Project not found"},
                )
            raise

        form = await request.form()
        file = form.get("file")
        if not file or not hasattr(file, "filename"):
            raise HTTPException(status_code=400, detail="缺少上传文件")

        content = await file.read()  # type: ignore[union-attr]
        ct = getattr(file, "content_type", "") or "application/octet-stream"
        fn = getattr(file, "filename", "") or "artifact"

        async with session_factory() as session:
            repo = SqlAlchemyArtifactRepository(session)
            storage_path = await storage.store(filename=fn, content=content)

            artifact = Artifact(
                id=ArtifactId(str(uuid4())),
                project_id=project_id,
                run_id=run_id,
                filename=fn,
                content_type=ct,
                size_bytes=len(content),
                storage_path=storage_path,
            )
            await repo.save(artifact, project_id=project_id)
            await session.commit()

            return {
                "id": str(artifact.id),
                "filename": artifact.filename,
                "content_type": artifact.content_type,
                "size_bytes": artifact.size_bytes,
                "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
            }

    @router.get(
        "/projects/{project_id}/runs/{run_id}/artifacts",
        summary="列出产物",
    )
    async def list_artifacts(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ):
        try:
            await _actor(request)
            await _check_project(project_id)
        except Exception as exc:
            if "InvalidSession" in type(exc).__name__:
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"detail": "Unauthorized"},
                )
            if "ProjectNotFound" in type(exc).__name__:
                return JSONResponse(
                    status_code=HTTP_404_NOT_FOUND,
                    content={"detail": "Project not found"},
                )
            raise

        async with session_factory() as session:
            repo = SqlAlchemyArtifactRepository(session)
            artifacts = await repo.list_by_run(run_id, project_id=project_id)
            return {
                "items": [
                    {
                        "id": str(a.id),
                        "filename": a.filename,
                        "content_type": a.content_type,
                        "size_bytes": a.size_bytes,
                        "created_at": a.created_at.isoformat(),  # type: ignore[union-attr]
                    }
                    for a in artifacts
                ]
            }

    @router.get(
        "/projects/{project_id}/artifacts/{artifact_id}/download",
        summary="下载产物",
    )
    async def download_artifact(
        request: Request,
        project_id: UUID,
        artifact_id: UUID,
    ):
        try:
            await _actor(request)
            await _check_project(project_id)
        except Exception as exc:
            if "InvalidSession" in type(exc).__name__:
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"detail": "Unauthorized"},
                )
            if "ProjectNotFound" in type(exc).__name__:
                return JSONResponse(
                    status_code=HTTP_404_NOT_FOUND,
                    content={"detail": "Project not found"},
                )
            raise

        async with session_factory() as session:
            repo = SqlAlchemyArtifactRepository(session)
            artifact = await repo.get(
                ArtifactId(str(artifact_id)),
                project_id=project_id,
            )
            if artifact is None:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="产物不存在")
            content = await storage.retrieve(artifact.storage_path)
            return StreamingResponse(
                iter([content]),
                media_type=artifact.content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{artifact.filename}"',
                    "Content-Length": str(artifact.size_bytes),
                },
            )

    @router.post("/internal/projects/{project_id}/runs/{run_id}/artifacts", status_code=201)
    async def upload_internal_artifact(
        request: Request,
        project_id: UUID,
        run_id: UUID,
        x_internal_token: str | None = Header(default=None),
    ):
        if x_internal_token != internal_token:
            return JSONResponse(status_code=403, content={"detail": "Permission denied"})
        form = await request.form()
        file = form.get("file")
        run_case_id = form.get("run_case_id")
        expected_hash = str(form.get("sha256") or "")
        if not file or not hasattr(file, "read") or not run_case_id:
            raise HTTPException(status_code=400, detail="Invalid artifact upload")
        content = await file.read()  # type: ignore[union-attr]
        digest = hashlib.sha256(content).hexdigest()
        if expected_hash and expected_hash != digest:
            raise HTTPException(status_code=422, detail="Artifact hash mismatch")
        from sqlalchemy import text

        async with session_factory() as session:
            scoped = await session.scalar(
                text(
                    """
                    SELECT 1 FROM run_cases rc JOIN runs r ON r.id = rc.run_id
                    WHERE r.project_id = :project_id AND r.id = :run_id AND rc.id = :case_id
                    """
                ),
                {"project_id": project_id, "run_id": run_id, "case_id": UUID(str(run_case_id))},
            )
            if scoped is None:
                raise HTTPException(status_code=404, detail="Run case not found")
            filename = getattr(file, "filename", "artifact") or "artifact"
            content_type = getattr(file, "content_type", None) or "application/octet-stream"
            storage_path = await storage.store(filename=filename, content=content)
            artifact = Artifact(
                id=ArtifactId(str(uuid4())),
                project_id=project_id,
                run_id=run_id,
                filename=filename,
                content_type=content_type,
                size_bytes=len(content),
                storage_path=storage_path,
            )
            await SqlAlchemyArtifactRepository(session).save(artifact, project_id=project_id)
            await session.commit()
        return {
            "id": str(artifact.id),
            "filename": artifact.filename,
            "content_type": artifact.content_type,
            "size_bytes": artifact.size_bytes,
            "storage_path": artifact.storage_path,
            "sha256": digest,
        }

    return router
