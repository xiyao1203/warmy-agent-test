from datetime import UTC, datetime
from uuid import uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.test_missions.api.router import (
    MissionApiDependencies,
    create_test_mission_router,
)
from agenttest.modules.test_missions.application.commands import (
    ConfirmMissionHandler,
    PreviewMissionHandler,
    UpsertMissionHandler,
)
from agenttest.modules.test_missions.application.intake import MissionIntake
from agenttest.modules.test_missions.application.preflight import MissionPreflight
from agenttest.modules.test_missions.application.queries import GetMissionHandler
from agenttest.modules.test_missions.domain.value_objects import MissionEvent
from fastapi import FastAPI
from fastapi.testclient import TestClient


class Repository:
    def __init__(self) -> None:
        self.items = {}
        self.events = []

    async def add(self, mission):
        self.items[mission.mission_id] = mission

    async def get(self, project_id, mission_id):
        item = self.items.get(mission_id)
        return item if item and item.project_id == project_id else None

    async def get_for_session(self, project_id, session_id):
        return next(
            (
                item
                for item in self.items.values()
                if item.project_id == project_id and item.session_id == session_id
            ),
            None,
        )

    async def save(self, mission, *, expected_lock_version):
        del expected_lock_version
        self.items[mission.mission_id] = mission

    async def append_event(self, project_id, mission_id, event_type, payload):
        event = MissionEvent(
            event_id=uuid4(),
            project_id=project_id,
            mission_id=mission_id,
            sequence=len(self.events) + 1,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        self.events.append(event)
        return event


class Runtime:
    async def start(self, mission, revision, idempotency_key):
        del idempotency_key
        return f"test-mission-{mission.mission_id}-{revision.revision_number}"


def build_client():
    repository = Repository()
    runtime = Runtime()
    actor = User.create(
        user_id=UserId.new(),
        email=Email("mission-api@example.com"),
        display_name="Mission API User",
        role=SystemRole.DEVELOPER,
    )
    project_id = uuid4()

    async def actor_for(request):
        del request
        return actor

    async def check_project(value):
        assert value == project_id

    dependencies = MissionApiDependencies(
        upsert=UpsertMissionHandler(repository, MissionIntake()),
        preview=PreviewMissionHandler(repository, MissionPreflight()),
        confirm=ConfirmMissionHandler(repository, MissionPreflight(), runtime),
        get=GetMissionHandler(repository, MissionPreflight()),
    )
    app = FastAPI()
    app.include_router(
        create_test_mission_router(
            dependencies=dependencies,
            actor_for=actor_for,
            check_project=check_project,
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="http://testserver")
    client.cookies.set("agenttest_session", "session")
    client.cookies.set("agenttest_csrf", "csrf")
    return client, project_id


def test_api_creates_previews_and_confirms_one_revision() -> None:
    client, project_id = build_client()
    created = client.post(
        f"/api/v1/projects/{project_id}/test-missions",
        headers={"X-CSRF-Token": "csrf"},
        json={
            "session_id": str(uuid4()),
            "facts": {
                "target_url": "https://agent.example",
                "access_strategy": "none",
                "test_goal": "验证多轮问答",
                "safety_scope": "read_only",
            },
        },
    )
    mission_id = created.json()["mission_id"]
    preview = client.post(
        f"/api/v1/projects/{project_id}/test-missions/{mission_id}/preview",
        headers={"X-CSRF-Token": "csrf"},
    )
    confirmed = client.post(
        f"/api/v1/projects/{project_id}/test-missions/{mission_id}/confirm-start",
        headers={"X-CSRF-Token": "csrf"},
        json={"revision_hash": preview.json()["revision_hash"], "idempotency_key": "once"},
    )

    assert created.status_code == 201
    assert preview.status_code == 200
    assert preview.json()["ready"] is True
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "provisioning"
    assert "workflow_id" in confirmed.json()


def test_api_rejects_csrf_stale_hash_and_sensitive_fact_material() -> None:
    client, project_id = build_client()
    url = f"/api/v1/projects/{project_id}/test-missions"
    body = {"session_id": str(uuid4()), "facts": {"target_url": "https://agent.example"}}

    assert client.post(url, json=body).status_code == 403
    secret = client.post(
        url,
        headers={"X-CSRF-Token": "csrf"},
        json={"session_id": str(uuid4()), "facts": {"token": "plaintext"}},
    )
    assert secret.status_code == 422
