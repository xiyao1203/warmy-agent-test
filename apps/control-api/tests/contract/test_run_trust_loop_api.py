from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.run_postprocessing.api.router import create_run_trust_loop_router
from agenttest.modules.run_postprocessing.application import PIPELINE_VERSION
from agenttest.modules.run_postprocessing.domain import (
    PostprocessStage,
    PostprocessStatus,
    RunPostprocessJob,
    StageResult,
)
from agenttest.modules.run_postprocessing.queries import RunTrustLoopQueryService
from agenttest.modules.runs.application.commands import RunNotFoundError
from agenttest.modules.runs.domain.entities import RunId
from fastapi import FastAPI
from fastapi.testclient import TestClient


class Access:
    def __init__(self, project_id: UUID, run_id: UUID) -> None:
        self.project_id = project_id
        self.run_id = run_id

    async def execute(
        self,
        _actor: User,
        project_id: ProjectId,
        run_id: RunId,
    ) -> object:
        if project_id.value != self.project_id:
            raise ProjectNotFoundError
        if run_id.value != self.run_id:
            raise RunNotFoundError
        return object()


class Records:
    def __init__(self, job: RunPostprocessJob | None) -> None:
        self.job = job
        now = datetime.now(UTC)
        self.diagnostics = [
            {
                "id": uuid4(),
                "run_case_id": uuid4(),
                "pipeline_version": PIPELINE_VERSION,
                "status": "inconclusive",
                "failure_class": "target",
                "confidence": 0.0,
                "evidence_ids": [],
                "summary": None,
                "counterevidence": [],
                "verification_steps": [],
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": uuid4(),
                "run_case_id": uuid4(),
                "pipeline_version": PIPELINE_VERSION,
                "status": "completed",
                "failure_class": "assertion",
                "confidence": 0.9,
                "evidence_ids": ["evidence-1"],
                "summary": "Evidence-bounded diagnosis",
                "counterevidence": [],
                "verification_steps": ["Replay the assertion"],
                "created_at": now,
                "updated_at": now,
            },
        ]
        self.regressions = [
            {
                "id": uuid4(),
                "run_case_id": uuid4(),
                "pipeline_version": PIPELINE_VERSION,
                "fingerprint": "a" * 64,
                "status": "published",
                "input_reference": {"run_case_id": "case-1"},
                "minimized_input": None,
                "reproduction_run_case_ids": ["evidence-1", "evidence-2"],
                "reproduction_count": 2,
                "target_dataset_version_id": None,
                "created_at": now,
                "updated_at": now,
            }
        ]
        self.calibration = {
            "id": uuid4(),
            "pipeline_version": PIPELINE_VERSION,
            "status": "completed",
            "sample_set_version": None,
            "metrics": {"accuracy": 0.75},
            "arbitration": {},
            "evaluator_version": None,
            "created_at": now,
            "updated_at": now,
        }
        self.gate = {
            "id": uuid4(),
            "pipeline_version": PIPELINE_VERSION,
            "baseline_run_id": None,
            "decision": "quarantine",
            "rules": [{"code": "security", "status": "block"}],
            "input_facts": {},
            "explanation": "Deterministic joint gate decision",
            "created_at": now,
        }

    async def get(self, project_id: UUID, run_id: UUID, pipeline_version: str):
        del project_id, run_id, pipeline_version
        return self.job

    async def list_diagnostics(
        self, project_id: UUID, run_id: UUID, pipeline_version: str, *, limit: int, offset: int
    ):
        del project_id, run_id, pipeline_version
        return self.diagnostics[offset : offset + limit], len(self.diagnostics)

    async def list_regressions(
        self, project_id: UUID, run_id: UUID, pipeline_version: str, *, limit: int, offset: int
    ):
        del project_id, run_id, pipeline_version
        return self.regressions[offset : offset + limit], len(self.regressions)

    async def get_calibration(self, project_id: UUID, run_id: UUID, pipeline_version: str):
        del project_id, run_id, pipeline_version
        return self.calibration

    async def get_joint_gate(self, project_id: UUID, run_id: UUID, pipeline_version: str):
        del project_id, run_id, pipeline_version
        return self.gate


