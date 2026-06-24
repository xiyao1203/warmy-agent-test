from fastapi import FastAPI

from agenttest.bootstrap.settings import Settings, get_settings
from agenttest.entrypoints.http.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Warmy Agent Test Control API",
        version=resolved_settings.app_version,
    )
    app.state.settings = resolved_settings
    app.include_router(health_router, prefix="/api/v1")
    return app
