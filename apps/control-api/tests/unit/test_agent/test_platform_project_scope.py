from types import SimpleNamespace
from uuid import uuid4

import pytest
from agenttest.modules.datasets.public import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
    ExecutionMode,
    PlatformTestCaseV1,
)
from agenttest.modules.datasets.public import (
    TestCase as DatasetCase,
)
from agenttest.modules.datasets.public import (
    TestCaseId as DatasetCaseId,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.adapters.platform import HandlerPlatformGateway
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.modules.test_agent.application.platform_catalog import (
    TestCaseCollectionInput as CaseCollectionInput,
)
from agenttest.modules.test_agent.application.platform_catalog import (
    TestCaseCreateInput as CaseCreateInput,
)
from agenttest.modules.test_agent.application.platform_catalog import (
    TestCaseResourceInput as CaseResourceInput,
)
from agenttest.modules.test_agent.application.platform_catalog import (
    TestCaseTrialRunInput as CaseTrialRunInput,
)
from agenttest.modules.test_agent.application.platform_catalog import (
    TestCaseUpdateInput as CaseUpdateInput,
)


class Executor:
    def __init__(self, result) -> None:
        self.result = result
        self.calls = 0

    async def execute(self, *_args, **_kwargs):
        self.calls += 1
        return self.result


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("multi-project@example.test"),
        display_name="Multi Project",
        role=SystemRole.DEVELOPER,
    )


def professional_contract() -> PlatformTestCaseV1:
    return PlatformTestCaseV1(
        name="跨项目用例",
        objective="必须被当前 Agent 项目拒绝",
        input={"message": "hello"},
        execution_mode=ExecutionMode.API,
        assertions=[{"type": "contains", "value": "hello"}],
    )


def gateway_for_foreign_case():
    foreign_project = ProjectId.new()
    owner = UserId.new()
    dataset = Dataset.create(
        dataset_id=DatasetId.new(),
        project_id=foreign_project,
        name="Foreign",
        created_by=owner,
    )
    version = DatasetVersion.create_draft(
        version_id=DatasetVersionId.new(),
        dataset_id=dataset.dataset_id,
        version_number=1,
        created_by=owner,
    )
    case = DatasetCase.create(
        case_id=DatasetCaseId.new(),
        dataset_version_id=version.version_id,
        name="Foreign case",
        objective="Foreign project",
        input={"message": "hello"},
        execution_mode=ExecutionMode.API,
        assertions=[{"type": "contains", "value": "hello"}],
        created_by=owner,
    )
    datasets = SimpleNamespace(
        get_dataset=Executor(dataset),
        get_version=Executor(version),
        get_case=Executor(case),
        list_cases=Executor(([case], None)),
        add_case=Executor(case),
        update_case=Executor(case),
        mark_case_ready=Executor(case),
        trial_run=Executor(SimpleNamespace(run=None)),
    )
    gateway = HandlerPlatformGateway(
        agents=None,
        datasets=datasets,
        environments=None,
        plans=None,
        runs=None,
        scorers=None,
        experiments=None,
        reviews=None,
        gates=None,
        security=None,
        accounts=None,
        promptfoo_bin="promptfoo",
        allow_private_security_targets=False,
        gate_evidence=None,
    )
    return gateway, datasets, version, case


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("capability", "payload"),
    [
        (
            "test_cases.list",
            lambda version, case: CaseCollectionInput(dataset_version_id=version.version_id.value),
        ),
        ("test_cases.get", lambda version, case: CaseResourceInput(case_id=case.case_id.value)),
        (
            "test_cases.create",
            lambda version, case: CaseCreateInput(
                dataset_version_id=version.version_id.value, case=professional_contract()
            ),
        ),
        (
            "test_cases.update",
            lambda version, case: CaseUpdateInput(
                case_id=case.case_id.value, case=professional_contract()
            ),
        ),
        (
            "test_cases.validate",
            lambda version, case: CaseResourceInput(case_id=case.case_id.value),
        ),
        (
            "test_cases.mark_ready",
            lambda version, case: CaseResourceInput(case_id=case.case_id.value),
        ),
        (
            "test_cases.trial_run",
            lambda version, case: CaseTrialRunInput(
                case_id=case.case_id.value,
                agent_version_id=uuid4(),
                environment_template_id=uuid4(),
            ),
        ),
    ],
)
async def test_case_capabilities_reject_resources_from_another_context_project(
    capability,
    payload,
) -> None:
    gateway, _, version, case = gateway_for_foreign_case()
    context = OrchestrationContext(actor(), ProjectId.new(), uuid4())

    with pytest.raises(ValueError, match="current project"):
        await gateway.execute(capability, context, payload(version, case))
