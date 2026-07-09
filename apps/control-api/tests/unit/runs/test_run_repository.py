from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.infrastructure.persistence import repositories
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    SqlAlchemyRunRepository,
)
from agenttest.modules.test_plans.public import TestPlanVersionId


def make_run() -> Run:
    return Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=TestPlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="repository-order",
        created_by=UserId.new(),
        config_snapshot={"timeout": 60},
        plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
        total_cases=1,
    )


def make_case(run: Run) -> RunCase:
    return RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=uuid4(),
        name="canvas case",
        input_snapshot={"url": "https://example.test/canvas"},
        assertion_snapshot=[],
        execution_mode="codex_explore",
    )


@pytest.mark.asyncio
async def test_repository_flushes_parent_run_before_adding_cases(monkeypatch: pytest.MonkeyPatch):
    events: list[str] = []
    session = Mock()
    session.add = Mock(side_effect=lambda _model: events.append("add_run"))
    session.flush = AsyncMock(side_effect=lambda: events.append("flush_run"))
    session.add_all = Mock(side_effect=lambda _models: events.append("add_cases"))

    @asynccontextmanager
    async def fake_transaction_scope(_session_factory):
        yield session

    monkeypatch.setattr(repositories, "transaction_scope", fake_transaction_scope)
    run = make_run()
    repository = SqlAlchemyRunRepository(Mock())

    await repository.add(run, [make_case(run)])

    assert events == ["add_run", "flush_run", "add_cases"]
