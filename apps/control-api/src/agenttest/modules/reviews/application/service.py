from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reviews.domain.entities import ReviewTask, ReviewTaskId
from agenttest.modules.runs.public import ProjectAccessPort


class ReviewRepository(Protocol):
    async def get_by_id_and_project(
        self,
        task_id: ReviewTaskId,
        project_id: ProjectId,
    ) -> ReviewTask | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ReviewTask], int]: ...

    async def save(self, task: ReviewTask) -> None: ...

    async def auto_enqueue_low_confidence(
        self,
        project_id: ProjectId,
        run_id: str,
        confidence_threshold: float,
    ) -> list[ReviewTask]: ...

    async def get_stats(self, project_id: ProjectId) -> dict[str, int]: ...


class ReviewTaskNotFound(Exception):
    pass


class ReviewTaskAlreadyReviewed(Exception):
    pass


class ReviewValidationError(Exception):
    pass


class ReviewService:
    def __init__(self, *, reviews: ReviewRepository, project_access: ProjectAccessPort) -> None:
        self._reviews = reviews
        self._project_access = project_access

    async def list_reviews(
        self,
        actor: User,
        project_id: UUID,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ReviewTask], int]:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        return await self._reviews.list_by_project(
            project,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def stats(self, actor: User, project_id: UUID) -> dict[str, int]:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        return await self._reviews.get_stats(project)

    async def auto_enqueue(
        self,
        actor: User,
        project_id: UUID,
        run_id: str,
        confidence_threshold: float,
    ) -> list[ReviewTask]:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        return await self._reviews.auto_enqueue_low_confidence(
            project,
            run_id,
            confidence_threshold,
        )

    async def score(
        self,
        actor: User,
        project_id: UUID,
        task_id: UUID,
        *,
        score: float,
        opinion: str | None,
        rubric_scores: dict[str, float] | None,
    ) -> ReviewTask:
        task = await self._pending(actor, project_id, task_id)
        try:
            task.approve(
                actor.user_id.value,
                score=score,
                opinion=opinion,
                rubric_scores=rubric_scores,
            )
        except ValueError as error:
            raise ReviewValidationError(str(error)) from error
        await self._reviews.save(task)
        return task

    async def reject(
        self,
        actor: User,
        project_id: UUID,
        task_id: UUID,
        opinion: str | None,
    ) -> ReviewTask:
        task = await self._pending(actor, project_id, task_id)
        task.reject(actor.user_id.value, opinion=opinion)
        await self._reviews.save(task)
        return task

    async def skip(self, actor: User, project_id: UUID, task_id: UUID) -> ReviewTask:
        task = await self._pending(actor, project_id, task_id)
        try:
            task.skip()
        except ValueError as error:
            raise ReviewValidationError(str(error)) from error
        await self._reviews.save(task)
        return task

    async def _pending(self, actor: User, project_id: UUID, task_id: UUID) -> ReviewTask:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        task = await self._reviews.get_by_id_and_project(ReviewTaskId(task_id), project)
        if task is None:
            raise ReviewTaskNotFound
        if task.status.value != "pending":
            raise ReviewTaskAlreadyReviewed
        return task
