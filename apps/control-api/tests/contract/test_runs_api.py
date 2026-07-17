from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.runs.api.router import RunApiDependencies, create_run_router
from agenttest.modules.runs.application.commands import (
    ApplyRunResultHandler,
    CancelRunHandler,
    CreateRunHandler,
)
from agenttest.modules.runs.application.ports import (
    RunDefinition,
    RunDefinitionCase,
    RunRuntimeUnavailableError,
)
from agenttest.modules.runs.application.queries import (
    GetRunHandler,
    ListRunCasesHandler,
    ListRunsHandler,
)
from agenttest.modules.runs.domain.entities import Run, RunCase, RunId
from agenttest.modules.runs.infrastructure.orchestrator import LocalRunOrchestrator
from agenttest.modules.test_plans.public import TestPlanVersionId
from fastapi import FastAPI
from fastapi.testclient import TestClient


class InMemoryRunRepository:
    def __init__(self) -> None:
        self.runs: dict[UUID, Run] = {}
        self.cases: dict[UUID, list[RunCase]] = {}

    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None:
        run = self.runs.get(run_id.value)
        return run if run and run.project_id == project_id else None

    async def get_by_idempotency_key(self, project_id: ProjectId, key: str) -> Run | None:
        return next(
            (
                run
                for run in self.runs.values()
                if run.project_id == project_id and run.idempotency_key == key
            ),
            None,
        )

    async def list_by_project(self, project_id: ProjectId, *, limit: int = 50) -> list[Run]:
        return [run for run in self.runs.values() if run.project_id == project_id][:limit]

    async def add(self, run: Run, cases: list[RunCase]) -> None:
        self.runs[run.run_id.value] = run
        self.cases[run.run_id.value] = cases

    async def save(self, run: Run) -> None:
        self.runs[run.run_id.value] = run

    async def save_result(
        self,
        run: Run,
        cases: list[RunCase],
        scores: dict[str, list[dict[str, object]]] | None = None,
    ) -> None:
        self.runs[run.run_id.value] = run
        self.cases[run.run_id.value] = cases

    async def list_cases(self, project_id: ProjectId, run_id: RunId) -> list[RunCase]:
        del project_id
        return self.cases.get(run_id.value, [])


class StubProjectAccess:
    def __init__(self, project_id: ProjectId, *, member: bool = True) -> None:
        self.project_id = project_id
        self.member = member

    async def ensure_member(self, _actor: User, project_id: ProjectId) -> None:
        if not self.member or project_id != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None:
        await self.ensure_member(actor, project_id)
        if actor.role is SystemRole.VIEWER:
            raise PermissionError


class StubRunSource:
    async def load(self, project_id: ProjectId, version_id: TestPlanVersionId) -> RunDefinition:
        return RunDefinition(
            project_id=project_id,
            test_plan_version_id=version_id,
            agent_version_id=uuid4(),
            dataset_version_id=uuid4(),
            config_snapshot={"concurrency": 2, "timeout": 30},
            plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
            cases=[
                RunDefinitionCase(
                    test_case_id=uuid4(),
                    name="hello",
                    input_snapshot={"message": "hello"},
                    assertion_snapshot=[],
                )
            ],
        )


class StubOrchestrator:
    def __init__(self) -> None:
        self.started: list[RunId] = []
        self.cancelled: list[RunId] = []
        self.cancel_unavailable = False

    async def ensure_available(self) -> None:
        return None

    async def start(self, run: Run, cases: list[RunCase]) -> str:
        self.started.append(run.run_id)
        return f"run-{run.run_id.value}"

    async def cancel(self, run: Run) -> None:
        if self.cancel_unavailable:
            raise RunRuntimeUnavailableError("Run execution runtime is unavailable")
        self.cancelled.append(run.run_id)


@dataclass
class StubCurrentUser:
    actor: User

    async def execute(self, _token: str) -> User:
        return self.actor


class StubCsrf:
    async def execute(self, *_args: object) -> None:
        return None


def make_user(role: SystemRole = SystemRole.DEVELOPER) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(f"{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def client_for(
    *,
    role: SystemRole = SystemRole.DEVELOPER,
    member: bool = True,
    orchestrator: StubOrchestrator | LocalRunOrchestrator | None = None,
) -> tuple[TestClient, ProjectId, StubOrchestrator | LocalRunOrchestrator, InMemoryRunRepository]:
    project_id = ProjectId.new()
    repo = InMemoryRunRepository()
    access = StubProjectAccess(project_id, member=member)
    selected_orchestrator = orchestrator or StubOrchestrator()
    dependencies = RunApiDependencies(
        create_run=CreateRunHandler(
            runs=repo,
            source=StubRunSource(),
            project_access=access,
            orchestrator=selected_orchestrator,
        ),
        list_runs=ListRunsHandler(runs=repo, project_access=access),
        get_run=GetRunHandler(runs=repo, project_access=access),
        list_cases=ListRunCasesHandler(runs=repo, project_access=access),
        cancel_run=CancelRunHandler(
            runs=repo,
            project_access=access,
            orchestrator=selected_orchestrator,
        ),
        apply_result=ApplyRunResultHandler(runs=repo),
    )
    app = FastAPI()
    app.include_router(
        create_run_router(
            dependencies,
            current_user=StubCurrentUser(make_user(role)),
            csrf=StubCsrf(),
            settings=Settings(internal_api_token="test-internal-token"),
        ),
        prefix="/api/v1",
    )
    client = TestClient(
        app,
        base_url="https://testserver",
        raise_server_exceptions=False,
    )
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    return client, project_id, selected_orchestrator, repo


