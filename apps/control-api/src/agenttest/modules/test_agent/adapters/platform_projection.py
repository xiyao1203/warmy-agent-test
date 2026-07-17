"""超级 Agent 到专业控制台公开应用能力的适配层。"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from agenttest.modules.agents.public import (
    AgentVersionId,
)
from agenttest.modules.datasets.public import (
    AddTestCaseCommand,
    DatasetVersionId,
    PlatformTestCaseV1,
    TestCaseId,
    TestCaseSource,
    UpdateTestCaseCommand,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.test_plans.public import (
    EnvironmentTemplateId,
)
from agenttest.shared.application.resource_reference import (
    ResourceReference,
    ResourceType,
)


def _artifact(kind: str, value: UUID, relation: str = "created") -> dict[str, str]:
    return {"type": kind, "id": str(value), "relation": relation}


def _created(kind, value, payload, relation="created"):
    return {**payload, "artifacts": [_artifact(kind, value, relation)]}


def _resource_ref(
    resource_type: ResourceType,
    resource_id: UUID,
    project_id: UUID,
    name: str,
    *,
    status: str | None = None,
) -> ResourceReference:
    return ResourceReference.build(
        resource_type=resource_type,
        resource_id=resource_id,
        project_id=project_id,
        name=name,
        status=status,
    )


def _summary_item(
    payload: dict[str, object],
    summary: BaseModel | None,
    resource_ref: ResourceReference,
) -> dict[str, object]:
    result = dict(payload)
    if summary is not None:
        result.update(summary.model_dump(mode="json"))
    result["resource_ref"] = resource_ref.model_dump(mode="json")
    return result


def _test_case_result(item, project_id: UUID) -> dict[str, object]:
    return _summary_item(
        _test_case(item),
        None,
        _resource_ref(
            ResourceType.TEST_CASE,
            item.case_id.value,
            project_id,
            item.name,
        ),
    )


def _case_trial_fallback_key(context, values, updated_at) -> str:
    updated = updated_at.isoformat() if updated_at else "unknown"
    return (
        f"agent-trial:{context.session_id}:{values['case_id']}:"
        f"{values['agent_version_id']}:{values['environment_template_id']}:{updated}"
    )[:200]


def _optional(value: Any) -> str | None:
    return str(value) if value else None


def _test_case_command_from_raw(
    *,
    dataset_version_id: DatasetVersionId,
    raw: dict[str, object],
    fallback_name: str,
    fallback_input: dict[str, object] | None,
    default_execution_mode: str,
    source_ref: str = "agent-generated",
) -> AddTestCaseCommand:
    case_input = _dict_value(raw.get("input")) or fallback_input
    if not case_input:
        raise ValueError(f"Test case {fallback_name} input is required")
    payload = dict(raw)
    payload["name"] = str(raw.get("name") or fallback_name)
    payload["objective"] = str(raw.get("objective") or payload["name"])
    payload["input"] = case_input
    payload["execution_mode"] = str(raw.get("execution_mode") or default_execution_mode)
    payload["source"] = TestCaseSource.AGENT_GENERATED
    contract = PlatformTestCaseV1.model_validate(payload)
    return _test_case_command_from_contract(
        dataset_version_id=dataset_version_id,
        contract=contract,
        source_ref=source_ref,
    )


def _test_case_command_from_contract(
    *,
    dataset_version_id: DatasetVersionId,
    contract: PlatformTestCaseV1,
    source_ref: str,
) -> AddTestCaseCommand:
    fields = _test_case_command_fields(contract)
    return AddTestCaseCommand(
        dataset_version_id=dataset_version_id,
        source=TestCaseSource.AGENT_GENERATED,
        source_ref=source_ref,
        **fields,
    )


def _test_case_update_command(
    case_id: TestCaseId,
    contract: PlatformTestCaseV1,
) -> UpdateTestCaseCommand:
    return UpdateTestCaseCommand(
        case_id=case_id,
        source_ref=contract.source_ref or "agent-updated",
        **_test_case_command_fields(contract),
    )


def _test_case_command_fields(contract: PlatformTestCaseV1) -> dict[str, Any]:
    return {
        "name": contract.name,
        "objective": contract.objective,
        "template": contract.template,
        "case_type": contract.case_type,
        "automation_status": contract.automation_status,
        "component": contract.component,
        "requirement_refs": contract.requirement_refs,
        "owner_id": UserId(contract.owner_id) if contract.owner_id else None,
        "preconditions": contract.preconditions,
        "input": contract.input,
        "data_bindings": [item.model_dump(mode="json") for item in contract.data_bindings],
        "steps": [item.model_dump(mode="json") for item in contract.steps],
        "execution_mode": contract.execution_mode,
        "assertions": contract.assertions,
        "scorers": contract.scorers,
        "initial_state": contract.initial_state,
        "expected_outcome": contract.expected_outcome,
        "security_policies": contract.security_policies,
        "artifact_requirements": [
            item.model_dump(mode="json") for item in contract.artifact_requirements
        ],
        "postconditions": contract.postconditions,
        "estimated_duration_seconds": contract.estimated_duration_seconds,
        "timeout_seconds": contract.timeout_seconds,
        "retry_count": contract.retry_count,
        "custom_fields": contract.custom_fields,
        "tags": contract.tags,
        "scenario": contract.scenario,
        "priority": contract.priority,
        "risk_level": contract.risk_level,
        "difficulty": contract.difficulty,
        "test_group": contract.test_group,
    }


def _dict_value(value: object) -> dict[str, object] | None:
    return dict(value) if isinstance(value, dict) else None


def _agent_version(value: Any):
    return AgentVersionId(UUID(str(value))) if value else None


def _dataset_version(value: Any):
    return DatasetVersionId(UUID(str(value))) if value else None


def _environment_id(value: Any):
    return EnvironmentTemplateId(UUID(str(value))) if value else None


def _agent(item):
    return {"id": str(item.agent_id.value), "name": item.name, "type": item.agent_type.value}


def _environment(item):
    return {"id": str(item.template_id.value), "name": item.name, "type": item.template_type.value}


def _dataset(item):
    return {"id": str(item.dataset_id.value), "name": item.name}


def _test_case(item):
    return {
        "id": str(item.case_id.value),
        "dataset_version_id": str(item.dataset_version_id.value),
        "case_key": item.case_key,
        "name": item.name,
        "objective": item.objective,
        "case_status": item.case_status.value,
        "template": item.template.value,
        "case_type": item.case_type.value,
        "automation_status": item.automation_status.value,
        "source": item.source.value,
        "source_ref": item.source_ref,
        "component": item.component,
        "requirement_refs": item.requirement_refs,
        "owner_id": str(item.owner_id.value) if item.owner_id else None,
        "preconditions": item.preconditions,
        "initial_state": item.initial_state,
        "input": item.input,
        "data_bindings": item.data_bindings,
        "steps": item.steps,
        "expected_outcome": item.expected_outcome,
        "assertions": item.assertions,
        "scorers": item.scorers,
        "security_policies": item.security_policies,
        "artifact_requirements": item.artifact_requirements,
        "postconditions": item.postconditions,
        "estimated_duration_seconds": item.estimated_duration_seconds,
        "execution_mode": item.execution_mode.value,
        "timeout_seconds": item.timeout_seconds,
        "retry_count": item.retry_count,
        "custom_fields": item.custom_fields,
        "tags": item.tags,
        "scenario": item.scenario,
        "priority": item.priority.value if item.priority else None,
        "risk_level": item.risk_level.value if item.risk_level else None,
        "difficulty": item.difficulty,
        "test_group": item.test_group.value if item.test_group else None,
    }


def _plan(item):
    return {"id": str(item.test_plan_id.value), "name": item.name}


def _run(item):
    return {
        "id": str(item.run_id.value),
        "status": item.status.value,
        "total_cases": item.total_cases,
    }


def _scorer(item):
    return {"id": str(item.scorer_id.value), "name": item.name, "type": item.scorer_type.value}


def _experiment(item):
    return {"id": str(item.experiment_id.value), "name": item.name, "status": item.status.value}


def _security_scan(item):
    return {"id": str(item.scan_id), "status": item.status.value, "summary": item.summary}


def _review(item):
    return {
        "id": str(item.task_id.value),
        "status": item.status.value,
        "confidence": item.confidence,
    }


def _gate(item):
    return {"id": str(item.gate_id.value), "name": item.name, "enabled": item.enabled}


def _serializable(value: object) -> object:
    """Convert a value to JSON-serializable form for safe inclusion in capability results."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, dict):
        return {str(k): _serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable(v) for v in value]
    if isinstance(value, UUID):
        return str(value)
    return str(value)[:500]


def _infer_json_schema(value: object) -> dict[str, object]:
    """Infer a simple JSON schema from a parsed value for LLM consumption."""
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {str(k): _infer_json_schema(v) for k, v in value.items()},
            "sample_keys": [str(k) for k in value.keys()][:20],
        }
    if isinstance(value, list):
        items = [_infer_json_schema(v) for v in value[:3]]
        return {"type": "array", "length": len(value), "sample_items": items}
    if isinstance(value, str):
        return {"type": "string", "max_length": min(len(value), 500)}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    return {"type": "null"}
