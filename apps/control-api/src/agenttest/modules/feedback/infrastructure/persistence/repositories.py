"""反馈仓储实现。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.feedback.domain.entities import Feedback
from agenttest.modules.feedback.infrastructure.persistence.models import FeedbackModel
from agenttest.shared.infrastructure.database import transaction_scope


class SqlAlchemyFeedbackRepository:
    """基于 SQLAlchemy 的反馈仓储。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, feedback: Feedback) -> None:
        model = FeedbackModel(
            id=feedback.id,
            type=feedback.type.value,
            title=feedback.title,
            description=feedback.description,
            contact=feedback.contact,
            user_id=feedback.user_id,
            created_at=feedback.created_at,
        )
        async with transaction_scope(self._session_factory) as session:
            session.add(model)
