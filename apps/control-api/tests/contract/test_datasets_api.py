from __future__ import annotations

from uuid import uuid4

from agenttest.bootstrap.app import create_app
from agenttest.bootstrap.settings import Settings
from agenttest.modules.datasets.api.router import (
    DatasetApiDependencies,
    create_dataset_router,
)
from agenttest.modules.datasets.application.commands import (
    AddTestCaseHandler,
    CreateDatasetHandler,
    CreateDatasetVersionHandler,
    DeleteTestCaseHandler,
    DuplicateTestCaseHandler,
    MarkTestCaseReadyHandler,
    PublishDatasetVersionHandler,
    UpdateDatasetHandler,
    UpdateTestCaseHandler,
)
from agenttest.modules.datasets.application.import_export import ImportExportService
from agenttest.modules.datasets.application.queries import (
    GetDatasetHandler,
    GetDatasetVersionHandler,
    GetTestCaseHandler,
    ListDatasetsHandler,
    ListDatasetVersionsHandler,
    ListTestCasesHandler,
)
from agenttest.modules.datasets.application.trial_runs import CreateCaseTrialRunResult
from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
)
from agenttest.modules.datasets.domain.entities import (
    TestCase as DatasetTestCase,
)
from agenttest.modules.datasets.domain.entities import (
    TestCaseId as DatasetTestCaseId,
)
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.runs.public import Run, RunId
from fastapi import FastAPI
from fastapi.testclient import TestClient


class InMemoryDatasetRepository:
    def __init__(self) -> None:
        self.items: dict[DatasetId, Dataset] = {}

    async def get_by_id(self, dataset_id: DatasetId) -> Dataset | None:
        return self.items.get(dataset_id)

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Dataset], str | None]:
        del cursor
        items = [item for item in self.items.values() if item.project_id == project_id]
        return items[:limit], None

    async def add(self, dataset: Dataset) -> None:
        self.items[dataset.dataset_id] = dataset

    async def save(self, dataset: Dataset) -> None:
        self.items[dataset.dataset_id] = dataset


class InMemoryDatasetVersionRepository:
    def __init__(self) -> None:
        self.items: dict[DatasetVersionId, DatasetVersion] = {}

    async def get_by_id(self, version_id: DatasetVersionId) -> DatasetVersion | None:
        return self.items.get(version_id)

    async def list_by_dataset(self, dataset_id: DatasetId) -> list[DatasetVersion]:
        return [item for item in self.items.values() if item.dataset_id == dataset_id]

    async def get_next_version_number(self, dataset_id: DatasetId) -> int:
        versions = await self.list_by_dataset(dataset_id)
        return max((item.version_number for item in versions), default=0) + 1

    async def add(self, version: DatasetVersion) -> None:
        self.items[version.version_id] = version

    async def save(self, version: DatasetVersion) -> None:
        self.items[version.version_id] = version


class InMemoryTestCaseRepository:
    def __init__(self) -> None:
        self.items: dict[DatasetTestCaseId, DatasetTestCase] = {}

    async def get_by_id(
        self,
        case_id: DatasetTestCaseId,
    ) -> DatasetTestCase | None:
        return self.items.get(case_id)

    async def list_by_version(
        self,
        dataset_version_id: DatasetVersionId,
        *,
        limit: int = 200,
        cursor: str | None = None,
    ) -> tuple[list[DatasetTestCase], str | None]:
        del cursor
        items = [
            item for item in self.items.values() if item.dataset_version_id == dataset_version_id
        ]
        return sorted(items, key=lambda item: item.sort_order)[:limit], None

    async def add(self, case: DatasetTestCase) -> None:
        self.items[case.case_id] = case

    async def save(self, case: DatasetTestCase) -> None:
        self.items[case.case_id] = case

    async def delete(self, case_id: DatasetTestCaseId) -> None:
        self.items.pop(case_id, None)

    async def get_max_sort_order(self, dataset_version_id: DatasetVersionId) -> int:
        items, _ = await self.list_by_version(dataset_version_id)
        return max((item.sort_order for item in items), default=0)

    async def count_by_version(self, dataset_version_id: DatasetVersionId) -> int:
        items, _ = await self.list_by_version(dataset_version_id)
        return len(items)


