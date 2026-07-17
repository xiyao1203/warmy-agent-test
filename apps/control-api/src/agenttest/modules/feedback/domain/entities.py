"""反馈实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.feedback.domain.value_objects import FeedbackType


@dataclass(slots=True)
class Feedback:
    """反馈实体。"""

    id: UUID
    type: FeedbackType
    title: str
    description: str
    contact: str | None
    user_id: UUID | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        contact: str | None,
        user_id: UUID | None,
    ) -> Feedback:
        return cls(
            id=uuid4(),
            type=feedback_type,
            title=title.strip(),
            description=description.strip(),
            contact=contact.strip() if contact else None,
            user_id=user_id,
            created_at=datetime.now(UTC),
        )
