"""专业测试控制台向超级 Agent 暴露的受控能力目录。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, Field

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


class TestCaseDraftInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    input: dict[str, object]
    execution_mode: Literal["api", "browser"] = Field(default="api")
    assertions: list[dict[str, object]] = Field(default_factory=list)
    scorers: list[dict[str, object]] = Field(default_factory=list)
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    scenario: str | None = None
    priority: Literal["P0", "P1", "P2", "P3"] | None = None
    risk_level: Literal["critical", "high", "medium", "low"] | None = None
    difficulty: str | None = None
    test_group: Literal["train", "validation", "test"] | None = None


class DatasetWithCasesInput(NamedResourceInput):
    cases: list[TestCaseDraftInput] = Field(min_length=1, max_length=500)


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
