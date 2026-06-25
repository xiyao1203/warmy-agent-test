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
