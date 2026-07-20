"""项目级大模型配置 HTTP 路由。"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.shared.api.pagination import resolve_page_request
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.pagination import paginate_items

from ..application.ports import (
    InvocationMessage,
    ModelInvoker,
    ModelRuntimeUnavailableError,
)
from ..application.service import ModelConfigService
from ..domain.entities import ModelConfigurationId
from ..domain.errors import (
    ModelConfigInUseError,
    ModelConfigNameConflictError,
    ModelConfigNotFoundError,
    ModelDefaultMissingError,
)
from ..domain.value_objects import ModelPurpose
from .schemas import (
    CreateModelConfigRequest,
    ModelConfigListResponse,
    ModelConfigResponse,
    ModelDefaultListResponse,
    ModelDefaultResponse,
    SetModelDefaultRequest,
    TextJudgeRequest,
    UpdateModelConfigRequest,
    VisionJudgeRequest,
)

CSRF_COOKIE_NAME = "agenttest_csrf"
logger = logging.getLogger(__name__)


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


def create_model_config_router(
    *,
    service: ModelConfigService,
    invoker: ModelInvoker,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    """创建项目模型配置与默认用途路由。"""

    router = APIRouter(prefix="/projects/{project_id}", tags=["model-configs"])

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return problem(401, "Authentication required", "A valid session is required")
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return problem(401, "Authentication required", "A valid session is required")

    async def writer(request: Request, csrf_header: str | None) -> User | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        token = request.cookies.get(settings.session_cookie_name)
        cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not token or not csrf_header or csrf_header != cookie:
            return problem(403, "CSRF validation failed", "A valid CSRF token is required")
        try:
            await csrf.execute(token, csrf_header)
        except InvalidSessionError:
            return problem(403, "CSRF validation failed", "A valid CSRF token is required")
        return actor

    @router.get("/model-configs", response_model=ModelConfigListResponse)
    async def list_configs(
        request: Request,
        project_id: UUID,
        page: int | None = Query(default=None),
        page_size: int | None = Query(default=None),
    ):
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items = await service.list_configs(actor, ProjectId(project_id))
        except ProjectNotFoundError:
            return problem(404, "Asset not found", "Project was not found")
        page_request = resolve_page_request(page=page, page_size=page_size)
        if page_request:
            result = paginate_items(items, page_request)
            items = result.items
            total = result.total
            response_page = result.page
            response_page_size = result.page_size
            total_pages = result.total_pages
        else:
            total = len(items)
            response_page = None
            response_page_size = 50
            total_pages = 1 if items else 0
        return ModelConfigListResponse(
            items=[ModelConfigResponse.from_domain(x) for x in items],
            total=total,
            page=response_page,
            page_size=response_page_size,
            total_pages=total_pages,
        )

    @router.post("/model-configs", response_model=ModelConfigResponse, status_code=201)
    async def create_config(
        request: Request,
        project_id: UUID,
        payload: CreateModelConfigRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            item = await service.create(
                actor,
                ProjectId(project_id),
                name=payload.name,
                base_url=payload.base_url,
                model_name=payload.model_name,
                api_key=payload.api_key,
                supports_vision=payload.supports_vision,
            )
        except ProjectNotFoundError:
            return problem(404, "Asset not found", "Project was not found")
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        except ModelConfigNameConflictError:
            return problem(
                409,
                "Model configuration conflict",
                "Model configuration name already exists",
            )
        except ValueError as error:
            return problem(400, "Invalid request", str(error))
        return ModelConfigResponse.from_domain(item)

    @router.get("/model-configs/{model_config_id}", response_model=ModelConfigResponse)
    async def get_config(request: Request, project_id: UUID, model_config_id: UUID):
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            item = await service.get(
                actor,
                ProjectId(project_id),
                ModelConfigurationId(model_config_id),
            )
        except (ProjectNotFoundError, ModelConfigNotFoundError):
            return problem(404, "Asset not found", "Model configuration was not found")
        return ModelConfigResponse.from_domain(item)

    @router.patch("/model-configs/{model_config_id}", response_model=ModelConfigResponse)
    async def update_config(
        request: Request,
        project_id: UUID,
        model_config_id: UUID,
        payload: UpdateModelConfigRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            item = await service.update(
                actor,
                ProjectId(project_id),
                ModelConfigurationId(model_config_id),
                **payload.model_dump(exclude_unset=True),
            )
        except (ProjectNotFoundError, ModelConfigNotFoundError):
            return problem(404, "Asset not found", "Model configuration was not found")
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        except ModelConfigInUseError:
            return problem(
                409, "Model configuration in use", "Reassign defaults before disabling it"
            )
        except ValueError as error:
            return problem(400, "Invalid request", str(error))
        return ModelConfigResponse.from_domain(item)

    @router.delete("/model-configs/{model_config_id}", status_code=204)
    async def delete_config(
        request: Request,
        project_id: UUID,
        model_config_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await service.delete(
                actor,
                ProjectId(project_id),
                ModelConfigurationId(model_config_id),
            )
        except (ProjectNotFoundError, ModelConfigNotFoundError):
            return problem(404, "Asset not found", "Model configuration was not found")
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        except ModelConfigInUseError:
            return problem(
                409, "Model configuration in use", "Reassign defaults before deleting it"
            )
        return Response(status_code=204)

    @router.post("/model-configs/{model_config_id}/test-connection")
    async def test_connection(
        request: Request,
        project_id: UUID,
        model_config_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        """由 Model Runner 发送最小真实请求验证连接。"""

        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            item = await service.get_for_execution(
                actor,
                ProjectId(project_id),
                ModelConfigurationId(model_config_id),
            )
            result = await invoker.invoke(
                item,
                [InvocationMessage(role="user", content="Reply with ok.")],
                timeout_seconds=15,
                max_tokens=8,
            )
        except (ProjectNotFoundError, ModelConfigNotFoundError):
            return problem(404, "Asset not found", "Model configuration was not found")
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        except ModelRuntimeUnavailableError as error:
            return problem(503, "Model runtime unavailable", str(error))
        except (ConnectionError, TimeoutError, ValueError) as error:
            logger.warning("Model connection test failed: %s", error)
            return problem(
                503, "Model connection failed", "Model Runner or provider is unavailable"
            )
        except Exception:
            logger.exception("Unexpected error during model connection test")
            return problem(
                503, "Model connection failed", "Model Runner or provider is unavailable"
            )
        return {"ok": True, "latency_ms": result.latency_ms, "total_tokens": result.total_tokens}

    @router.get("/model-defaults", response_model=ModelDefaultListResponse)
    async def list_defaults(request: Request, project_id: UUID):
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items = await service.list_defaults(actor, ProjectId(project_id))
        except ProjectNotFoundError:
            return problem(404, "Asset not found", "Project was not found")
        return ModelDefaultListResponse(items=[ModelDefaultResponse.from_domain(x) for x in items])

    @router.put("/model-defaults/{purpose}", response_model=ModelDefaultResponse)
    async def set_default(
        request: Request,
        project_id: UUID,
        purpose: ModelPurpose,
        payload: SetModelDefaultRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            value = await service.set_default(
                actor,
                ProjectId(project_id),
                purpose,
                ModelConfigurationId(UUID(payload.model_config_id)),
            )
        except (ProjectNotFoundError, ModelConfigNotFoundError):
            return problem(404, "Asset not found", "Model configuration was not found")
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        except ValueError as error:
            return problem(400, "Invalid request", str(error))
        return ModelDefaultResponse.from_domain(value)

    @router.delete("/model-defaults/{purpose}", status_code=204)
    async def delete_default(
        request: Request,
        project_id: UUID,
        purpose: ModelPurpose,
        x_csrf_token: str | None = Header(default=None),
    ):
        """取消项目某个用途的默认模型绑定。"""
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await service.clear_default(actor, ProjectId(project_id), purpose)
        except ProjectNotFoundError:
            return problem(404, "Asset not found", "Project was not found")
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        return Response(status_code=204)

    @router.post("/model-judges/text")
    async def judge_text(
        request: Request,
        project_id: UUID,
        payload: TextJudgeRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """使用项目文本裁判默认模型执行真实评分。"""

        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        from agenttest.modules.scorers.public import (
            InvalidJudgeResultError,
            ModelJudge,
        )

        try:
            result = await ModelJudge(service, invoker).judge_text(
                actor,
                ProjectId(project_id),
                input_text=payload.input_text,
                output_text=payload.output_text,
                rubric=payload.rubric,
            )
        except ModelDefaultMissingError:
            return problem(409, "Default model missing", "项目尚未配置文本裁判默认模型")
        except InvalidJudgeResultError as error:
            return problem(422, "Invalid judge result", str(error))
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        except ModelRuntimeUnavailableError as error:
            return problem(503, "Model runtime unavailable", str(error))
        except (ConnectionError, TimeoutError, ValueError) as error:
            logger.warning("Model text judge failed: %s", error)
            return problem(503, "Model judge failed", "Model Runner or provider is unavailable")
        except Exception:
            logger.exception("Unexpected error during text judge")
            return problem(503, "Model judge failed", "Model Runner or provider is unavailable")
        return asdict(result)

    @router.post("/model-judges/vision")
    async def judge_vision(
        request: Request,
        project_id: UUID,
        payload: VisionJudgeRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """使用项目视觉裁判默认模型执行真实评分。"""

        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        from agenttest.modules.scorers.public import (
            InvalidJudgeResultError,
            ModelJudge,
        )

        try:
            result = await ModelJudge(service, invoker).judge_vision(
                actor,
                ProjectId(project_id),
                prompt=payload.prompt,
                image_data_url=payload.image_data_url,
                rubric=payload.rubric,
            )
        except ModelDefaultMissingError:
            return problem(409, "Default model missing", "项目尚未配置视觉裁判默认模型")
        except (InvalidJudgeResultError, ValueError) as error:
            return problem(422, "Invalid judge result", str(error))
        except PermissionError:
            return problem(403, "Permission denied", "Project editor access is required")
        except ModelRuntimeUnavailableError as error:
            return problem(503, "Model runtime unavailable", str(error))
        except (ConnectionError, TimeoutError) as error:
            logger.warning("Model vision judge failed: %s", error)
            return problem(503, "Model judge failed", "Model Runner or provider is unavailable")
        except Exception:
            logger.exception("Unexpected error during vision judge")
            return problem(503, "Model judge failed", "Model Runner or provider is unavailable")
        return asdict(result)

    return router


def problem(status: int, title: str, detail: str) -> JSONResponse:
    """创建统一 RFC 7807 响应。"""

    value = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=value.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
