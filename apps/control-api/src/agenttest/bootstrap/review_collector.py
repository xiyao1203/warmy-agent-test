from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
)
from agenttest.modules.runs.domain.entities import RunId


class SqlAlchemyRunReviewCollector:
    def __init__(self, repository: SqlAlchemyReviewTaskRepository) -> None:
        self._repository = repository

    async def collect(self, project_id: ProjectId, run_id: RunId) -> None:
        await self._repository.auto_enqueue_low_confidence(
            project_id,
            str(run_id.value),
            0.7,
        )
