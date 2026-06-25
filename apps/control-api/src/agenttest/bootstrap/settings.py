from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# 本地开发使用的 SQLite 数据库路径
LOCAL_SQLITE_PATH = "data/local.db"


class Settings(BaseSettings):
    """应用配置，支持环境变量 AGENTTEST_* 覆盖。

    数据库 URL 支持两种格式：
    - PostgreSQL: postgresql+asyncpg://user:pass@host:port/db
    - SQLite:     sqlite+aiosqlite:///data/local.db

    本地开发默认使用 SQLite 以降低环境依赖。
    """
    model_config = SettingsConfigDict(
        env_prefix="AGENTTEST_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "control-api"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = f"sqlite+aiosqlite:///{LOCAL_SQLITE_PATH}"
    web_origin: AnyHttpUrl = AnyHttpUrl("http://localhost:5175")
    session_cookie_name: str = "agenttest_session"
    session_ttl_seconds: int = Field(default=28800, ge=300, le=604800)


@lru_cache
def get_settings() -> Settings:
    return Settings()
