from uuid import uuid4

import pytest
from agenttest.modules.feedback.application.commands import CreateFeedbackHandler
from agenttest.modules.feedback.domain.entities import Feedback
from agenttest.modules.feedback.domain.value_objects import FeedbackType
from agenttest.modules.feedback.infrastructure.persistence.models import FeedbackModel
from agenttest.modules.feedback.infrastructure.persistence.repositories import (
    SqlAlchemyFeedbackRepository,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class StubFeedbackRepository:
    """记录 Application 保存结果的内存仓储。"""

    def __init__(self) -> None:
        self.saved: Feedback | None = None

    async def save(self, feedback: Feedback) -> None:
        self.saved = feedback


@pytest.mark.asyncio
async def test_feedback_handler_uses_repository_contract() -> None:
    repository = StubFeedbackRepository()
    user_id = uuid4()
    handler = CreateFeedbackHandler(repository)

    feedback_id = await handler.execute(
        feedback_type=FeedbackType.FEATURE,
        title="  Export filters  ",
        description="  Allow saved filters in report exports.  ",
        contact="  qa@example.com  ",
        user_id=user_id,
    )

    assert repository.saved is not None
    assert feedback_id == repository.saved.id
    assert repository.saved.type is FeedbackType.FEATURE
    assert repository.saved.title == "Export filters"
    assert repository.saved.description == "Allow saved filters in report exports."
    assert repository.saved.contact == "qa@example.com"
    assert repository.saved.user_id == user_id


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
