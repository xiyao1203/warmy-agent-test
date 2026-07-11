import hashlib
import json
from uuid import uuid4

import pytest
from agenttest.modules.browser_profiles.application.auth_state import BrowserAuthStateService
from agenttest.modules.browser_profiles.infrastructure.auth_state_cipher import (
    BrowserAuthStateCipher,
)


def service() -> BrowserAuthStateService:
    return BrowserAuthStateService(BrowserAuthStateCipher(b"s" * 32))


def test_snapshot_is_canonical_hashed_encrypted_and_round_trips() -> None:
    project_id = uuid4()
    profile_id = uuid4()
    state = {
        "origins": [
            {
                "origin": "https://app.tapnow.ai",
                "localStorage": [{"name": "session", "value": "local-secret"}],
                "indexedDB": [{"name": "auth", "data": "indexed-secret"}],
            }
        ],
        "cookies": [],
    }

    snapshot = service().seal(
        project_id=project_id,
        profile_id=profile_id,
        target_domain="https://app.tapnow.ai/workspace",
        storage_state=state,
    )

    canonical = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert snapshot.sha256 == hashlib.sha256(canonical.encode()).hexdigest()
    assert "local-secret" not in snapshot.envelope
    assert "indexed-secret" not in snapshot.envelope
    assert service().open(project_id, profile_id, snapshot.envelope) == state


def test_snapshot_accepts_parent_domain_cookie_for_target_host() -> None:
    snapshot = service().seal(
        project_id=uuid4(),
        profile_id=uuid4(),
        target_domain="app.tapnow.ai",
        storage_state={
            "cookies": [
                {
                    "name": "session",
                    "value": "secret",
                    "domain": ".tapnow.ai",
                    "path": "/",
                }
            ],
            "origins": [],
        },
    )

    assert len(snapshot.sha256) == 64


@pytest.mark.parametrize(
    "state",
    [
        {"cookies": [], "origins": []},
        {
            "cookies": [{"name": "session", "value": "x", "domain": ".example.com"}],
            "origins": [],
        },
        {
            "cookies": [],
            "origins": [
                {
                    "origin": "https://example.com",
                    "localStorage": [{"name": "session", "value": "x"}],
                }
            ],
        },
    ],
)
def test_snapshot_rejects_empty_or_wrong_domain_state(state: dict) -> None:
    with pytest.raises(ValueError, match="目标域"):
        service().seal(
            project_id=uuid4(),
            profile_id=uuid4(),
            target_domain="app.tapnow.ai",
            storage_state=state,
        )


def test_open_rejects_non_object_storage_state() -> None:
    project_id = uuid4()
    profile_id = uuid4()
    envelope = BrowserAuthStateCipher(b"s" * 32).encrypt(project_id, profile_id, "[]")

    with pytest.raises(ValueError, match="格式"):
        service().open(project_id, profile_id, envelope)
