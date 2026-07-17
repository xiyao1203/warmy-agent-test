from fastapi import FastAPI
from starlette.requests import Request

from agenttest.bootstrap.core_summaries import SqlAlchemyCoreSummaryReader
from agenttest.bootstrap.gate_evidence import SqlAlchemyGateEvidence
from agenttest.bootstrap.providers.core import (
    build_agent_dependencies,
    build_dataset_dependencies,
    build_environment_dependencies,
    build_model_config_service,
    build_run_dependencies,
    build_test_plan_dependencies,
)
from agenttest.bootstrap.settings import Settings
from agenttest.modules.agents.infrastructure.connection_validator import (
    HttpAgentConnectionValidator,
)
from agenttest.modules.agents.infrastructure.persistence.repositories import (
    SqlAlchemyAgentVersionRepository,
)
from agenttest.modules.audit.application.record import AuditRecorder
from agenttest.modules.audit.infrastructure.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from agenttest.modules.identity.infrastructure.persistence.repositories import (
    SqlAlchemyUserRepository,
)
from agenttest.modules.model_configs.infrastructure.temporal_invoker import TemporalModelInvoker
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def _register_test_agent_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册测试 Agent 对话 API。"""
    from agenttest.modules.browser_profiles.infrastructure.repository import (
        SqlAlchemyBrowserProfileRepository,
    )
    from agenttest.modules.experiments.infrastructure.persistence.repositories import (
        SqlAlchemyExperimentRepository,
    )
    from agenttest.modules.gates.infrastructure.persistence.repositories import (
        SqlAlchemyReleaseGateRepository,
    )
    from agenttest.modules.run_postprocessing.infrastructure.repository import (
        SqlAlchemyPostprocessRepository,
    )
    from agenttest.modules.run_postprocessing.queries import RunTrustLoopQueryService
    from agenttest.modules.scorers.infrastructure.persistence.repositories import (
        SqlAlchemyScorerRepository,
    )
    from agenttest.modules.security.infrastructure.repositories import (
        SqlAlchemySecurityScanRepository,
    )
    from agenttest.modules.test_accounts.infrastructure.persistence.repositories import (
        SqlAlchemyTestAccountRepository,
    )
    from agenttest.modules.test_agent.adapters.platform import (
        CompositePlatformGateway,
        HandlerPlatformGateway,
    )
    from agenttest.modules.test_agent.api.router import create_test_agent_router
    from agenttest.modules.test_agent.api.target_chat import create_target_chat_router
    from agenttest.modules.test_agent.application.conversation import SuperAgentConversation
    from agenttest.modules.test_agent.application.generations import GenerationCoordinator
    from agenttest.modules.test_agent.application.mission_executor import (
        ConfirmedMissionAssetExecutor,
    )
    from agenttest.modules.test_agent.application.orchestrator import SuperAgentOrchestrator
    from agenttest.modules.test_agent.application.platform_catalog import (
        build_platform_registry,
    )
    from agenttest.modules.test_agent.application.target_chat import TargetChatService
    from agenttest.modules.test_agent.infrastructure.repositories import (
        SqlAlchemyChatGenerationRepository,
        SqlAlchemyChatSessionRepository,
        SqlAlchemyOrchestrationRepository,
        SqlAlchemyTargetChatRepository,
    )
    from agenttest.modules.test_agent.infrastructure.target_runtime import (
        TemporalTargetAgentRuntime,
    )
    from agenttest.modules.test_missions.api.internal_router import (
        create_internal_mission_stage_router,
    )
    from agenttest.modules.test_missions.api.router import (
        MissionApiDependencies,
        create_test_mission_router,
    )
    from agenttest.modules.test_missions.application.capability_gateway import (
        MissionCapabilityGateway,
    )
    from agenttest.modules.test_missions.application.commands import (
        CancelMissionHandler,
        ConfirmMissionHandler,
        DiscoverMissionHandler,
        PreviewMissionHandler,
        ResumeMissionHandler,
        UpsertMissionHandler,
    )
    from agenttest.modules.test_missions.application.compiler import MissionCompiler
    from agenttest.modules.test_missions.application.discovery import MissionDiscovery
    from agenttest.modules.test_missions.application.intake import MissionIntake
    from agenttest.modules.test_missions.application.preflight import MissionPreflight
    from agenttest.modules.test_missions.application.queries import GetMissionHandler
    from agenttest.modules.test_missions.application.resolution import PlatformAssetResolver
    from agenttest.modules.test_missions.application.stage_controller import (
        MissionStageController,
    )
    from agenttest.modules.test_missions.application.stages import MissionStageService
    from agenttest.modules.test_missions.application.url_policy import TargetUrlPolicy
    from agenttest.modules.test_missions.infrastructure.http_discovery import (
        HttpTargetDiscoveryProbe,
        ProjectMissionAccessCatalog,
    )
    from agenttest.modules.test_missions.infrastructure.platform_resolver import (
        PublishedAgentMissionCatalog,
    )
    from agenttest.modules.test_missions.infrastructure.repositories import (
        SqlAlchemyMissionRepository,
    )
    from agenttest.modules.test_missions.infrastructure.temporal_orchestrator import (
        TemporalMissionOrchestrator,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    orchestration = SqlAlchemyOrchestrationRepository(session_factory)
    model_config_service = build_model_config_service(settings)
    temporal_invoker = TemporalModelInvoker(
        address=settings.temporal_address,
        namespace=settings.temporal_namespace,
        task_queue=settings.model_runner_task_queue,
        allow_private_network=settings.model_allow_private_network,
    )
    mission_repository = SqlAlchemyMissionRepository(session_factory)
    mission_preflight = MissionPreflight()
    mission_runtime = TemporalMissionOrchestrator(
        address=settings.temporal_address,
        namespace=settings.temporal_namespace,
        task_queue=settings.temporal_task_queue,
        callback_base_url=str(settings.control_api_base_url),
    )
    mission_audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    mission_upsert = UpsertMissionHandler(mission_repository, MissionIntake())
    browser_profiles = SqlAlchemyBrowserProfileRepository(session_factory)
    test_accounts = SqlAlchemyTestAccountRepository(session_factory)
    mission_discover = DiscoverMissionHandler(
        mission_repository,
        MissionDiscovery(
            HttpTargetDiscoveryProbe(
                access_catalog=ProjectMissionAccessCatalog(browser_profiles, test_accounts),
                url_policy=TargetUrlPolicy(
                    allowed_local_hosts=settings.mission_local_host_allowlist
                ),
            )
        ),
        PlatformAssetResolver(
            PublishedAgentMissionCatalog(SqlAlchemyAgentVersionRepository(session_factory)),
            url_policy=TargetUrlPolicy(allowed_local_hosts=settings.mission_local_host_allowlist),
        ),
    )
    mission_preview = PreviewMissionHandler(mission_repository, mission_preflight)
    mission_confirm = ConfirmMissionHandler(
        mission_repository, mission_preflight, mission_runtime, mission_audit
    )
    mission_get = GetMissionHandler(mission_repository, mission_preflight)
    mission_runs = build_run_dependencies(settings)
    gateway = HandlerPlatformGateway(
        agents=build_agent_dependencies(settings),
        datasets=build_dataset_dependencies(settings),
        environments=build_environment_dependencies(settings),
        plans=build_test_plan_dependencies(settings),
        runs=mission_runs,
        scorers=SqlAlchemyScorerRepository(session_factory),
        experiments=SqlAlchemyExperimentRepository(session_factory),
        reviews=SqlAlchemyReviewTaskRepository(session_factory),
        gates=SqlAlchemyReleaseGateRepository(session_factory),
        security=SqlAlchemySecurityScanRepository(session_factory),
        accounts=test_accounts,
        promptfoo_bin=settings.promptfoo_bin,
        allow_private_security_targets=settings.security_scan_allow_private_network,
        gate_evidence=SqlAlchemyGateEvidence(session_factory),
        models=model_config_service,
        invoker=temporal_invoker,
        connection_validator=HttpAgentConnectionValidator(
            allow_private_network=settings.security_scan_allow_private_network
        ),
        summaries=SqlAlchemyCoreSummaryReader(session_factory),
    )
    composite_gateway = CompositePlatformGateway(
        gateway,
        MissionCapabilityGateway(
            upsert=mission_upsert,
            discover=mission_discover,
            preview=mission_preview,
            confirm=mission_confirm,
            get=mission_get,
        ),
    )
    registry = build_platform_registry(composite_gateway)

    async def check_project(project_id):
        from sqlalchemy import text

        # Convert UUID to hex format (no hyphens) for SQLite compatibility
        if isinstance(project_id, str):
            pid_str = project_id.replace("-", "")
        else:
            pid_str = (
                project_id.hex if hasattr(project_id, "hex") else str(project_id).replace("-", "")
            )

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": pid_str},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=404,
                    detail="Project not found",
                )

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_test_agent_router(
        sessions=SqlAlchemyChatSessionRepository(session_factory),
        orchestration=orchestration,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
        conversation=SuperAgentConversation(
            model_config_service,
            temporal_invoker,
            capabilities=registry.describe_all(),
            platform_gateway=composite_gateway,
        ),
        agent_orchestrator=SuperAgentOrchestrator(registry, orchestration),
        generation_coordinator=GenerationCoordinator(
            SqlAlchemyChatGenerationRepository(session_factory),
            orchestration,
            temporal_invoker,
        ),
    )
    app.include_router(router, prefix="/api/v1")
    app.include_router(
        create_test_mission_router(
            dependencies=MissionApiDependencies(
                upsert=mission_upsert,
                discover=mission_discover,
                preview=mission_preview,
                confirm=mission_confirm,
                get=mission_get,
                cancel=CancelMissionHandler(mission_repository, mission_runtime, mission_audit),
                resume=ResumeMissionHandler(mission_repository, mission_runtime, mission_audit),
            ),
            actor_for=actor_for,
            check_project=check_project,
            settings=settings,
        ),
        prefix="/api/v1",
    )
    mission_stages = MissionStageService(
        MissionCompiler(),
        ConfirmedMissionAssetExecutor(registry),
        mission_repository,
        RunTrustLoopQueryService(
            SqlAlchemyPostprocessRepository(session_factory), mission_runs.get_run
        ),
    )
    app.include_router(
        create_internal_mission_stage_router(
            internal_token=settings.internal_api_token,
            controller=MissionStageController(
                mission_repository,
                mission_stages,
                SqlAlchemyUserRepository(session_factory),
            ),
        ),
        prefix="/api/v1",
    )
    target_repository = SqlAlchemyTargetChatRepository(session_factory)
    app.include_router(
        create_target_chat_router(
            service=TargetChatService(
                target_repository,
                TemporalTargetAgentRuntime(
                    address=settings.temporal_address,
                    namespace=settings.temporal_namespace,
                    task_queue=settings.temporal_task_queue,
                ),
            ),
            repository=target_repository,
            agents=build_agent_dependencies(settings),
            environments=build_environment_dependencies(settings),
            datasets=build_dataset_dependencies(settings),
            actor_for=actor_for,
            settings=settings,
        ),
        prefix="/api/v1",
    )
