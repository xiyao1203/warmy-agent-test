from uuid import uuid4

import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.run_postprocessing.snapshot_reader import RunPostprocessSnapshotReader
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.outcomes import Outcome, RunCaseOutcomes
from agenttest.modules.runs.domain.value_objects import RunCaseStatus
from agenttest.modules.test_plans.public import TestPlanVersionId


class Runs:
    def __init__(self, run: Run, case: RunCase) -> None:
        self.run = run
        self.case = case

    async def get_by_id(self, project_id, run_id):
        return self.run if project_id == self.run.project_id and run_id == self.run.run_id else None

    async def list_cases(self, project_id, run_id):
        return [self.case]


@pytest.mark.asyncio
async def test_snapshot_reader_projects_only_sanitized_evidence_and_outcome_code() -> None:
    run = Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=TestPlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key="snapshot",
        created_by=UserId.new(),
        config_snapshot={"timeout": 30},
        plugin_snapshot={"id": "generic-http"},
        total_cases=1,
    )
    case = RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=uuid4(),
        name="failure",
        input_snapshot={"prompt": "hello"},
        assertion_snapshot=[],
    )
    case.start()
    case.fail(
        status=RunCaseStatus.FAILED,
        error_type="AssertionError",
        error_message="mismatch",
        trace=[{"name": "http.request"}],
        duration_ms=1,
    )
    case.evidence = {"token": "must-not-leak", "execution_outcome": "success"}
    evidence_id = uuid4()
    case.outcomes = RunCaseOutcomes(
        execution=Outcome.passed(),
        assertion=Outcome.failed("assertion_mismatch", evidence_ids=(evidence_id,)),
        quality=Outcome.passed(),
        security=Outcome.passed(),
    )

    snapshot = await RunPostprocessSnapshotReader(Runs(run, case)).load(
        run.project_id.value, run.run_id.value
    )

    projected = snapshot.cases[0]
    assert projected.error_code == "assertion_mismatch"
    assert projected.tool_chain == ("http.request",)
    assert "must-not-leak" not in repr(projected.evidence_view)
