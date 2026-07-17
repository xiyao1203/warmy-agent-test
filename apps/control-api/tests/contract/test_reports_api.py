"""报告导出 HTTP 契约测试。"""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.reports.api.router import create_report_router
from agenttest.modules.reports.application.export import ExportedReport
from fastapi import FastAPI
from fastapi.testclient import TestClient


class StubCurrentUser:
    """返回固定登录用户。"""

    def __init__(self) -> None:
        self.user = User.create(
            user_id=UserId.new(),
            email=Email("reporter@example.com"),
            display_name="Reporter",
            role=SystemRole.DEVELOPER,
        )

    async def execute(self, _session_token: str) -> User:
        return self.user


class StubExporter:
    """返回固定格式内容的 Application 导出器。"""

    def __init__(self, media_type: str, content: str) -> None:
        self.media_type = media_type
        self.content = content
        self.formats: list[str] = []

    async def export(self, _actor, _project_id, _run_id, report_format: str):
        self.formats.append(report_format)
        return ExportedReport(content=self.content, media_type=self.media_type)


@pytest.mark.parametrize(
    ("report_format", "media_type", "content"),
    [
        ("json", "application/json", '{"status":"passed"}'),
        ("junit", "application/xml", "<testsuites />"),
        ("html", "text/html", "<!DOCTYPE html><html></html>"),
    ],
)
def test_report_export_preserves_media_type_and_body(
    report_format: str,
    media_type: str,
    content: str,
) -> None:
    exporter = StubExporter(media_type, content)
    app = FastAPI()
    app.include_router(
        create_report_router(
            exporter=exporter,
            current_user=StubCurrentUser(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")

    response = client.get(
        f"/api/v1/projects/{uuid4()}/runs/{uuid4()}/export",
        params={"format": report_format},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(media_type)
    assert response.text == content
    assert exporter.formats == [report_format]
