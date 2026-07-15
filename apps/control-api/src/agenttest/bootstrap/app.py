from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from agenttest.bootstrap.context import AppOverrides, build_context
from agenttest.bootstrap.modules import MODULE_REGISTRARS
from agenttest.bootstrap.settings import Settings, get_settings
from agenttest.modules.agents.api.router import AgentApiDependencies
from agenttest.modules.audit.api.router import AuditApiDependencies
from agenttest.modules.datasets.api.router import DatasetApiDependencies
from agenttest.modules.environments.api.router import EnvironmentApiDependencies
from agenttest.modules.feedback.api.router import FeedbackApiDependencies
from agenttest.modules.identity.api.admin_router import AdminApiDependencies
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.projects.api.router import ProjectApiDependencies
from agenttest.modules.runs.api.router import RunApiDependencies
from agenttest.modules.test_plans.api.router import TestPlanApiDependencies
from agenttest.modules.user_settings.api.router import UserSettingsApiDependencies

__all__ = ["AppOverrides", "create_app"]


class PreflightMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return Response()
        return await call_next(request)


def create_app(
    settings: Settings | None = None,
    overrides: AppOverrides | None = None,
    auth_dependencies: AuthApiDependencies | None = None,
    admin_dependencies: AdminApiDependencies | None = None,
    project_dependencies: ProjectApiDependencies | None = None,
    audit_dependencies: AuditApiDependencies | None = None,
    agent_dependencies: AgentApiDependencies | None = None,
    dataset_dependencies: DatasetApiDependencies | None = None,
    test_plan_dependencies: TestPlanApiDependencies | None = None,
    environment_dependencies: EnvironmentApiDependencies | None = None,
    run_dependencies: RunApiDependencies | None = None,
    user_settings_dependencies: UserSettingsApiDependencies | None = None,
    feedback_dependencies: FeedbackApiDependencies | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_overrides = _legacy_overrides(
        overrides or AppOverrides(),
        auth=auth_dependencies,
        admin=admin_dependencies,
        projects=project_dependencies,
        audit=audit_dependencies,
        agents=agent_dependencies,
        datasets=dataset_dependencies,
        test_plans=test_plan_dependencies,
        environments=environment_dependencies,
        runs=run_dependencies,
        user_settings=user_settings_dependencies,
        feedback=feedback_dependencies,
    )
    context = build_context(resolved_settings, resolved_overrides)
    app = FastAPI(
        title="Warmy Agent Test Control API",
        version=resolved_settings.app_version,
    )
    app.state.settings = resolved_settings
    app.add_middleware(PreflightMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(resolved_settings.web_origin).rstrip("/")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=500)
    for register in MODULE_REGISTRARS:
        register(app, context)
    return app


def _legacy_overrides(
    overrides: AppOverrides,
    *,
    auth: AuthApiDependencies | None = None,
    admin: AdminApiDependencies | None = None,
    projects: ProjectApiDependencies | None = None,
    audit: AuditApiDependencies | None = None,
    agents: AgentApiDependencies | None = None,
    datasets: DatasetApiDependencies | None = None,
    test_plans: TestPlanApiDependencies | None = None,
    environments: EnvironmentApiDependencies | None = None,
    runs: RunApiDependencies | None = None,
    user_settings: UserSettingsApiDependencies | None = None,
    feedback: FeedbackApiDependencies | None = None,
) -> AppOverrides:
    return AppOverrides(
        auth=auth if auth is not None else overrides.auth,
        admin=admin if admin is not None else overrides.admin,
        projects=projects if projects is not None else overrides.projects,
        audit=audit if audit is not None else overrides.audit,
        agents=agents if agents is not None else overrides.agents,
        datasets=datasets if datasets is not None else overrides.datasets,
        test_plans=test_plans if test_plans is not None else overrides.test_plans,
        environments=(environments if environments is not None else overrides.environments),
        runs=runs if runs is not None else overrides.runs,
        user_settings=(user_settings if user_settings is not None else overrides.user_settings),
        feedback=feedback if feedback is not None else overrides.feedback,
    )
