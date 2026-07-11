from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.browser_profiles.api.lease_router import (
    create_browser_session_lease_router,
)
from agenttest.modules.browser_profiles.application.auth_state import BrowserAuthStateService
from agenttest.modules.browser_profiles.application.leases import (
    BrowserSessionLeaseService,
    BrowserSessionSnapshotRef,
)
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.browser_profiles.infrastructure.auth_state_cipher import (
    BrowserAuthStateCipher,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


class Repository:
    def __init__(self, item: BrowserProfile):
        self.item = item

    async def get(self, project_id: UUID, profile_id: UUID) -> BrowserProfile | None:
        if self.item.project_id == project_id and self.item.id == profile_id:
            return self.item
        return None


class ScopeReader:
    def __init__(self, ref: BrowserSessionSnapshotRef | None):
        self.ref = ref

    async def resolve(self, project_id: UUID, run_id: UUID, run_case_id: UUID):
        return self.ref


def ready_profile(project_id: UUID) -> tuple[BrowserProfile, BrowserAuthStateService]:
    item = BrowserProfile.create(
        project_id=project_id,
        name="TapNow",
        target_domain="app.tapnow.ai",
        created_by=uuid4(),
        now=datetime.now(UTC),
    )
    auth_state = BrowserAuthStateService(BrowserAuthStateCipher(b"l" * 32))
    snapshot = auth_state.seal(
        project_id=project_id,
        profile_id=item.id,
        target_domain=item.target_domain,
        storage_state={
            "cookies": [
                {
                    "name": "session",
                    "value": "worker-secret",
                    "domain": ".tapnow.ai",
                }
            ],
            "origins": [],
        },
    )
    item.store_auth_state(
        envelope=snapshot.envelope,
        sha256=snapshot.sha256,
        saved_at=datetime.now(UTC),
    )
    return item, auth_state


def build_client(
    item: BrowserProfile,
    auth_state: BrowserAuthStateService,
    ref: BrowserSessionSnapshotRef | None,
) -> TestClient:
    service = BrowserSessionLeaseService(
        repository=Repository(item),
        auth_state=auth_state,
        scope_reader=ScopeReader(ref),
    )
    app = FastAPI()
    app.include_router(
        create_browser_session_lease_router(internal_token="internal", service=service),
        prefix="/api/v1",
    )
    return TestClient(app)


def test_browser_session_lease_requires_internal_token_and_exact_snapshot_scope() -> None:
    project_id, run_id, run_case_id = uuid4(), uuid4(), uuid4()
    item, auth_state = ready_profile(project_id)
    ref = BrowserSessionSnapshotRef(
        browser_profile_id=item.id,
        auth_state_version=item.auth_state_version,
        auth_state_sha256=item.auth_state_sha256 or "",
    )
    client = build_client(item, auth_state, ref)
    url = f"/api/v1/internal/projects/{project_id}/browser-session-leases:redeem"
    body = {
        "run_id": str(run_id),
        "run_case_id": str(run_case_id),
        "browser_profile_id": str(item.id),
    }

    assert client.post(url, json=body).status_code == 403
    response = client.post(url, headers={"X-Internal-Token": "internal"}, json=body)

    assert response.status_code == 200
    assert response.json()["auth_state_version"] == 1
    assert response.json()["storage_state"]["cookies"][0]["value"] == "worker-secret"
    assert "envelope" not in response.text
    assert item.auth_state_envelope not in response.text


def test_browser_session_lease_rejects_profile_not_in_immutable_run_snapshot() -> None:
    project_id = uuid4()
    item, auth_state = ready_profile(project_id)
    wrong_ref = BrowserSessionSnapshotRef(
        browser_profile_id=uuid4(),
        auth_state_version=item.auth_state_version,
        auth_state_sha256=item.auth_state_sha256 or "",
    )
    client = build_client(item, auth_state, wrong_ref)

    response = client.post(
        f"/api/v1/internal/projects/{project_id}/browser-session-leases:redeem",
        headers={"X-Internal-Token": "internal"},
        json={
            "run_id": str(uuid4()),
            "run_case_id": str(uuid4()),
            "browser_profile_id": str(item.id),
        },
    )

    assert response.status_code == 404


def test_browser_session_lease_rejects_changed_or_expired_auth_state() -> None:
    project_id = uuid4()
    item, auth_state = ready_profile(project_id)
    stale_ref = BrowserSessionSnapshotRef(
        browser_profile_id=item.id,
        auth_state_version=item.auth_state_version + 1,
        auth_state_sha256="f" * 64,
    )
    client = build_client(item, auth_state, stale_ref)
    url = f"/api/v1/internal/projects/{project_id}/browser-session-leases:redeem"
    body = {
        "run_id": str(uuid4()),
        "run_case_id": str(uuid4()),
        "browser_profile_id": str(item.id),
    }

    assert client.post(url, headers={"X-Internal-Token": "internal"}, json=body).status_code == 409
    item.auth_state_status = "expired"
    current_ref = BrowserSessionSnapshotRef(
        browser_profile_id=item.id,
        auth_state_version=item.auth_state_version,
        auth_state_sha256=item.auth_state_sha256 or "",
    )
    expired_client = build_client(item, auth_state, current_ref)
    assert (
        expired_client.post(url, headers={"X-Internal-Token": "internal"}, json=body).status_code
        == 409
    )
