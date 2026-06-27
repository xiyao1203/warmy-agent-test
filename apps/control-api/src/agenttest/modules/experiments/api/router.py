"""Experiment CRUD + 对比 API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from agenttest.modules.experiments.domain.entities import (
    Experiment,
    ExperimentId,
)
from agenttest.modules.experiments.infrastructure.persistence.repositories import (
    SqlAlchemyExperimentRepository,
)
from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError


class CreateExperimentRequest(BaseModel):
    name: str
    run_a_id: UUID
    run_b_id: UUID
    description: str | None = None


def create_experiment_router(
    *, session_factory, actor_for, check_project,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/experiments",
        tags=["experiments"],
    )

    @router.get("")
    async def list_experiments(
        request: Request, project_id: UUID, limit: int = 50, offset: int = 0,
    ):
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        async with session_factory() as session:
            repo = SqlAlchemyExperimentRepository(session)
            experiments = await repo.list_by_project(
                ProjectId(project_id), limit=limit, offset=offset,
            )
            return {"items": [_to_dict(e) for e in experiments]}

    @router.post("")
    async def create_experiment(
        request: Request, project_id: UUID, body: CreateExperimentRequest,
    ):
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
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
        async with session_factory() as session:
            repo = SqlAlchemyExperimentRepository(session)
            await repo.add(exp)
            await session.commit()
        return _to_dict(exp)

    @router.get("/{experiment_id}")
    async def get_experiment(
        request: Request, project_id: UUID, experiment_id: UUID,
    ):
        async with session_factory() as session:
            repo = SqlAlchemyExperimentRepository(session)
            exp = await repo.get_by_id_and_project(
                ExperimentId(experiment_id), ProjectId(project_id),
            )
            if exp is None:
                return JSONResponse(status_code=404, content={"detail": "实验不存在"})
            return _to_dict(exp)

    @router.post("/{experiment_id}/run")
    async def run_experiment(
        request: Request, project_id: UUID, experiment_id: UUID,
    ):
        """执行对比实验：逐用例对比 + 统计。"""
        async with session_factory() as session:
            repo = SqlAlchemyExperimentRepository(session)
            exp = await repo.get_by_id_and_project(
                ExperimentId(experiment_id), ProjectId(project_id),
            )
            if exp is None:
                return JSONResponse(status_code=404, content={"detail": "实验不存在"})

            # 获取两个运行的用例
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
                        # "passed" → "failed"/"error" = degraded
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
                    category = "no_change"
                    unchanged += 1
                else:
                    status_b = b.get("status")  # type: ignore[assignment]
                    category = "no_change"
                    unchanged += 1

                case_diffs.append({
                    "test_case_id": cid,
                    "status_a": status_a,
                    "status_b": status_b,
                    "status_changed": changed,
                    "duration_delta_ms": dur_delta,
                    "category": category,
                })

            # 统计
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

            result_json = {"case_diffs": case_diffs, "summary": summary}
            exp.complete(result_json)
            await repo.save(exp)
            await session.commit()

            return _to_dict(exp)

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
