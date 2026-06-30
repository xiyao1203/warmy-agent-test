"""发布门禁 CRUD + 评估 API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.modules.gates.domain.entities import (
    ReleaseGate,
    ReleaseGateId,
)
from agenttest.modules.gates.infrastructure.persistence.repositories import (
    SqlAlchemyReleaseGateRepository,
)
from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor, require_writer


class CreateGateRequest(BaseModel):
    name: str
    success_rate_threshold: float = 0.8
    critical_cases: list[str] = []
    cost_limit: float | None = None
    security_threshold: float = 0.8


class EvaluateGateRequest(BaseModel):
    actual_pass_rate: float
    critical_passed: bool
    actual_cost: float | None = None
    security_score: float | None = None


class ExemptRequest(BaseModel):
    reason: str


def create_gate_router(
    *,
    session_factory,
    actor_for,
    check_project,
    settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/gates",
        tags=["release-gates"],
    )

    repo = SqlAlchemyReleaseGateRepository(session_factory)

    @router.get("")
    async def list_gates(request: Request, project_id: UUID):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(
                status_code=404,
                content={"detail": "项目不存在"},
            )
        except InvalidSessionError:
            return JSONResponse(
                status_code=401,
                content={"detail": "认证失败"},
            )
        gates = await repo.list_by_project(project_id)
        return {"items": [_gate_to_dict(g) for g in gates]}

    @router.post("")
    async def create_gate(
        request: Request,
        project_id: UUID,
        body: CreateGateRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request,
            actor_for,
            settings,
            x_csrf_token,
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(
                status_code=404,
                content={"detail": "项目不存在"},
            )
        except InvalidSessionError:
            return JSONResponse(
                status_code=401,
                content={"detail": "认证失败"},
            )
        try:
            gate = ReleaseGate.create(
                project_id=project_id,
                name=body.name,
                success_rate_threshold=body.success_rate_threshold,
                critical_cases=body.critical_cases,
                cost_limit=body.cost_limit,
                security_threshold=body.security_threshold,
            )
        except ValueError as e:
            return JSONResponse(status_code=422, content={"detail": str(e)})
        await repo.add(gate)
        return _gate_to_dict(gate)

    @router.get("/{gate_id}")
    async def get_gate(
        request: Request,
        project_id: UUID,
        gate_id: UUID,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        gate = await repo.get_by_id_and_project(
            ReleaseGateId(gate_id),
            project_id,
        )
        if gate is None:
            return JSONResponse(
                status_code=404,
                content={"detail": "门禁不存在"},
            )
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
            request,
            actor_for,
            settings,
            x_csrf_token,
        )
        if isinstance(actor, JSONResponse):
            return actor
        gate = await repo.get_by_id_and_project(
            ReleaseGateId(gate_id),
            project_id,
        )
        if gate is None:
            return JSONResponse(
                status_code=404,
                content={"detail": "门禁不存在"},
            )
        if not gate.enabled:
            return {
                "gate_id": str(gate_id),
                "result": {"passed": True, "failures": [], "disabled": True},
            }
        result = gate.evaluate(
            actual_pass_rate=body.actual_pass_rate,
            critical_passed=body.critical_passed,
            actual_cost=body.actual_cost,
            security_score=body.security_score,
        )
        return {"gate_id": str(gate_id), "result": result.to_dict()}

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
            request,
            actor_for,
            settings,
            x_csrf_token,
        )
        if isinstance(actor, JSONResponse):
            return actor
        gate = await repo.get_by_id_and_project(
            ReleaseGateId(gate_id),
            project_id,
        )
        if gate is None:
            return JSONResponse(
                status_code=404,
                content={"detail": "门禁不存在"},
            )
        gate.toggle()
        await repo.save(gate)
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
            request,
            actor_for,
            settings,
            x_csrf_token,
        )
        if isinstance(actor, JSONResponse):
            return actor
        gate = await repo.get_by_id_and_project(
            ReleaseGateId(gate_id),
            project_id,
        )
        if gate is None:
            return JSONResponse(
                status_code=404,
                content={"detail": "门禁不存在"},
            )
        await repo.delete(ReleaseGateId(gate_id))
        return {"status": "deleted", "gate_id": str(gate_id)}

    return router


def _gate_to_dict(g: ReleaseGate) -> dict[str, object]:
    return {
        "id": str(g.gate_id.value),
        "project_id": str(g.project_id),
        "name": g.name,
        "success_rate_threshold": g.success_rate_threshold,
        "critical_cases": g.critical_cases,
        "cost_limit": g.cost_limit,
        "security_threshold": g.security_threshold,
        "enabled": g.enabled,
        "created_at": g.created_at.isoformat(),
        "updated_at": g.updated_at.isoformat(),
    }
