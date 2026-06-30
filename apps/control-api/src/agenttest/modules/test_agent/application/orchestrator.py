"""超级测试 Agent 的能力委派、确认与资产追溯。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.conversation import ActionIntent
from agenttest.modules.test_agent.application.ports import OrchestrationRepository
from agenttest.modules.test_agent.application.registry import CapabilityRegistry
from agenttest.modules.test_agent.domain.entities import (
    AgentConfirmation,
    AgentTask,
    ArtifactLink,
    ChatSessionId,
    ConfirmationStatus,
    RiskLevel,
)


@dataclass(frozen=True, slots=True)
class OrchestrationContext:
    actor: User
    project_id: ProjectId
    session_id: UUID


class SuperAgentOrchestrator:
    def __init__(
        self,
        registry: CapabilityRegistry,
        repository: OrchestrationRepository,
    ) -> None:
        self._registry = registry
        self._repository = repository

    async def delegate(
        self,
        context: OrchestrationContext,
        intent: ActionIntent,
        *,
        child_agent: str,
        idempotency_key: str,
    ) -> AgentTask:
        capability, payload = self._registry.resolve(
            child_agent, intent.capability, intent.arguments
        )
        task = AgentTask.create(
            project_id=context.project_id.value,
            session_id=context.session_id,
            child_agent=child_agent,
            capability=capability.name,
            risk_level=capability.risk,
            idempotency_key=idempotency_key,
            input=payload.model_dump(mode="json"),
        )
        await self._repository.add_task(task)
        if capability.risk is RiskLevel.READ:
            return await self._execute(context, task, capability, payload)

        confirmation = AgentConfirmation.create(
            project_id=context.project_id.value,
            task_id=task.task_id,
            preview={
                "capability": capability.name,
                "child_agent": child_agent,
                "arguments": payload.model_dump(mode="json"),
                "rationale": intent.rationale,
            },
        )
        await self._repository.add_confirmation(confirmation)
        await self._event(
            context,
            "tool.confirmation_required",
            {
                "task_id": str(task.task_id),
                "confirmation_id": str(confirmation.confirmation_id),
                "preview": confirmation.preview,
            },
        )
        return task

    async def decide_confirmation(
        self,
        context: OrchestrationContext,
        confirmation_id: UUID,
        *,
        approved: bool,
    ) -> AgentTask:
        confirmation = await self._repository.get_confirmation(
            context.project_id, confirmation_id
        )
        if confirmation is None:
            raise ValueError("Confirmation does not exist in project")
        if confirmation.status is not ConfirmationStatus.PENDING:
            raise ValueError("Confirmation already decided")
        task = await self._repository.get_task(context.project_id, confirmation.task_id)
        if task is None or task.session_id != context.session_id:
            raise ValueError("Task does not exist in session")
        if not approved:
            confirmation.reject(context.actor.user_id.value)
            await self._repository.save_confirmation(confirmation)
            task.reject()
            await self._repository.save_task(task)
            return task

        confirmation.approve(context.actor.user_id.value)
        await self._repository.save_confirmation(confirmation)
        task.approve()
        await self._repository.save_task(task)
        capability, payload = self._registry.resolve(
            task.child_agent, task.capability, task.input
        )
        return await self._execute(context, task, capability, payload)

    async def _execute(self, context, task, capability, payload) -> AgentTask:
        task.start()
        await self._repository.save_task(task)
        await self._event(
            context,
            "agent.progress",
            {"task_id": str(task.task_id), "capability": task.capability},
        )
        try:
            result = await capability.execute(context, payload)
            task.complete(result)
            await self._repository.save_task(task)
            for raw in result.get("artifacts", []):
                if not isinstance(raw, dict):
                    continue
                link = ArtifactLink(
                    link_id=uuid4(),
                    project_id=context.project_id.value,
                    session_id=context.session_id,
                    task_id=task.task_id,
                    artifact_type=str(raw["type"]),
                    artifact_id=UUID(str(raw["id"])),
                    relation=str(raw.get("relation", "created")),
                    created_at=task.updated_at,
                )
                await self._repository.add_artifact_link(link)
                await self._event(
                    context,
                    "asset.created",
                    {
                        "task_id": str(task.task_id),
                        "type": link.artifact_type,
                        "id": str(link.artifact_id),
                        "relation": link.relation,
                    },
                )
        except Exception as error:
            task.fail({"type": type(error).__name__, "message": str(error)})
            await self._repository.save_task(task)
            await self._event(
                context,
                "error",
                {"task_id": str(task.task_id), "detail": str(error)},
            )
            raise
        await self._event(
            context,
            "agent.completed",
            {"task_id": str(task.task_id), "output": task.output or {}},
        )
        return task

    async def _event(
        self,
        context: OrchestrationContext,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        await self._repository.append_event(
            context.project_id,
            ChatSessionId(context.session_id),
            event_type,
            payload,
        )