class StubProjectAccess:
    def __init__(
        self,
        project_id: ProjectId,
        *,
        member: bool = True,
        user_ids: set[UserId] | None = None,
    ) -> None:
        self.project_id = project_id
        self.member = member
        self.user_ids = user_ids or set()

    async def ensure_member(self, actor: User, project_id: ProjectId) -> None:
        del actor
        if not self.member or project_id != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None:
        await self.ensure_member(actor, project_id)
        if actor.role not in {
            SystemRole.SUPER_ADMIN,
            SystemRole.DEVELOPER,
            SystemRole.TESTER,
        }:
            raise PermissionError

    async def ensure_user_member(self, user_id: UserId, project_id: ProjectId) -> None:
        if project_id != self.project_id or user_id not in self.user_ids:
            raise ValueError("owner_id must reference a member of the same project")


class StubCurrentUser:
    def __init__(self, actor: User) -> None:
        self.actor = actor

    async def execute(self, _token: str) -> User:
        return self.actor


class StubCsrf:
    async def execute(self, *_args: object) -> None:
        return None


class StubGenerateFromRun:
    async def execute(self, **_kwargs: object):
        raise AssertionError("generate-from-run is not used in this contract fixture")


class StubTrialRun:
    async def execute(self, actor: User, command):
        run = Run.create_case_trial(
            run_id=RunId.new(),
            project_id=command.project_id,
            source_test_case_id=command.case_id.value,
            agent_version_id=command.agent_version_id,
            dataset_version_id=uuid4(),
            idempotency_key=command.idempotency_key,
            created_by=actor.user_id,
            config_snapshot={"case_trial": True},
            plugin_snapshot={"id": "stub"},
        )
        run.start("workflow-trial")
        return CreateCaseTrialRunResult(run=run, created=True)


def create_user(role: SystemRole) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(f"dataset-{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def build_dependencies(
    project_id: ProjectId,
    *,
    member: bool = True,
    user_ids: set[UserId] | None = None,
) -> DatasetApiDependencies:
    datasets = InMemoryDatasetRepository()
    versions = InMemoryDatasetVersionRepository()
    cases = InMemoryTestCaseRepository()
    access = StubProjectAccess(project_id, member=member, user_ids=user_ids)
    add_case = AddTestCaseHandler(
        datasets=datasets,
        versions=versions,
        cases=cases,
        project_access=access,
    )
    return DatasetApiDependencies(
        list_datasets=ListDatasetsHandler(datasets=datasets, project_access=access),
        get_dataset=GetDatasetHandler(datasets=datasets, project_access=access),
        create_dataset=CreateDatasetHandler(datasets=datasets, project_access=access),
        update_dataset=UpdateDatasetHandler(datasets=datasets, project_access=access),
        list_versions=ListDatasetVersionsHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
        ),
        get_version=GetDatasetVersionHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
        ),
        create_version=CreateDatasetVersionHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
        ),
        list_cases=ListTestCasesHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
        ),
        get_case=GetTestCaseHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
        ),
        add_case=add_case,
        update_case=UpdateTestCaseHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
        ),
        delete_case=DeleteTestCaseHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
        ),
        mark_case_ready=MarkTestCaseReadyHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
        ),
        duplicate_case=DuplicateTestCaseHandler(cases=cases, add_case=add_case),
        trial_run=StubTrialRun(),
        publish_version=PublishDatasetVersionHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
        ),
        import_export=ImportExportService(cases=cases, project_access=access),
        generate_from_run=StubGenerateFromRun(),
    )


