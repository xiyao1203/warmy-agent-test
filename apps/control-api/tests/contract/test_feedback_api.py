from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from agenttest.bootstrap.app import create_app
from agenttest.modules.feedback.api.router import FeedbackApiDependencies
from agenttest.modules.feedback.api.schemas import FeedbackType
from agenttest.modules.identity.application.queries.current_user import InvalidSessionError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from fastapi.testclient import TestClient


def create_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("user@example.com"),
        display_name="User",
        role=SystemRole.DEVELOPER,
    )


@dataclass
class StubCurrentUser:
    user: User | None

    async def execute(self, _session_token: str) -> User:
        if self.user is None:
            raise InvalidSessionError
        return self.user


class StubCreateFeedback:
    def __init__(self) -> None:
        self.feedback_id = uuid4()
        self.user_ids: list[UUID | None] = []

    async def execute(
        self,
        *,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        contact: str | None,
        user_id: UUID | None,
    ) -> UUID:
        self.user_ids.append(user_id)
        return self.feedback_id


def feedback_client(user: User | None) -> tuple[TestClient, StubCreateFeedback]:
    creator = StubCreateFeedback()
    dependencies = FeedbackApiDependencies(
        current_user=StubCurrentUser(user),
        create_feedback=creator,
    )
    client = TestClient(
        create_app(feedback_dependencies=dependencies),
        base_url="https://testserver",
    )
    return client, creator


def test_authenticated_feedback_records_the_user() -> None:
    user = create_user()
    client, creator = feedback_client(user)
    client.cookies.set("agenttest_session", "session-token")

    response = client.post(
        "/api/v1/feedback",
        json={
            "type": "ux",
            "title": "Improve navigation",
            "description": "The account navigation needs clearer grouping.",
            "contact": "user@example.com",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(creator.feedback_id)
    assert creator.user_ids == [user.user_id.value]


def test_anonymous_feedback_is_allowed() -> None:
    client, creator = feedback_client(None)

    response = client.post(
        "/api/v1/feedback",
        json={
            "type": "bug",
            "title": "Broken link",
            "description": "The documentation link returns a missing page.",
        },
    )

    assert response.status_code == 201
    assert creator.user_ids == [None]
