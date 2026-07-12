from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.agents.public import AgentConfig
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


class PublicationBrowserProfileRepository(Protocol):
    async def get(self, project_id: UUID, profile_id: UUID) -> BrowserProfile | None: ...


class BrowserProfilePublicationValidator:
    def __init__(self, repository: PublicationBrowserProfileRepository) -> None:
        self._repository = repository

    async def validate(self, project_id: UUID, config: AgentConfig) -> None:
        target_config = config.target_config
        login = target_config.get("login")
        login = dict(login) if isinstance(login, dict) else {}
        if str(login.get("strategy") or "") != "browser_profile":
            return
        raw_profile_id = target_config.get("browser_profile_id")
        if not raw_profile_id:
            raise ValueError("请选择浏览器实例后再发布")
        try:
            profile_id = UUID(str(raw_profile_id))
        except ValueError as error:
            raise ValueError("浏览器实例 ID 无效") from error
        profile = await self._repository.get(project_id, profile_id)
        if profile is None:
            raise ValueError("浏览器实例不存在或不属于当前项目")
        if profile.auth_state_status != "ready" or not profile.auth_state_envelope:
            raise ValueError("浏览器实例登录态未就绪，请先完成登录并验证")
