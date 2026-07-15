import pytest
from agenttest.bootstrap.settings import LOCAL_SQLITE_PATH, Settings
from pydantic import ValidationError


def test_settings_default_to_sqlite() -> None:
    """默认使用 SQLite 数据库，无需手动配置 DATABASE_URL。"""
    settings = Settings()
    assert "sqlite+aiosqlite" in settings.database_url
    assert LOCAL_SQLITE_PATH in settings.database_url


def test_settings_web_origin_default() -> None:
    """web_origin 默认为 localhost:5175。"""
    settings = Settings()
    assert "localhost:5175" in str(settings.web_origin)


def test_local_settings_allow_http_session_cookie() -> None:
    settings = Settings()

    assert settings.session_cookie_secure is False


def test_browser_profile_root_defaults_to_private_user_directory() -> None:
    settings = Settings()

    assert settings.browser_profile_root.endswith("/.agenttest/browser-profiles/data")


def test_artifact_upload_limits_are_positive_and_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.artifact_user_upload_max_bytes == 64 * 1024 * 1024
    assert settings.artifact_internal_upload_max_bytes == 256 * 1024 * 1024

    with pytest.raises(ValidationError):
        Settings(artifact_user_upload_max_bytes=0)
    with pytest.raises(ValidationError):
        Settings(artifact_internal_upload_max_bytes=0)


def test_production_rejects_local_internal_token() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", internal_api_token="local-internal-token")


def test_production_rejects_insecure_session_cookie() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            internal_api_token="production-internal-token",
            session_cookie_secure=False,
        )


def test_production_requires_auth_state_master_key() -> None:
    with pytest.raises(ValidationError, match="MODEL_CREDENTIAL_KEY"):
        Settings(
            environment="production",
            internal_api_token="production-internal-token",
            session_cookie_secure=True,
        )


def test_local_mission_target_allowlist_is_test_only() -> None:
    settings = Settings(environment="test", mission_allowed_local_hosts="127.0.0.1")
    assert settings.mission_local_host_allowlist == frozenset({"127.0.0.1"})

    with pytest.raises(ValidationError, match="local mission target"):
        Settings(
            environment="production",
            internal_api_token="production-internal-token",
            session_cookie_secure=True,
            model_credential_key="synthetic-key",
            mission_allowed_local_hosts="127.0.0.1",
        )
