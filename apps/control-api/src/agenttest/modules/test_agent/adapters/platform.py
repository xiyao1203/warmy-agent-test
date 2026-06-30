"""超级 Agent 到专业控制台公开应用能力的适配层。"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel

from agenttest.modules.agents.application.commands import (
    CreateAgentCommand,
    PublishAgentVersionCommand,
)
from agenttest.modules.agents.domain.entities import AgentVersionId
from agenttest.modules.agents.domain.value_objects import AgentType
from agenttest.modules.datasets.application.commands import (
    AddTestCaseCommand,
    CreateDatasetCommand,
    CreateDatasetVersionCommand,
    PublishDatasetVersionCommand,
)
from agenttest.modules.datasets.domain.entities import DatasetVersionId
from agenttest.modules.datasets.domain.value_objects import ExecutionMode
from agenttest.modules.environments.application.commands import (
    CreateEnvironmentTemplateCommand,
)
from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.modules.experiments.domain.entities import Experiment, ExperimentId
from agenttest.modules.experiments.infrastructure.persistence.repositories import (
    SqlAlchemyExperimentRepository,
)
from agenttest.modules.gates.domain.entities import ReleaseGateId
from agenttest.modules.gates.infrastructure.persistence.repositories import (
    SqlAlchemyReleaseGateRepository,
)
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
)
from agenttest.modules.runs.application.commands import CreateRunCommand
from agenttest.modules.runs.domain.entities import RunId
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId
from agenttest.modules.scorers.domain.value_objects import ScorerType
from agenttest.modules.scorers.infrastructure.persistence.repositories import (
    SqlAlchemyScorerRepository,
)
from agenttest.modules.security.adapters import create_scanner
from agenttest.modules.security.domain.models import ScanStatus, SecurityScan
from agenttest.modules.security.domain.targets import validate_agent_endpoint
from agenttest.modules.security.infrastructure.repositories import (
    SqlAlchemySecurityScanRepository,
)
from agenttest.modules.test_accounts.domain.entities import TestAccountId
from agenttest.modules.test_accounts.infrastructure.persistence.repositories import (
    SqlAlchemyTestAccountRepository,
)
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.modules.test_plans.application.commands import (
    CreateTestPlanCommand,
    CreateTestPlanVersionCommand,
    PublishTestPlanVersionCommand,
)
from agenttest.modules.test_plans.domain.entities import (
    EnvironmentTemplateId,
    TestPlanVersionId,
)
from agenttest.modules.test_plans.domain.value_objects import TestPlanConfig


class HandlerPlatformGateway:
    def __init__(
        self,
        *,
        agents,
        datasets,
        environments,
        plans,
        runs,
        session_factory,
        promptfoo_bin: str,
        allow_private_security_targets: bool,
    ) -> None:
        self._agents = agents
        self._datasets = datasets
        self._environments = environments
        self._plans = plans
        self._runs = runs
        self._scorers = SqlAlchemyScorerRepository(session_factory)
        self._experiments = SqlAlchemyExperimentRepository(session_factory)
        self._reviews = SqlAlchemyReviewTaskRepository(session_factory)
        self._gates = SqlAlchemyReleaseGateRepository(session_factory)
        self._security = SqlAlchemySecurityScanRepository(session_factory)
        self._accounts = SqlAlchemyTestAccountRepository(session_factory)
        self._promptfoo_bin = promptfoo_bin
        self._allow_private_security_targets = allow_private_security_targets

    async def execute(
        self,
        capability: str,
        context: object,
        payload: BaseModel,
    ) -> dict[str, object]:
        if not isinstance(context, OrchestrationContext):
            raise TypeError("Orchestration context is required")
        values = payload.model_dump()
        project_id = context.project_id
        actor = context.actor

        if capability == "agents.list":
            items, _ = await self._agents.list_agents.execute(actor, project_id)
            return {"items": [_agent(item) for item in items]}
        if capability == "agents.create":
            agent_type = AgentType(str(values["config"].get("agent_type", "generic_http")))
            item = await self._agents.create_agent.execute(
                actor,
                CreateAgentCommand(
                    project_id=project_id,
                    name=str(values["name"]),
                    description=_optional(values.get("description")),
                    agent_type=agent_type,
                ),
            )
            return _created("agent", item.agent_id.value, _agent(item))
        if capability == "agents.publish_version":
            item = await self._agents.publish_version.execute(
                actor,
                PublishAgentVersionCommand(AgentVersionId(UUID(str(values["id"])))),
            )
            return _created("agent_version", item.version_id.value, {"status": item.status.value})

        if capability == "environments.list":
            items, _ = await self._environments.list_templates.execute(actor, project_id)
            return {"items": [_environment(item) for item in items]}
        if capability == "environments.create":
            item = await self._environments.create_template.execute(
                actor,
                CreateEnvironmentTemplateCommand(
                    project_id=project_id,
                    name=str(values["name"]),
                    description=_optional(values.get("description")),
                    template_type=TemplateType(str(values["config"].get("template_type", "blank"))),
                    config=dict(values["config"]),
                ),
            )
            return _created("environment", item.template_id.value, _environment(item))
        if capability == "credentials.list":
            items = await self._accounts.list_by_project(project_id.value)
            return {
                "items": [
                    {
                        "id": str(item.account_id.value),
                        "name": item.name,
                        "username": item.username,
                        "enabled": item.enabled,
                    }
                    for item in items
                ]
            }
        if capability == "credentials.validate":
            item = await self._accounts.get_by_id_and_project(
                TestAccountId(UUID(str(values["id"]))), project_id.value
            )
            if item is None:
                raise ValueError("Credential reference does not exist in project")
            return {"id": str(item.account_id.value), "valid": item.enabled}

        if capability == "datasets.list":
            items, _ = await self._datasets.list_datasets.execute(actor, project_id)
            return {"items": [_dataset(item) for item in items]}
        if capability == "datasets.create_with_cases":
            async with self._datasets.uow_factory():
                dataset = await self._datasets.create_dataset.execute(
                    actor,
                    CreateDatasetCommand(
                        project_id=project_id,
                        name=str(values["name"]),
                        description=_optional(values.get("description")),
                    ),
                )
                version = await self._datasets.create_version.execute(
                    actor, CreateDatasetVersionCommand(dataset.dataset_id)
                )
                cases = []
                for index, raw in enumerate(values["cases"]):
                    case_input = dict(raw.get("input") or {})
                    if not case_input:
                        raise ValueError(f"Test case {index + 1} input is required")
                    case = await self._datasets.add_case.execute(
                        actor,
                        AddTestCaseCommand(
                            dataset_version_id=version.version_id,
                            name=str(raw.get("name") or f"Case {index + 1}"),
                            input=case_input,
                            execution_mode=ExecutionMode(str(raw.get("execution_mode", "api"))),
                            assertions=list(raw.get("assertions") or []),
                            scorers=list(raw.get("scorers") or []),
                            tags=list(raw.get("tags") or []),
                        ),
                    )
                    cases.append(str(case.case_id.value))
            result = _created("dataset", dataset.dataset_id.value, {"case_ids": cases})
            result["artifacts"].append(_artifact("dataset_version", version.version_id.value))
            return result
        if capability == "datasets.publish_version":
            item = await self._datasets.publish_version.execute(
                actor,
                PublishDatasetVersionCommand(DatasetVersionId(UUID(str(values["id"])))),
            )
            return _created("dataset_version", item.version_id.value, {"status": item.status.value})

        if capability == "test_plans.list":
            items, _ = await self._plans.list_plans.execute(actor, project_id)
            return {"items": [_plan(item) for item in items]}
        if capability == "test_plans.create_version":
            async with self._plans.uow_factory():
                plan = await self._plans.create_plan.execute(
                    actor,
                    CreateTestPlanCommand(
                        project_id=project_id,
                        name=str(values["name"]),
                        description=_optional(values.get("description")),
                    ),
                )
                config = TestPlanConfig.from_dict(dict(values["config"]))
                version = await self._plans.create_version.execute(
                    actor,
                    CreateTestPlanVersionCommand(
                        test_plan_id=plan.test_plan_id,
                        config=config,
                        agent_version_id=_agent_version(values.get("agent_version_id")),
                        dataset_version_id=_dataset_version(values.get("dataset_version_id")),
                        environment_template_id=_environment_id(
                            values.get("environment_template_id")
                        ),
                    ),
                )
            result = _created("test_plan", plan.test_plan_id.value, _plan(plan))
            result["artifacts"].append(_artifact("test_plan_version", version.version_id.value))
            return result
        if capability == "test_plans.publish_version":
            item = await self._plans.publish_version.execute(
                actor,
                PublishTestPlanVersionCommand(TestPlanVersionId(UUID(str(values["id"])))),
            )
            return _created(
                "test_plan_version", item.version_id.value, {"status": item.status.value}
            )

        if capability == "runs.list":
            items = await self._runs.list_runs.execute(actor, project_id)
            return {"items": [_run(item) for item in items]}
        if capability == "runs.start":
            result = await self._runs.create_run.execute(
                actor,
                CreateRunCommand(
                    project_id=project_id,
                    test_plan_version_id=TestPlanVersionId(
                        UUID(str(values["test_plan_version_id"]))
                    ),
                    idempotency_key=f"super-agent:{context.session_id}:{uuid4()}",
                ),
            )
            return _created("run", result.run.run_id.value, _run(result.run))
        if capability == "runs.cancel":
            item = await self._runs.cancel_run.execute(
                actor, project_id, RunId(UUID(str(values["id"])))
            )
            return _created("run", item.run_id.value, _run(item), relation="updated")

        return await self._execute_quality(capability, context, values)

    async def _execute_quality(self, capability, context, values):
        project_id = context.project_id
        if capability == "scorers.list":
            items, _ = await self._scorers.list_by_project(project_id)
            return {"items": [_scorer(item) for item in items]}
        if capability == "scorers.create":
            config = dict(values["config"])
            item = Scorer.create(
                scorer_id=ScorerId.new(),
                project_id=project_id,
                name=str(values["name"]),
                scorer_type=ScorerType(str(config.pop("scorer_type", "rule"))),
                weight=float(config.pop("weight", 1)),
                threshold=float(config.pop("threshold", 0.8)),
                config_json=config,
                description=_optional(values.get("description")),
            )
            await self._scorers.add(item)
            return _created("scorer", item.scorer_id.value, _scorer(item))
        if capability == "experiments.list":
            items = await self._experiments.list_by_project(project_id)
            return {"items": [_experiment(item) for item in items]}
        if capability == "experiments.create":
            item = Experiment.create(
                experiment_id=ExperimentId.new(),
                project_id=project_id,
                name=str(values["name"]),
                run_a_id=UUID(str(values["baseline_run_id"])),
                run_b_id=UUID(str(values["candidate_run_id"])),
                description=_optional(values.get("description")),
            )
            await self._experiments.add(item)
            return _created("experiment", item.experiment_id.value, _experiment(item))
        if capability == "security_scans.list":
            items = await self._security.list_by_project(project_id.value)
            return {"items": [_security_scan(item) for item in items]}
        if capability == "security_scans.start":
            endpoint = str(values["target_url"])
            validate_agent_endpoint(
                endpoint,
                allow_private_network=self._allow_private_security_targets,
            )
            scan = SecurityScan.create(project_id=project_id.value, scan_type="full")
            await self._security.add(scan)
            scan.status = ScanStatus.RUNNING
            await self._security.save(scan)
            try:
                findings = await create_scanner(self._promptfoo_bin).run_scan(
                    agent_endpoint=endpoint, scan_type="full"
                )
                scan.complete(findings)
            except Exception as error:
                scan.fail(str(error))
                await self._security.save(scan)
                raise
            await self._security.save(scan)
            return _created("security_scan", scan.scan_id, _security_scan(scan))
        if capability == "reviews.list":
            items, total = await self._reviews.list_by_project(project_id)
            return {"items": [_review(item) for item in items], "total": total}
        if capability == "reviews.enqueue":
            items = await self._reviews.auto_enqueue_low_confidence(
                project_id,
                str(values["run_id"]),
                float(values["confidence_threshold"]),
            )
            return {
                "items": [_review(item) for item in items],
                "artifacts": [_artifact("review_task", item.task_id.value) for item in items],
            }
        if capability == "release_gates.list":
            items = await self._gates.list_by_project(project_id.value)
            return {"items": [_gate(item) for item in items]}
        if capability == "release_gates.evaluate":
            gate = await self._gates.get_by_id_and_project(
                ReleaseGateId(UUID(str(values["gate_id"]))), project_id.value
            )
            if gate is None:
                raise ValueError("Release gate does not exist in project")
            run = await self._runs.get_run.execute(
                context.actor, project_id, RunId(UUID(str(values["run_id"])))
            )
            result = gate.evaluate(
                actual_pass_rate=(run.passed_cases / run.total_cases),
                critical_passed=run.failed_cases == 0 and run.error_cases == 0,
            )
            return _created(
                "release_gate",
                gate.gate_id.value,
                result.to_dict(),
                relation="evaluated",
            )
        raise KeyError(f"Unsupported platform capability: {capability}")


def _artifact(kind: str, value: UUID, relation: str = "created") -> dict[str, str]:
    return {"type": kind, "id": str(value), "relation": relation}


def _created(kind, value, payload, relation="created"):
    return {**payload, "artifacts": [_artifact(kind, value, relation)]}


def _optional(value: Any) -> str | None:
    return str(value) if value else None


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
