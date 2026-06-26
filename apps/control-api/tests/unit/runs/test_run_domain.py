from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.value_objects import RunCaseStatus, RunStatus
from agenttest.modules.test_plans.public import TestPlanVersionId


def make_run() -> Run:
    return Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=TestPlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="run-once",
        created_by=UserId.new(),
        config_snapshot={"concurrency": 4},
        plugin_snapshot={"id": "generic-http", "version": "1.0.0"},
        total_cases=2,
    )


def test_run_follows_explicit_state_machine() -> None:
    run = make_run()

    assert run.status is RunStatus.QUEUED
    run.start()
    assert run.status is RunStatus.RUNNING

    run.complete(passed_cases=2, failed_cases=0, error_cases=0)
    assert run.status is RunStatus.PASSED
    assert run.completed_at is not None

    with pytest.raises(ValueError, match="terminal"):
        run.cancel()


def test_run_distinguishes_failed_error_and_cancelled() -> None:
    failed = make_run()
    failed.start()
    failed.complete(passed_cases=1, failed_cases=1, error_cases=0)
    assert failed.status is RunStatus.FAILED

    errored = make_run()
    errored.start()
    errored.complete(passed_cases=1, failed_cases=0, error_cases=1)
    assert errored.status is RunStatus.ERROR

    cancelled = make_run()
    cancelled.start()
    cancelled.cancel()
    assert cancelled.status is RunStatus.CANCELLED


def test_run_rejects_inconsistent_case_totals() -> None:
    run = make_run()
    run.start()

    with pytest.raises(ValueError, match="case counts"):
        run.complete(passed_cases=1, failed_cases=0, error_cases=0)


def test_run_case_records_trace_and_error_classification() -> None:
    case = RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=RunId.new(),
        test_case_id=uuid4(),
        name="streaming response",
        input_snapshot={"message": "hello"},
        assertion_snapshot=[{"type": "contains", "value": "world"}],
    )
    case.start()
    case.fail(
        status=RunCaseStatus.ERROR,
        error_type="TransientError",
        error_message="upstream timed out",
        trace=[{"name": "http.request", "status": "error"}],
    )

    assert case.status is RunCaseStatus.ERROR
    assert case.error_type == "TransientError"
    assert case.trace[0]["name"] == "http.request"
    assert case.completed_at is not None


def test_run_requires_reproducible_snapshots() -> None:
    with pytest.raises(ValueError, match="idempotency_key"):
        Run.create(
            run_id=RunId.new(),
            project_id=ProjectId.new(),
            test_plan_version_id=TestPlanVersionId.new(),
            agent_version_id=uuid4(),
            dataset_version_id=uuid4(),
            idempotency_key=" ",
            created_by=UserId.new(),
            config_snapshot={},
            plugin_snapshot={},
            total_cases=1,
        )


def test_run_cannot_start_already_running() -> None:
    """已开始的运行不能重复启动。"""
    run = make_run()
    run.start()
    with pytest.raises(ValueError, match="queued"):
        run.start()


def test_run_cannot_start_completed() -> None:
    """已完成的运行不能再次启动。"""
    run = make_run()
    run.start()
    run.complete(passed_cases=2, failed_cases=0, error_cases=0)
    with pytest.raises(ValueError, match="queued"):
        run.start()


def test_run_cannot_cancel_queued() -> None:
    """QUEUED 状态的运行可以取消（尚未开始即可中止）。"""
    run = make_run()
    run.cancel()
    assert run.status is RunStatus.CANCELLED
    assert run.completed_at is not None


def test_run_case_idempotent_result_write() -> None:
    """RunCase 结果写入幂等：终态后不能重复写入。"""
    case = RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=RunId.new(),
        test_case_id=uuid4(),
        name="test case",
        input_snapshot={"x": 1},
        assertion_snapshot=[],
    )
    case.start()
    case.pass_case(output={"ok": True}, trace=[], duration_ms=100)
    with pytest.raises(ValueError, match="running"):
        case.pass_case(output={"ok": False}, trace=[], duration_ms=50)


def test_run_cancel_mid_execution() -> None:
    """运行中取消：状态转为 CANCELLED，记录完成时间。"""
    run = make_run()
    run.start()
    run.cancel()
    assert run.status is RunStatus.CANCELLED
    assert run.completed_at is not None

