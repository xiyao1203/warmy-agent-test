from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.api.schemas import (
    ConfirmMissionRequest,
    UpsertMissionRequest,
)
from agenttest.modules.test_missions.application.commands import (
    ConfirmMissionHandler,
    MissionPreviewChangedError,
    PreviewMissionHandler,
    UpsertMissionHandler,
)
from agenttest.modules.test_missions.application.queries import GetMissionHandler
from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import MissionFact
from agenttest.shared.api.auth_guard import require_actor, require_writer


@dataclass(frozen=True, slots=True)
class MissionApiDependencies:
    upsert: UpsertMissionHandler
    preview: PreviewMissionHandler
    confirm: ConfirmMissionHandler
    get: GetMissionHandler


def create_test_mission_router(
    *, dependencies: MissionApiDependencies, actor_for, check_project, settings
) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/test-missions", tags=["test-missions"])

    async def authorize(request: Request, project_id: UUID, *, write: bool, csrf=None):
        actor = (
            await require_writer(request, actor_for, settings, csrf)
            if write
            else await require_actor(request, actor_for, settings)
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except Exception:
            return _error(404, "Project not found")
        return actor

    @router.post("", status_code=201)
    async def upsert_mission(
        request: Request,
        project_id: UUID,
        body: UpsertMissionRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize(request, project_id, write=True, csrf=x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            mission = await dependencies.upsert.execute(
                actor, ProjectId(project_id), session_id=body.session_id, values=body.facts
            )
        except ValueError as error:
            return _error(422, str(error))
        return _mission_response(mission)

    @router.get("/{mission_id}")
    async def get_mission(request: Request, project_id: UUID, mission_id: UUID):
        actor = await authorize(request, project_id, write=False)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            mission, preview = await dependencies.get.execute(actor, project_id, mission_id)
        except LookupError:
            return _error(404, "Mission not found")
        return {**_mission_response(mission), **_preview_response(preview.preview, None, None)}

    @router.post("/{mission_id}/preview")
    async def preview_mission(
        request: Request,
        project_id: UUID,
        mission_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize(request, project_id, write=True, csrf=x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            result = await dependencies.preview.execute(actor, project_id, mission_id)
        except LookupError:
            return _error(404, "Mission not found")
        return _preview_response(result.preview, result.revision_hash, result.snapshot)

    @router.post("/{mission_id}/confirm-start")
    async def confirm_mission(
        request: Request,
        project_id: UUID,
        mission_id: UUID,
        body: ConfirmMissionRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize(request, project_id, write=True, csrf=x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            result = await dependencies.confirm.execute(
                actor,
                project_id,
                mission_id,
                revision_hash=body.revision_hash,
                idempotency_key=body.idempotency_key,
            )
        except LookupError:
            return _error(404, "Mission not found")
        except MissionPreviewChangedError as error:
            return _error(409, str(error))
        except ValueError as error:
            return _error(422, str(error))
        return {
            **_mission_response(result.mission),
            "revision_id": str(result.revision.revision_id),
            "revision_hash": result.revision.content_hash,
            "workflow_id": result.workflow_id,
        }

    return router


def _mission_response(mission: TestMission) -> dict[str, object]:
    return {
        "mission_id": str(mission.mission_id),
        "project_id": str(mission.project_id),
        "session_id": str(mission.session_id),
        "status": mission.status.value,
        "active_revision_id": (
            str(mission.active_revision_id) if mission.active_revision_id else None
        ),
        "workflow_id": mission.workflow_id,
        "facts": {key: _fact_response(fact) for key, fact in sorted(mission.facts.items())},
        "updated_at": mission.updated_at.isoformat(),
    }


def _fact_response(fact: MissionFact) -> dict[str, object]:
    return {
        "value": None if fact.sensitive else fact.value,
        "source": fact.source.value,
        "confidence": fact.confidence,
        "verified": fact.verified,
        "sensitive": fact.sensitive,
    }


def _preview_response(preview, revision_hash, snapshot) -> dict[str, object]:
    return {
        "ready": preview.ready,
        "missing_inputs": [
            {"key": item.key, "reason": item.reason} for item in preview.missing_inputs
        ],
        "execution_channels": list(preview.execution_channels),
        "action_allowlist": list(preview.action_allowlist),
        "inferred_scenarios": list(preview.inferred_scenarios),
        "revision_hash": revision_hash,
        "snapshot": snapshot,
    }


def _error(status: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail})
