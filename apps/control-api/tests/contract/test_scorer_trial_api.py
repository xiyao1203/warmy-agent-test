"""Contract tests for the scorer trial API.

Covers:
- Rule scorer trial returns deterministic result
- Reference scorer trial requires reference
- Model scorer trial requires runtime (503 when absent)
- Unsupported scorer type is rejected
- Trial for non-existent scorer returns 404
"""

from __future__ import annotations

from uuid import uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.scorers.api.router import (
    ScorerApiDependencies,
    create_scorer_router,
)
from agenttest.modules.scorers.application.service import ScorerService
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── In-memory test double ──────────────────────────────────────────────────


class InMemScorerRepo:
    def __init__(self) -> None:
        self.items: dict[ScorerId, Scorer] = {}

    async def get_by_id_and_project(self, sid: ScorerId, _pid: ProjectId) -> Scorer | None:
        scorer = self.items.get(sid)
        if scorer is None or scorer.project_id != _pid:
            return None
        return scorer

    async def list_by_project(
        self, pid: ProjectId, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[Scorer], int]:
        items = [s for s in self.items.values() if s.project_id == pid]
        return items[offset : offset + limit], len(items)

    async def get_by_id(self, sid: ScorerId) -> Scorer | None:
        return self.items.get(sid)

    async def add(self, s: Scorer) -> None:
        self.items[s.scorer_id] = s

    async def save(self, s: Scorer) -> None:
        self.items[s.scorer_id] = s

    async def delete(self, sid: ScorerId) -> None:
        self.items.pop(sid, None)

    async def count_by_project(self, _pid: ProjectId) -> int:
        return sum(1 for s in self.items.values() if s.project_id == _pid)


class StubActorFor:
    def __init__(self, actor: User) -> None:
        self.actor = actor

    async def __call__(self, _request) -> User:
        return self.actor


class StubProjectAccess:
    def __init__(self, pid: ProjectId) -> None:
        self.project_id = pid

    async def ensure_member(self, _actor: User, project_id: ProjectId) -> None:
        if project_id != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, _actor: User, project_id: ProjectId) -> None:
        if project_id != self.project_id:
            raise ProjectNotFoundError


# ── Helpers ────────────────────────────────────────────────────────────────


def mkuser(role: SystemRole) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(f"trial-{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def client(
    actor: User,
    *,
    pid: ProjectId | None = None,
    repo: InMemScorerRepo | None = None,
) -> tuple[TestClient, ProjectId, InMemScorerRepo]:
    project_id = pid or ProjectId(uuid4())
    scorer_repo = repo or InMemScorerRepo()

    app = FastAPI()
    app.include_router(
        create_scorer_router(
            ScorerApiDependencies(
                service=ScorerService(
                    scorers=scorer_repo,
                    project_access=StubProjectAccess(project_id),
                    publish_versions=False,
                ),
                actor_for=StubActorFor(actor),
                settings=Settings(),
            )
        ),
        prefix="/api/v1",
    )
    c = TestClient(app, base_url="https://testserver")
    c.cookies.set("agenttest_session", "session-token")
    c.cookies.set("agenttest_csrf", "csrf-token")
    return c, project_id, scorer_repo


def create_rule_scorer(c: TestClient, pid: ProjectId, name: str = "Rule Scorer") -> str:
    csrf = {"X-CSRF-Token": "csrf-token"}
    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers",
        headers=csrf,
        json={
            "name": name,
            "scorer_type": "rule",
            "config_json": {"operator": "contains", "expected": "pass"},
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def create_reference_scorer(c: TestClient, pid: ProjectId, name: str = "Ref Scorer") -> str:
    csrf = {"X-CSRF-Token": "csrf-token"}
    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers",
        headers=csrf,
        json={
            "name": name,
            "scorer_type": "reference",
            "config_json": {"operator": "exact"},
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def create_model_scorer(c: TestClient, pid: ProjectId, name: str = "Model Scorer") -> str:
    csrf = {"X-CSRF-Token": "csrf-token"}
    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers",
        headers=csrf,
        json={
            "name": name,
            "scorer_type": "model",
            "config_json": {"rubric": "Score 1 if correct"},
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ── Tests ──────────────────────────────────────────────────────────────────


def test_rule_trial_returns_deterministic_result() -> None:
    """Rule scorer trial returns a deterministic pass/fail result."""
    c, pid, _ = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    sid = create_rule_scorer(c, pid, name="Contains Rule")

    # Should pass: output contains expected
    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers/{sid}/trial",
        headers=csrf,
        json={"output": "this should pass because pass is in here"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 1.0
    assert body["passed"] is True
    assert "passed" in body["explanation"]

    # Should fail: output does not contain expected
    r2 = c.post(
        f"/api/v1/projects/{pid.value}/scorers/{sid}/trial",
        headers=csrf,
        json={"output": "nothing here"},
    )
    assert r2.status_code == 200
    assert r2.json()["passed"] is False
    assert r2.json()["score"] == 0.0


def test_reference_trial_requires_reference() -> None:
    """Reference scorer trial returns 422 when reference is missing."""
    c, pid, _ = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    sid = create_reference_scorer(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers/{sid}/trial",
        headers=csrf,
        json={"output": "some output"},
    )
    assert r.status_code == 422


def test_reference_trial_passes_with_correct_reference() -> None:
    """Reference scorer with exact operator passes when reference matches."""
    c, pid, _ = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    sid = create_reference_scorer(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers/{sid}/trial",
        headers=csrf,
        json={"output": "hello", "reference": "hello"},
    )
    assert r.status_code == 200
    assert r.json()["passed"] is True
    assert r.json()["score"] == 1.0


def test_model_trial_without_judge_returns_503() -> None:
    """Model scorer trial returns 503 when ModelJudge runtime is absent."""
    c, pid, _ = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    sid = create_model_scorer(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers/{sid}/trial",
        headers=csrf,
        json={"output": "any output", "input": "any input"},
    )
    assert r.status_code == 503
    assert "模型评分运行时不可用" in r.json()["detail"]


def test_trial_for_non_existent_scorer_returns_404() -> None:
    """Trial for a non-existent scorer returns 404."""
    c, pid, _ = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    fake_id = uuid4()

    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers/{fake_id}/trial",
        headers=csrf,
        json={"output": "test"},
    )
    assert r.status_code == 404


def test_unsupported_scorer_type_rejected_at_create() -> None:
    """Creating a scorer with an unsupported type returns 422."""
    c, pid, _ = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}

    r = c.post(
        f"/api/v1/projects/{pid.value}/scorers",
        headers=csrf,
        json={
            "name": "Bad Scorer",
            "scorer_type": "unknown",
            "config_json": {},
        },
    )
    assert r.status_code == 422
