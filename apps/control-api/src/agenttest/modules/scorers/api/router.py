"""Scorer CRUD API 路由。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, select

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.scorers.application.evaluate import evaluate_deterministic
from agenttest.modules.scorers.application.model_judge import ModelJudge
from agenttest.modules.scorers.domain.config import ModelScorerConfig, parse_scorer_config
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId
from agenttest.modules.scorers.domain.value_objects import ScorerType
from agenttest.modules.scorers.infrastructure.persistence.models import ScorerVersionModel
from agenttest.modules.scorers.infrastructure.persistence.repositories import (
    SqlAlchemyScorerRepository,
)
from agenttest.shared.api.auth_guard import require_actor, require_writer


class CreateScorerRequest(BaseModel):
    name: str
    scorer_type: str
    weight: float = 1.0
    threshold: float = 0.8
    config_json: dict[str, object] = Field(default_factory=dict)
    description: str | None = None


class UpdateScorerRequest(BaseModel):
    name: str | None = None
    weight: float | None = None
    threshold: float | None = None
    config_json: dict[str, object] | None = None
    description: str | None = None
    enabled: bool | None = None


class TrialScorerRequest(BaseModel):
    output: object
    input: object | None = None
    reference: object | None = None


def create_scorer_router(
    *,
    session_factory,
    actor_for,
    check_project,
    settings,
    model_judge: ModelJudge | None = None,
    repo: SqlAlchemyScorerRepository | None = None,
) -> APIRouter:
    """创建评分器 CRUD 路由。"""
    router = APIRouter(
        prefix="/projects/{project_id}/scorers",
        tags=["scorers"],
    )

    versioning_enabled = repo is None
    if repo is None:
        repo = SqlAlchemyScorerRepository(session_factory)

    @router.get("")
    async def list_scorers(
        request: Request,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        scorers, total = await repo.list_by_project(
            ProjectId(project_id),
            limit=limit,
            offset=offset,
        )
        published_versions = (
            await _latest_published_versions(
                session_factory,
                ProjectId(project_id),
                [s.scorer_id.value for s in scorers],
            )
            if versioning_enabled
            else {}
        )
        return {
            "items": [
                _scorer_to_dict(s, published_version=published_versions.get(s.scorer_id.value))
                for s in scorers
            ],
            "total": total,
        }

    @router.post("")
    async def create_scorer(
        request: Request,
        project_id: UUID,
        body: CreateScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        try:
            scorer_type = ScorerType(body.scorer_type)
        except ValueError:
            return JSONResponse(
                status_code=422,
                content={"detail": f"无效的评分器类型: {body.scorer_type}"},
            )
        try:
            validated_config = parse_scorer_config(scorer_type.value, body.config_json)
        except (ValueError, ValidationError) as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})

        try:
            scorer = Scorer.create(
                scorer_id=ScorerId.new(),
                project_id=ProjectId(project_id),
                name=body.name,
                scorer_type=scorer_type,
                weight=body.weight,
                threshold=body.threshold,
                config_json=validated_config.model_dump(mode="json", exclude={"type"}),
                description=body.description,
            )
        except ValueError as e:
            return JSONResponse(status_code=422, content={"detail": str(e)})

        await repo.add(scorer)
        published_version = None
        if versioning_enabled:
            published_version = await _publish_scorer_version(
                session_factory,
                scorer,
                actor.user_id.value,
            )
        return _scorer_to_dict(scorer, published_version=published_version)

    @router.get("/{scorer_id}")
    async def get_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor

        scorer = await repo.get_by_id_and_project(
            ScorerId(scorer_id),
            ProjectId(project_id),
        )
        if scorer is None:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        return _scorer_to_dict(scorer)

    @router.patch("/{scorer_id}")
    async def update_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        body: UpdateScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor

        scorer = await repo.get_by_id_and_project(
            ScorerId(scorer_id),
            ProjectId(project_id),
        )
        if scorer is None:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})

        if body.name is not None:
            try:
                scorer.rename(body.name)
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
        if body.weight is not None:
            try:
                scorer.update_weight(body.weight)
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
        if body.threshold is not None:
            try:
                scorer.update_threshold(body.threshold)
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
        if body.config_json is not None:
            try:
                validated_config = parse_scorer_config(scorer.scorer_type.value, body.config_json)
            except (ValueError, ValidationError) as error:
                return JSONResponse(status_code=422, content={"detail": str(error)})
            scorer.config_json = validated_config.model_dump(mode="json", exclude={"type"})
            scorer.updated_at = datetime.now(UTC)
        if body.description is not None:
            scorer.description = body.description
            scorer.updated_at = datetime.now(UTC)
        if body.enabled is not None and body.enabled != scorer.enabled:
            scorer.toggle()

        await repo.save(scorer)
        published_version = None
        if versioning_enabled:
            published_version = await _publish_scorer_version(
                session_factory,
                scorer,
                actor.user_id.value,
            )
        return _scorer_to_dict(scorer, published_version=published_version)

    @router.delete("/{scorer_id}")
    async def delete_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor

        scorer = await repo.get_by_id_and_project(
            ScorerId(scorer_id),
            ProjectId(project_id),
        )
        if scorer is None:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        await repo.delete(ScorerId(scorer_id))
        return {"status": "deleted", "scorer_id": str(scorer_id)}

    @router.post("/{scorer_id}/trial")
    async def trial_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        body: TrialScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        scorer = await repo.get_by_id_and_project(ScorerId(scorer_id), ProjectId(project_id))
        if scorer is None:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        try:
            config = parse_scorer_config(scorer.scorer_type.value, scorer.config_json)
            if isinstance(config, ModelScorerConfig):
                if model_judge is None:
                    return JSONResponse(status_code=503, content={"detail": "模型评分运行时不可用"})
                judged = await model_judge.judge_text(
                    actor,
                    ProjectId(project_id),
                    input_text=json.dumps(body.input, ensure_ascii=False),
                    output_text=json.dumps(body.output, ensure_ascii=False),
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
            result = evaluate_deterministic(
                config,
                output=body.output,
                reference=body.reference,
            )
            return {
                "score": result.score,
                "passed": result.passed,
                "explanation": result.explanation,
                "confidence": result.confidence,
            }
        except (ValueError, ValidationError) as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})

    return router


async def _publish_scorer_version(
    session_factory,
    scorer: Scorer,
    created_by: UUID,
) -> tuple[UUID, int]:
    now = datetime.now(UTC)
    async with session_factory() as session:
        async with session.begin():
            latest_version = await session.scalar(
                select(func.max(ScorerVersionModel.version_number)).where(
                    ScorerVersionModel.scorer_id == scorer.scorer_id.value,
                    ScorerVersionModel.project_id == scorer.project_id.value,
                )
            )
            version_number = int(latest_version or 0) + 1
            version_id = uuid4()
            session.add(
                ScorerVersionModel(
                    id=version_id,
                    project_id=scorer.project_id.value,
                    scorer_id=scorer.scorer_id.value,
                    version_number=version_number,
                    status="published",
                    config=dict(scorer.config_json),
                    published_at=now,
                    created_by=created_by,
                    created_at=now,
                    updated_at=now,
                )
            )
    return version_id, version_number


async def _latest_published_versions(
    session_factory,
    project_id: ProjectId,
    scorer_ids: list[UUID],
) -> dict[UUID, tuple[UUID, int]]:
    if not scorer_ids:
        return {}
    async with session_factory() as session:
        rows = (
            await session.execute(
                select(
                    ScorerVersionModel.scorer_id,
                    ScorerVersionModel.id,
                    ScorerVersionModel.version_number,
                )
                .where(
                    ScorerVersionModel.project_id == project_id.value,
                    ScorerVersionModel.scorer_id.in_(scorer_ids),
                    ScorerVersionModel.status == "published",
                )
                .order_by(
                    ScorerVersionModel.scorer_id,
                    ScorerVersionModel.version_number.desc(),
                )
            )
        ).all()
    result: dict[UUID, tuple[UUID, int]] = {}
    for scorer_id, version_id, version_number in rows:
        result.setdefault(scorer_id, (version_id, int(version_number)))
    return result


def _scorer_to_dict(
    s: Scorer,
    *,
    published_version: tuple[UUID, int] | None = None,
) -> dict[str, object]:
    version_id, version_number = published_version or (None, None)
    return {
        "id": str(s.scorer_id.value),
        "project_id": str(s.project_id.value),
        "name": s.name,
        "scorer_type": s.scorer_type.value,
        "weight": s.weight,
        "threshold": s.threshold,
        "config_json": s.config_json,
        "description": s.description,
        "enabled": s.enabled,
        "latest_published_version_id": str(version_id) if version_id else None,
        "latest_published_version_number": version_number,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }
