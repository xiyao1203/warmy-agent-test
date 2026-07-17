"""反馈命令处理器。"""

from __future__ import annotations

from uuid import UUID

from agenttest.modules.feedback.application.ports import FeedbackRepository
from agenttest.modules.feedback.domain.entities import Feedback
from agenttest.modules.feedback.domain.value_objects import FeedbackType


class CreateFeedbackHandler:
    """创建反馈处理器。"""

    def __init__(self, repository: FeedbackRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        contact: str | None,
        user_id: UUID | None,
    ) -> UUID:
        feedback = Feedback.create(
            feedback_type=feedback_type,
            title=title,
            description=description,
            contact=contact,
            user_id=user_id,
        )
        await self._repository.save(feedback)
        return feedback.id
