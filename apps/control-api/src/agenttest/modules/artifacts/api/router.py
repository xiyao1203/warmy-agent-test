"""Artifact API 路由。

提供产物上传、列表和下载端点。
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from starlette.responses import StreamingResponse
from starlette.status import HTTP_404_NOT_FOUND

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
    *,
    current_user,
    csrf,
    settings,
    session_factory,
) -> APIRouter:
    """创建 artifact API 路由。"""
    router = APIRouter(tags=["artifacts"])

    @router.post(
        "/projects/{project_id}/runs/{run_id}/artifacts",
        summary="上传产物",
    )
    async def upload_artifact(
        project_id: UUID,
        run_id: UUID,
        file: UploadFile,
        _user=Depends(current_user),  # noqa: B008
        _csrf=Depends(csrf),  # noqa: B008
    ):
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        filename = file.filename or "artifact"

        async with session_factory() as session:
            repo = SqlAlchemyArtifactRepository(session)
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
        project_id: UUID,
        run_id: UUID,
        _user=Depends(current_user),  # noqa: B008
    ):
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
        project_id: UUID,
        artifact_id: UUID,
        _user=Depends(current_user),  # noqa: B008
    ):
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

    return router
