from collections.abc import Awaitable, Callable

import pytest
from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError
from agenttest.shared.api.auth_guard import require_actor
from fastapi import Request
from fastapi.responses import JSONResponse


def request_with_cookie(value: str | None = "session") -> Request:
    headers = [] if value is None else [(b"cookie", f"agenttest_session={value}".encode())]
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers})


@pytest.mark.asyncio
async def test_require_actor_returns_401_without_session_cookie() -> None:
    async def actor_for(_: Request) -> object:
        raise AssertionError("identity dependency must not be called")

    result = await require_actor(request_with_cookie(None), actor_for, Settings())

    assert isinstance(result, JSONResponse)
    assert result.status_code == 401


@pytest.mark.asyncio
async def test_require_actor_returns_401_for_invalid_session() -> None:
    async def actor_for(_: Request) -> object:
        raise InvalidSessionError

    result = await require_actor(request_with_cookie(), actor_for, Settings())

    assert isinstance(result, JSONResponse)
    assert result.status_code == 401


@pytest.mark.asyncio
async def test_require_actor_does_not_hide_infrastructure_failure_as_401() -> None:
    actor_for: Callable[[Request], Awaitable[object]]

    async def actor_for(_: Request) -> object:
        raise RuntimeError("identity database unavailable")

    with pytest.raises(RuntimeError, match="identity database unavailable"):
        await require_actor(request_with_cookie(), actor_for, Settings())
