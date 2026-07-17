"""超级 Agent 到专业控制台公开应用能力的适配层。"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from agenttest.modules.model_configs.public import ModelInvoker
from agenttest.modules.test_agent.adapters.platform_assets import (
    PlatformAssetCapabilities,
)
from agenttest.modules.test_agent.adapters.platform_execution import (
    PlatformExecutionCapabilities,
)
from agenttest.modules.test_agent.adapters.platform_quality import (
    PlatformQualityCapabilities,
)
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.shared.application.core_summaries import CoreSummaryReader

ASSET_CAPABILITIES = frozenset(
    {
        "agents.list",
        "agents.create",
        "agents.publish_version",
        "agents.create_version",
        "environments.list",
        "environments.create",
        "credentials.list",
        "credentials.validate",
        "credentials.create",
        "datasets.list",
        "datasets.create_with_cases",
        "datasets.publish_version",
        "datasets.auto_generate_cases",
        "test_cases.list",
        "test_cases.get",
        "test_cases.create",
        "test_cases.update",
        "test_cases.validate",
        "test_cases.mark_ready",
        "test_cases.trial_run",
        "test_plans.list",
        "test_plans.create_version",
        "test_plans.publish_version",
    }
)
EXECUTION_CAPABILITIES = frozenset(
    {
        "runs.list",
        "runs.get_status",
        "runs.start",
        "runs.cancel",
        "agents.analyze_endpoint",
        "reports.generate",
    }
)
QUALITY_CAPABILITIES = frozenset(
    {
        "scorers.list",
        "scorers.create",
        "experiments.list",
        "experiments.create",
        "security_scans.list",
        "security_scans.start",
        "reviews.list",
        "reviews.enqueue",
        "release_gates.list",
        "release_gates.evaluate",
    }
)


class PlatformCapabilityGroup(Protocol):
    async def execute(
        self,
        capability: str,
        context: OrchestrationContext,
        values: dict[str, Any],
    ) -> dict[str, object]: ...


def capability_group_for(capability: str) -> str:
    if capability in ASSET_CAPABILITIES:
        return "assets"
    if capability in EXECUTION_CAPABILITIES:
        return "execution"
    if capability in QUALITY_CAPABILITIES:
        return "quality"
    raise KeyError(f"Unsupported platform capability: {capability}")


class HandlerPlatformGateway:
    def __init__(
        self,
        *,
        agents,
        datasets,
        environments,
        plans,
        runs,
        scorers,
        experiments,
        reviews,
        gates,
        security,
        accounts,
        promptfoo_bin: str,
        allow_private_security_targets: bool,
        gate_evidence,
        models=None,
        invoker: ModelInvoker | None = None,
        connection_validator=None,
        summaries: CoreSummaryReader | None = None,
    ) -> None:
        self._groups: dict[str, PlatformCapabilityGroup] = {
            "assets": PlatformAssetCapabilities(
                agents=agents,
                datasets=datasets,
                environments=environments,
                plans=plans,
                accounts=accounts,
                models=models,
                invoker=invoker,
                summaries=summaries,
            ),
            "execution": PlatformExecutionCapabilities(
                runs=runs,
                agents=agents,
                connection_validator=connection_validator,
                allow_private_security_targets=allow_private_security_targets,
                summaries=summaries,
            ),
            "quality": PlatformQualityCapabilities(
                scorers=scorers,
                experiments=experiments,
                reviews=reviews,
                gates=gates,
                security=security,
                agents=agents,
                promptfoo_bin=promptfoo_bin,
                allow_private_security_targets=allow_private_security_targets,
                gate_evidence=gate_evidence,
                summaries=summaries,
            ),
        }

    async def execute(
        self,
        capability: str,
        context: object,
        payload: BaseModel,
    ) -> dict[str, object]:
        if not isinstance(context, OrchestrationContext):
            raise TypeError("Orchestration context is required")
        group = self._groups[capability_group_for(capability)]
        return await group.execute(capability, context, payload.model_dump())


class CompositePlatformGateway:
    def __init__(self, platform: HandlerPlatformGateway, missions) -> None:
        self._platform = platform
        self._missions = missions

    async def execute(
        self, capability: str, context: object, payload: BaseModel
    ) -> dict[str, object]:
        if not isinstance(context, OrchestrationContext):
            raise TypeError("Orchestration context is required")
        if capability.startswith("test_missions."):
            return await self._missions.execute(capability, context, payload)
        return await self._platform.execute(capability, context, payload)
