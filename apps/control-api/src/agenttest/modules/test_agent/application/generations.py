from __future__ import annotations

from uuid import UUID

from agenttest.modules.model_configs.public import ModelInvoker
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.ports import (
    ChatGenerationRepository,
    OrchestrationRepository,
)
from agenttest.modules.test_agent.domain.entities import (
    ChatGeneration,
    ChatSessionId,
    GenerationStatus,
)


class GenerationCoordinator:
    def __init__(
        self,
        generations: ChatGenerationRepository,
        events: OrchestrationRepository,
        model_invoker: ModelInvoker,
    ) -> None:
        self._generations = generations
        self._events = events
        self._model_invoker = model_invoker

    async def begin(
        self,
        project_id: ProjectId,
        session_id: ChatSessionId,
        generation_id: UUID,
    ) -> ChatGeneration:
        existing = await self._generations.get(project_id, generation_id)
        if existing is not None:
            if existing.session_id != session_id.value:
                raise ValueError("Generation does not belong to session")
            return existing
        active = await self._generations.get_active(project_id, session_id)
        if active is not None:
            raise ValueError("A generation is already active for this session")
        generation = ChatGeneration.create(
            project_id=project_id.value,
            session_id=session_id.value,
            generation_id=generation_id,
        )
        await self._generations.add(generation)
        await self._event(generation, "generation.pending", {})
        return generation

    async def get_active(
        self, project_id: ProjectId, session_id: ChatSessionId
    ) -> ChatGeneration | None:
        return await self._generations.get_active(project_id, session_id)

    async def get(self, project_id: ProjectId, generation_id: UUID) -> ChatGeneration | None:
        return await self._generations.get(project_id, generation_id)

    async def start(self, generation: ChatGeneration) -> ChatGeneration:
        if generation.status is GenerationStatus.PENDING:
            generation.start(f"test-agent-chat-{generation.generation_id}")
            await self._generations.save(generation)
            await self._event(
                generation,
                "generation.started",
                {"workflow_id": generation.workflow_id or ""},
            )
        return generation

    async def complete(self, generation: ChatGeneration, content: str) -> ChatGeneration:
        generation.complete(content)
        await self._generations.save(generation)
        await self._event(generation, "generation.completed", {"content": content})
        return generation

    async def mark_cancelled(self, generation: ChatGeneration, content: str) -> ChatGeneration:
        generation.cancel(content)
        await self._generations.save(generation)
        await self._event(generation, "generation.cancelled", {"content": content})
        return generation

    async def fail(self, generation: ChatGeneration, detail: str) -> ChatGeneration:
        generation.fail()
        await self._generations.save(generation)
        await self._event(generation, "generation.failed", {"detail": detail})
        return generation

    async def cancel(
        self,
        project_id: ProjectId,
        session_id: ChatSessionId,
        generation_id: UUID,
    ) -> ChatGeneration:
        generation = await self._generations.get(project_id, generation_id)
        if generation is None or generation.session_id != session_id.value:
            raise ValueError("Generation does not exist in session")
        if generation.status in {
            GenerationStatus.COMPLETED,
            GenerationStatus.CANCELLED,
            GenerationStatus.FAILED,
            GenerationStatus.CANCELLING,
        }:
            return generation
        generation.request_cancel()
        await self._generations.save(generation)
        if generation.workflow_id:
            await self._model_invoker.cancel_workflow(generation.workflow_id)
        await self._event(generation, "generation.cancelling", {})
        return generation

    async def _event(
        self,
        generation: ChatGeneration,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        await self._events.append_event(
            ProjectId(generation.project_id),
            ChatSessionId(generation.session_id),
            event_type,
            {"generation_id": str(generation.generation_id), **payload},
            generation_id=generation.generation_id,
        )
