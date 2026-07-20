"""Release-gate HTTP adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.bootstrap.settings import Settings
from agenttest.modules.gates.application.service import (
    GateEvidenceNotFound,
    GateNotFound,
    GateService,
    GateValidationError,
)
from agenttest.modules.gates.domain.entities import ReleaseGate
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor, require_writer
from agenttest.shared.api.pagination import resolve_page_request
from agenttest.shared.application.core_summaries import CoreSummaryReader, GateSummaryMetrics
from agenttest.shared.application.pagination import paginate_items


class CreateGateRequest(BaseModel):
    name: str
    success_rate_threshold: float = 0.8
    critical_cases: list[str] = []
    cost_limit: float | None = None
    security_threshold: float = 0.8


class EvaluateGateRequest(BaseModel):
    run_id: UUID
    experiment_id: UUID | None = None


class ExemptRequest(BaseModel):
    reason: str


class GateSummaryResponse(GateSummaryMetrics):
    id: UUID
    project_id: UUID
    name: str
    success_rate_threshold: float
    critical_cases: list[str]
    cost_limit: float | None
    security_threshold: float
    enabled: bool
    created_at: datetime
    updated_at: datetime


class GateListResponse(BaseModel):
    items: list[GateSummaryResponse]
    total: int
    page: int | None = None
    page_size: int = 50
    total_pages: int = 0


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class GateApiDependencies:
    service: GateService
    actor_for: ActorResolver
    settings: Settings
    summaries: CoreSummaryReader | None = None


def create_gate_router(dependencies: GateApiDependencies) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/gates", tags=["release-gates"])

    @router.get("", response_model=GateListResponse)
    async def list_gates(
        request: Request,
        project_id: UUID,
        page: int | None = Query(default=None),
        page_size: int | None = Query(default=None),
    ):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            gates = await dependencies.service.list_gates(actor, project_id)
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        page_request = resolve_page_request(page=page, page_size=page_size)
        if page_request:
            result = paginate_items(gates, page_request)
            gates = result.items
            total = result.total
            response_page = result.page
            response_page_size = result.page_size
            total_pages = result.total_pages
        else:
            total = len(gates)
            response_page = None
            response_page_size = 50
            total_pages = 1 if gates else 0
        summaries = (
            await dependencies.summaries.gates(
                project_id,
                [gate.gate_id.value for gate in gates],
            )
            if dependencies.summaries
            else {}
        )
        return {
            "items": [
                {**_gate_to_dict(gate), **summaries[gate.gate_id.value].model_dump()}
                if gate.gate_id.value in summaries
                else _gate_to_dict(gate)
                for gate in gates
            ],
            "total": total,
            "page": response_page,
            "page_size": response_page_size,
            "total_pages": total_pages,
        }

    @router.post("")
    async def create_gate(
        request: Request,
        project_id: UUID,
        body: CreateGateRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            gate = await dependencies.service.create(
                actor,
                project_id,
                name=body.name,
                success_rate_threshold=body.success_rate_threshold,
                critical_cases=body.critical_cases,
                cost_limit=body.cost_limit,
                security_threshold=body.security_threshold,
            )
        except GateValidationError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _gate_to_dict(gate)

    @router.get("/{gate_id}")
    async def get_gate(request: Request, project_id: UUID, gate_id: UUID):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            gate = await dependencies.service.get(actor, project_id, gate_id)
        except GateNotFound:
            return JSONResponse(status_code=404, content={"detail": "门禁不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _gate_to_dict(gate)

    @router.post("/{gate_id}/evaluate")
    async def evaluate_gate(
        request: Request,
        project_id: UUID,
        gate_id: UUID,
        body: EvaluateGateRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """评估门禁是否通过。"""
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            evaluated = await dependencies.service.evaluate(
                actor,
                project_id,
                gate_id,
                run_id=body.run_id,
                experiment_id=body.experiment_id,
            )
        except GateNotFound:
            return JSONResponse(status_code=404, content={"detail": "门禁不存在"})
        except GateEvidenceNotFound:
            return JSONResponse(status_code=404, content={"detail": "执行记录不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        evidence = evaluated.evidence
        return {
            "gate_id": str(gate_id),
            "decision_id": str(evaluated.decision_id),
            "run_id": str(body.run_id),
            "result": evaluated.result.to_dict(),
            "facts": {
                "pass_rate": evidence.pass_rate,
                "critical_passed": evidence.critical_passed,
                "total_cost": evidence.total_cost,
                "security_score": evidence.security_score,
                "pending_reviews": evidence.pending_reviews,
            },
        }

    @router.post("/{gate_id}/exempt")
    async def exempt_gate(
        request: Request,
        project_id: UUID,
        gate_id: UUID,
        body: ExemptRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """临时豁免门禁（记录审计日志）。"""
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.service.exempt(actor, project_id, gate_id)
        except GateNotFound:
            return JSONResponse(status_code=404, content={"detail": "门禁不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return {
            "gate_id": str(gate_id),
            "exempted": True,
            "reason": body.reason,
            "exempted_by": str(actor.user_id.value),
        }

    @router.delete("/{gate_id}")
    async def delete_gate(
        request: Request,
        project_id: UUID,
        gate_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.service.delete(actor, project_id, gate_id)
        except GateNotFound:
            return JSONResponse(status_code=404, content={"detail": "门禁不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return {"status": "deleted", "gate_id": str(gate_id)}

    return router


def _access_error(error: Exception) -> JSONResponse | None:
    if isinstance(error, InvalidSessionError):
        return JSONResponse(status_code=401, content={"detail": "认证失败"})
    if isinstance(error, PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    if isinstance(error, ProjectNotFoundError):
        return JSONResponse(status_code=404, content={"detail": "项目不存在"})
    return None


def _gate_to_dict(gate: ReleaseGate) -> dict[str, object]:
    return {
        "id": str(gate.gate_id.value),
        "project_id": str(gate.project_id),
        "name": gate.name,
        "success_rate_threshold": gate.success_rate_threshold,
        "critical_cases": gate.critical_cases,
        "cost_limit": gate.cost_limit,
        "security_threshold": gate.security_threshold,
        "enabled": gate.enabled,
        "created_at": gate.created_at.isoformat(),
        "updated_at": gate.updated_at.isoformat(),
    }
