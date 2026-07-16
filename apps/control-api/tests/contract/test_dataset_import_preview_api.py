"""Contract tests for the dataset import preview and strict import API.

Covers the import wizard API surface:
- Preview returns {valid_count, errors, preview}
- Import to published version is rejected
- Atomic import (all-or-nothing)
- CSV import works through the API
- Preview → Import flow end-to-end
"""

from __future__ import annotations

import json

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
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── In-memory test doubles ───────────────────────────────────────────────


class InMemDatasets:
    def __init__(self) -> None:
        self.items: dict[DatasetId, Dataset] = {}

    async def get_by_id(self, dataset_id: DatasetId) -> Dataset | None:
        return self.items.get(dataset_id)

    async def list_by_project(
        self, pid: ProjectId, *, limit: int = 50, cursor: str | None = None
    ) -> tuple[list[Dataset], str | None]:
        del cursor
        return [i for i in self.items.values() if i.project_id == pid][:limit], None

    async def add(self, d: Dataset) -> None:
        self.items[d.dataset_id] = d

    async def save(self, d: Dataset) -> None:
        self.items[d.dataset_id] = d


class InMemVersions:
    def __init__(self) -> None:
        self.items: dict[DatasetVersionId, DatasetVersion] = {}

    async def get_by_id(self, vid: DatasetVersionId) -> DatasetVersion | None:
        return self.items.get(vid)

    async def list_by_dataset(self, did: DatasetId) -> list[DatasetVersion]:
        return [i for i in self.items.values() if i.dataset_id == did]

    async def get_next_version_number(self, did: DatasetId) -> int:
        versions = await self.list_by_dataset(did)
        return max((i.version_number for i in versions), default=0) + 1

    async def add(self, v: DatasetVersion) -> None:
        self.items[v.version_id] = v

    async def save(self, v: DatasetVersion) -> None:
        self.items[v.version_id] = v


class InMemCases:
    def __init__(self) -> None:
        self.items: dict[DatasetTestCaseId, DatasetTestCase] = {}

    async def get_by_id(self, cid: DatasetTestCaseId) -> DatasetTestCase | None:
        return self.items.get(cid)

    async def list_by_version(
        self, vid: DatasetVersionId, *, limit: int = 200, cursor: str | None = None
    ) -> tuple[list[DatasetTestCase], str | None]:
        del cursor
        items = [i for i in self.items.values() if i.dataset_version_id == vid]
        return sorted(items, key=lambda i: i.sort_order)[:limit], None

    async def add(self, c: DatasetTestCase) -> None:
        self.items[c.case_id] = c

    async def save(self, c: DatasetTestCase) -> None:
        self.items[c.case_id] = c

    async def delete(self, cid: DatasetTestCaseId) -> None:
        self.items.pop(cid, None)

    async def get_max_sort_order(self, vid: DatasetVersionId) -> int:
        items, _ = await self.list_by_version(vid)
        return max((i.sort_order for i in items), default=0)

    async def count_by_version(self, vid: DatasetVersionId) -> int:
        items, _ = await self.list_by_version(vid)
        return len(items)


class StubAccess:
    def __init__(self, pid: ProjectId, *, member: bool = True) -> None:
        self.project_id = pid
        self.member = member

    async def ensure_member(self, _actor: User, pid: ProjectId) -> None:
        if not self.member or pid != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor: User, pid: ProjectId) -> None:
        await self.ensure_member(actor, pid)
        if actor.role not in {SystemRole.SUPER_ADMIN, SystemRole.DEVELOPER, SystemRole.TESTER}:
            raise PermissionError

    async def ensure_user_member(self, _user_id: UserId, pid: ProjectId) -> None:
        if not self.member or pid != self.project_id:
            raise ValueError("owner_id must reference a member of the same project")


class StubUser:
    def __init__(self, actor: User) -> None:
        self.actor = actor

    async def execute(self, _token: str) -> User:
        return self.actor


class StubCsrfOp:
    async def execute(self, *_args: object) -> None:
        return None


class StubGenRun:
    async def execute(self, **_kw: object):
        raise AssertionError("unused")