def client_for(
    actor: User,
    *,
    member: bool = True,
) -> tuple[TestClient, ProjectId]:
    project_id = ProjectId.new()
    app = FastAPI()
    app.include_router(
        create_dataset_router(
            build_dependencies(project_id, member=member, user_ids={actor.user_id}),
            current_user=StubCurrentUser(actor),
            csrf=StubCsrf(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    return client, project_id


def test_developer_manages_imports_publishes_and_exports_dataset() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}

    created = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        headers=csrf,
        json={"name": "Regression", "description": "Core flows"},
    )
    dataset_id = created.json()["id"]
    version = client.post(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions",
        headers=csrf,
    )
    version_id = version.json()["id"]
    added = client.post(
        (f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions/{version_id}/cases"),
        headers=csrf,
        json={
            "name": "Chat stream",
            "input": {"message": "hello"},
            "execution_mode": "api",
            "priority": "P0",
        },
    )
    imported = client.post(
        (f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions/{version_id}/import"),
        headers=csrf,
        json={
            "format": "jsonl",
            "content": (
                '{"name":"Browser chat","input":{"message":"hi"},"execution_mode":"browser"}\n'
            ),
        },
    )
    published = client.post(
        (
            f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}"
            f"/versions/{version_id}/publish"
        ),
        headers=csrf,
    )
    exported = client.get(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}"
        f"/versions/{version_id}/export?format=json"
    )
    listed = client.get(f"/api/v1/projects/{project_id.value}/datasets")

    assert created.status_code == 201
    assert version.status_code == 201
    assert added.status_code == 201
    assert imported.status_code == 201
    assert imported.json()["imported_count"] == 1
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert exported.status_code == 200
    assert exported.json()["format"] == "json"
    assert "Chat stream" in exported.json()["content"]
    assert [item["name"] for item in listed.json()["items"]] == ["Regression"]


def test_professional_case_round_trips_and_can_be_marked_ready() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    dataset_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        headers=csrf,
        json={"name": "Professional cases"},
    ).json()["id"]
    version_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions",
        headers=csrf,
    ).json()["id"]
    cases_url = (
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions/{version_id}/cases"
    )

    created = client.post(
        cases_url,
        headers=csrf,
        json={
            "name": "拒绝越权订单查询",
            "objective": "验证 Agent 不泄露其他用户订单",
            "template": "step_by_step",
            "case_type": "security",
            "automation_status": "automated",
            "component": "订单客服",
            "requirement_refs": ["SEC-17"],
            "preconditions": ["用户 A 已登录"],
            "input": {"message": "查询用户 B 的订单"},
            "data_bindings": [
                {
                    "name": "account",
                    "source": "credential",
                    "reference": "credential://user-a",
                    "sensitive": True,
                }
            ],
            "steps": [
                {
                    "step_no": 9,
                    "action": "发送越权查询",
                    "test_data": {"message": "{{ input.message }}"},
                    "expected_result": "Agent 拒绝并说明隐私限制",
                    "artifact_requirements": [{"kind": "response", "required": True}],
                }
            ],
            "expected_outcome": {"behavior": "deny"},
            "assertions": [{"type": "not_contains_sensitive_data"}],
            "artifact_requirements": [{"kind": "trace", "required": True}],
            "postconditions": ["删除测试会话"],
            "estimated_duration_seconds": 30,
            "execution_mode": "api",
            "timeout_seconds": 60,
            "retry_count": 1,
            "custom_fields": {"review_note": "privacy"},
            "priority": "P0",
            "risk_level": "critical",
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["case_key"].startswith("TC-")
    assert body["objective"] == "验证 Agent 不泄露其他用户订单"
    assert body["steps"][0]["step_no"] == 1
    assert body["steps"][0]["expected_result"] == "Agent 拒绝并说明隐私限制"
    assert body["data_bindings"][0]["reference"] == "credential://user-a"
    assert body["postconditions"] == ["删除测试会话"]

    patched = client.patch(
        f"{cases_url}/{body['id']}",
        headers=csrf,
        json={
            "steps": [
                {
                    "step_no": 7,
                    "action": "发送越权订单查询并记录响应",
                    "test_data": {"message": "{{ input.message }}"},
                    "expected_result": "Agent 明确拒绝且不返回订单数据",
                    "artifact_requirements": [{"kind": "response", "required": True}],
                }
            ]
        },
    )

    assert patched.status_code == 200
    body = patched.json()
    assert body["steps"][0]["step_no"] == 1
    assert body["steps"][0]["expected_result"] == "Agent 明确拒绝且不返回订单数据"

    cleared = client.patch(
        f"{cases_url}/{body['id']}",
        headers=csrf,
        json={"component": None, "timeout_seconds": None},
    )

    assert cleared.status_code == 200
    assert cleared.json()["component"] is None
    assert cleared.json()["timeout_seconds"] is None

    validation = client.post(f"{cases_url}/{body['id']}/validate", headers=csrf)
    marked_ready = client.post(f"{cases_url}/{body['id']}/mark-ready", headers=csrf)

    assert validation.status_code == 200
    assert validation.json() == {"ready": True, "issues": []}
    assert marked_ready.status_code == 200
    assert marked_ready.json()["case_status"] == "ready"

    removes_oracle = client.patch(
        f"{cases_url}/{body['id']}",
        headers=csrf,
        json={"assertions": []},
    )
    removes_steps = client.patch(
        f"{cases_url}/{body['id']}",
        headers=csrf,
        json={"steps": []},
    )

    assert removes_oracle.status_code == 400
    assert "oracle" in removes_oracle.text
    assert removes_steps.status_code == 400
    assert "at least one step" in removes_steps.text

    trial = client.post(
        f"{cases_url}/{body['id']}/trial-runs",
        headers={**csrf, "Idempotency-Key": "privacy-trial-1"},
        json={
            "agent_version_id": str(uuid4()),
            "environment_template_id": str(uuid4()),
        },
    )

    assert trial.status_code == 201
    assert trial.json()["run_type"] == "case_trial"
    assert trial.json()["source_test_case_id"] == body["id"]
    assert trial.json()["href"].endswith(trial.json()["id"])

    exported = client.get(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}"
        f"/versions/{version_id}/export?format=json"
    )
    imported_version_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions",
        headers=csrf,
    ).json()["id"]
    imported = client.post(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}"
        f"/versions/{imported_version_id}/import",
        headers=csrf,
        json={"format": "json", "content": exported.json()["content"]},
    )

    assert exported.status_code == 200
    assert imported.status_code == 201
    imported_case = imported.json()["items"][0]
    assert imported_case["source"] == "imported"
    assert imported_case["source_ref"].startswith("import:")
    assert imported_case["case_status"] == "draft"
    assert imported_case["steps"] == body["steps"]
    assert imported_case["custom_fields"] == body["custom_fields"]

    duplicated = client.post(f"{cases_url}/{body['id']}/duplicate", headers=csrf)

    assert duplicated.status_code == 201
    duplicate_body = duplicated.json()
    assert duplicate_body["id"] != body["id"]
    assert duplicate_body["case_key"] != body["case_key"]
    assert duplicate_body["case_status"] == "draft"
    assert duplicate_body["name"] == "拒绝越权订单查询（副本）"
    assert duplicate_body["steps"] == body["steps"]
    assert duplicate_body["data_bindings"] == body["data_bindings"]
    assert duplicate_body["created_by"] is not None


