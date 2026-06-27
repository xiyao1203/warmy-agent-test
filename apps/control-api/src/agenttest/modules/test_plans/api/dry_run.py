"""试运行 API 端点。

POST /api/v1/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}/dry-run
返回预计用例数、配置参数、关联版本有效性校验结果。
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.test_plans.domain.entities import TestPlanVersionId
from agenttest.modules.test_plans.infrastructure.persistence.repositories import (
    SqlAlchemyTestPlanVersionRepository,
)


def create_dry_run_router(
    *,
    session_factory,
    actor_for,
    check_project,
) -> APIRouter:
    """创建试运行 API 路由。"""
    router = APIRouter(
        prefix="/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}/dry-run",
        tags=["test-plan-dry-run"],
    )

    @router.post("")
    async def dry_run(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
    ):
        """试运行：预览测试计划版本的执行参数。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(
                status_code=404, content={"detail": "项目不存在"}
            )

        async with session_factory() as session:
            version_repo = SqlAlchemyTestPlanVersionRepository(session)
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
                    {
                        "tid": version.environment_template_id.value,
                        "pid": project_id,
                    },
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
                "validation": {
                    "valid": len(errors) == 0,
                    "errors": errors,
                },
            }

    return router
