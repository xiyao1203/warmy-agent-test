"""专业测试控制台向超级 Agent 暴露的受控能力目录。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.modules.datasets.public import PlatformTestCaseV1
from agenttest.modules.test_agent.application.registry import (
    Capability,
    CapabilityRegistry,
)
from agenttest.modules.test_agent.domain.entities import RiskLevel


class QueryInput(BaseModel):
    query: str | None = None


class ResourceInput(BaseModel):
    id: str


class NamedResourceInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    config: dict[str, object] = Field(default_factory=dict)


class DatasetWithCasesInput(NamedResourceInput):
    cases: list[PlatformTestCaseV1] = Field(min_length=1, max_length=500)


class TestCaseCollectionInput(BaseModel):
    dataset_version_id: UUID


class TestCaseResourceInput(BaseModel):
    case_id: UUID


class TestCaseCreateInput(TestCaseCollectionInput):
    case: PlatformTestCaseV1


class TestCaseUpdateInput(TestCaseResourceInput):
    case: PlatformTestCaseV1


class TestCaseTrialRunInput(TestCaseResourceInput):
    agent_version_id: UUID
    environment_template_id: UUID


class TestPlanVersionInput(NamedResourceInput):
    agent_version_id: str | None = None
    dataset_version_id: str | None = None
    environment_template_id: str | None = None


class RunInput(BaseModel):
    test_plan_version_id: str


class ExperimentInput(NamedResourceInput):
    baseline_run_id: str
    candidate_run_id: str


class SecurityScanInput(BaseModel):
    agent_version_id: str
    run_id: str | None = None
    security_profile_id: str | None = None


class ReviewInput(BaseModel):
    run_id: str
    confidence_threshold: float = Field(default=0.5, ge=0, le=1)


class GateEvaluationInput(BaseModel):
    gate_id: str
    run_id: str


class AnalyzeEndpointInput(BaseModel):
    agent_version_id: str
    probe_input: dict[str, object] | None = None


class AutoGenerateCasesInput(BaseModel):
    agent_version_id: str
    dataset_name: str = Field(min_length=1, max_length=200)
    scenario_hints: list[str] | None = Field(default=None, max_length=20)


class ReportInput(BaseModel):
    run_id: str


class CreateAgentVersionInput(BaseModel):
    agent_id: str
    config: dict[str, object] = Field(
        description=(
            "AgentConfig 配置字典。必填: api_url。可选: protocol (默认 sync_json), "
            'request_template (默认 {"input": "{{ input }}"}), '
            "response_path (默认 output), timeout (默认 30), "
            "credential_binding_ids (凭证绑定 ID 列表), model, system_prompt"
        )
    )


class CreateCredentialInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    username: str = Field(min_length=1, max_length=200)
    credential: str = Field(min_length=1, max_length=500)
    account_type: str = Field(default="user")
    description: str | None = Field(default=None, max_length=2000)


class MissionUpsertInput(BaseModel):
    target_url: str | None = Field(default=None, max_length=2000)
    agent_version_id: str | None = None
    browser_profile_id: str | None = None
    access_strategy: Literal["none", "browser_profile", "credential"] | None = None
    credential_binding_id: str | None = None
    test_goal: str | None = Field(default=None, max_length=4000)
    safety_scope: Literal["read_only", "draft_write"] | None = None
    scenario_hints: list[str] = Field(default_factory=list, max_length=20)


class MissionResourceInput(BaseModel):
    mission_id: str


class MissionConfirmInput(MissionResourceInput):
    revision_hash: str = Field(min_length=64, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=200)


class PlatformCapabilityGateway(Protocol):
    async def execute(
        self, capability: str, context: object, payload: BaseModel
    ) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class CapabilitySpec:
    name: str
    child_agent: str
    risk: RiskLevel
    input_model: type[BaseModel]


def capability_specs() -> list[CapabilitySpec]:
    return [
        CapabilitySpec(
            "test_missions.create_or_update", "mission", RiskLevel.READ, MissionUpsertInput
        ),
        CapabilitySpec("test_missions.discover", "mission", RiskLevel.READ, MissionResourceInput),
        CapabilitySpec("test_missions.preview", "mission", RiskLevel.READ, MissionResourceInput),
        CapabilitySpec("test_missions.get_status", "mission", RiskLevel.READ, MissionResourceInput),
        CapabilitySpec(
            "test_missions.confirm_and_start",
            "mission",
            RiskLevel.HIGH_IMPACT,
            MissionConfirmInput,
        ),
        CapabilitySpec("agents.list", "target_agent", RiskLevel.READ, QueryInput),
        CapabilitySpec("agents.create", "target_agent", RiskLevel.DRAFT_WRITE, NamedResourceInput),
        CapabilitySpec(
            "agents.publish_version", "target_agent", RiskLevel.HIGH_IMPACT, ResourceInput
        ),
        CapabilitySpec("environments.list", "environment", RiskLevel.READ, QueryInput),
        CapabilitySpec(
            "environments.create", "environment", RiskLevel.DRAFT_WRITE, NamedResourceInput
        ),
        CapabilitySpec("credentials.list", "environment", RiskLevel.READ, QueryInput),
        CapabilitySpec("credentials.validate", "environment", RiskLevel.HIGH_IMPACT, ResourceInput),
        CapabilitySpec("datasets.list", "test_data", RiskLevel.READ, QueryInput),
        CapabilitySpec("test_cases.list", "test_data", RiskLevel.READ, TestCaseCollectionInput),
        CapabilitySpec("test_cases.get", "test_data", RiskLevel.READ, TestCaseResourceInput),
        CapabilitySpec(
            "test_cases.create", "test_data", RiskLevel.DRAFT_WRITE, TestCaseCreateInput
        ),
        CapabilitySpec(
            "test_cases.update", "test_data", RiskLevel.DRAFT_WRITE, TestCaseUpdateInput
        ),
        CapabilitySpec("test_cases.validate", "test_data", RiskLevel.READ, TestCaseResourceInput),
        CapabilitySpec(
            "test_cases.mark_ready", "test_data", RiskLevel.DRAFT_WRITE, TestCaseResourceInput
        ),
        CapabilitySpec(
            "test_cases.trial_run",
            "test_data",
            RiskLevel.HIGH_IMPACT,
            TestCaseTrialRunInput,
        ),
        CapabilitySpec(
            "datasets.create_with_cases",
            "test_data",
            RiskLevel.DRAFT_WRITE,
            DatasetWithCasesInput,
        ),
        CapabilitySpec(
            "datasets.publish_version", "test_data", RiskLevel.HIGH_IMPACT, ResourceInput
        ),
        CapabilitySpec("test_plans.list", "test_plan", RiskLevel.READ, QueryInput),
        CapabilitySpec(
            "test_plans.create_version",
            "test_plan",
            RiskLevel.DRAFT_WRITE,
            TestPlanVersionInput,
        ),
        CapabilitySpec(
            "test_plans.publish_version", "test_plan", RiskLevel.HIGH_IMPACT, ResourceInput
        ),
        CapabilitySpec("runs.list", "execution", RiskLevel.READ, QueryInput),
        CapabilitySpec("runs.get_status", "execution", RiskLevel.READ, ResourceInput),
        CapabilitySpec("runs.start", "execution", RiskLevel.HIGH_IMPACT, RunInput),
        CapabilitySpec("runs.cancel", "execution", RiskLevel.HIGH_IMPACT, ResourceInput),
        CapabilitySpec("scorers.list", "evaluation", RiskLevel.READ, QueryInput),
        CapabilitySpec("scorers.create", "evaluation", RiskLevel.DRAFT_WRITE, NamedResourceInput),
        CapabilitySpec("experiments.list", "experiment", RiskLevel.READ, QueryInput),
        CapabilitySpec("experiments.create", "experiment", RiskLevel.DRAFT_WRITE, ExperimentInput),
        CapabilitySpec("security_scans.list", "security", RiskLevel.READ, QueryInput),
        CapabilitySpec(
            "security_scans.start", "security", RiskLevel.HIGH_IMPACT, SecurityScanInput
        ),
        CapabilitySpec("reviews.list", "review_gate", RiskLevel.READ, QueryInput),
        CapabilitySpec("reviews.enqueue", "review_gate", RiskLevel.HIGH_IMPACT, ReviewInput),
        CapabilitySpec("release_gates.list", "review_gate", RiskLevel.READ, QueryInput),
        CapabilitySpec(
            "release_gates.evaluate",
            "review_gate",
            RiskLevel.HIGH_IMPACT,
            GateEvaluationInput,
        ),
        CapabilitySpec(
            "agents.analyze_endpoint", "target_agent", RiskLevel.READ, AnalyzeEndpointInput
        ),
        CapabilitySpec(
            "datasets.auto_generate_cases",
            "test_data",
            RiskLevel.DRAFT_WRITE,
            AutoGenerateCasesInput,
        ),
        CapabilitySpec("reports.generate", "execution", RiskLevel.READ, ReportInput),
        CapabilitySpec(
            "agents.create_version",
            "target_agent",
            RiskLevel.DRAFT_WRITE,
            CreateAgentVersionInput,
        ),
        CapabilitySpec(
            "credentials.create",
            "environment",
            RiskLevel.DRAFT_WRITE,
            CreateCredentialInput,
        ),
    ]


def build_platform_registry(gateway: PlatformCapabilityGateway) -> CapabilityRegistry:
    registry = CapabilityRegistry()
    for spec in capability_specs():

        async def execute(context, payload, *, name=spec.name):
            return await gateway.execute(name, context, payload)

        registry.register(
            Capability(
                name=spec.name,
                version="1",
                child_agent=spec.child_agent,
                risk=spec.risk,
                input_model=spec.input_model,
                execute=execute,
            )
        )
    return registry
