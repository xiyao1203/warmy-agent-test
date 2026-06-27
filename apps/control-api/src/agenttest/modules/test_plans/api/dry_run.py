"""试运行 API 端点。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.test_plans.infrastructure.persistence.repositories import (
    SqlAlchemyTestPlanVersionRepository,
)
from agenttest.shared.api.auth_guard import require_writer


def create_dry_run_router(
    *,
    session_factory,
    actor_for,
    check_project,
    settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}/dry-run",
        tags=["test-plan-dry-run"],
    )

    version_repo = SqlAlchemyTestPlanVersionRepository(session_factory)

    @router.post("")
    async def dry_run(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        """试运行：预览测试计划版本的执行参数。"""
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        async with session_factory() as session:
            # 校验版本属于当前项目的测试计划
            version_check = await session.execute(
                text(
                    "SELECT tpv.id FROM test_plan_versions tpv "
                    "JOIN test_plans tp ON tpv.test_plan_id = tp.id "
                    "WHERE tpv.id = :vid AND tp.project_id = :pid AND tp.id = :plan_id"
                ),
                {"vid": version_id, "pid": project_id, "plan_id": plan_id},
            )
            if version_check.scalar() is None:
                return JSONResponse(
                    status_code=404, content={"detail": "测试计划版本不存在"}
                )

            from agenttest.modules.test_plans.domain.entities import TestPlanVersionId

            version = await version_repo.get_by_id(TestPlanVersionId(version_id))
            if version is None:
                return JSONResponse(
                    status_code=404, content={"detail": "测试计划版本不存在"}
                )

            errors: list[str] = []

            if version.agent_version_id is not None:
                result = await session.execute(
                    text(
                        "SELECT 1 FROM agent_versions WHERE id = :vid AND status = 'published'"
                    ),
                    {"vid": version.agent_version_id.value},
                )
                if result.scalar() is None:
                    errors.append("关联的 Agent 版本不存在或未发布")

            if version.dataset_version_id is not None:
                result = await session.execute(
                    text(
                        "SELECT 1 FROM dataset_versions WHERE id = :vid AND status = 'published'"
                    ),
                    {"vid": version.dataset_version_id.value},
                )
                if result.scalar() is None:
                    errors.append("关联的数据集版本不存在或未发布")

            if version.environment_template_id is not None:
                result = await session.execute(
                    text(
                        "SELECT 1 FROM environment_templates WHERE id = :tid AND project_id = :pid"
                    ),
                    {"tid": version.environment_template_id.value, "pid": project_id},
                )
                if result.scalar() is None:
                    errors.append("关联的环境模板不存在")

            num_cases = 0
            if version.dataset_version_id is not None:
                result = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM test_cases "
                        "WHERE dataset_version_id = :dvid"
                    ),
                    {"dvid": version.dataset_version_id.value},
                )
                num_cases = result.scalar() or 0

            preview = version.config.dry_run_preview(num_cases=num_cases)

            return {
                "version_id": str(version_id),
                "status": version.status.value,
                "preview": preview,
                "validation": {"valid": len(errors) == 0, "errors": errors},
            }

    return router
