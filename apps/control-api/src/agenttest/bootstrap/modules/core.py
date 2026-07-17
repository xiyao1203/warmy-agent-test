from fastapi import FastAPI

from agenttest.bootstrap import wiring
from agenttest.bootstrap.context import BootstrapContext
from agenttest.entrypoints.http.health import router as health_router
from agenttest.modules.agents.api.router import create_agent_router
from agenttest.modules.audit.api.router import create_audit_router
from agenttest.modules.datasets.api.router import create_dataset_router
from agenttest.modules.environments.api.router import create_environment_router
from agenttest.modules.feedback.api.router import create_feedback_router
from agenttest.modules.identity.api.admin_router import create_admin_router
from agenttest.modules.identity.api.router import create_auth_router
from agenttest.modules.model_configs.api.router import create_model_config_router
from agenttest.modules.model_configs.infrastructure.temporal_invoker import (
    TemporalModelInvoker,
)
from agenttest.modules.projects.api.router import create_project_router
from agenttest.modules.reports.api.router import create_report_router
from agenttest.modules.reports.application.export import ReportExportService
from agenttest.modules.reports.application.service import ReportService
from agenttest.modules.reports.infrastructure.generators.html_report import (
    HtmlReportGenerator,
)
from agenttest.modules.reports.infrastructure.generators.json_report import (
    JsonReportGenerator,
)
from agenttest.modules.reports.infrastructure.generators.junit_report import (
    JunitReportGenerator,
)
from agenttest.modules.run_postprocessing.api.internal_router import (
    create_internal_postprocess_router,
)
from agenttest.modules.run_postprocessing.api.router import create_run_trust_loop_router
from agenttest.modules.run_postprocessing.application import PostprocessStageController
from agenttest.modules.run_postprocessing.infrastructure.repository import (
    SqlAlchemyPostprocessRepository,
)
from agenttest.modules.run_postprocessing.queries import RunTrustLoopQueryService
from agenttest.modules.run_postprocessing.snapshot_reader import (
    RunPostprocessSnapshotReader,
)
from agenttest.modules.run_postprocessing.stages import PostprocessStageService
from agenttest.modules.runs.api.router import create_run_router
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    SqlAlchemyRunRepository,
)
from agenttest.modules.test_plans.api.router import create_test_plan_router
from agenttest.modules.user_settings.api.router import create_user_settings_router


def register(app: FastAPI, context: BootstrapContext) -> None:
    settings = context.settings
    auth = context.auth
    overrides = context.overrides

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(create_auth_router(auth, settings), prefix="/api/v1")

    admin = overrides.admin or wiring.build_admin_dependencies(settings)
    app.include_router(
        create_admin_router(
            admin,
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    projects = overrides.projects or wiring.build_project_dependencies(settings)
    app.include_router(
        create_project_router(
            projects,
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    audits = overrides.audit or wiring.build_audit_dependencies(settings)
    app.include_router(
        create_audit_router(
            audits,
            current_user=auth.current_user,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    agents = overrides.agents or wiring.build_agent_dependencies(settings)
    app.include_router(
        create_agent_router(
            agents,
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    datasets = overrides.datasets or wiring.build_dataset_dependencies(settings)
    app.include_router(
        create_dataset_router(
            datasets,
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    test_plans = overrides.test_plans or wiring.build_test_plan_dependencies(settings)
    app.include_router(
        create_test_plan_router(
            test_plans,
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    environments = overrides.environments or wiring.build_environment_dependencies(settings)
    app.include_router(
        create_environment_router(
            environments,
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    app.include_router(
        create_model_config_router(
            service=wiring.build_model_config_service(settings),
            invoker=TemporalModelInvoker(
                address=settings.temporal_address,
                namespace=settings.temporal_namespace,
                task_queue=settings.model_runner_task_queue,
                allow_private_network=settings.model_allow_private_network,
            ),
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    runs = overrides.runs or wiring.build_run_dependencies(settings)
    app.include_router(
        create_run_router(
            runs,
            current_user=auth.current_user,
            csrf=auth.csrf,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    postprocess_repository = SqlAlchemyPostprocessRepository(context.session_factory)
    postprocess_runs = SqlAlchemyRunRepository(context.session_factory)
    app.include_router(
        create_internal_postprocess_router(
            internal_token=settings.internal_api_token,
            controller=PostprocessStageController(
                postprocess_repository,
                PostprocessStageService(RunPostprocessSnapshotReader(postprocess_runs)),
            ),
            uow_factory=context.uow_factory,
        ),
        prefix="/api/v1",
    )
    app.include_router(
        create_run_trust_loop_router(
            service=RunTrustLoopQueryService(postprocess_repository, runs.get_run),
            current_user=auth.current_user,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    app.include_router(
        create_report_router(
            exporter=ReportExportService(
                reports=ReportService(
                    runs=SqlAlchemyRunRepository(context.session_factory),
                    project_access=context.project_access,
                ),
                renderers=[
                    JsonReportGenerator(),
                    JunitReportGenerator(),
                    HtmlReportGenerator(),
                ],
            ),
            current_user=auth.current_user,
            settings=settings,
        ),
        prefix="/api/v1",
    )

    user_settings = overrides.user_settings or wiring.build_user_settings_dependencies(settings)
    app.include_router(
        create_user_settings_router(user_settings, settings),
        prefix="/api/v1",
    )

    feedback = overrides.feedback or wiring.build_feedback_dependencies(settings)
    app.include_router(
        create_feedback_router(feedback, settings),
        prefix="/api/v1",
    )
