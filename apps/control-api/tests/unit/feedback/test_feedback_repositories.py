from uuid import uuid4

import pytest
from agenttest.modules.feedback.api.schemas import FeedbackType
from agenttest.modules.feedback.domain.entities import Feedback
from agenttest.modules.feedback.infrastructure.persistence.models import FeedbackModel
from agenttest.modules.feedback.infrastructure.persistence.repositories import (
    SqlAlchemyFeedbackRepository,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_feedback_repository_persists_with_a_session_factory() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(FeedbackModel.__table__.create)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlAlchemyFeedbackRepository(session_factory)
    feedback = Feedback.create(
        feedback_type=FeedbackType.UX,
        title="Improve navigation",
        description="The account navigation needs clearer grouping.",
        contact=None,
        user_id=uuid4(),
    )

    await repository.save(feedback)

    async with session_factory() as session:
        persisted = await session.get(FeedbackModel, feedback.id)
    assert persisted is not None
    assert persisted.title == "Improve navigation"
    await engine.dispose()
