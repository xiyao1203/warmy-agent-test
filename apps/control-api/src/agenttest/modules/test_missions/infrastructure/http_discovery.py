from __future__ import annotations

from typing import Protocol
from urllib.parse import urljoin, urlsplit
from uuid import UUID

import httpx

from agenttest.modules.test_accounts.public import TestAccountId
from agenttest.modules.test_missions.application.discovery import DiscoveryResult
from agenttest.modules.test_missions.application.url_policy import (
    HostAddressResolver,
    SystemHostAddressResolver,
    TargetUrlPolicy,
)


class MissionAccessCatalog(Protocol):
    async def browser_profile_ready(self, project_id: UUID, profile_id: UUID) -> bool: ...

    async def credential_ready(self, project_id: UUID, binding_id: UUID) -> bool: ...


class ProjectMissionAccessCatalog:
    """Validate access references without exposing credential or browser state material."""

    def __init__(self, browser_profiles, credentials) -> None:
        self._browser_profiles = browser_profiles
        self._credentials = credentials

    async def browser_profile_ready(self, project_id: UUID, profile_id: UUID) -> bool:
        profile = await self._browser_profiles.get(project_id, profile_id)
        return bool(
            profile
            and profile.auth_state_status == "ready"
            and profile.auth_state_envelope
            and profile.auth_state_sha256
        )

    async def credential_ready(self, project_id: UUID, binding_id: UUID) -> bool:
        credential = await self._credentials.get_by_id_and_project(
            TestAccountId(binding_id), project_id
        )
        return bool(credential and credential.enabled)


class HttpTargetDiscoveryProbe:
    """Bounded, read-only and SSRF-safe discovery of a target Agent surface."""

    def __init__(
        self,
        *,
        access_catalog: MissionAccessCatalog,
        url_policy: TargetUrlPolicy | None = None,
        address_resolver: HostAddressResolver | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        max_redirects: int = 5,
        max_body_bytes: int = 65_536,
    ) -> None:
        self._access = access_catalog
        self._url_policy = url_policy or TargetUrlPolicy()
        self._resolver = address_resolver or SystemHostAddressResolver()
        self._transport = transport
        self._max_redirects = max_redirects
        self._max_body_bytes = max_body_bytes

    async def probe(
        self,
        *,
        project_id: UUID,
        target: object,
        access: object,
        read_only: bool,
    ) -> DiscoveryResult:
        if not read_only:
            raise ValueError("Target discovery must be read-only")
        target_map = dict(target) if isinstance(target, dict) else {}
        access_map = dict(access) if isinstance(access, dict) else {}
        raw_url = target_map.get("url")
        if not isinstance(raw_url, str) or not raw_url:
            raise ValueError("Target discovery requires a URL")

        final_url, status, content_type, body = await self._fetch(raw_url)
        text = body.decode("utf-8", errors="replace")
        lowered = text.lower()
        is_json = "json" in content_type
        is_html = "html" in content_type or any(
            marker in lowered for marker in ("<html", "<main", "<textarea", "<form")
        )
        looks_like_chat = any(
            marker in lowered
            for marker in ("textarea", "contenteditable", "send", "chat", "message")
        )
        path = urlsplit(final_url).path.lower()
        api_available = is_json or "/api/" in path or "openapi" in lowered
        browser_available = is_html
        capabilities: list[str] = []
        if looks_like_chat:
            capabilities.append("chat")
        if api_available:
            capabilities.append("api")
        if browser_available:
            capabilities.append("browser")

        login_valid = await self._access_valid(project_id, access_map)
        if access_map.get("strategy") == "none":
            login_valid = login_valid and status not in {401, 403}
        scenarios = ["核心任务可达性"]
        if looks_like_chat:
            scenarios.extend(["单轮问答", "多轮上下文"])
        return DiscoveryResult(
            capabilities=tuple(dict.fromkeys(capabilities)),
            api_available=api_available,
            browser_available=browser_available,
            login_valid=login_valid,
            inferred_scenarios=tuple(scenarios),
            untrusted_content=text[:4000],
        )

    async def _fetch(self, raw_url: str) -> tuple[str, int, str, bytes]:
        current = raw_url
        async with httpx.AsyncClient(
            transport=self._transport,
            timeout=httpx.Timeout(15.0),
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "AgentTest-ReadOnly-Discovery/1.0"},
        ) as client:
            for redirect_count in range(self._max_redirects + 1):
                await self._validate_url(current)
                async with client.stream(
                    "GET", current, headers={"Accept": "text/html, application/json;q=0.9"}
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location or redirect_count >= self._max_redirects:
                            raise ValueError("Target discovery exceeded redirect limit")
                        current = urljoin(current, location)
                        continue
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        remaining = self._max_body_bytes - len(body)
                        if remaining <= 0:
                            break
                        body.extend(chunk[:remaining])
                    return (
                        str(response.url),
                        response.status_code,
                        response.headers.get("content-type", "").lower(),
                        bytes(body),
                    )
        raise ValueError("Target discovery failed")

    async def _validate_url(self, value: str) -> None:
        self._url_policy.validate(value)
        host = urlsplit(value).hostname
        if host is None:
            raise ValueError("Target discovery requires a host")
        addresses = await self._resolver.resolve(host)
        self._url_policy.validate(value, addresses)

    async def _access_valid(self, project_id: UUID, access: dict[str, object]) -> bool:
        strategy = str(access.get("strategy") or "")
        if strategy == "none":
            return True
        if strategy == "browser_profile" and access.get("browser_profile_id"):
            return await self._access.browser_profile_ready(
                project_id, UUID(str(access["browser_profile_id"]))
            )
        if strategy == "credential" and access.get("credential_binding_id"):
            return await self._access.credential_ready(
                project_id, UUID(str(access["credential_binding_id"]))
            )
        return False
