"""Trace 对比 API 端点。

GET /api/v1/projects/{project_id}/runs/{run_a_id}/diff/{run_b_id}
返回两个运行之间的逐用例执行时间差异、评分差异和状态差异。
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError


def create_trace_diff_router(
    *,
    session_factory,
    actor_for,
    check_project,
) -> APIRouter:
    """创建 Trace 对比 API 路由。"""
    router = APIRouter(
        prefix="/projects/{project_id}/runs/{run_a_id}/diff/{run_b_id}",
        tags=["trace-diff"],
    )

    @router.get("")
    async def diff_runs(
        request: Request,
        project_id: UUID,
        run_a_id: UUID,
        run_b_id: UUID,
    ):
        """对比两个运行的执行结果。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(
                status_code=404, content={"detail": "项目不存在"}
            )

        async with session_factory() as session:
            # 获取两个运行的基础信息
            run_a = await _get_run_summary(session, run_a_id)
            run_b = await _get_run_summary(session, run_b_id)

            if run_a is None:
                return JSONResponse(status_code=404, content={"detail": f"运行 {run_a_id} 不存在"})
            if run_b is None:
                return JSONResponse(status_code=404, content={"detail": f"运行 {run_b_id} 不存在"})

            # 获取两个运行的用例详情
            cases_a = await _get_run_cases_summary(session, run_a_id)
            cases_b = await _get_run_cases_summary(session, run_b_id)

            # 按 test_case_id 对齐
            case_map_a = {c["test_case_id"]: c for c in cases_a}
            case_map_b = {c["test_case_id"]: c for c in cases_b}
            all_case_ids = sorted(set(case_map_a.keys()) | set(case_map_b.keys()))

            case_diffs = []
            for cid in all_case_ids:
                a = case_map_a.get(cid)
                b = case_map_b.get(cid)
                diff: dict[str, object] = {"test_case_id": cid}
                if a and b:
                    a_dur = a.get("duration_ms") or 0
                    b_dur = b.get("duration_ms") or 0
                    diff["duration_delta_ms"] = b_dur - a_dur
                    diff["status_a"] = a.get("status")
                    diff["status_b"] = b.get("status")
                    diff["status_changed"] = a.get("status") != b.get("status")
                    diff["error_type_a"] = a.get("error_type")
                    diff["error_type_b"] = b.get("error_type")
                elif a and not b:
                    diff["status_a"] = a.get("status")
                    diff["status_b"] = None
                    diff["status_changed"] = True
                    diff["note"] = "仅存在于运行 A"
                else:
                    diff["status_a"] = None
                    diff["status_b"] = b.get("status")  # type: ignore[union-attr]
                    diff["status_changed"] = True
                    diff["note"] = "仅存在于运行 B"
                case_diffs.append(diff)

            return {
                "run_a": run_a,
                "run_b": run_b,
                "case_diffs": case_diffs,
                "summary": {
                    "total_cases": len(all_case_ids),
                    "status_changes": sum(1 for d in case_diffs if d.get("status_changed")),
                    "duration_delta_ms_total": sum(
                        d.get("duration_delta_ms", 0)  # type: ignore[arg-type]
                        for d in case_diffs
                        if isinstance(d.get("duration_delta_ms"), (int, float))
                    ),
                },
            }

    return router


async def _get_run_summary(session, run_id: UUID) -> dict[str, object] | None:
    result = await session.execute(
        text(
            "SELECT id, status, total_cases, passed_cases, failed_cases, "
            "error_cases, cancelled_cases, started_at, completed_at "
            "FROM runs WHERE id = :rid"
        ),
        {"rid": run_id},
    )
    row = result.mappings().first()
    if row is None:
        return None
    return {
        "id": str(row["id"]),
        "status": row["status"],
        "total_cases": row["total_cases"],
        "passed_cases": row["passed_cases"],
        "failed_cases": row["failed_cases"],
        "error_cases": row["error_cases"],
        "cancelled_cases": row["cancelled_cases"],
        "started_at": row["started_at"].isoformat() if row["started_at"] else None,
        "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
    }


async def _get_run_cases_summary(session, run_id: UUID) -> list[dict[str, object]]:
    result = await session.execute(
        text(
            "SELECT test_case_id, status, duration_ms, error_type "
            "FROM run_cases WHERE run_id = :rid"
        ),
        {"rid": run_id},
    )
    return [
        {
            "test_case_id": str(row["test_case_id"]),
            "status": row["status"],
            "duration_ms": row["duration_ms"],
            "error_type": row["error_type"],
        }
        for row in result.mappings().all()
    ]
