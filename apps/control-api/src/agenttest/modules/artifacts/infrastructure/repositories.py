"""Artifact ORM 与持久化。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.modules.artifacts.domain.models import (
    Artifact,
    ArtifactId,
)
from agenttest.shared.infrastructure.database import Base, session_scope, transaction_scope


class ArtifactModel(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "run_id"],
            ["runs.project_id", "runs.id"],
            name="fk_artifacts_project_run",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )


def _to_domain(row: ArtifactModel) -> Artifact:
    return Artifact(
        id=ArtifactId(str(row.id)),
        project_id=row.project_id,
        run_id=row.run_id,
        filename=row.filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        storage_path=row.storage_path,
        created_at=row.created_at,
    )


class SqlAlchemyArtifactRepository:
    """SqlAlchemy 产物仓库实现。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def run_exists(
        self,
        *,
        project_id: UUID,
        run_id: UUID,
        run_case_id: UUID | None,
    ) -> bool:
        if run_case_id is None:
            statement = text("SELECT 1 FROM runs WHERE project_id = :project_id AND id = :run_id")
            parameters = {"project_id": project_id, "run_id": run_id}
        else:
            statement = text(
                """
                SELECT 1
                FROM run_cases rc
                JOIN runs r ON r.id = rc.run_id
                WHERE r.project_id = :project_id
                  AND r.id = :run_id
                  AND rc.id = :run_case_id
                """
            )
            parameters = {
                "project_id": project_id,
                "run_id": run_id,
                "run_case_id": run_case_id,
            }
        async with session_scope(self._session_factory) as session:
            return await session.scalar(statement, parameters) is not None

    async def save(self, artifact: Artifact, *, project_id: UUID) -> None:
        row = ArtifactModel(
            id=artifact.id,
            project_id=project_id,
            run_id=artifact.run_id,
            filename=artifact.filename,
            content_type=artifact.content_type,
            size_bytes=artifact.size_bytes,
            storage_path=artifact.storage_path,
        )
        async with transaction_scope(self._session_factory) as session:
            session.add(row)
            await session.flush()

    async def get(self, artifact_id: ArtifactId, *, project_id: UUID) -> Artifact | None:
        async with session_scope(self._session_factory) as session:
            row = await session.get(ArtifactModel, artifact_id)
        if row is None or row.project_id != project_id:
            return None
        return _to_domain(row)

    async def list_by_run(self, run_id: UUID, *, project_id: UUID) -> list[Artifact]:
        stmt = (
            select(ArtifactModel)
            .where(ArtifactModel.run_id == run_id)
            .where(ArtifactModel.project_id == project_id)
            .order_by(ArtifactModel.created_at.desc())
        )
        async with session_scope(self._session_factory) as session:
            result = await session.execute(stmt)
            return [_to_domain(r) for r in result.scalars().all()]
