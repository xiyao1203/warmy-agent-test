from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.datasets.application.commands import AddTestCaseCommand
from agenttest.modules.datasets.application.generate_from_run import (
    GenerateCasesFromFailedRunHandler,
    GenerateFromRunCommand,
)
from agenttest.modules.datasets.domain.entities import (
    DatasetVersionId,
)
from agenttest.modules.datasets.domain.entities import (
    TestCase as DatasetCase,
)
from agenttest.modules.datasets.domain.entities import (
    TestCaseId as DatasetCaseId,
)
from agenttest.modules.datasets.domain.value_objects import (
    AutomationStatus,
    ExecutionMode,
)
from agenttest.modules.datasets.domain.value_objects import (
    TestCaseSource as CaseSource,
)
from agenttest.modules.datasets.domain.value_objects import (
    TestCaseTemplate as CaseTemplate,
)
from agenttest.modules.datasets.domain.value_objects import (
    TestCaseType as CaseType,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.public import Run, RunCase, RunCaseId, RunCaseStatus, RunId
from agenttest.modules.test_plans.public import TestPlanVersionId as PlanVersionId


class StubRuns:
    def __init__(self, run: Run, cases: list[RunCase]) -> None:
        self.run = run
        self.cases = cases

    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None:
        return self.run if (project_id, run_id) == (self.run.project_id, self.run.run_id) else None

    async def list_cases(self, project_id: ProjectId, run_id: RunId) -> list[RunCase]:
        return self.cases if (project_id, run_id) == (self.run.project_id, self.run.run_id) else []


class StubCases:
    def __init__(self, source: DatasetCase) -> None:
        self.source = source
        self.existing: list[DatasetCase] = []

    async def get_by_id(self, case_id: DatasetCaseId) -> DatasetCase | None:
        return self.source if case_id == self.source.case_id else None

    async def list_by_version(
        self,
        dataset_version_id: DatasetVersionId,
        *,
        limit: int = 200,
        cursor: str | None = None,
    ) -> tuple[list[DatasetCase], str | None]:
        del dataset_version_id, limit, cursor
        return self.existing, None


class StubAddCase:
    def __init__(self, cases: StubCases) -> None:
        self.cases = cases

    async def execute(self, actor: User, command: AddTestCaseCommand) -> DatasetCase:
        del actor
        case = DatasetCase.create(
            case_id=DatasetCaseId.new(),
            dataset_version_id=command.dataset_version_id,
            name=command.name,
            input=command.input,
            execution_mode=command.execution_mode,
            assertions=command.assertions,
            scorers=command.scorers,
            objective=command.objective,
            template=command.template,
            case_type=command.case_type,
            automation_status=command.automation_status,
            source=command.source,
            source_ref=command.source_ref,
            component=command.component,
            requirement_refs=command.requirement_refs,
            owner_id=command.owner_id,
            preconditions=command.preconditions,
            data_bindings=command.data_bindings,
            steps=command.steps,
            expected_outcome=command.expected_outcome,
            security_policies=command.security_policies,
            artifact_requirements=command.artifact_requirements,
            postconditions=command.postconditions,
            estimated_duration_seconds=command.estimated_duration_seconds,
            timeout_seconds=command.timeout_seconds,
            retry_count=command.retry_count,
            custom_fields=command.custom_fields,
            tags=command.tags,
        )
        self.cases.existing.append(case)
        return case


@pytest.mark.asyncio
async def test_generates_only_failed_cases_and_persists_real_input() -> None:
    actor = User.create(
        user_id=UserId.new(),
        email=Email("dataset@example.com"),
        display_name="Dataset Developer",
        role=SystemRole.DEVELOPER,
    )
    source = DatasetCase.create(
        case_id=DatasetCaseId.new(),
        dataset_version_id=DatasetVersionId.new(),
        name="source",
        input={"prompt": "source"},
        execution_mode=ExecutionMode.BROWSER,
        assertions=[],
        scorers=[],
        objective="验证结账完成并显示收据",
        template=CaseTemplate.STEP_BY_STEP,
        case_type=CaseType.E2E,
        automation_status=AutomationStatus.AUTOMATED,
        component="checkout",
        requirement_refs=["ORDER-17"],
        preconditions=["购物车中存在商品"],
        data_bindings=[{"name": "account", "source": "fixture", "reference": "user-a"}],
        steps=[
            {
                "step_no": 1,
                "action": "提交订单",
                "test_data": {},
                "expected_result": "显示收据",
                "assertions": [],
                "artifact_requirements": [],
            }
        ],
        expected_outcome={"receipt": "visible"},
        artifact_requirements=[{"kind": "screenshot", "required": True}],
        postconditions=["清理订单"],
        timeout_seconds=90,
    )
    run = Run.create(
        run_id=RunId.new(),
        project_id=ProjectId.new(),
        test_plan_version_id=PlanVersionId.new(),
        agent_version_id=uuid4(),
        dataset_version_id=source.dataset_version_id.value,
        idempotency_key="generate-regression",
        created_by=actor.user_id,
        config_snapshot={"concurrency": 1},
        plugin_snapshot={"id": "web", "version": "1"},
        total_cases=1,
    )
    failed = RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=source.case_id.value,
        name="checkout fails",
        input_snapshot={"url": "https://target.test/checkout"},
        assertion_snapshot=[{"type": "visible", "target": "receipt"}],
    )
    failed.start()
    failed.fail(
        status=RunCaseStatus.FAILED,
        error_type="AssertionError",
        error_message="receipt missing",
        trace=[],
    )
    cases = StubCases(source)
    handler = GenerateCasesFromFailedRunHandler(
        runs=StubRuns(run, [failed]),
        cases=cases,
        add_case=StubAddCase(cases),
    )

    result = await handler.execute(
        actor=actor,
        project_id=run.project_id,
        command=GenerateFromRunCommand(
            run_id=run.run_id.value,
            dataset_version_id=uuid4(),
        ),
    )

    assert result.total_failed == 1
    assert result.skipped_existing == 0
    assert result.generated_cases[0].input == failed.input_snapshot
    assert result.generated_cases[0].execution_mode is ExecutionMode.BROWSER
    generated = result.generated_cases[0]
    assert generated.source is CaseSource.RUN_REGRESSION
    assert generated.source_ref == str(run.run_id.value)
    assert generated.objective == "回归失败：receipt missing"
    assert generated.template is CaseTemplate.STEP_BY_STEP
    assert generated.steps == source.steps
    assert generated.expected_outcome == source.expected_outcome
    assert generated.assertions == failed.assertion_snapshot
    assert generated.artifact_requirements == source.artifact_requirements
    assert generated.postconditions == source.postconditions
