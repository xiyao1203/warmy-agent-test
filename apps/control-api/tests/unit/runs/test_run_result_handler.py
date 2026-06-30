from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.commands import (
    ApplyRunCaseResult,
    ApplyRunResultCommand,
    ApplyRunResultHandler,
    RunNotFoundError,
)
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.value_objects import RunCaseStatus, RunStatus
from agenttest.modules.test_plans.public import TestPlanVersionId


class InMemoryRunRepository:
    def __init__(self, run: Run, cases: list[RunCase]) -> None:
        self.run = run
        self.cases = cases
        self.saved_results = 0

    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None:
        if self.run.project_id == project_id and self.run.run_id == run_id:
            return self.run
        return None

    async def get_by_idempotency_key(
        self,
        project_id: ProjectId,
        key: str,
    ) -> Run | None:
        if self.run.project_id == project_id and self.run.idempotency_key == key:
            return self.run
        return None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
    ) -> list[Run]:
        if self.run.project_id == project_id:
            return [self.run][:limit]
        return []

    async def add(self, run: Run, cases: list[RunCase]) -> None:
        self.run = run
        self.cases = cases

    async def save(self, run: Run) -> None:
        self.run = run

    async def save_result(self, run: Run, cases: list[RunCase]) -> None:
        self.saved_results += 1
        self.run = run
        self.cases = cases

    async def list_cases(self, project_id: ProjectId, run_id: RunId) -> list[RunCase]:
        if self.run.project_id == project_id and self.run.run_id == run_id:
            return self.cases
        return []


def make_run_with_cases() -> tuple[Run, list[RunCase]]:
    run = Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=TestPlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="result-once",
        created_by=UserId.new(),
        config_snapshot={"concurrency": 2},
        plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
        total_cases=2,
    )
    run.start("workflow-1")
    cases = [
        RunCase.create(
            run_case_id=RunCaseId.new(),
            run_id=run.run_id,
            test_case_id=uuid4(),
            name="case passes",
            input_snapshot={"prompt": "hello"},
            assertion_snapshot=[],
        ),
        RunCase.create(
            run_case_id=RunCaseId.new(),
            run_id=run.run_id,
            test_case_id=uuid4(),
            name="case fails",
            input_snapshot={"prompt": "bye"},
            assertion_snapshot=[],
        ),
    ]
    return run, cases


@pytest.mark.asyncio
async def test_apply_run_result_updates_cases_and_aggregates_status() -> None:
    run, cases = make_run_with_cases()
    repo = InMemoryRunRepository(run, cases)
    handler = ApplyRunResultHandler(runs=repo)

    updated = await handler.execute(
        ApplyRunResultCommand(
            project_id=run.project_id,
            run_id=run.run_id,
            cases=[
                ApplyRunCaseResult(
                    run_case_id=cases[0].run_case_id,
                    status=RunCaseStatus.PASSED,
                    output={"answer": "hello world"},
                    trace=[{"name": "http.request", "status": "ok"}],
                    duration_ms=25,
                ),
                ApplyRunCaseResult(
                    run_case_id=cases[1].run_case_id,
                    status=RunCaseStatus.FAILED,
                    error_type="AssertionError",
                    error_message="missing expected text",
                    trace=[{"name": "assert.contains", "status": "failed"}],
                    duration_ms=18,
                ),
            ],
        )
    )

    assert updated.status is RunStatus.FAILED
    assert updated.passed_cases == 1
    assert updated.failed_cases == 1
    assert cases[0].status is RunCaseStatus.PASSED
    assert cases[0].output == {"answer": "hello world"}
    assert cases[1].status is RunCaseStatus.FAILED
    assert cases[1].error_type == "AssertionError"
    assert cases[1].duration_ms == 18


@pytest.mark.asyncio
async def test_apply_run_result_is_idempotent_after_terminal_run() -> None:
    run, cases = make_run_with_cases()
    repo = InMemoryRunRepository(run, cases)
    handler = ApplyRunResultHandler(runs=repo)
    command = ApplyRunResultCommand(
        project_id=run.project_id,
        run_id=run.run_id,
        cases=[
            ApplyRunCaseResult(
                run_case_id=case.run_case_id,
                status=RunCaseStatus.PASSED,
                output={"ok": True},
                trace=[],
                duration_ms=1,
            )
            for case in cases
        ],
    )

    first = await handler.execute(command)
    second = await handler.execute(command)

    assert first.status is RunStatus.PASSED
    assert second.status is RunStatus.PASSED
    assert repo.saved_results == 1


@pytest.mark.asyncio
async def test_apply_run_result_rejects_unknown_case() -> None:
    run, cases = make_run_with_cases()
    repo = InMemoryRunRepository(run, cases)
    handler = ApplyRunResultHandler(runs=repo)

    with pytest.raises(ValueError, match="Unknown run case"):
        await handler.execute(
            ApplyRunResultCommand(
                project_id=run.project_id,
                run_id=run.run_id,
                cases=[
                    ApplyRunCaseResult(
                        run_case_id=RunCaseId.new(),
                        status=RunCaseStatus.PASSED,
                        output={},
                        trace=[],
                        duration_ms=1,
                    ),
                    ApplyRunCaseResult(
                        run_case_id=cases[1].run_case_id,
                        status=RunCaseStatus.PASSED,
                        output={},
                        trace=[],
                        duration_ms=1,
                    ),
                ],
            )
        )


@pytest.mark.asyncio
async def test_apply_run_result_requires_existing_run() -> None:
    run, cases = make_run_with_cases()
    repo = InMemoryRunRepository(run, cases)
    handler = ApplyRunResultHandler(runs=repo)

    with pytest.raises(RunNotFoundError):
        await handler.execute(
            ApplyRunResultCommand(
                project_id=ProjectId.new(),
                run_id=run.run_id,
                cases=[],
            )
        )
