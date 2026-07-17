from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from pydantic import ValidationError

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.scorers.application.evaluate import evaluate_deterministic
from agenttest.modules.scorers.application.model_judge import ModelJudge
from agenttest.modules.scorers.domain.config import ModelScorerConfig, parse_scorer_config
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId
from agenttest.modules.scorers.domain.value_objects import ScorerType

PublishedVersion = tuple[UUID, int]


class ScorerRepository(Protocol):
    async def get_by_id_and_project(
        self, scorer_id: ScorerId, project_id: ProjectId
    ) -> Scorer | None: ...

    async def list_by_project(
        self, project_id: ProjectId, *, limit: int, offset: int
    ) -> tuple[list[Scorer], int]: ...

    async def add(self, scorer: Scorer) -> None: ...

    async def save(self, scorer: Scorer) -> None: ...

    async def delete(self, scorer_id: ScorerId) -> None: ...

    async def publish_version(self, scorer: Scorer, created_by: UUID) -> PublishedVersion: ...

    async def latest_published_versions(
        self, project_id: ProjectId, scorer_ids: list[UUID]
    ) -> dict[UUID, PublishedVersion]: ...


class ProjectAccessPort(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class ScorerNotFound(Exception):
    pass


class ScorerValidationError(Exception):
    pass


class ScorerRuntimeUnavailable(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ScorerItem:
    scorer: Scorer
    published_version: PublishedVersion | None = None


@dataclass(frozen=True, slots=True)
class ScorerPage:
    items: list[ScorerItem]
    total: int


class ScorerService:
    def __init__(
        self,
        *,
        scorers: ScorerRepository,
        project_access: ProjectAccessPort,
        model_judge: ModelJudge | None = None,
        publish_versions: bool = True,
    ) -> None:
        self._scorers = scorers
        self._project_access = project_access
        self._model_judge = model_judge
        self._publish_versions = publish_versions

    async def list(self, actor: User, project_id: UUID, *, limit: int, offset: int) -> ScorerPage:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        scorers, total = await self._scorers.list_by_project(project, limit=limit, offset=offset)
        versions = (
            await self._scorers.latest_published_versions(
                project, [item.scorer_id.value for item in scorers]
            )
            if self._publish_versions
            else {}
        )
        return ScorerPage(
            [ScorerItem(item, versions.get(item.scorer_id.value)) for item in scorers],
            total,
        )

    async def create(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str,
        scorer_type: str,
        weight: float,
        threshold: float,
        config_json: dict[str, object],
        description: str | None,
    ) -> ScorerItem:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        try:
            kind = ScorerType(scorer_type)
            config = parse_scorer_config(kind.value, config_json)
            scorer = Scorer.create(
                scorer_id=ScorerId.new(),
                project_id=project,
                name=name,
                scorer_type=kind,
                weight=weight,
                threshold=threshold,
                config_json=config.model_dump(mode="json", exclude={"type"}),
                description=description,
            )
        except (ValueError, ValidationError) as error:
            raise ScorerValidationError(str(error)) from error
        await self._scorers.add(scorer)
        version = await self._publish(scorer, actor)
        return ScorerItem(scorer, version)

    async def get(self, actor: User, project_id: UUID, scorer_id: UUID) -> Scorer:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        return await self._scorer(project, scorer_id)

    async def update(
        self,
        actor: User,
        project_id: UUID,
        scorer_id: UUID,
        *,
        name: str | None,
        weight: float | None,
        threshold: float | None,
        config_json: dict[str, object] | None,
        description: str | None,
        enabled: bool | None,
    ) -> ScorerItem:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        scorer = await self._scorer(project, scorer_id)
        try:
            if name is not None:
                scorer.rename(name)
            if weight is not None:
                scorer.update_weight(weight)
            if threshold is not None:
                scorer.update_threshold(threshold)
            if config_json is not None:
                config = parse_scorer_config(scorer.scorer_type.value, config_json)
                scorer.config_json = config.model_dump(mode="json", exclude={"type"})
                scorer.updated_at = datetime.now(UTC)
        except (ValueError, ValidationError) as error:
            raise ScorerValidationError(str(error)) from error
        if description is not None:
            scorer.description = description
            scorer.updated_at = datetime.now(UTC)
        if enabled is not None and enabled != scorer.enabled:
            scorer.toggle()
        await self._scorers.save(scorer)
        return ScorerItem(scorer, await self._publish(scorer, actor))

    async def delete(self, actor: User, project_id: UUID, scorer_id: UUID) -> None:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        await self._scorer(project, scorer_id)
        await self._scorers.delete(ScorerId(scorer_id))

    async def trial(
        self,
        actor: User,
        project_id: UUID,
        scorer_id: UUID,
        *,
        output: object,
        input_value: object | None,
        reference: object | None,
    ) -> dict[str, object]:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        scorer = await self._scorer(project, scorer_id)
        try:
            config = parse_scorer_config(scorer.scorer_type.value, scorer.config_json)
            if isinstance(config, ModelScorerConfig):
                if self._model_judge is None:
                    raise ScorerRuntimeUnavailable
                judged = await self._model_judge.judge_text(
                    actor,
                    project,
                    input_text=json.dumps(input_value, ensure_ascii=False),
                    output_text=json.dumps(output, ensure_ascii=False),
                    rubric=config.rubric,
                )
                return {
                    "score": judged.score,
                    "passed": judged.passed,
                    "explanation": judged.explanation,
                    "confidence": judged.confidence,
                    "model_config_id": judged.model_config_id,
                    "model_name": judged.model_name,
                }
            result = evaluate_deterministic(config, output=output, reference=reference)
            return {
                "score": result.score,
                "passed": result.passed,
                "explanation": result.explanation,
                "confidence": result.confidence,
            }
        except (ValueError, ValidationError) as error:
            raise ScorerValidationError(str(error)) from error

    async def _scorer(self, project_id: ProjectId, scorer_id: UUID) -> Scorer:
        scorer = await self._scorers.get_by_id_and_project(ScorerId(scorer_id), project_id)
        if scorer is None:
            raise ScorerNotFound
        return scorer

    async def _publish(self, scorer: Scorer, actor: User) -> PublishedVersion | None:
        if not self._publish_versions:
            return None
        return await self._scorers.publish_version(scorer, actor.user_id.value)