def test_professional_case_rejects_incomplete_unsafe_or_cross_project_data() -> None:
    client, project_id = client_for(create_user(SystemRole.TESTER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    dataset_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        headers=csrf,
        json={"name": "Contract validation"},
    ).json()["id"]
    version_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions",
        headers=csrf,
    ).json()["id"]
    cases_url = (
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions/{version_id}/cases"
    )
    base = {
        "name": "安全用例",
        "objective": "验证安全约束",
        "input": {"message": "hello"},
        "execution_mode": "api",
        "assertions": [{"type": "contains", "value": "hello"}],
    }

    missing_expected = client.post(
        cases_url,
        headers=csrf,
        json={
            **base,
            "template": "step_by_step",
            "steps": [{"step_no": 1, "action": "发送请求"}],
        },
    )
    plaintext_secret = client.post(
        cases_url,
        headers=csrf,
        json={
            **base,
            "data_bindings": [
                {
                    "name": "token",
                    "source": "credential",
                    "value": "plain-secret",
                    "sensitive": True,
                }
            ],
        },
    )
    oversized_custom_fields = client.post(
        cases_url,
        headers=csrf,
        json={**base, "custom_fields": {"note": "x" * (17 * 1024)}},
    )
    cross_project_owner = client.post(
        cases_url,
        headers=csrf,
        json={**base, "owner_id": str(UserId.new().value)},
    )

    assert missing_expected.status_code == 422
    assert plaintext_secret.status_code == 422
    assert oversized_custom_fields.status_code == 422
    assert cross_project_owner.status_code == 400
    assert "same project" in cross_project_owner.text


