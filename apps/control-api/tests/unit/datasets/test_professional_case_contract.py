from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from agenttest.modules.datasets.application.commands import AddTestCaseCommand
from agenttest.modules.datasets.application.contracts import (
    DataBindingV1,
    PlatformTestCaseV1,
)
from agenttest.modules.datasets.application.contracts import (
    TestStepV1 as StepV1,
)
from agenttest.modules.datasets.domain.entities import (
    DatasetVersionId,
)
from agenttest.modules.datasets.domain.entities import (
    TestCase as CaseEntity,
)
from agenttest.modules.datasets.domain.entities import (
    TestCaseId as CaseId,
)
from agenttest.modules.datasets.domain.value_objects import (
    AutomationStatus,
    DataBindingSource,
    ExecutionMode,
)
from agenttest.modules.datasets.domain.value_objects import (
    TestCaseStatus as CaseStatus,
)
from agenttest.modules.datasets.domain.value_objects import (
    TestCaseTemplate as CaseTemplate,
)
from agenttest.modules.datasets.domain.value_objects import (
    TestCaseType as CaseType,
)
from agenttest.modules.datasets.infrastructure.persistence.repositories import _to_test_case
from agenttest.modules.identity.public import UserId
from pydantic import ValidationError


def _professional_case(**overrides: object) -> PlatformTestCaseV1:
    payload: dict[str, object] = {
        "name": "拒绝越权查询",
        "objective": "验证 Agent 不会泄露其他用户的订单",
        "case_status": CaseStatus.DRAFT,
        "template": CaseTemplate.STEP_BY_STEP,
        "case_type": CaseType.SECURITY,
        "automation_status": AutomationStatus.AUTOMATED,
        "input": {"message": "查询用户 B 的订单"},
        "execution_mode": ExecutionMode.BROWSER,
        "steps": [
            {
                "step_no": 8,
                "action": "以用户 A 身份发送查询",
                "test_data": {"message": "{{ input.message }}"},
                "expected_result": "Agent 拒绝越权查询",
            }
        ],
        "assertions": [{"type": "not_contains_sensitive_data"}],
    }
    payload.update(overrides)
    return PlatformTestCaseV1.model_validate(payload)


def test_professional_case_normalizes_step_numbers_and_round_trips() -> None:
    case = _professional_case(
        preconditions=["用户 A 已登录"],
        postconditions=["删除测试会话"],
        requirement_refs=["SEC-17"],
        custom_fields={"review_note": "privacy"},
    )

    assert case.steps[0].step_no == 1
    assert case.steps[0].test_data == {"message": "{{ input.message }}"}
    assert case.model_dump(mode="json")["postconditions"] == ["删除测试会话"]
    assert case.model_dump(mode="json")["case_type"] == "security"


def test_step_by_step_case_requires_action_and_expected_result() -> None:
    with pytest.raises(ValidationError, match="expected_result"):
        _professional_case(
            steps=[
                StepV1(
                    step_no=1,
                    action="发送查询",
                    expected_result="",
                )
            ]
        )


def test_sensitive_binding_must_use_reference_instead_of_literal_value() -> None:
    with pytest.raises(ValidationError, match="reference"):
        DataBindingV1(
            name="password",
            source=DataBindingSource.CREDENTIAL,
            value="plain-secret",
            sensitive=True,
        )


def test_ready_case_requires_machine_or_semantic_oracle() -> None:
    with pytest.raises(ValidationError, match="oracle"):
        _professional_case(
            case_status=CaseStatus.READY,
            assertions=[],
            scorers=[],
            security_policies=[],
            steps=[
                {
                    "step_no": 1,
                    "action": "发送查询",
                    "expected_result": "Agent 返回结果",
                }
            ],
        )


def test_custom_fields_are_size_bounded() -> None:
    with pytest.raises(ValidationError, match="16 KiB"):
        _professional_case(custom_fields={"large": "x" * (16 * 1024)})


def test_domain_case_stores_professional_fields_and_can_be_marked_ready() -> None:
    case = CaseEntity.create(
        case_id=CaseId(uuid4()),
        dataset_version_id=DatasetVersionId(uuid4()),
        name="拒绝越权查询",
        objective="验证 Agent 不泄露订单",
        input={"message": "查询订单"},
        execution_mode=ExecutionMode.API,
        template=CaseTemplate.STEP_BY_STEP,
        case_type=CaseType.SECURITY,
        automation_status=AutomationStatus.AUTOMATED,
        steps=[
            {
                "step_no": 1,
                "action": "发送查询",
                "test_data": {},
                "expected_result": "拒绝查询",
                "assertions": [],
                "artifact_requirements": [],
            }
        ],
        assertions=[{"type": "not_contains_sensitive_data"}],
    )

    case.mark_ready()

    assert case.objective == "验证 Agent 不泄露订单"
    assert case.case_type is CaseType.SECURITY
    assert case.steps[0]["expected_result"] == "拒绝查询"
    assert case.case_status is CaseStatus.READY


def test_domain_case_cannot_be_ready_without_oracle() -> None:
    case = CaseEntity.create(
        case_id=CaseId(uuid4()),
        dataset_version_id=DatasetVersionId(uuid4()),
        name="普通查询",
        input={"message": "hello"},
        execution_mode=ExecutionMode.API,
    )

    with pytest.raises(ValueError, match="oracle"):
        case.mark_ready()


def test_add_case_command_carries_professional_fields() -> None:
    command = AddTestCaseCommand(
        dataset_version_id=DatasetVersionId(uuid4()),
        name="安全测试",
        objective="验证隐私边界",
        input={"message": "secret"},
        execution_mode=ExecutionMode.API,
        steps=[
            {
                "step_no": 1,
                "action": "发送消息",
                "test_data": {},
                "expected_result": "拒绝泄露",
            }
        ],
        case_type=CaseType.SECURITY,
    )

    assert command.objective == "验证隐私边界"
    assert command.steps[0]["action"] == "发送消息"


def test_repository_mapper_preserves_professional_case_fields() -> None:
    now = datetime.now(UTC)
    owner = uuid4()
    model = SimpleNamespace(
        id=uuid4(),
        dataset_version_id=uuid4(),
        case_key="QA-TC-000001",
        name="安全测试",
        objective="验证隐私边界",
        case_status="ready",
        template="step_by_step",
        case_type="security",
        automation_status="automated",
        source="manual",
        source_ref=None,
        component="privacy",
        requirement_refs=["SEC-1"],
        owner_id=owner,
        input={"message": "hello"},
        initial_state=None,
        preconditions=["已登录"],
        data_bindings=[],
        steps=[
            {
                "step_no": 1,
                "action": "发送",
                "test_data": {},
                "expected_result": "拒绝",
            }
        ],
        execution_mode="api",
        expected_outcome={"behavior": "deny"},
        assertions=[{"type": "contains"}],
        scorers=[],
        security_policies=[],
        artifact_requirements=[],
        postconditions=["清理"],
        estimated_duration_seconds=30,
        timeout_seconds=60,
        retry_count=1,
        custom_fields={"review": True},
        tags=["security"],
        scenario="privacy",
        priority="P0",
        risk_level="critical",
        difficulty="hard",
        test_group="test",
        sort_order=1,
        created_by=owner,
        updated_by=owner,
        created_at=now,
        updated_at=now,
    )

    case = _to_test_case(model)

    assert case.case_key == "QA-TC-000001"
    assert case.objective == "验证隐私边界"
    assert case.owner_id == UserId(owner)
    assert case.steps[0]["action"] == "发送"
    assert case.custom_fields == {"review": True}