@dataclass
class CurrentUser:
    actor: User

    async def execute(self, _token: str) -> User:
        return self.actor


def _user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("trust-loop@example.com"),
        display_name="Trust Loop Reader",
        role=SystemRole.VIEWER,
    )


def _completed_job(project_id: UUID, run_id: UUID) -> RunPostprocessJob:
    now = datetime.now(UTC)
    return RunPostprocessJob(
        job_id=uuid4(),
        project_id=project_id,
        run_id=run_id,
        pipeline_version=PIPELINE_VERSION,
        status=PostprocessStatus.COMPLETED_WITH_WARNINGS,
        current_stage=PostprocessStage.FINALIZE,
        workflow_id=f"run-trust-loop-{run_id}-{PIPELINE_VERSION}",
        attempt=1,
        warning_codes=["diagnostic_model_unavailable"],
        error_type=None,
        error_message="provider api key leaked detail",
        stage_results=[
            StageResult(
                PostprocessStage.DIAGNOSE,
                "warning",
                {"items": []},
                "diagnostic_model_unavailable",
                "provider_error",
                "provider api key leaked detail",
                now,
            )
        ],
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=now,
    )


def client_for(*, completed: bool = True) -> tuple[TestClient, UUID, UUID]:
    project_id = uuid4()
    run_id = uuid4()
    records = Records(_completed_job(project_id, run_id) if completed else None)
    service = RunTrustLoopQueryService(records, Access(project_id, run_id))
    app = FastAPI()
    app.include_router(
        create_run_trust_loop_router(
            service=service,
            current_user=CurrentUser(_user()),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
    client.cookies.set("agenttest_session", "session-token")
    return client, project_id, run_id


def test_member_reads_warning_projection_without_internal_error_details() -> None:
    client, project_id, run_id = client_for()

    response = client.get(f"/api/v1/projects/{project_id}/runs/{run_id}/trust-loop")

    assert response.status_code == 200
    assert response.json()["status"] == "completed_with_warnings"
    assert response.json()["diagnostics"]["status"] == "inconclusive"
    assert response.json()["warning_codes"] == ["diagnostic_model_unavailable"]
    assert "provider" not in response.text.lower()
    assert "api key" not in response.text.lower()


def test_missing_job_projects_pending_but_unknown_or_foreign_run_is_not_found() -> None:
    client, project_id, run_id = client_for(completed=False)

    pending = client.get(f"/api/v1/projects/{project_id}/runs/{run_id}/trust-loop")
    unknown = client.get(f"/api/v1/projects/{project_id}/runs/{uuid4()}/trust-loop")
    foreign = client.get(f"/api/v1/projects/{uuid4()}/runs/{run_id}/trust-loop")

    assert pending.status_code == 200
    assert pending.json()["status"] == "pending"
    assert pending.json()["job_id"] is None
    assert unknown.status_code == 404
    assert foreign.status_code == 404


def test_diagnostics_and_regressions_are_paginated_and_detail_views_are_typed() -> None:
    client, project_id, run_id = client_for()
    prefix = f"/api/v1/projects/{project_id}/runs/{run_id}"

    diagnostics = client.get(f"{prefix}/diagnostics?limit=1&offset=1")
    regressions = client.get(f"{prefix}/regressions?limit=1&offset=0")
    calibration = client.get(f"{prefix}/calibration")
    gate = client.get(f"{prefix}/joint-gate")

    assert diagnostics.status_code == 200
    assert diagnostics.json()["total"] == 2
    assert len(diagnostics.json()["items"]) == 1
    assert diagnostics.json()["offset"] == 1
    assert regressions.status_code == 200
    assert regressions.json()["items"][0]["reproduction_count"] == 2
    assert calibration.json()["metrics"] == {"accuracy": 0.75}
    assert gate.json()["decision"] == "quarantine"


def test_trust_loop_requires_authenticated_session() -> None:
    client, project_id, run_id = client_for()
    client.cookies.clear()

    response = client.get(f"/api/v1/projects/{project_id}/runs/{run_id}/trust-loop")

    assert response.status_code == 401