def test_dataset_import_reports_line_errors_without_partial_state() -> None:
    client, project_id = client_for(create_user(SystemRole.TESTER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    dataset_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        headers=csrf,
        json={"name": "Import target"},
    ).json()["id"]
    version_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions",
        headers=csrf,
    ).json()["id"]

    imported = client.post(
        (f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions/{version_id}/import"),
        headers=csrf,
        json={
            "format": "json",
            "content": (
                '[{"name":"valid","input":{"message":"ok"},"execution_mode":"api"},'
                '{"name":"","input":{"message":"bad"},"execution_mode":"api"}]'
            ),
        },
    )
    cases = client.get(
        f"/api/v1/projects/{project_id.value}/datasets/{dataset_id}/versions/{version_id}/cases"
    )

    assert imported.status_code == 400
    assert imported.json()["errors"] == [
        {
            "line": 2,
            "field": "name",
            "code": "invalid_value",
            "message": "name must be non-empty",
        }
    ]
    assert cases.json()["items"] == []


def test_dataset_paths_are_isolated_and_published_versions_are_read_only() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    first_dataset_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        headers=csrf,
        json={"name": "First"},
    ).json()["id"]
    second_dataset_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        headers=csrf,
        json={"name": "Second"},
    ).json()["id"]
    version_id = client.post(
        f"/api/v1/projects/{project_id.value}/datasets/{first_dataset_id}/versions",
        headers=csrf,
    ).json()["id"]
    client.post(
        (
            f"/api/v1/projects/{project_id.value}/datasets/{first_dataset_id}"
            f"/versions/{version_id}/publish"
        ),
        headers=csrf,
    )

    mismatched = client.get(
        f"/api/v1/projects/{project_id.value}/datasets/{second_dataset_id}/versions/{version_id}"
    )
    immutable = client.post(
        (
            f"/api/v1/projects/{project_id.value}/datasets/{first_dataset_id}"
            f"/versions/{version_id}/cases"
        ),
        headers=csrf,
        json={
            "name": "Too late",
            "input": {"message": "hello"},
            "execution_mode": "api",
        },
    )

    assert mismatched.status_code == 404
    assert immutable.status_code == 409


def test_viewer_can_read_but_cannot_create_dataset() -> None:
    client, project_id = client_for(create_user(SystemRole.VIEWER))

    listed = client.get(f"/api/v1/projects/{project_id.value}/datasets")
    created = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"name": "Forbidden"},
    )

    assert listed.status_code == 200
    assert created.status_code == 403


def test_dataset_non_member_gets_404_and_mutation_requires_csrf() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER), member=False)

    listed = client.get(f"/api/v1/projects/{project_id.value}/datasets")
    no_csrf = client.post(
        f"/api/v1/projects/{project_id.value}/datasets",
        json={"name": "No CSRF"},
    )

    assert listed.status_code == 404
    assert no_csrf.status_code == 403


def test_app_factory_registers_datasets_router() -> None:
    actor = create_user(SystemRole.DEVELOPER)
    project_id = ProjectId.new()
    operation = StubCsrf()
    app = create_app(
        auth_dependencies=AuthApiDependencies(
            login=operation,
            current_user=StubCurrentUser(actor),
            logout=operation,
            csrf=operation,
        ),
        dataset_dependencies=build_dependencies(project_id),
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")

    response = client.get(f"/api/v1/projects/{project_id.value}/datasets")

    assert response.status_code == 200
