from fastapi import FastAPI
from starlette.requests import Request

from agenttest.bootstrap.core_summaries import SqlAlchemyCoreSummaryReader
from agenttest.bootstrap.gate_evidence import SqlAlchemyGateEvidence
from agenttest.bootstrap.project_access import ProjectAccessAdapter
from agenttest.bootstrap.providers.core import build_model_config_service
from agenttest.bootstrap.settings import Settings
from agenttest.modules.model_configs.infrastructure.temporal_invoker import TemporalModelInvoker
from agenttest.modules.projects.infrastructure.persistence.repositories import (
    SqlAlchemyProjectRepository,
)
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
)
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    SqlAlchemyRunRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def _register_security_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册安全策略 CRUD 端点（auth+csrf+project 保护）。"""
    from uuid import UUID, uuid4

    from fastapi import Header, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    from agenttest.bootstrap.project_access import ProjectAccessAdapter
    from agenttest.modules.identity.application.queries.current_user import (
        InvalidSessionError,
    )
    from agenttest.modules.identity.public import User
    from agenttest.modules.projects.infrastructure.persistence.repositories import (
        SqlAlchemyProjectRepository,
    )
    from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
    from agenttest.modules.security.domain.models import (
        SecurityPolicy,
    )
    from agenttest.modules.security.infrastructure.repositories import (
        SqlAlchemySecurityPolicyRepository,
    )

    class CreatePolicyRequest(BaseModel):
        name: str
        max_steps: int = 20
        timeout_seconds: int = 300
        blocked_tools: list[str] = []
        require_confirmation: bool = True
        enabled: bool = True

    CSRF_NAME = "agenttest_csrf"
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    project_repo = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(project_repo)

    async def _actor(request: Request) -> User:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise InvalidSessionError
        return await auth_deps.current_user.execute(token)

    @app.get("/api/v1/projects/{project_id}/security/policies")
    async def list_policies(
        request: Request,
        project_id: UUID,
    ):
        try:
            await _actor(request)
            # 项目存在性检查
            from sqlalchemy import text

            async with session_factory() as session:
                result = await session.execute(
                    text("SELECT 1 FROM projects WHERE id = :pid"),
                    {"pid": project_id},
                )
                if result.scalar() is None:
                    return JSONResponse(status_code=404, content={"detail": "Not Found"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        async with session_factory() as session:
            repo = SqlAlchemySecurityPolicyRepository(session)
            policies = await repo.list_all(project_id=project_id)
            return {
                "items": [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "max_steps": p.max_steps,
                        "timeout_seconds": p.timeout_seconds,
                        "blocked_tools": p.blocked_tools,
                        "require_confirmation": p.require_confirmation,
                        "enabled": p.enabled,
                    }
                    for p in policies
                ]
            }

    @app.post("/api/v1/projects/{project_id}/security/policies")
    async def create_policy(
        request: Request,
        project_id: UUID,
        body: CreatePolicyRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        try:
            actor = await _actor(request)
            if not x_csrf_token or x_csrf_token != request.cookies.get(CSRF_NAME):
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})
            await access.ensure_editor(actor, ProjectId(project_id))
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        async with session_factory() as session:
            repo = SqlAlchemySecurityPolicyRepository(session)
            policy = SecurityPolicy(
                id=uuid4(),
                project_id=project_id,
                name=body.name,
                max_steps=body.max_steps,
                timeout_seconds=body.timeout_seconds,
                blocked_tools=body.blocked_tools,
                require_confirmation=body.require_confirmation,
                enabled=body.enabled,
            )
            await repo.save(policy, project_id=project_id)
            await session.commit()
            return {"id": str(policy.id), "name": policy.name}


def _register_scorer_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册评分器 CRUD API。"""
    from agenttest.modules.scorers.api.router import (
        ScorerApiDependencies,
        create_scorer_router,
    )
    from agenttest.modules.scorers.application.model_judge import ModelJudge
    from agenttest.modules.scorers.application.service import ScorerService
    from agenttest.modules.scorers.infrastructure.persistence.repositories import (
        SqlAlchemyScorerRepository,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_scorer_router(
        ScorerApiDependencies(
            service=ScorerService(
                scorers=SqlAlchemyScorerRepository(session_factory),
                project_access=ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory)),
                model_judge=ModelJudge(
                    build_model_config_service(settings),
                    TemporalModelInvoker(
                        address=settings.temporal_address,
                        namespace=settings.temporal_namespace,
                        task_queue=settings.model_runner_task_queue,
                        allow_private_network=settings.model_allow_private_network,
                    ),
                ),
            ),
            actor_for=actor_for,
            settings=settings,
            summaries=SqlAlchemyCoreSummaryReader(session_factory),
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_experiment_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册实验对比 API。"""
    from agenttest.modules.experiments.api.router import (
        ExperimentApiDependencies,
        create_experiment_router,
    )
    from agenttest.modules.experiments.application.service import ExperimentService
    from agenttest.modules.experiments.infrastructure.persistence.repositories import (
        SqlAlchemyExperimentRepository,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    access = ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory))

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_experiment_router(
        ExperimentApiDependencies(
            service=ExperimentService(
                experiments=SqlAlchemyExperimentRepository(session_factory),
                runs=SqlAlchemyRunRepository(session_factory),
                project_access=access,
            ),
            actor_for=actor_for,
            settings=settings,
            summaries=SqlAlchemyCoreSummaryReader(session_factory),
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_review_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册人工审核 API。"""
    from agenttest.modules.reviews.api.router import (
        ReviewApiDependencies,
        create_review_router,
    )
    from agenttest.modules.reviews.application.service import ReviewService
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    access = ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory))

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_review_router(
        ReviewApiDependencies(
            service=ReviewService(
                reviews=SqlAlchemyReviewTaskRepository(session_factory),
                project_access=access,
            ),
            actor_for=actor_for,
            settings=settings,
            summaries=SqlAlchemyCoreSummaryReader(session_factory),
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_security_scan_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册安全扫描 API。"""
    from agenttest.bootstrap.security_target import SqlAlchemySecurityTargetResolver
    from agenttest.modules.security.adapters import create_scanner
    from agenttest.modules.security.api.scan_router import (
        SecurityScanApiDependencies,
        create_security_scan_router,
    )
    from agenttest.modules.security.application.scan_service import SecurityScanService
    from agenttest.modules.security.infrastructure.repositories import (
        SqlAlchemySecurityScanRepository,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_security_scan_router(
        SecurityScanApiDependencies(
            service=SecurityScanService(
                scans=SqlAlchemySecurityScanRepository(session_factory),
                targets=SqlAlchemySecurityTargetResolver(session_factory),
                scanner_factory=lambda: create_scanner(settings.promptfoo_bin),
                project_access=ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory)),
                allow_private_network=settings.security_scan_allow_private_network,
            ),
            actor_for=actor_for,
            settings=settings,
            summaries=SqlAlchemyCoreSummaryReader(session_factory),
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_gate_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册发布门禁 API。"""
    from agenttest.modules.gates.api.router import (
        GateApiDependencies,
        create_gate_router,
    )
    from agenttest.modules.gates.application.service import GateService
    from agenttest.modules.gates.infrastructure.persistence.repositories import (
        SqlAlchemyReleaseGateRepository,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_gate_router(
        GateApiDependencies(
            service=GateService(
                gates=SqlAlchemyReleaseGateRepository(session_factory),
                evidence=SqlAlchemyGateEvidence(session_factory),
                project_access=ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory)),
            ),
            actor_for=actor_for,
            settings=settings,
            summaries=SqlAlchemyCoreSummaryReader(session_factory),
        )
    )
    app.include_router(router, prefix="/api/v1")
