from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.bootstrap.project_access import ProjectAccessAdapter
from agenttest.bootstrap.settings import Settings
from agenttest.modules.agents.api.router import AgentApiDependencies
from agenttest.modules.audit.api.router import AuditApiDependencies
from agenttest.modules.datasets.api.router import DatasetApiDependencies
from agenttest.modules.environments.api.router import EnvironmentApiDependencies
from agenttest.modules.feedback.api.router import FeedbackApiDependencies
from agenttest.modules.identity.api.admin_router import AdminApiDependencies
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.projects.api.router import ProjectApiDependencies
from agenttest.modules.projects.infrastructure.persistence.repositories import (
    SqlAlchemyProjectRepository,
)
from agenttest.modules.runs.api.router import RunApiDependencies
from agenttest.modules.test_plans.api.router import TestPlanApiDependencies
from agenttest.modules.user_settings.api.router import UserSettingsApiDependencies
from agenttest.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)

UnitOfWorkFactory = Callable[[], SqlAlchemyUnitOfWork]


@dataclass(frozen=True, slots=True)
class AppOverrides:
    auth: AuthApiDependencies | None = None
    admin: AdminApiDependencies | None = None
    projects: ProjectApiDependencies | None = None
    audit: AuditApiDependencies | None = None
    agents: AgentApiDependencies | None = None
    datasets: DatasetApiDependencies | None = None
    test_plans: TestPlanApiDependencies | None = None
    environments: EnvironmentApiDependencies | None = None
    runs: RunApiDependencies | None = None
    user_settings: UserSettingsApiDependencies | None = None
    feedback: FeedbackApiDependencies | None = None


@dataclass(frozen=True, slots=True)
class BootstrapContext:
    settings: Settings
    session_factory: async_sessionmaker[AsyncSession]
    auth: AuthApiDependencies
    project_access: ProjectAccessAdapter
    uow_factory: UnitOfWorkFactory
    overrides: AppOverrides


def build_context(settings: Settings, overrides: AppOverrides) -> BootstrapContext:
    from agenttest.bootstrap.wiring import build_auth_dependencies

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    auth = overrides.auth or build_auth_dependencies(settings)
    return BootstrapContext(
        settings=settings,
        session_factory=session_factory,
        auth=auth,
        project_access=ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory)),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        overrides=overrides,
    )
