from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reports.application.export import ReportExportService
from agenttest.modules.reports.application.service import ReportService
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.value_objects import RunCaseStatus
from agenttest.modules.test_plans.public import TestPlanVersionId as PlanVersionId


class StubAccess:
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None:
        del actor, project_id


class StubRuns:
    def __init__(self, run: Run, cases: list[RunCase]) -> None:
        self.run = run
        self.cases = cases

    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None:
        if self.run.project_id == project_id and self.run.run_id == run_id:
            return self.run
        return None

    async def list_cases(
        self,
        project_id: ProjectId,
        run_id: RunId,
    ) -> list[RunCase]:
        if self.run.project_id == project_id and self.run.run_id == run_id:
            return self.cases
        return []


class StubRenderer:
    """记录结构化报告输入的格式渲染器。"""

    format = "json"
    media_type = "application/json"

    def __init__(self) -> None:
        self.report = None

    def generate(self, report):
        self.report = report
        return '{"rendered":true}'


def make_report_state() -> tuple[User, Run, list[RunCase]]:
    actor = User.create(
        user_id=UserId.new(),
        email=Email("developer@example.com"),
        display_name="Developer",
        role=SystemRole.DEVELOPER,
    )
    run = Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=PlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="report-real-data",
        created_by=actor.user_id,
        config_snapshot={"concurrency": 1},
        plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
        total_cases=1,
    )
    run.start("workflow-report")
    case = RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=uuid4(),
        name="real failed case",
        input_snapshot={"prompt": "real input"},
        assertion_snapshot=[],
    )
    case.start()
    case.fail(
        status=RunCaseStatus.FAILED,
        error_type="TimeoutError",
        error_message="real timeout",
        trace=[],
        duration_ms=125,
    )
    run.complete(passed_cases=0, failed_cases=1, error_cases=0)
    return actor, run, [case]


@pytest.mark.asyncio
async def test_build_report_uses_project_scoped_run_and_cases() -> None:
    actor, run, cases = make_report_state()
    service = ReportService(runs=StubRuns(run, cases), project_access=StubAccess())

    report = await service.build(actor, run.project_id, run.run_id)

    assert report["project_id"] == str(run.project_id.value)
    assert report["status"] == "failed"
    assert report["cases"] == [
        {
            "case_id": str(cases[0].run_case_id.value),
            "name": "real failed case",
            "status": "failed",
            "duration_ms": 125,
            "error_type": "TimeoutError",
            "error": "real timeout",
        }
    ]


@pytest.mark.asyncio
async def test_export_service_selects_allowlisted_renderer() -> None:
    actor, run, cases = make_report_state()
    renderer = StubRenderer()
    exporter = ReportExportService(
        reports=ReportService(runs=StubRuns(run, cases), project_access=StubAccess()),
        renderers=[renderer],
    )

    exported = await exporter.export(actor, run.project_id, run.run_id, "json")

    assert exported.content == '{"rendered":true}'
    assert exported.media_type == "application/json"
    assert renderer.report is not None
    assert renderer.report["project_id"] == str(run.project_id.value)
