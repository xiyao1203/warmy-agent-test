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
