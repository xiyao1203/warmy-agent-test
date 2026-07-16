"""超级 Agent 到专业控制台公开应用能力的适配层。"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, TypeAdapter, ValidationError

from agenttest.modules.agents.public import (
    AgentConfig,
    AgentId,
    AgentType,
    AgentVersionId,
    CreateAgentCommand,
    CreateAgentVersionCommand,
    PublishAgentVersionCommand,
)
from agenttest.modules.datasets.public import (
    AddTestCaseCommand,
    CreateCaseTrialRunCommand,
    CreateDatasetCommand,
    CreateDatasetVersionCommand,
    DatasetVersionId,
    MarkTestCaseReadyCommand,
    PlatformTestCaseV1,
    PublishDatasetVersionCommand,
    TestCaseId,
    TestCaseSource,
    UpdateTestCaseCommand,
)
from agenttest.modules.environments.public import (
    CreateEnvironmentTemplateCommand,
    TemplateType,
)
from agenttest.modules.experiments.public import Experiment, ExperimentId
from agenttest.modules.gates.public import ReleaseGateId, evaluate_evidence
from agenttest.modules.identity.public import UserId
from agenttest.modules.model_configs.public import (
    InvocationMessage,
    ModelInvoker,
    ModelPurpose,
)
from agenttest.modules.runs.public import CreateRunCommand, RunId
from agenttest.modules.scorers.public import Scorer, ScorerId, ScorerType
from agenttest.modules.security.public import (
    ScanStatus,
    SecurityScan,
    create_scanner,
    validate_agent_endpoint,
)
from agenttest.modules.test_accounts.public import TestAccount, TestAccountId
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.modules.test_plans.public import (
    CreateTestPlanCommand,
    CreateTestPlanVersionCommand,
    EnvironmentTemplateId,
    PublishTestPlanVersionCommand,
    TestPlanConfig,
    TestPlanVersionId,
)
from agenttest.shared.application.core_summaries import CoreSummaryReader
from agenttest.shared.application.resource_reference import (
    ResourceReference,
    ResourceType,
)


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
        self._agents = agents
        self._datasets = datasets
        self._environments = environments
        self._plans = plans
        self._runs = runs
        self._scorers = scorers
        self._experiments = experiments
        self._reviews = reviews
        self._gates = gates
        self._security = security
        self._accounts = accounts
        self._promptfoo_bin = promptfoo_bin
        self._allow_private_security_targets = allow_private_security_targets
        self._gate_evidence = gate_evidence
        self._models = models
        self._invoker = invoker
        self._connection_validator = connection_validator
        self._summaries = summaries

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
            agent_summaries = (
                await self._summaries.agents(
                    project_id.value, [item.agent_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _agent(item),
                        agent_summaries.get(item.agent_id.value),
                        _resource_ref(
                            ResourceType.AGENT,
                            item.agent_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
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
            environment_summaries = (
                await self._summaries.environments(
                    project_id.value, [item.template_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _environment(item),
                        environment_summaries.get(item.template_id.value),
                        _resource_ref(
                            ResourceType.ENVIRONMENT,
                            item.template_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
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
            dataset_summaries = (
                await self._summaries.datasets(
                    project_id.value, [item.dataset_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _dataset(item),
                        dataset_summaries.get(item.dataset_id.value),
                        _resource_ref(
                            ResourceType.DATASET,
                            item.dataset_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "test_cases.list":
            items, _ = await self._datasets.list_cases.execute(
                actor,
                DatasetVersionId(UUID(str(values["dataset_version_id"]))),
            )
            return {
                "items": [
                    _summary_item(
                        _test_case(item),
                        None,
                        _resource_ref(
                            ResourceType.TEST_CASE,
                            item.case_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "test_cases.get":
            item = await self._datasets.get_case.execute(
                actor,
                TestCaseId(UUID(str(values["case_id"]))),
            )
            return _test_case(item)
        if capability == "test_cases.create":
            contract = PlatformTestCaseV1.model_validate(values["case"])
            item = await self._datasets.add_case.execute(
                actor,
                _test_case_command_from_contract(
                    dataset_version_id=DatasetVersionId(UUID(str(values["dataset_version_id"]))),
                    contract=contract,
                    source_ref=f"agent-session:{context.session_id}",
                ),
            )
            return _created("test_case", item.case_id.value, _test_case(item))
        if capability == "test_cases.update":
            contract = PlatformTestCaseV1.model_validate(values["case"])
            item = await self._datasets.update_case.execute(
                actor,
                _test_case_update_command(
                    TestCaseId(UUID(str(values["case_id"]))),
                    contract,
                ),
            )
            return _created(
                "test_case",
                item.case_id.value,
                _test_case(item),
                relation="updated",
            )
        if capability == "test_cases.validate":
            item = await self._datasets.get_case.execute(
                actor,
                TestCaseId(UUID(str(values["case_id"]))),
            )
            issues = item.readiness_issues()
            return {
                "test_case": _test_case(item),
                "ready": not issues,
                "issues": [
                    {"field": field, "code": code, "message": message}
                    for field, code, message in issues
                ],
            }
        if capability == "test_cases.mark_ready":
            item = await self._datasets.mark_case_ready.execute(
                actor,
                MarkTestCaseReadyCommand(TestCaseId(UUID(str(values["case_id"])))),
            )
            return _created("test_case", item.case_id.value, _test_case(item), relation="updated")
        if capability == "test_cases.trial_run":
            result = await self._datasets.trial_run.execute(
                actor,
                CreateCaseTrialRunCommand(
                    project_id=project_id,
                    case_id=TestCaseId(UUID(str(values["case_id"]))),
                    agent_version_id=UUID(str(values["agent_version_id"])),
                    environment_template_id=UUID(str(values["environment_template_id"])),
                    idempotency_key=(
                        context.idempotency_key
                        or f"agent-trial:{context.session_id}:{values['case_id']}"
                    ),
                ),
            )
            return _created("run", result.run.run_id.value, _run(result.run))
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
                    case = await self._datasets.add_case.execute(
                        actor,
                        _test_case_command_from_raw(
                            dataset_version_id=version.version_id,
                            raw=dict(raw),
                            fallback_name=f"Case {index + 1}",
                            fallback_input=None,
                            default_execution_mode="api",
                            source_ref=f"agent-session:{context.session_id}",
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
            plan_summaries = (
                await self._summaries.test_plans(
                    project_id.value, [item.test_plan_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _plan(item),
                        plan_summaries.get(item.test_plan_id.value),
                        _resource_ref(
                            ResourceType.TEST_PLAN,
                            item.test_plan_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
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
            run_summaries = (
                await self._summaries.runs(
                    project_id.value, [item.run_id.value for item in items]
                )
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
        if capability == "agents.create_version":
            return await self._create_agent_version(context, values)
        if capability == "datasets.auto_generate_cases":
            return await self._auto_generate_cases(context, values)
        if capability == "reports.generate":
            return await self._generate_report(context, values)
        if capability == "credentials.create":
            return await self._create_credential(context, values)

        return await self._execute_quality(capability, context, values)

    async def _execute_quality(self, capability, context, values):
        project_id = context.project_id
        if capability == "scorers.list":
            items, _ = await self._scorers.list_by_project(project_id)
            scorer_summaries = (
                await self._summaries.scorers(
                    project_id.value, [item.scorer_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _scorer(item),
                        scorer_summaries.get(item.scorer_id.value),
                        _resource_ref(
                            ResourceType.SCORER,
                            item.scorer_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
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
            experiment_summaries = (
                await self._summaries.experiments(
                    project_id.value, [item.experiment_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _experiment(item),
                        experiment_summaries.get(item.experiment_id.value),
                        _resource_ref(
                            ResourceType.EXPERIMENT,
                            item.experiment_id.value,
                            project_id.value,
                            item.name,
                            status=item.status.value,
                        ),
                    )
                    for item in items
                ]
            }
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
            scan_summaries = (
                await self._summaries.security_scans(
                    project_id.value, [item.scan_id for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _security_scan(item),
                        scan_summaries.get(item.scan_id),
                        _resource_ref(
                            ResourceType.SECURITY_SCAN,
                            item.scan_id,
                            project_id.value,
                            f"Security scan {str(item.scan_id)[:8]}",
                            status=item.status.value,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "security_scans.start":
            version = await self._agents.get_version.execute(
                context.actor,
                AgentVersionId(UUID(str(values["agent_version_id"]))),
            )
            agent = await self._agents.get_agent.execute(context.actor, version.agent_id)
            if agent.project_id != project_id:
                raise ValueError("Agent version does not exist in project")
            endpoint = version.config.api_url
            validate_agent_endpoint(
                endpoint,
                allow_private_network=self._allow_private_security_targets,
            )
            scan = SecurityScan.create(
                project_id=project_id.value,
                scan_type="full",
                agent_version_id=version.version_id.value,
                run_id=UUID(str(values["run_id"])) if values.get("run_id") else None,
                security_profile_id=(
                    UUID(str(values["security_profile_id"]))
                    if values.get("security_profile_id")
                    else None
                ),
            )
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
            review_summaries = (
                await self._summaries.reviews(
                    project_id.value, [item.task_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _review(item),
                        review_summaries.get(item.task_id.value),
                        _resource_ref(
                            ResourceType.REVIEW,
                            item.task_id.value,
                            project_id.value,
                            f"Review {str(item.task_id.value)[:8]}",
                            status=item.status.value,
                        ),
                    )
                    for item in items
                ],
                "total": total,
            }
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
            gate_summaries = (
                await self._summaries.gates(
                    project_id.value, [item.gate_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _gate(item),
                        gate_summaries.get(item.gate_id.value),
                        _resource_ref(
                            ResourceType.RELEASE_GATE,
                            item.gate_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "release_gates.evaluate":
            gate = await self._gates.get_by_id_and_project(
                ReleaseGateId(UUID(str(values["gate_id"]))), project_id.value
            )
            if gate is None:
                raise ValueError("Release gate does not exist in project")
            run_id = UUID(str(values["run_id"]))
            evidence = await self._gate_evidence.load(project_id.value, run_id)
            if evidence is None:
                raise ValueError("Run does not exist in project")
            result = evaluate_evidence(gate, evidence)
            decision_id = await self._gate_evidence.record(
                project_id=project_id.value,
                gate_id=gate.gate_id.value,
                actor_id=context.actor.user_id.value,
                evidence=evidence,
                passed=result.passed,
                failures=result.failures,
                experiment_id=None,
            )
            return _created(
                "release_decision",
                decision_id,
                {**result.to_dict(), "run_id": str(run_id)},
                relation="evaluated",
            )
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

    async def _auto_generate_cases(self, context, values):
        """Use LLM to generate structured test cases for an agent."""
        if self._invoker is None or self._models is None:
            raise ValueError("LLM invoker is not configured for case generation")

        version = await self._agents.get_version.execute(
            context.actor,
            AgentVersionId(UUID(str(values["agent_version_id"]))),
        )
        agent = await self._agents.get_agent.execute(context.actor, version.agent_id)
        if agent.project_id != context.project_id:
            raise ValueError("Agent version does not exist in project")

        config = await self._models.resolve_default(
            context.actor, context.project_id, ModelPurpose.TEST_AGENT_CHAT
        )

        hints = values.get("scenario_hints") or []
        hints_text = ""
        if hints:
            hints_text = "\n".join(f"- {h}" for h in hints)

        is_canvas = agent.agent_type.value == "canvas"
        canvas_url = str(values.get("canvas_url", version.config.api_url))
        professional_contract = (
            "每条用例必须严格使用平台 PlatformTestCaseV1 格式：\n"
            "- name、objective、template、case_type、automation_status\n"
            "- component、requirement_refs、preconditions、input、data_bindings\n"
            "- steps: 有序数组，每步必须含 step_no、action、test_data、expected_result\n"
            "- expected_outcome、assertions、scorers、security_policies\n"
            "- artifact_requirements、postconditions、execution_mode、timeout_seconds、"
            "retry_count、tags、priority、risk_level\n"
            "不得在 data_bindings 写入密码或 Token 明文；敏感数据只写 reference。\n"
        )

        if is_canvas:
            prompt = (
                "你是画布 Agent 测试用例生成专家。被测 Agent 通过画布（Canvas）与用户交互，"
                "测试需要在浏览器中打开画布页面，输入提示词，等待画布生成结果后验证。\n\n"
                f"被测 Agent:\n"
                f"- 名称: {agent.name}\n"
                f"- 类型: canvas\n"
                f"- 画布 URL: {canvas_url}\n"
                f"- 描述: {agent.description or '未提供'}\n"
                + (f"\n场景提示:\n{hints_text}\n" if hints else "")
                + "\n"
                + professional_contract
                + '- execution_mode 必须为 "codex_explore"\n'
                + "- input 包含 url 和 test_intent\n"
                + "- assertions 可使用 canvas 专用规则：\n"
                '  支持: { type: "canvas_schema" }, '
                '{ type: "node_count", min_count: N }, '
                '{ type: "node_types", required_types: ["text", "image"] }, '
                '{ type: "required_connection", from_type: "text", to_type: "image" }, '
                '{ type: "no_orphan_nodes" }\n'
                "- tags: 标签列表\n\n"
                "按以下分类各生成 2-3 条: 基础画布操作、复杂链路、边界异常。\n"
                '返回 JSON: {"cases": [...]}'
            )
        else:
            prompt = (
                "你是测试用例生成专家。根据被测 Agent 信息生成结构化测试用例。\n\n"
                f"被测 Agent:\n"
                f"- 名称: {agent.name}\n"
                f"- 类型: {agent.agent_type.value}\n"
                f"- API: {version.config.api_url}\n"
                f"- 描述: {agent.description or '未提供'}\n"
                + (f"\n场景提示:\n{hints_text}\n" if hints else "")
                + "\n"
                + professional_contract
                + '- execution_mode 必须为 "api"\n\n'
                "按以下分类各生成 2-3 条: 正常场景、边界条件、异常输入。\n"
                '返回 JSON: {"cases": [...]}'
            )

        result = await self._invoker.invoke(
            config,
            [InvocationMessage(role="system", content=prompt)],
            response_format={"type": "json_object"},
            timeout_seconds=60,
            max_tokens=4096,
        )

        import json

        try:
            parsed = json.loads(result.content)
            cases = parsed.get("cases", [])
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("LLM did not return valid JSON for test cases") from exc

        if not cases or not isinstance(cases, list):
            raise ValueError("No valid test cases generated")
        try:
            validated_cases = TypeAdapter(list[PlatformTestCaseV1]).validate_python(cases)
        except ValidationError as error:
            raise ValueError(
                f"Generated test cases do not match platform format: {error}"
            ) from error

        async with self._datasets.uow_factory():
            dataset = await self._datasets.create_dataset.execute(
                context.actor,
                CreateDatasetCommand(
                    project_id=context.project_id,
                    name=str(values["dataset_name"]),
                    description=f"由超级 Agent 为 {agent.name} 自动生成",
                ),
            )
            version = await self._datasets.create_version.execute(
                context.actor, CreateDatasetVersionCommand(dataset.dataset_id)
            )
            case_ids = []
            for contract in validated_cases:
                case = await self._datasets.add_case.execute(
                    context.actor,
                    _test_case_command_from_contract(
                        dataset_version_id=version.version_id,
                        contract=contract,
                        source_ref=f"agent-generation:{context.session_id}",
                    ),
                )
                case_ids.append(str(case.case_id.value))

        result_obj = _created("dataset", dataset.dataset_id.value, {"case_ids": case_ids})
        result_obj["artifacts"].append(_artifact("dataset_version", version.version_id.value))
        return result_obj

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

    async def _create_agent_version(self, context, values):
        """为 Agent 创建新版本，写入完整的运行时配置。"""
        raw_config = dict(values["config"])
        if "api_url" not in raw_config or not raw_config["api_url"]:
            raise ValueError("config.api_url is required")
        config = AgentConfig.from_dict(raw_config)
        agent_id = AgentId(UUID(str(values["agent_id"])))

        agent = await self._agents.get_agent.execute(context.actor, agent_id)
        if agent.project_id != context.project_id:
            raise ValueError("Agent does not exist in project")

        version = await self._agents.create_version.execute(
            context.actor,
            CreateAgentVersionCommand(agent_id=agent_id, config=config),
        )
        return _created(
            "agent_version",
            version.version_id.value,
            {
                "version_number": version.version_number,
                "status": version.status.value,
                "api_url": config.api_url,
            },
        )

    async def _create_credential(self, context, values):
        """为被测 Agent 创建测试凭证（用户名/密码或 API Key）。"""
        account = TestAccount.create(
            project_id=context.project_id.value,
            name=str(values["name"]),
            username=str(values["username"]),
            credential_encrypted=str(values["credential"]),
            account_type=str(values.get("account_type", "user")),
            description=_optional(values.get("description")),
        )
        await self._accounts.add(account)
        return _created(
            "credential",
            account.account_id.value,
            {
                "name": account.name,
                "username": account.username,
                "account_type": account.account_type,
            },
        )


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
