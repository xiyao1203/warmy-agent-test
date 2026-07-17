"""超级 Agent 到专业控制台公开应用能力的适配层。"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from agenttest.modules.agents.public import (
    AgentVersionId,
)
from agenttest.modules.runs.public import CreateRunCommand, RunId
from agenttest.modules.security.public import (
    validate_agent_endpoint,
)
from agenttest.modules.test_agent.adapters.platform_projection import (
    _artifact,
    _created,
    _infer_json_schema,
    _resource_ref,
    _run,
    _serializable,
    _summary_item,
)
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.modules.test_plans.public import (
    TestPlanVersionId,
)
from agenttest.shared.application.core_summaries import CoreSummaryReader
from agenttest.shared.application.resource_reference import (
    ResourceType,
)


class PlatformExecutionCapabilities:
    def __init__(
        self,
        *,
        runs,
        agents,
        connection_validator=None,
        allow_private_security_targets: bool,
        summaries: CoreSummaryReader | None = None,
    ) -> None:
        self._runs = runs
        self._agents = agents
        self._connection_validator = connection_validator
        self._allow_private_security_targets = allow_private_security_targets
        self._summaries = summaries

    async def execute(
        self,
        capability: str,
        context: OrchestrationContext,
        values: dict[str, Any],
    ) -> dict[str, object]:
        project_id = context.project_id
        actor = context.actor

        if capability == "runs.list":
            items = await self._runs.list_runs.execute(actor, project_id)
            run_summaries = (
                await self._summaries.runs(project_id.value, [item.run_id.value for item in items])
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _run(item),
                        run_summaries.get(item.run_id.value),
                        _resource_ref(
                            ResourceType.RUN,
                            item.run_id.value,
                            project_id.value,
                            f"Run {str(item.run_id.value)[:8]}",
                            status=item.status.value,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "runs.get_status":
            run_id = RunId(UUID(str(values["id"])))
            item = await self._runs.get_run.execute(actor, project_id, run_id)
            cases = await self._runs.list_cases.execute(actor, project_id, run_id)
            errors = [case for case in cases if case.error_type]
            return {
                **_run(item),
                "error_type": errors[0].error_type if errors else None,
                "error_message": errors[0].error_message if errors else None,
                "cases": [
                    {
                        "id": str(case.run_case_id.value),
                        "name": case.name,
                        "status": case.status.value,
                        "execution_mode": case.execution_mode,
                        "input": case.input_snapshot,
                        "assertions": case.assertion_snapshot,
                        "error_type": case.error_type,
                        "error_message": case.error_message,
                    }
                    for case in cases
                ],
            }
        if capability == "runs.start":
            result = await self._runs.create_run.execute(
                actor,
                CreateRunCommand(
                    project_id=project_id,
                    test_plan_version_id=TestPlanVersionId(
                        UUID(str(values["test_plan_version_id"]))
                    ),
                    idempotency_key=(
                        context.idempotency_key or f"super-agent:{context.session_id}:{uuid4()}"
                    ),
                ),
            )
            return _created("run", result.run.run_id.value, _run(result.run))
        if capability == "runs.cancel":
            item = await self._runs.cancel_run.execute(
                actor, project_id, RunId(UUID(str(values["id"])))
            )
            return _created("run", item.run_id.value, _run(item), relation="updated")
        if capability == "agents.analyze_endpoint":
            return await self._analyze_endpoint(context, values)
        if capability == "reports.generate":
            return await self._generate_report(context, values)
        raise KeyError(f"Unsupported platform capability: {capability}")

    async def _analyze_endpoint(self, context, values):
        """Probe an agent's API endpoint and return contract information."""
        version = await self._agents.get_version.execute(
            context.actor,
            AgentVersionId(UUID(str(values["agent_version_id"]))),
        )
        agent = await self._agents.get_agent.execute(context.actor, version.agent_id)
        if agent.project_id != context.project_id:
            raise ValueError("Agent version does not exist in project")

        config = version.config
        validate_agent_endpoint(
            config.api_url,
            allow_private_network=self._allow_private_security_targets,
        )

        if self._connection_validator is None:
            raise ValueError("Agent connection validator is not configured")
        probe = dict(values.get("probe_input") or {"input": "Hello, this is a probe test"})
        result = await self._connection_validator.validate(config, probe)

        return {
            "agent_name": agent.name,
            "agent_type": agent.agent_type.value,
            "endpoint": config.api_url,
            "timeout_ms": config.timeout,
            "connection": {
                "status_code": result.status_code,
                "latency_ms": result.latency_ms,
            },
            "response_preview": _serializable(result.response_preview),
            "response_schema": _infer_json_schema(result.response_preview),
            "artifacts": [
                _artifact("agent_version", version.version_id.value, relation="analyzed")
            ],
        }

    async def _generate_report(self, context, values):
        """Build a test run report summary."""
        run_id = UUID(str(values["run_id"]))
        run = await self._runs.get_run.execute(context.actor, context.project_id, RunId(run_id))
        cases = await self._runs.list_cases.execute(
            context.actor, context.project_id, RunId(run_id)
        )

        duration_ms = None
        if run.started_at is not None and run.completed_at is not None:
            duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)

        return {
            "run_id": str(run_id),
            "status": run.status.value,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_ms": duration_ms,
            "total_cases": run.total_cases,
            "passed_cases": run.passed_cases,
            "failed_cases": run.failed_cases,
            "error_cases": run.error_cases,
            "cancelled_cases": run.cancelled_cases,
            "cases_summary": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "duration_ms": c.duration_ms,
                }
                for c in cases
            ],
            "artifacts": [_artifact("run", run_id, relation="reported")],
        }
