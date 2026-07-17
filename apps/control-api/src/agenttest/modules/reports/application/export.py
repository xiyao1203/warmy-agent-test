"""报告导出 Application 服务。"""

from __future__ import annotations

from dataclasses import dataclass

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reports.application.contracts import ReportRenderer
from agenttest.modules.reports.application.service import ReportService
from agenttest.modules.runs.public import RunId


@dataclass(frozen=True, slots=True)
class ExportedReport:
    """API 返回所需的报告正文与媒体类型。"""

    content: str
    media_type: str


class ReportExportService:
    """读取结构化报告并选择受控 Renderer。"""

    def __init__(
        self,
        *,
        reports: ReportService,
        renderers: list[ReportRenderer],
    ) -> None:
        self._reports = reports
        self._renderers: dict[str, ReportRenderer] = {
            renderer.format: renderer for renderer in renderers
        }

    async def export(
        self,
        actor: User,
        project_id: ProjectId,
        run_id: RunId,
        report_format: str,
    ) -> ExportedReport:
        """按 Allowlist 格式导出项目内运行报告。"""

        renderer = self._renderers[report_format]
        report = await self._reports.build(actor, project_id, run_id)
        return ExportedReport(
            content=renderer.generate(report),
            media_type=renderer.media_type,
        )
