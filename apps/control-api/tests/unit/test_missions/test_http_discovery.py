import asyncio
from uuid import uuid4

import httpx
import pytest
from agenttest.modules.test_missions.application.url_policy import TargetUrlPolicy
from agenttest.modules.test_missions.infrastructure.http_discovery import (
    HttpTargetDiscoveryProbe,
)


class Resolver:
    async def resolve(self, host: str) -> tuple[str, ...]:
        del host
        return ("93.184.216.34",)


class AccessCatalog:
    def __init__(self, *, browser_ready: bool = True) -> None:
        self.browser_ready = browser_ready

    async def browser_profile_ready(self, project_id, profile_id):
        del project_id, profile_id
        return self.browser_ready

    async def credential_ready(self, project_id, binding_id):
        del project_id, binding_id
        return True


@pytest.mark.asyncio
async def test_http_discovery_revalidates_redirect_and_detects_agent_surface() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "agent.example":
            return httpx.Response(302, headers={"location": "https://chat.example/app"})
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<main><textarea></textarea><button>Send</button></main>",
        )

    probe = HttpTargetDiscoveryProbe(
        access_catalog=AccessCatalog(),
        address_resolver=Resolver(),
        transport=httpx.MockTransport(respond),
    )
    result = await probe.probe(
        project_id=uuid4(),
        target={"url": "https://agent.example"},
        access={"strategy": "none"},
        read_only=True,
    )

    assert [request.url.host for request in requests] == ["agent.example", "chat.example"]
    assert result.browser_available is True
    assert result.login_valid is True
    assert "chat" in result.capabilities
    assert result.untrusted_content


@pytest.mark.asyncio
async def test_http_discovery_requires_ready_same_project_browser_profile() -> None:
    probe = HttpTargetDiscoveryProbe(
        access_catalog=AccessCatalog(browser_ready=False),
        address_resolver=Resolver(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, headers={"content-type": "text/html"}, text="login"
            )
        ),
    )

    result = await probe.probe(
        project_id=uuid4(),
        target={"url": "https://agent.example"},
        access={"strategy": "browser_profile", "browser_profile_id": str(uuid4())},
        read_only=True,
    )

    assert result.login_valid is False


@pytest.mark.asyncio
async def test_http_discovery_rejects_non_read_only_invocation() -> None:
    probe = HttpTargetDiscoveryProbe(
        access_catalog=AccessCatalog(),
        address_resolver=Resolver(),
        transport=httpx.MockTransport(lambda request: httpx.Response(200)),
    )

    with pytest.raises(ValueError, match="read-only"):
        await probe.probe(
            project_id=uuid4(),
            target={"url": "https://agent.example"},
            access={"strategy": "none"},
            read_only=False,
        )


@pytest.mark.asyncio
async def test_http_discovery_calls_a_real_fake_target_over_tcp() -> None:
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readuntil(b"\r\n\r\n")
        body = b"<html><textarea></textarea><button>Send</button></html>"
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: "
            + str(len(body)).encode()
            + b"\r\nConnection: close\r\n\r\n"
            + body
        )
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        result = await HttpTargetDiscoveryProbe(
            access_catalog=AccessCatalog(),
            url_policy=TargetUrlPolicy(allowed_local_hosts=frozenset({"127.0.0.1"})),
        ).probe(
            project_id=uuid4(),
            target={"url": f"http://127.0.0.1:{port}/agent"},
            access={"strategy": "none"},
            read_only=True,
        )
    finally:
        server.close()
        await server.wait_closed()

    assert result.capabilities == ("chat", "browser")
    assert result.login_valid is True
