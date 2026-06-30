from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.identity.infrastructure.persistence import (
    models as identity_models,  # noqa: F401
)
from agenttest.modules.projects.infrastructure.persistence import (
    models as project_models,  # noqa: F401
)
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.domain.entities import ChatSession
from agenttest.modules.test_agent.infrastructure.models import (
    TestAgentMessageModel as ChatMessageModel,
)
from agenttest.modules.test_agent.infrastructure.models import (
    TestAgentSessionModel as ChatSessionModel,
)
from agenttest.modules.test_agent.infrastructure.repositories import (
    SqlAlchemyChatSessionRepository,
)
from agenttest.shared.infrastructure.database import (
    Base,
    create_database_engine,
    create_session_factory,
)


@pytest.mark.asyncio
async def test_repository_round_trip_is_ordered_and_project_scoped(tmp_path) -> None:
    engine = create_database_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: Base.metadata.create_all(
                sync_connection,
                tables=[
                    ChatSessionModel.__table__,
                    ChatMessageModel.__table__,
                ],
            )
        )
    repository = SqlAlchemyChatSessionRepository(create_session_factory(engine))
    project_id = ProjectId.new()
    session = ChatSession.create(
        project_id=project_id.value,
        created_by=uuid4(),
    )
    session.add_user_message("first")
    session.add_assistant_message("second", plan_draft={"estimated_cases": 1})

    await repository.save(session)

    restored = await repository.get(project_id, session.session_id)
    foreign = await repository.get(ProjectId.new(), session.session_id)
    await engine.dispose()

    assert restored is not None
    assert [message.content for message in restored.messages] == ["first", "second"]
    assert [message.sequence for message in restored.messages] == [1, 2]
    assert restored.plan_draft == {"estimated_cases": 1}
    assert foreign is None
