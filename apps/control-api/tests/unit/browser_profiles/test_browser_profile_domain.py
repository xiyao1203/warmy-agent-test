from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


def profile() -> BrowserProfile:
    now = datetime.now(UTC)
    return BrowserProfile.create(
        project_id=uuid4(),
        name="TapNow 登录态",
        target_domain="https://app.tapnow.ai/workspace",
        created_by=uuid4(),
        now=now,
    )


def test_new_profile_has_stopped_runtime_and_missing_auth_state() -> None:
    item = profile()

    assert item.status == "stopped"
    assert item.auth_state_status == "missing"
    assert item.auth_state_version == 0


def test_profile_auth_snapshot_increments_version_and_becomes_ready() -> None:
    item = profile()
    saved_at = datetime.now(UTC)

    item.store_auth_state(
        envelope="v1.ciphertext",
        sha256="a" * 64,
        saved_at=saved_at,
    )

    assert item.auth_state_status == "ready"
    assert item.auth_state_version == 1
    assert item.auth_state_updated_at == saved_at
    assert item.last_login_at == saved_at


def test_profile_cannot_be_ready_without_an_auth_snapshot() -> None:
    item = profile()

    with pytest.raises(ValueError, match="登录态"):
        item.mark_auth_ready(datetime.now(UTC))


def test_public_projection_never_exposes_runtime_or_auth_secrets() -> None:
    item = profile()
    item.user_data_dir = "/secret/browser/profile"
    item.cdp_port = 9333
    item.cdp_endpoint = "ws://127.0.0.1:9333/devtools/browser/secret"
    item.store_auth_state(
        envelope="v1.super-secret-envelope",
        sha256="b" * 64,
        saved_at=datetime.now(UTC),
    )

    result = item.to_public_dict()

    assert result["profile_id"] == str(item.id)
    assert result["auth_state_status"] == "ready"
    assert "user_data_dir" not in result
    assert "cdp_port" not in result
    assert "cdp_endpoint" not in result
    assert "auth_state_envelope" not in result
    assert "auth_state_sha256" not in result
    assert "secret" not in repr(result)


def test_profile_rejects_invalid_snapshot_hash() -> None:
    item = profile()

    with pytest.raises(ValueError, match="SHA-256"):
        item.store_auth_state(
            envelope="v1.ciphertext",
            sha256="short",
            saved_at=datetime.now(UTC),
        )
