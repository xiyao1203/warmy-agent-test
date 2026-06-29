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
                {
                    "name": "注册测试",
                    "status": "failed",
                    "duration_ms": 300,
                    "error_message": "超时",
                },
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
