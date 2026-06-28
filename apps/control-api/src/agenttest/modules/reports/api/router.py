"""报告 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

from agenttest.modules.reports.generators.json_report import JsonReportGenerator
from agenttest.modules.reports.generators.junit_report import JunitReportGenerator
from agenttest.modules.reports.generators.html_report import HtmlReportGenerator

router = APIRouter(prefix="/api/v1", tags=["reports"])

# 报告生成器映射
GENERATORS = {
    "json": JsonReportGenerator(),
    "junit": JunitReportGenerator(),
    "html": HtmlReportGenerator(),
}


@router.get("/projects/{project_id}/runs/{run_id}/reports/{format}")
async def generate_report(
    project_id: str,
    run_id: str,
    format: str,
) -> Response:
    """生成测试报告。

    Args:
        project_id: 项目 ID。
        run_id: 运行 ID。
        format: 报告格式（json|junit|html）。

    Returns:
        报告内容。

    Raises:
        HTTPException: 格式不支持或运行不存在。
    """
    if format not in GENERATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Use json, junit, or html.",
        )

    # TODO: 从数据库获取运行数据
    # 这里使用模拟数据，实际实现需要查询数据库
    run_data = {
        "run_id": run_id,
        "plan_id": "plan-456",
        "status": "completed",
        "started_at": "2026-06-29T10:00:00",
        "completed_at": "2026-06-29T10:05:00",
        "total_cases": 10,
        "passed_cases": 8,
        "failed_cases": 2,
        "cases": [
            {
                "case_id": "case-1",
                "status": "passed",
                "duration_ms": 1000,
                "scorer_results": [{"scorer": "accuracy", "score": 0.95}],
            },
            {
                "case_id": "case-2",
                "status": "failed",
                "duration_ms": 2000,
                "error": "AssertionError: expected 'A' but got 'B'",
                "scorer_results": [{"scorer": "accuracy", "score": 0.3}],
            },
        ],
    }

    generator = GENERATORS[format]
    content = generator.generate(run_data)

    # 根据格式返回对应的响应类型
    if format == "html":
        return HTMLResponse(content=content)
    elif format == "json":
        return JSONResponse(content=content)
    else:
        return Response(content=content, media_type="application/xml")
"""报告导出 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from agenttest.modules.reports.generators import ReportGenerator, RunReport


def create_report_router() -> APIRouter:
    """创建报告导出路由。"""
    router = APIRouter(prefix="/reports", tags=["reports"])
    generator = ReportGenerator()

    @router.get("/runs/{run_id}/export")
    async def export_run_report(
        run_id: str,
        format: str = Query(default="json", regex="^(json|junit|html)$"),
    ):
        """导出运行报告。

        Args:
            run_id: 运行 ID。
            format: 导出格式（json/junit/html）。

        Returns:
            对应格式的报告内容。
        """
        # TODO: 从数据库获取实际运行数据
        # 这里使用示例数据
        report = RunReport(
            run_id=run_id,
            project_id="demo-project",
            test_plan_name="示例测试计划",
            status="passed",
            total_cases=10,
            passed_cases=8,
            failed_cases=2,
            error_cases=0,
            duration_ms=5000,
            cases=[
                {"name": "登录测试", "status": "passed", "duration_ms": 200},
                {"name": "注册测试", "status": "failed", "duration_ms": 300, "error_message": "超时"},
            ],
        )

        if format == "json":
            content = generator.generate_json(report)
            return JSONResponse(content=content, media_type="application/json")
        elif format == "junit":
            content = generator.generate_junit_xml(report)
            return PlainTextResponse(content=content, media_type="application/xml")
        else:
            content = generator.generate_html(report)
            return HTMLResponse(content=content)

    return router
