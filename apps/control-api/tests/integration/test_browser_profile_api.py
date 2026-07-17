from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.browser_profiles.api.router import (
    BrowserProfileApiDependencies,
    create_browser_profile_router,
)
from agenttest.modules.browser_profiles.application.auth_state import BrowserAuthStateService
from agenttest.modules.browser_profiles.application.service import BrowserProfileService
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.browser_profiles.infrastructure.auth_state_cipher import (
    BrowserAuthStateCipher,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeRepository:
    def __init__(self, items: list[BrowserProfile] | None = None, events: list[str] | None = None):
        self.items = {item.id: item for item in items or []}
        self.events = events if events is not None else []

    async def list(self, project_id: UUID) -> list[BrowserProfile]:
        return [item for item in self.items.values() if item.project_id == project_id]

    async def get(self, project_id: UUID, profile_id: UUID) -> BrowserProfile | None:
        item = self.items.get(profile_id)
        return item if item and item.project_id == project_id else None

    async def add(self, item: BrowserProfile) -> None:
        self.items[item.id] = item

    async def save(self, item: BrowserProfile) -> None:
        self.events.append("save")
        self.items[item.id] = item

    async def delete(self, project_id: UUID, profile_id: UUID) -> bool:
        item = await self.get(project_id, profile_id)
        if item is None:
            return False
        del self.items[profile_id]
        return True


class FakeRuntime:
    def __init__(self, events: list[str] | None = None) -> None:
        self.events = events if events is not None else []

    def profile_dir(self, profile_id: UUID) -> str:
        return f"/private/runtime/{profile_id}"

    async def start(self, profile: BrowserProfile, login_url: str) -> None:
        profile.status = "running"
        profile.cdp_port = 9444
        profile.cdp_endpoint = "ws://127.0.0.1:9444/devtools/browser/private"

    async def stop(self, profile_id: UUID) -> None:
        self.events.append("stop")

    async def export_storage_state(self, profile: BrowserProfile) -> dict:
        self.events.append("export")
        return {
            "cookies": [
                {
                    "name": "session",
                    "value": "runtime-secret",
                    "domain": ".tapnow.ai",
                    "path": "/",
                }
            ],
            "origins": [],
        }

    async def verify(self, profile: BrowserProfile, storage_state: dict) -> bool:
        self.events.append("verify")
        return bool(storage_state.get("cookies"))


def existing_profile(project_id: UUID) -> BrowserProfile:
    item = BrowserProfile.create(
        project_id=project_id,
        name="TapNow",
        target_domain="https://app.tapnow.ai",
        created_by=uuid4(),
        now=datetime.now(UTC),
    )
    item.user_data_dir = f"/private/runtime/{item.id}"
    item.status = "running"
    return item


class FakeProjectAccess:
    def __init__(self, allow: bool) -> None:
        self.allow = allow

    async def ensure_member(self, _actor, _project_id) -> None:
        if not self.allow:
            raise PermissionError

    async def ensure_editor(self, _actor, _project_id) -> None:
        if not self.allow:
            raise PermissionError


def client(repository: FakeRepository, runtime: FakeRuntime, *, allow: bool = True) -> TestClient:
    app = FastAPI()
    user = User.create(
        user_id=UserId.new(),
        email=Email("browser-profile@example.com"),
        display_name="Browser Profile",
        role=SystemRole.DEVELOPER,
    )

    async def actor_for(_request):
        return user

    app.include_router(
        create_browser_profile_router(
            BrowserProfileApiDependencies(
                service=BrowserProfileService(
                    repository=repository,
                    runtime=runtime,
                    auth_state=BrowserAuthStateService(BrowserAuthStateCipher(b"z" * 32)),
                    project_access=FakeProjectAccess(allow),
                ),
                actor_for=actor_for,
                settings=Settings(session_cookie_name="session"),
            )
        )
    )
    result = TestClient(app)
    result.cookies.set("session", "valid")
    result.cookies.set("agenttest_csrf", "csrf")
    return result


def test_create_and_list_never_expose_host_paths_cdp_or_auth_material() -> None:
    project_id = uuid4()
    repository = FakeRepository()
    api = client(repository, FakeRuntime())

    created = api.post(
        f"/api/v1/projects/{project_id}/browser-profiles",
        headers={"X-Csrf-Token": "csrf"},
        json={
            "name": "TapNow",
            "target_domain": "app.tapnow.ai",
            "user_data_dir": "/attacker/chosen/path",
        },
    )

    assert created.status_code == 201
    assert created.json()["auth_state_status"] == "missing"
    listed = api.get(f"/api/v1/projects/{project_id}/browser-profiles")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body["items"]) == 1
    serialized = repr(body)
    assert "user_data_dir" not in serialized
    assert "cdp_" not in serialized
    assert "auth_state_envelope" not in serialized
    assert "attacker" not in serialized


def test_project_access_denial_is_hidden_as_not_found() -> None:
    project_id = uuid4()
    response = client(FakeRepository(), FakeRuntime(), allow=False).get(
        f"/api/v1/projects/{project_id}/browser-profiles"
    )

    assert response.status_code == 404


def test_login_complete_exports_encrypts_saves_then_stops() -> None:
    project_id = uuid4()
    item = existing_profile(project_id)
    events: list[str] = []
    repository = FakeRepository([item], events)
    runtime = FakeRuntime(events)
    api = client(repository, runtime)

    response = api.post(
        f"/api/v1/projects/{project_id}/browser-profiles/{item.id}/login-complete",
        headers={"X-Csrf-Token": "csrf"},
        json={"stop_after_save": True},
    )

    assert response.status_code == 200
    assert response.json()["auth_state_status"] == "ready"
    assert "runtime-secret" not in response.text
    assert item.auth_state_envelope and "runtime-secret" not in item.auth_state_envelope
    assert events == ["export", "save", "stop", "save"]
    assert item.status == "stopped"


def test_verify_uses_decrypted_snapshot_and_updates_timestamp() -> None:
    project_id = uuid4()
    item = existing_profile(project_id)
    auth_state = BrowserAuthStateService(BrowserAuthStateCipher(b"z" * 32))
    sealed = auth_state.seal(
        project_id=project_id,
        profile_id=item.id,
        target_domain=item.target_domain,
        storage_state={
            "cookies": [{"name": "session", "value": "secret", "domain": ".tapnow.ai"}],
            "origins": [],
        },
    )
    item.store_auth_state(
        envelope=sealed.envelope,
        sha256=sealed.sha256,
        saved_at=datetime.now(UTC),
    )
    repository = FakeRepository([item])
    runtime = FakeRuntime()

    response = client(repository, runtime).post(
        f"/api/v1/projects/{project_id}/browser-profiles/{item.id}/verify",
        headers={"X-Csrf-Token": "csrf"},
    )

    assert response.status_code == 200
    assert response.json()["auth_state_status"] == "ready"
    assert response.json()["last_verified_at"] is not None
