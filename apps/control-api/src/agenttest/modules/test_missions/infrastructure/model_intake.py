from __future__ import annotations

import json
from typing import Protocol

from agenttest.modules.identity.public import User
from agenttest.modules.model_configs.public import (
    InvocationMessage,
    ModelConfiguration,
    ModelInvoker,
    ModelPurpose,
)
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.intake import FactProposal


class MissionModelResolver(Protocol):
    async def resolve_default(
        self, actor: User, project_id: ProjectId, purpose: ModelPurpose
    ) -> ModelConfiguration: ...


class ModelMissionIntakeExtractor:
    def __init__(self, models: MissionModelResolver, invoker: ModelInvoker) -> None:
        self._models = models
        self._invoker = invoker

    async def extract(
        self,
        actor: User,
        project_id: ProjectId,
        history: list[tuple[str, str]],
    ) -> FactProposal:
        config = await self._models.resolve_default(actor, project_id, ModelPurpose.TEST_AGENT_CHAT)
        prompt = (
            "Extract only explicit Agent test mission facts as JSON. Allowed fields: "
            "target_url, agent_version_id, browser_profile_id, access_strategy, "
            "credential_binding_id, test_goal, safety_scope, scenario_hints, inferred_fields. "
            "Never return passwords, tokens, cookies, credentials, project IDs or actions."
        )
        result = await self._invoker.invoke(
            config,
            [InvocationMessage(role="system", content=prompt)]
            + [InvocationMessage(role=role, content=content) for role, content in history],
            response_format={"type": "json_object"},
            timeout_seconds=60,
            max_tokens=1200,
        )
        return FactProposal.model_validate(json.loads(result.content))
