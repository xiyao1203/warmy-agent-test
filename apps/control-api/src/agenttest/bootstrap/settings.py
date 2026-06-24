from functools import lru_cache

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTTEST_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "control-api"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://agenttest:agenttest-local@localhost:5432/agenttest"
    )
    web_origin: AnyHttpUrl = AnyHttpUrl("http://localhost:3000")
    session_cookie_name: str = "agenttest_session"
    session_ttl_seconds: int = Field(default=28800, ge=300, le=604800)


@lru_cache
def get_settings() -> Settings:
    return Settings()