def mkuser(role: SystemRole) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(f"import-{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def deps(pid: ProjectId, *, member: bool = True) -> DatasetApiDependencies:
    ds = InMemDatasets()
    vs = InMemVersions()
    cs = InMemCases()
    ac = StubAccess(pid, member=member)
    add_case = AddTestCaseHandler(datasets=ds, versions=vs, cases=cs, project_access=ac)
    return DatasetApiDependencies(
        list_datasets=ListDatasetsHandler(datasets=ds, project_access=ac),
        get_dataset=GetDatasetHandler(datasets=ds, project_access=ac),
        create_dataset=CreateDatasetHandler(datasets=ds, project_access=ac),
        update_dataset=UpdateDatasetHandler(datasets=ds, project_access=ac),
        list_versions=ListDatasetVersionsHandler(datasets=ds, versions=vs, project_access=ac),
        get_version=GetDatasetVersionHandler(datasets=ds, versions=vs, project_access=ac),
        create_version=CreateDatasetVersionHandler(datasets=ds, versions=vs, project_access=ac),
        list_cases=ListTestCasesHandler(datasets=ds, versions=vs, cases=cs, project_access=ac),
        get_case=GetTestCaseHandler(datasets=ds, versions=vs, cases=cs, project_access=ac),
        add_case=add_case,
        update_case=UpdateTestCaseHandler(datasets=ds, versions=vs, cases=cs, project_access=ac),
        delete_case=DeleteTestCaseHandler(datasets=ds, versions=vs, cases=cs, project_access=ac),
        mark_case_ready=MarkTestCaseReadyHandler(
            datasets=ds,
            versions=vs,
            cases=cs,
            project_access=ac,
        ),
        duplicate_case=DuplicateTestCaseHandler(cases=cs, add_case=add_case),
        publish_version=PublishDatasetVersionHandler(datasets=ds, versions=vs, project_access=ac),
        import_export=ImportExportService(cases=cs, project_access=ac),
        generate_from_run=StubGenRun(),
    )


def client(actor: User, *, member: bool = True) -> tuple[TestClient, ProjectId]:
    pid = ProjectId.new()
    app = FastAPI()
    app.include_router(
        create_dataset_router(
            deps(pid, member=member),
            current_user=StubUser(actor),
            csrf=StubCsrfOp(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    c = TestClient(app, base_url="https://testserver")
    c.cookies.set("agenttest_session", "session-token")
    c.cookies.set("agenttest_csrf", "csrf-token")
    return c, pid


def draft(c: TestClient, pid: ProjectId) -> tuple[str, str]:
    csrf = {"X-CSRF-Token": "csrf-token"}
    ds = c.post(f"/api/v1/projects/{pid.value}/datasets", headers=csrf, json={"name": "Import DS"})
    did = ds.json()["id"]
    ver = c.post(f"/api/v1/projects/{pid.value}/datasets/{did}/versions", headers=csrf)
    return did, ver.json()["id"]


# ── Tests ────────────────────────────────────────────────────────────────


def test_preview_returns_valid_count_errors_and_preview() -> None:
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    did, vid = draft(c, pid)
    csrf = {"X-CSRF-Token": "csrf-token"}

    r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/imports:preview",
        headers=csrf,
        json={
            "format": "json",
            "content": json.dumps(
                [
                    {"name": "ok", "input": {}, "execution_mode": "api"},
                    {"name": "bad enum", "input": {}, "execution_mode": "unknown"},
                ]
            ),
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body["valid_count"] == 1
    assert len(body["errors"]) == 1
    assert body["errors"][0]["line"] == 2
    assert body["errors"][0]["field"] == "execution_mode"
    assert body["errors"][0]["code"] == "invalid_enum"
    assert len(body["preview"]) == 1
    assert body["preview"][0]["name"] == "ok"


def test_preview_rejects_published_version() -> None:
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    did, vid = draft(c, pid)

    pub = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/publish",
        headers=csrf,
    )
    assert pub.status_code == 200

    r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/imports:preview",
        headers=csrf,
        json={
            "format": "json",
            "content": json.dumps([{"name": "ok", "input": {}, "execution_mode": "api"}]),
        },
    )

    assert r.status_code == 400
    assert "published" in r.json()["detail"].lower()


def test_import_to_published_version_is_rejected() -> None:
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    did, vid = draft(c, pid)

    c.post(f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/publish", headers=csrf)

    r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers=csrf,
        json={
            "format": "json",
            "content": json.dumps([{"name": "ok", "input": {}, "execution_mode": "api"}]),
        },
    )

    assert r.status_code == 400


def test_import_is_atomic_no_partial_state_on_error() -> None:
    c, pid = client(mkuser(SystemRole.TESTER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    did, vid = draft(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers=csrf,
        json={
            "format": "json",
            "content": json.dumps(
                [
                    {"name": "valid", "input": {}, "execution_mode": "api"},
                    {"name": "", "input": {}, "execution_mode": "api"},
                ]
            ),
        },
    )

    assert r.status_code == 400

    cases = c.get(f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/cases")
    assert cases.json()["items"] == []


def test_csv_import_through_api() -> None:
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    did, vid = draft(c, pid)

    json_r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers=csrf,
        json={
            "format": "json",
            "content": json.dumps(
                [
                    {
                        "name": "API Flow",
                        "input": {"q": "test"},
                        "execution_mode": "api",
                        "priority": "P0",
                    }
                ]
            ),
        },
    )
    assert json_r.status_code == 201
    assert json_r.json()["imported_count"] == 1

    ver2 = c.post(f"/api/v1/projects/{pid.value}/datasets/{did}/versions", headers=csrf)
    vid2 = ver2.json()["id"]

    csv_r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid2}/import",
        headers=csrf,
        json={
            "format": "csv",
            "content": ('name,input,execution_mode,priority\nAPI Flow,"{""q"":""test""}",api,P0\n'),
        },
    )
    assert csv_r.status_code == 201
    assert csv_r.json()["imported_count"] == 1


def test_chinese_csv_import_through_api() -> None:
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    did, vid = draft(c, pid)

    csv_r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers=csrf,
        json={
            "format": "csv",
            "content": (
                "用例名称,输入,执行模式,风险等级,测试分组\n"
                '中文导入,"{""q"":""test""}",浏览器,高,验证集\n'
            ),
        },
    )

    assert csv_r.status_code == 201
    body = csv_r.json()
    assert body["imported_count"] == 1
    assert body["items"][0]["name"] == "中文导入"
    assert body["items"][0]["execution_mode"] == "browser"
    assert body["items"][0]["risk_level"] == "high"
    assert body["items"][0]["test_group"] == "validation"


def test_preview_then_import_flow() -> None:
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    did, vid = draft(c, pid)

    content = (
        '{"name":"Flow 1","input":{"q":1},"execution_mode":"api"}\n'
        '{"name":"Flow 2","input":{"msg":"hi"},"execution_mode":"browser","priority":"P1"}\n'
    )
    preview = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/imports:preview",
        headers=csrf,
        json={"format": "jsonl", "content": content},
    )
    assert preview.status_code == 200
    assert preview.json()["valid_count"] == 2
    assert preview.json()["errors"] == []

    imported = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers=csrf,
        json={"format": "jsonl", "content": content},
    )
    assert imported.status_code == 201
    assert imported.json()["imported_count"] == 2
    assert len(imported.json()["items"]) == 2

    cases = c.get(f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/cases")
    names = [c["name"] for c in cases.json()["items"]]
    assert "Flow 1" in names
    assert "Flow 2" in names


def test_viewer_cannot_import() -> None:
    dev = mkuser(SystemRole.DEVELOPER)
    viewer = mkuser(SystemRole.VIEWER)

    pid = ProjectId.new()
    # Shared dependencies so viewer can find the dataset created by developer
    shared_deps = deps(pid)

    # Developer client
    app_dev = FastAPI()
    app_dev.include_router(
        create_dataset_router(
            shared_deps,
            current_user=StubUser(dev),
            csrf=StubCsrfOp(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    dc = TestClient(app_dev, base_url="https://testserver")
    dc.cookies.set("agenttest_session", "session-token")
    dc.cookies.set("agenttest_csrf", "csrf-token")

    did, vid = draft(dc, pid)

    # Viewer client (same deps, same project)
    app_viewer = FastAPI()
    app_viewer.include_router(
        create_dataset_router(
            shared_deps,
            current_user=StubUser(viewer),
            csrf=StubCsrfOp(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    vc = TestClient(app_viewer, base_url="https://testserver")
    vc.cookies.set("agenttest_session", "session-token")
    vc.cookies.set("agenttest_csrf", "csrf-token")

    r = vc.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers={"X-CSRF-Token": "csrf-token"},
        json={
            "format": "json",
            "content": json.dumps([{"name": "ok", "input": {"x": 1}, "execution_mode": "api"}]),
        },
    )
    assert r.status_code == 403


def test_import_publish_verify_chain() -> None:
    """导入 → 发布 → 验证版本状态与用例持久化。"""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    did, vid = draft(c, pid)

    # Step 1: 导入 JSONL 用例
    content = json.dumps(
        [
            {
                "name": "Chain Test 1",
                "input": {"q": "hello"},
                "execution_mode": "api",
                "priority": "P0",
                "tags": ["chain"],
            },
            {
                "name": "Chain Test 2",
                "input": {"url": "https://a.com"},
                "execution_mode": "browser",
                "risk_level": "high",
            },
        ]
    )
    imported = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers=csrf,
        json={"format": "json", "content": content},
    )
    assert imported.status_code == 201
    assert imported.json()["imported_count"] == 2

    # Step 2: 发布版本
    pub = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/publish",
        headers=csrf,
    )
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"

    # Step 3: 已发布版本用例可查询
    cases = c.get(f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/cases")
    assert cases.status_code == 200
    items = cases.json()["items"]
    assert len(items) == 2
    names = {c["name"] for c in items}
    assert names == {"Chain Test 1", "Chain Test 2"}

    # Step 4: 已发布版本拒绝二次导入
    r = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/import",
        headers=csrf,
        json={
            "format": "json",
            "content": json.dumps([{"name": "bad", "input": {}, "execution_mode": "api"}]),
        },
    )
    assert r.status_code == 400

    # Step 5: 已发布版本拒绝二次发布
    pub2 = c.post(
        f"/api/v1/projects/{pid.value}/datasets/{did}/versions/{vid}/publish",
        headers=csrf,
    )
    assert pub2.status_code == 409
