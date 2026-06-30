"""新端点共享的认证与 CSRF 校验工具。

所有通过 _register_xxx_endpoints 注册的路由使用此模块。
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from agenttest.modules.identity.public import InvalidSessionError

CSRF_COOKIE_NAME = "agenttest_csrf"


def authentication_required() -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "Authentication required"})


def csrf_failed() -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})


async def require_actor(request: Request, actor_for, settings):
    """验证用户认证。返回 User 或 JSONResponse(401)。"""
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return authentication_required()
    try:
        return await actor_for(request)
    except InvalidSessionError:
        return authentication_required()


async def require_writer(request: Request, actor_for, settings, csrf_header: str | None = None):
    """验证用户认证 + CSRF token。返回 User 或 JSONResponse(401/403)。"""
    actor = await require_actor(request, actor_for, settings)
    if isinstance(actor, JSONResponse):
        return actor
    cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf_header or not cookie or cookie != csrf_header:
        return csrf_failed()
    return actor