def test_create_is_idempotent_and_can_be_cancelled() -> None:
    client, project_id, orchestrator, _ = client_for()
    version_id = uuid4()
    headers = {"X-CSRF-Token": "csrf-token", "Idempotency-Key": "release-42"}
    first = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers=headers,
        json={"test_plan_version_id": str(version_id)},
    )
    second = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers=headers,
        json={"test_plan_version_id": str(version_id)},
    )
    run_id = first.json()["id"]
    cancelled = client.post(
        f"/api/v1/projects/{project_id.value}/runs/{run_id}/cancel",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert first.status_code == 201
    assert first.json()["status"] == "running"
    assert second.status_code == 200
    assert second.json()["id"] == run_id
    assert len(orchestrator.started) == 1
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_create_rejects_same_idempotency_key_for_a_different_plan() -> None:
    client, project_id, orchestrator, _ = client_for()
    headers = {"X-CSRF-Token": "csrf-token", "Idempotency-Key": "release-conflict"}

    first = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers=headers,
        json={"test_plan_version_id": str(uuid4())},
    )
    conflict = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers=headers,
        json={"test_plan_version_id": str(uuid4())},
    )

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert len(orchestrator.started) == 1


def test_run_list_and_cases_are_project_scoped() -> None:
    client, project_id, _, _ = client_for()
    created = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers={
            "X-CSRF-Token": "csrf-token",
            "Idempotency-Key": "scope-test",
        },
        json={"test_plan_version_id": str(uuid4())},
    )
    run_id = created.json()["id"]

    runs = client.get(f"/api/v1/projects/{project_id.value}/runs")
    cases = client.get(f"/api/v1/projects/{project_id.value}/runs/{run_id}/cases")
    foreign = client.get(f"/api/v1/projects/{uuid4()}/runs/{run_id}")

    assert runs.status_code == 200
    assert runs.json()["items"][0]["id"] == run_id
    assert cases.status_code == 200
    assert cases.json()["items"][0]["name"] == "hello"
    assert foreign.status_code == 404


def test_read_only_user_cannot_create_run() -> None:
    client, project_id, _, _ = client_for(role=SystemRole.VIEWER)
    response = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers={"X-CSRF-Token": "csrf-token", "Idempotency-Key": "denied"},
        json={"test_plan_version_id": str(uuid4())},
    )
    assert response.status_code == 403


def test_internal_result_callback_updates_run_and_cases() -> None:
    client, project_id, _, _ = client_for()
    created = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers={
            "X-CSRF-Token": "csrf-token",
            "Idempotency-Key": "callback-test",
        },
        json={"test_plan_version_id": str(uuid4())},
    )
    run_id = created.json()["id"]
    cases = client.get(f"/api/v1/projects/{project_id.value}/runs/{run_id}/cases").json()["items"]

    response = client.post(
        f"/api/v1/projects/{project_id.value}/runs/{run_id}/result",
        headers={"X-Internal-Token": "test-internal-token"},
        json={
            "cases": [
                {
                    "run_case_id": cases[0]["id"],
                    "status": "passed",
                    "output": {"answer": "hello world"},
                    "trace": [{"name": "http.request", "status": "ok"}],
                    "duration_ms": 42,
                    "evidence": {
                        "execution_outcome": "success",
                        "quality_decision": "pass",
                        "security_decision": "clear",
                        "canvas": {"nodes": [], "connections": []},
                    },
                }
            ]
        },
    )
    updated_cases = client.get(f"/api/v1/projects/{project_id.value}/runs/{run_id}/cases").json()[
        "items"
    ]

    assert response.status_code == 200
    assert response.json()["status"] == "passed"
    assert response.json()["passed_cases"] == 1
    assert updated_cases[0]["status"] == "passed"
    assert updated_cases[0]["output"] == {"answer": "hello world"}
    assert updated_cases[0]["trace"][0]["name"] == "http.request"
    assert updated_cases[0]["evidence"]["execution_outcome"] == "success"
    assert updated_cases[0]["quality_summary"] == {"decision": "pass"}


def test_internal_result_callback_requires_token() -> None:
    client, project_id, _, _ = client_for()
    created = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers={
            "X-CSRF-Token": "csrf-token",
            "Idempotency-Key": "callback-token-test",
        },
        json={"test_plan_version_id": str(uuid4())},
    )

    response = client.post(
        f"/api/v1/projects/{project_id.value}/runs/{created.json()['id']}/result",
        headers={"X-Internal-Token": "wrong-token"},
        json={"cases": []},
    )

    assert response.status_code == 403


def test_create_run_fails_closed_when_execution_runtime_is_unavailable() -> None:
    client, project_id, _, repository = client_for(orchestrator=LocalRunOrchestrator())

    response = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers={
            "X-CSRF-Token": "csrf-token",
            "Idempotency-Key": "runtime-unavailable",
        },
        json={"test_plan_version_id": str(uuid4())},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Run execution runtime is unavailable"
    assert repository.runs == {}


def test_cancel_run_reports_unavailable_execution_runtime() -> None:
    client, project_id, orchestrator, _ = client_for()
    created = client.post(
        f"/api/v1/projects/{project_id.value}/runs",
        headers={
            "X-CSRF-Token": "csrf-token",
            "Idempotency-Key": "cancel-runtime-unavailable",
        },
        json={"test_plan_version_id": str(uuid4())},
    )
    assert isinstance(orchestrator, StubOrchestrator)
    orchestrator.cancel_unavailable = True

    response = client.post(
        f"/api/v1/projects/{project_id.value}/runs/{created.json()['id']}/cancel",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Run execution runtime is unavailable"
