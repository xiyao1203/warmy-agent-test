from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 本地开发使用的 SQLite 数据库路径
LOCAL_SQLITE_PATH = str(Path(__file__).resolve().parents[5] / "data" / "local.db")


class Settings(BaseSettings):
    """应用配置，支持环境变量 AGENTTEST_* 覆盖。

    数据库 URL 支持两种格式：
    - PostgreSQL: postgresql+asyncpg://user:pass@host:port/db
    - SQLite:     sqlite+aiosqlite:///data/local.db

    本地开发默认使用 SQLite 以降低环境依赖。
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENTTEST_",
        env_file=None,
        extra="ignore",
    )

    app_name: str = "control-api"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = f"sqlite+aiosqlite:///{LOCAL_SQLITE_PATH}"
    web_origin: AnyHttpUrl = AnyHttpUrl("http://localhost:5175")
    session_cookie_name: str = "agenttest_session"
    session_cookie_secure: bool = False
    session_ttl_seconds: int = Field(default=28800, ge=300, le=604800)
    control_api_base_url: str = "http://localhost:8181"
    internal_api_token: str = Field(default="local-internal-token", min_length=16)
    temporal_address: str | None = None
    temporal_namespace: str = "default"
    temporal_task_queue: str = "agenttest-api-runner"
    model_runner_task_queue: str = "agenttest-model-runner"
    model_credential_key: str | None = None
    model_allow_private_network: bool = False
    promptfoo_bin: str = "promptfoo"
    security_scan_allow_private_network: bool = False

    @model_validator(mode="after")
    def reject_unsafe_non_local_defaults(self) -> "Settings":
        if self.environment not in {"local", "test"}:
            if self.internal_api_token == "local-internal-token":
                raise ValueError("A non-local internal API token is required")
            if not self.session_cookie_secure:
                raise ValueError("Secure session cookies are required outside local/test")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=".env")
