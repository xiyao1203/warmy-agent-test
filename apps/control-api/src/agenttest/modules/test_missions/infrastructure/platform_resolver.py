from __future__ import annotations

from typing import Protocol
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from agenttest.modules.agents.public import AgentVersion, VersionStatus
from agenttest.modules.test_missions.application.resolution import ResolvedTarget


class PublishedAgentVersionSource(Protocol):
    async def list_published(self, project_id: UUID) -> list[AgentVersion]: ...


class PublishedAgentMissionCatalog:
    """Match a target URL against project-scoped published Agent versions."""

    def __init__(self, versions: PublishedAgentVersionSource) -> None:
        self._versions = versions

    async def find_target(self, project_id: UUID, target_url: str) -> ResolvedTarget | None:
        expected = _normalized_url(target_url)
        for version in await self._versions.list_published(project_id):
            if version.status is not VersionStatus.PUBLISHED:
                continue
            candidates = [version.config.api_url, version.config.web_url]
            target_config = version.config.target_config
            candidates.extend(
                str(target_config[key])
                for key in ("target_url", "web_url", "api_url")
                if target_config.get(key)
            )
            if expected not in {_normalized_url(value) for value in candidates if value}:
                continue
            return ResolvedTarget(
                agent_version_id=version.version_id.value,
                target_url=target_url,
                api_available=bool(version.config.api_url),
            )
        return None


def _normalized_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.query,
            "",
        )
    )
