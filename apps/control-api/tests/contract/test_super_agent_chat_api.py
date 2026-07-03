from datetime import UTC, datetime
from uuid import uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.conversation import ConversationResponse
from agenttest.modules.test_agent.application.generations import GenerationCoordinator
from agenttest.modules.test_agent.domain.entities import AgentEvent
from fastapi import FastAPI
from fastapi.testclient import TestClient


class Sessions:
    def __init__(self) -> None:
        self.items = {}

    async def list_by_project(self, project_id, *, include_archived=False):
        return [
            item
            for item in self.items.values()
            if item.project_id == project_id.value
            and (include_archived or item.archived_at is None)
        ]

    async def get(self, project_id, session_id):
        item = self.items.get(session_id.value)
        return item if item and item.project_id == project_id.value else None

    async def save(self, session):
        self.items[session.session_id.value] = session


class Events:
    def __init__(self) -> None:
        self.items = []

    async def append_event(self, project_id, session_id, event_type, payload, generation_id=None):
        event = AgentEvent(
            event_id=uuid4(),
            project_id=project_id.value,
            session_id=session_id.value,
            sequence=len(self.items) + 1,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(UTC),
            generation_id=generation_id,
        )
        self.items.append(event)
        return event

    async def list_events(self, project_id, session_id, *, after=0):
        return [
            event
            for event in self.items
            if event.project_id == project_id.value
            and event.session_id == session_id.value
            and event.sequence > after
        ]

    async def list_artifact_links(self, project_id, session_id):
        return []

    async def latest_sequence(self, project_id, session_id):
        matching = await self.list_events(project_id, session_id)
        return max((event.sequence for event in matching), default=0)


class Generations:
    def __init__(self) -> None:
        self.items = {}

    async def add(self, generation):
        self.items[generation.generation_id] = generation

    async def get(self, project_id, generation_id):
        item = self.items.get(generation_id)
        return item if item and item.project_id == project_id.value else None

    async def get_active(self, project_id, session_id):
        return next(
            (
                item
                for item in self.items.values()
                if item.project_id == project_id.value
                and item.session_id == session_id.value
                and item.completed_at is None
            ),
            None,
        )

    async def save(self, generation):
        self.items[generation.generation_id] = generation


class Invoker:
    async def cancel_workflow(self, workflow_id):
        self.cancelled = workflow_id


class Conversation:
    async def respond(
        self,
        actor,
        project_id,
        *,
        history,
        stream_callback=None,
        reasoning_stream_callback=None,
        action_context=None,
        stream_context=None,
    ):
        assert history[-1] == ("user", "你好")
        return ConversationResponse(content="你好，请告诉我要测试哪个 Agent。")


def build_client():
    from agenttest.modules.test_agent.api.router import create_test_agent_router

    actor = User.create(
        user_id=UserId.new(),
        email=Email("chat@example.com"),
        display_name="Chat User",
        role=SystemRole.DEVELOPER,
    )
    project_id = ProjectId.new()
    sessions = Sessions()
    events = Events()
    generations = Generations()
    invoker = Invoker()

    async def actor_for(request):
        return actor

    async def check_project(value):
        assert value == project_id.value

    app = FastAPI()
    app.include_router(
        create_test_agent_router(
            sessions=sessions,
            orchestration=events,
            actor_for=actor_for,
            check_project=check_project,
            settings=Settings(),
            conversation=Conversation(),
            generation_coordinator=GenerationCoordinator(generations, events, invoker),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="http://testserver")
    client.cookies.set("agenttest_session", "session")
    client.cookies.set("agenttest_csrf", "csrf")
    return client, project_id


def test_real_conversation_is_persisted_and_restored_from_history() -> None:
    client, project_id = build_client()

    created = client.post(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions",
        headers={"X-CSRF-Token": "csrf"},
    )
    session_id = created.json()["session_id"]
    response = client.post(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}/messages",
        headers={"X-CSRF-Token": "csrf"},
        json={"message": "你好", "generation_id": str(uuid4())},
    )
    restored = client.get(f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}")
    history = client.get(f"/api/v1/projects/{project_id.value}/test-agent/sessions")

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json()["messages"][-1]["content"] == "你好，请告诉我要测试哪个 Agent。"
    assert restored.json()["messages"] == response.json()["messages"]
    assert restored.json()["event_cursor"] >= 1
    assert any(item["kind"] == "event" for item in restored.json()["timeline"])
    assert history.json()["items"][0]["session_id"] == session_id


def test_event_stream_replays_after_last_event_id() -> None:
    client, project_id = build_client()
    created = client.post(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions",
        headers={"X-CSRF-Token": "csrf"},
    )
    session_id = created.json()["session_id"]
    client.post(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}/messages",
        headers={"X-CSRF-Token": "csrf"},
        json={"message": "你好", "generation_id": str(uuid4())},
    )

    stream = client.get(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}/events",
        params={"after": 1},
    )

    assert stream.status_code == 200
    assert "event: stream.ready" in stream.text
    assert "event: message.completed" in stream.text
    assert "id: 1\n" not in stream.text


def test_model_runner_callback_persists_each_real_delta_and_requires_token() -> None:
    client, project_id = build_client()
    created = client.post(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions",
        headers={"X-CSRF-Token": "csrf"},
    )
    session_id = created.json()["session_id"]
    url = f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}/model-events"

    denied = client.post(url, json={"content": "你"})
    first = client.post(
        url,
        headers={"X-Internal-Token": "local-internal-token"},
        json={"content": "你"},
    )
    second = client.post(
        url,
        headers={"X-Internal-Token": "local-internal-token"},
        json={"content": "好"},
    )
    stream = client.get(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}/events",
        headers={"Last-Event-ID": "1"},
    )

    assert denied.status_code == 401
    assert first.status_code == 200
    assert second.json()["sequence"] == first.json()["sequence"] + 1
    assert 'data: {"content":"你"}' in stream.text
    assert 'data: {"content":"好"}' in stream.text


def test_generation_cancel_is_idempotent() -> None:
    client, project_id = build_client()
    created = client.post(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions",
        headers={"X-CSRF-Token": "csrf"},
    )
    session_id = created.json()["session_id"]
    generation_id = str(uuid4())
    client.post(
        f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}/messages",
        headers={"X-CSRF-Token": "csrf"},
        json={"message": "你好", "generation_id": generation_id},
    )
    cancel_url = (
        f"/api/v1/projects/{project_id.value}/test-agent/sessions/{session_id}"
        f"/generations/{generation_id}/cancel"
    )

    first = client.post(cancel_url, headers={"X-CSRF-Token": "csrf"})
    second = client.post(cancel_url, headers={"X-CSRF-Token": "csrf"})

    assert first.status_code == second.status_code == 200
    assert first.json()["status"] in {"cancelling", "completed"}
