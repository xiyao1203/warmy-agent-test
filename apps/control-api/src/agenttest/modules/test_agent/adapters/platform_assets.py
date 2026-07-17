"""超级 Agent 到专业控制台公开应用能力的适配层。"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

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
    CreateCaseTrialRunCommand,
    CreateDatasetCommand,
    CreateDatasetVersionCommand,
    DatasetVersionId,
    MarkTestCaseReadyCommand,
    PlatformTestCaseV1,
    PublishDatasetVersionCommand,
    TestCaseId,
)
from agenttest.modules.environments.public import (
    CreateEnvironmentTemplateCommand,
    TemplateType,
)
from agenttest.modules.model_configs.public import (
    InvocationMessage,
    ModelInvoker,
    ModelPurpose,
)
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_accounts.public import TestAccount, TestAccountId
from agenttest.modules.test_agent.adapters.platform_projection import (
    _agent,
    _agent_version,
    _artifact,
    _case_trial_fallback_key,
    _created,
    _dataset,
    _dataset_version,
    _environment,
    _environment_id,
    _optional,
    _plan,
    _resource_ref,
    _run,
    _summary_item,
    _test_case,
    _test_case_command_from_contract,
    _test_case_command_from_raw,
    _test_case_result,
    _test_case_update_command,
)
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.modules.test_plans.public import (
    CreateTestPlanCommand,
    CreateTestPlanVersionCommand,
    PublishTestPlanVersionCommand,
    TestPlanConfig,
    TestPlanVersionId,
)
from agenttest.shared.application.core_summaries import CoreSummaryReader
from agenttest.shared.application.resource_reference import (
    ResourceType,
)


class PlatformAssetCapabilities:
    def __init__(
        self,
        *,
        agents,
        datasets,
        environments,
        plans,
        accounts,
        models=None,
        invoker: ModelInvoker | None = None,
        summaries: CoreSummaryReader | None = None,
    ) -> None:
        self._agents = agents
        self._datasets = datasets
        self._environments = environments
        self._plans = plans
        self._accounts = accounts
        self._models = models
        self._invoker = invoker
        self._summaries = summaries

    async def execute(
        self,
        capability: str,
        context: OrchestrationContext,
        values: dict[str, Any],
    ) -> dict[str, object]:
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
            version_id = DatasetVersionId(UUID(str(values["dataset_version_id"])))
            await self._require_dataset_version_in_project(actor, project_id, version_id)
            items, _ = await self._datasets.list_cases.execute(
                actor,
                version_id,
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
            item = await self._require_test_case_in_project(
                actor, project_id, TestCaseId(UUID(str(values["case_id"])))
            )
            return _test_case_result(item, project_id.value)
        if capability == "test_cases.create":
            contract = PlatformTestCaseV1.model_validate(values["case"])
            version_id = DatasetVersionId(UUID(str(values["dataset_version_id"])))
            await self._require_dataset_version_in_project(actor, project_id, version_id)
            item = await self._datasets.add_case.execute(
                actor,
                _test_case_command_from_contract(
                    dataset_version_id=version_id,
                    contract=contract,
                    source_ref=f"agent-session:{context.session_id}",
                ),
            )
            return _created(
                "test_case",
                item.case_id.value,
                _test_case_result(item, project_id.value),
            )
        if capability == "test_cases.update":
            contract = PlatformTestCaseV1.model_validate(values["case"])
            case_id = TestCaseId(UUID(str(values["case_id"])))
            await self._require_test_case_in_project(actor, project_id, case_id)
            item = await self._datasets.update_case.execute(
                actor,
                _test_case_update_command(
                    case_id,
                    contract,
                ),
            )
            return _created(
                "test_case",
                item.case_id.value,
                _test_case_result(item, project_id.value),
                relation="updated",
            )
        if capability == "test_cases.validate":
            item = await self._require_test_case_in_project(
                actor, project_id, TestCaseId(UUID(str(values["case_id"])))
            )
            issues = item.readiness_issues()
            return {
                "test_case": _test_case_result(item, project_id.value),
                "ready": not issues,
                "issues": [
                    {"field": field, "code": code, "message": message}
                    for field, code, message in issues
                ],
            }
        if capability == "test_cases.mark_ready":
            case_id = TestCaseId(UUID(str(values["case_id"])))
            await self._require_test_case_in_project(actor, project_id, case_id)
            item = await self._datasets.mark_case_ready.execute(
                actor,
                MarkTestCaseReadyCommand(case_id),
            )
            return _created(
                "test_case",
                item.case_id.value,
                _test_case_result(item, project_id.value),
                relation="updated",
            )
        if capability == "test_cases.trial_run":
            case_id = TestCaseId(UUID(str(values["case_id"])))
            case = await self._require_test_case_in_project(actor, project_id, case_id)
            result = await self._datasets.trial_run.execute(
                actor,
                CreateCaseTrialRunCommand(
                    project_id=project_id,
                    case_id=case_id,
                    agent_version_id=UUID(str(values["agent_version_id"])),
                    environment_template_id=UUID(str(values["environment_template_id"])),
                    idempotency_key=(
                        context.idempotency_key
                        or _case_trial_fallback_key(context, values, case.updated_at)
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
        if capability == "agents.create_version":
            return await self._create_agent_version(context, values)
        if capability == "datasets.auto_generate_cases":
            return await self._auto_generate_cases(context, values)
        if capability == "credentials.create":
            return await self._create_credential(context, values)
        raise KeyError(f"Unsupported platform capability: {capability}")

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
            "- browser 模式的每个 steps 项还必须含 operation: "
            '{action: "goto|click|fill|wait|screenshot", target, value}；'
            "action 保留人工可读描述，不得用它代替 operation\n"
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

    async def _require_dataset_version_in_project(
        self,
        actor,
        project_id: ProjectId,
        version_id: DatasetVersionId,
    ):
        version = await self._datasets.get_version.execute(actor, version_id)
        dataset = await self._datasets.get_dataset.execute(actor, version.dataset_id)
        if dataset.project_id != project_id:
            raise ValueError("Dataset version does not exist in current project")
        return version

    async def _require_test_case_in_project(
        self,
        actor,
        project_id: ProjectId,
        case_id: TestCaseId,
    ):
        case = await self._datasets.get_case.execute(actor, case_id)
        await self._require_dataset_version_in_project(
            actor,
            project_id,
            case.dataset_version_id,
        )
        return case
