from __future__ import annotations

from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.modules.test_agent.application.registry import CapabilityRegistry


class ConfirmedMissionAssetExecutor:
    """Execute capabilities covered by an immutable Mission confirmation."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    async def execute(
        self,
        *,
        capability: str,
        child_agent: str,
        actor: User,
        project_id: ProjectId,
        session_id: UUID,
        arguments: dict[str, object],
        idempotency_key: str,
    ) -> dict[str, object]:
        del idempotency_key
        resolved, payload = self._registry.resolve(child_agent, capability, arguments)
        return await resolved.execute(OrchestrationContext(actor, project_id, session_id), payload)
