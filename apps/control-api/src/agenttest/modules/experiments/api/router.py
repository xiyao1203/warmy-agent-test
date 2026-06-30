"""Experiment CRUD + 对比 API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from agenttest.modules.experiments.domain.entities import (
    Experiment,
    ExperimentId,
)
from agenttest.modules.experiments.domain.statistics import (
    calculate_statistics,
    identify_degradation,
)
from agenttest.modules.experiments.infrastructure.persistence.repositories import (
    SqlAlchemyExperimentRepository,
)
from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor, require_writer


class CreateExperimentRequest(BaseModel):
    name: str
    run_a_id: UUID
    run_b_id: UUID
    description: str | None = None


def create_experiment_router(
    *, session_factory, actor_for, check_project, settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/experiments",
        tags=["experiments"],
    )

    repo = SqlAlchemyExperimentRepository(session_factory)

    @router.get("")
    async def list_experiments(
        request: Request, project_id: UUID, limit: int = 50, offset: int = 0,
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
        experiments = await repo.list_by_project(
            ProjectId(project_id), limit=limit, offset=offset,
        )
        return {"items": [_to_dict(e) for e in experiments]}

    @router.post("")
    async def create_experiment(
        request: Request,
        project_id: UUID,
        body: CreateExperimentRequest,
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

        # 校验 run_a_id 和 run_b_id 属于同一项目
        async with session_factory() as session:
            for run_id in [body.run_a_id, body.run_b_id]:
                result = await session.execute(
                    text("SELECT 1 FROM runs WHERE id = :rid AND project_id = :pid"),
                    {"rid": run_id, "pid": project_id},
                )
                if result.scalar() is None:
                    return JSONResponse(
                        status_code=422,
                        content={"detail": f"运行 {run_id} 不存在或不属于该项目"},
                    )

        try:
            exp = Experiment.create(
                experiment_id=ExperimentId.new(),
                project_id=ProjectId(project_id),
                name=body.name,
                run_a_id=body.run_a_id,
                run_b_id=body.run_b_id,
                description=body.description,
            )
        except ValueError as e:
            return JSONResponse(status_code=422, content={"detail": str(e)})
        await repo.add(exp)
        return _to_dict(exp)

    @router.get("/{experiment_id}")
    async def get_experiment(
        request: Request, project_id: UUID, experiment_id: UUID,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor

        exp = await repo.get_by_id_and_project(
            ExperimentId(experiment_id), ProjectId(project_id),
        )
        if exp is None:
            return JSONResponse(status_code=404, content={"detail": "实验不存在"})
        return _to_dict(exp)

    @router.post("/{experiment_id}/run")
    async def run_experiment(
        request: Request,
        project_id: UUID,
        experiment_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        """执行对比实验：逐用例对比 + 统计。"""
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor

        exp = await repo.get_by_id_and_project(
            ExperimentId(experiment_id), ProjectId(project_id),
        )
        if exp is None:
            return JSONResponse(status_code=404, content={"detail": "实验不存在"})

        # 幂等：已完成的实验直接返回现有结果
        if exp.status.value == "completed":
            return _to_dict(exp)

        async with session_factory() as session:
            # 校验 run 归属（双重校验）
            for run_id in [exp.run_a_id, exp.run_b_id]:
                result = await session.execute(
                    text("SELECT 1 FROM runs WHERE id = :rid AND project_id = :pid"),
                    {"rid": run_id, "pid": project_id},
                )
                if result.scalar() is None:
                    return JSONResponse(
                        status_code=422,
                        content={"detail": f"运行 {run_id} 不属于该项目"},
                    )

            cases_a = await _get_run_cases(session, exp.run_a_id)
            cases_b = await _get_run_cases(session, exp.run_b_id)

            map_a = {c["test_case_id"]: c for c in cases_a}
            map_b = {c["test_case_id"]: c for c in cases_b}
            all_ids = sorted(set(map_a) | set(map_b))

            case_diffs = []
            duration_deltas: list[int] = []
            improved = degraded = unchanged = 0

            for cid in all_ids:
                a = map_a.get(cid)
                b = map_b.get(cid)
                dur_delta = 0
                status_a = status_b = None
                changed = False
                category = "no_change"

                if a and b:
                    status_a = a.get("status")
                    status_b = b.get("status")
                    dur_a = a.get("duration_ms") or 0
                    dur_b = b.get("duration_ms") or 0
                    dur_delta = dur_b - dur_a
                    changed = status_a != status_b
                    if changed:
                        if status_a == "passed" and status_b != "passed":
                            category = "degraded"
                            degraded += 1
                        elif status_a != "passed" and status_b == "passed":
                            category = "improved"
                            improved += 1
                        else:
                            unchanged += 1
                    else:
                        unchanged += 1
                    duration_deltas.append(dur_delta)
                elif a and not b:
                    status_a = a.get("status")
                    unchanged += 1
                else:
                    if b is not None:
                        status_b = b.get("status")
                    unchanged += 1

                case_diffs.append({
                    "test_case_id": cid,
                    "status_a": status_a,
                    "status_b": status_b,
                    "status_changed": changed,
                    "duration_delta_ms": dur_delta,
                    "category": category,
                })

            import statistics

            avg_dur = statistics.mean(duration_deltas) if duration_deltas else 0.0
            sorted_durs = sorted(duration_deltas) if duration_deltas else [0]
            p50_idx = int(len(sorted_durs) * 0.5)
            p95_idx = int(len(sorted_durs) * 0.95)
            p50 = sorted_durs[min(p50_idx, len(sorted_durs) - 1)]
            p95 = sorted_durs[min(p95_idx, len(sorted_durs) - 1)]

            summary = {
                "total_cases": len(all_ids),
                "improved": improved,
                "degraded": degraded,
                "unchanged": unchanged,
                "avg_duration_delta_ms": round(avg_dur, 2),
                "p50_duration_delta_ms": float(p50),
                "p95_duration_delta_ms": float(p95),
            }

        result_json: dict[str, object] = {"case_diffs": case_diffs, "summary": summary}
        exp.complete(result_json)
        await repo.save(exp)
        return _to_dict(exp)

    @router.get("/statistics")
    async def get_statistics(
        request: Request,
        project_id: UUID,
        run_id: UUID | None = None,
        experiment_id: UUID | None = None,
    ):
        """获取运行统计或实验对比统计。"""
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        async with session_factory() as session:
            if run_id:
                # 获取单个运行的统计
                cases = await _get_run_cases(session, run_id)
                stats = calculate_statistics(cases)
                return {
                    "run_id": str(run_id),
                    "statistics": stats.to_dict(),
                }
            elif experiment_id:
                # 获取实验对比统计
                exp = await repo.get_by_id_and_project(
                    ExperimentId(experiment_id), ProjectId(project_id),
                )
                if exp is None:
                    return JSONResponse(status_code=404, content={"detail": "实验不存在"})

                cases_a = await _get_run_cases(session, exp.run_a_id)
                cases_b = await _get_run_cases(session, exp.run_b_id)

                stats_a = calculate_statistics(cases_a)
                stats_b = calculate_statistics(cases_b)
                degradations = identify_degradation(cases_a, cases_b)

                return {
                    "experiment_id": str(experiment_id),
                    "run_a": {"id": str(exp.run_a_id), "statistics": stats_a.to_dict()},
                    "run_b": {"id": str(exp.run_b_id), "statistics": stats_b.to_dict()},
                    "degradation": degradations,
                }
            else:
                return JSONResponse(
                    status_code=422,
                    content={"detail": "run_id 或 experiment_id 必须提供一个"},
                )

    return router


async def _get_run_cases(session, run_id: UUID) -> list[dict]:
    result = await session.execute(
        text(
            "SELECT test_case_id, status, duration_ms "
            "FROM run_cases WHERE run_id = :rid"
        ),
        {"rid": run_id},
    )
    return [
        {
            "test_case_id": str(row["test_case_id"]),
            "status": row["status"],
            "duration_ms": row["duration_ms"],
        }
        for row in result.mappings().all()
    ]


def _to_dict(e: Experiment) -> dict:
    return {
        "id": str(e.experiment_id.value),
        "project_id": str(e.project_id.value),
        "name": e.name,
        "run_a_id": str(e.run_a_id),
        "run_b_id": str(e.run_b_id),
        "status": e.status.value,
        "result_json": e.result_json,
        "description": e.description,
        "created_at": e.created_at.isoformat(),
        "updated_at": e.updated_at.isoformat(),
    }
