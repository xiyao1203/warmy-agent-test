"""验证 Run 快照从已发布资产到 Worker 载荷的完整契约。

覆盖：
- RunDefinition 包含 agent_config、environment_config、scorer_configs
- _payload 构建正确的 Worker 载荷（含 scorer_configs 和 callback）
- plugin_snapshot 字段完整性与向后兼容
- 不同执行策略（超时、重试）正确传递
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from agenttest.bootstrap.run_source import (
    _run_definition_case,
    browser_profile_snapshot,
    secret_free_credential_bindings,
)
from agenttest.modules.agents.domain.invocation import (
    AgentInvocationConfig,
    InvocationProtocol,
    invocation_from_stored_config,
)
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.datasets.public import DatasetVersionId, ExecutionMode, TestCase, TestCaseId
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.ports import RunDefinition, RunDefinitionCase
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.infrastructure.temporal_orchestrator import (
    _payload,
)
from agenttest.modules.test_plans.public import TestPlanVersionId


def make_run_definition(
    *,
    agent_config: dict[str, object] | None = None,
    environment_config: dict[str, object] | None = None,
    scorer_configs: list[dict[str, object]] | None = None,
    config_snapshot: dict[str, object] | None = None,
) -> RunDefinition:
    return RunDefinition(
        project_id=ProjectId(uuid4()),
        test_plan_version_id=TestPlanVersionId(uuid4()),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        config_snapshot=config_snapshot or {"timeout": 60, "max_retries": 2},
        plugin_snapshot={
            "id": "generic-http",
            "version": "1.0.0",
            "agent_type": "http_agent",
            "agent_config": agent_config
            or {
                "endpoint_url": "https://agent.example/run",
                "protocol": "sync_json",
                "response_path": "output",
                "timeout_seconds": 30,
                "credential_binding_ids": [],
            },
            "environment_config": environment_config or {},
            "scorer_configs": scorer_configs or [],
        },
        cases=[
            RunDefinitionCase(
                test_case_id=uuid4(),
                name="greeting test",
                input_snapshot={"message": "hello"},
                assertion_snapshot=[{"type": "contains", "value": "hello"}],
            ),
            RunDefinitionCase(
                test_case_id=uuid4(),
                name="error test",
                input_snapshot={"message": "fail"},
                assertion_snapshot=[{"type": "contains", "value": "ok"}],
            ),
        ],
    )


def make_run(definition: RunDefinition) -> Run:
    return Run.create(
        run_id=RunId.new(),
        project_id=definition.project_id,
        test_plan_version_id=definition.test_plan_version_id,
        agent_version_id=definition.agent_version_id,
        dataset_version_id=definition.dataset_version_id,
        idempotency_key="snapshot-test-key",
        created_by=UserId.new(),
        config_snapshot=definition.config_snapshot,
        plugin_snapshot=definition.plugin_snapshot,
        total_cases=len(definition.cases),
    )


def make_cases(run: Run, definition: RunDefinition) -> list[RunCase]:
    return [
        RunCase.create(
            run_case_id=RunCaseId.new(),
            run_id=run.run_id,
            test_case_id=case.test_case_id,
            name=case.name,
            input_snapshot=case.input_snapshot,
            assertion_snapshot=case.assertion_snapshot,
        )
        for case in definition.cases
    ]


# ── RunDefinition 契约测试 ─────────────────────────────────────────────


def test_run_definition_includes_agent_config_via_invocation_contract() -> None:
    """RunDefinition.plugin_snapshot 包含通过 AgentInvocationConfig 序列化的 agent_config。"""
    config = AgentInvocationConfig(
        endpoint_url="https://agent.example/run",
        protocol=InvocationProtocol.SYNC_JSON,
        response_path="output",
    )
    definition = make_run_definition(
        agent_config=config.model_dump(mode="json"),
    )

    agent_config = definition.plugin_snapshot["agent_config"]
    assert isinstance(agent_config, dict)
    assert agent_config["endpoint_url"] == "https://agent.example/run"
    assert agent_config["protocol"] == "sync_json"


def test_run_definition_includes_environment_config_without_credentials() -> None:
    """RunDefinition 携带环境变量和 header，但不包含明文凭证值。"""
    definition = make_run_definition(
        environment_config={
            "variables": {"API_ENV": "staging"},
            "headers": {"X-Custom": "value"},
            "credential_binding_ids": [str(uuid4())],
            "credential_bindings": secret_free_credential_bindings(
                [
                    {
                        "id": str(uuid4()),
                        "kind": "api_key",
                        "injection_location": "header",
                        "injection_name": "Authorization",
                        "encrypted_value": "aes-gcm:ciphertext",
                    }
                ]
            ),
        },
    )

    env = definition.plugin_snapshot["environment_config"]
    assert isinstance(env, dict)
    assert env["variables"] == {"API_ENV": "staging"}
    assert env["headers"] == {"X-Custom": "value"}
    # Workflow 快照只保留注入元数据，不能包含密文或明文
    for binding in env.get("credential_bindings", []):
        assert "encrypted_value" not in binding
        assert set(binding) == {"id", "kind", "injection_location", "injection_name"}


def test_run_source_strips_encrypted_credential_values() -> None:
    result = secret_free_credential_bindings(
        [
            {
                "id": str(uuid4()),
                "kind": "bearer",
                "injection_location": "header",
                "injection_name": "Authorization",
                "encrypted_value": "ciphertext",
            }
        ]
    )

    assert "encrypted_value" not in result[0]


def test_run_source_browser_profile_snapshot_contains_only_immutable_reference() -> None:
    now = datetime.now(UTC)
    profile = BrowserProfile.create(
        project_id=uuid4(),
        name="TapNow",
        target_domain="app.tapnow.ai",
        created_by=uuid4(),
        now=now,
    )
    profile.store_auth_state(
        envelope="v1.encrypted-secret",
        sha256="a" * 64,
        saved_at=now,
    )

    snapshot = browser_profile_snapshot(profile)

    assert snapshot == {
        "browser_profile_id": str(profile.id),
        "auth_state_version": 1,
        "auth_state_sha256": "a" * 64,
    }
    assert "encrypted" not in repr(snapshot)


def test_plan_run_case_uses_one_secret_free_snapshot_for_storage_and_temporal() -> None:
    case = TestCase.create(
        case_id=TestCaseId.new(),
        dataset_version_id=DatasetVersionId.new(),
        name="secure plan case",
        input={
            "message": "hello",
            "apiKey": "input-secret",
            "token_usage": 7,
        },
        assertions=[
            {
                "type": "contains",
                "value": "hello",
                "clientSecret": "assertion-secret",
            }
        ],
        execution_mode=ExecutionMode.API,
        created_by=UserId.new(),
    )

    definition_case = _run_definition_case(case)

    assert definition_case.input_snapshot == {
        "message": "hello",
        "apiKey": "[REDACTED]",
        "token_usage": 7,
    }
    assert definition_case.assertion_snapshot[0]["clientSecret"] == "[REDACTED]"
    assert definition_case.input_snapshot == definition_case.case_spec_snapshot["input"]
    assert definition_case.assertion_snapshot == definition_case.case_spec_snapshot["assertions"]


def test_run_definition_includes_scorer_configs_for_all_scorer_types() -> None:
    """RunDefinition 可以携带多种评分器类型配置。"""
    scorer_configs = [
        {
            "scorer_version_id": str(uuid4()),
            "scorer_type": "rule",
            "weight": 1.0,
            "threshold": 0.8,
            "config": {"rule_type": "contains", "expected": "hello"},
        },
        {
            "scorer_version_id": str(uuid4()),
            "scorer_type": "reference",
            "weight": 0.5,
            "threshold": 0.7,
            "config": {"comparison_method": "exact"},
        },
    ]
    definition = make_run_definition(scorer_configs=scorer_configs)

    configs = definition.plugin_snapshot["scorer_configs"]
    assert isinstance(configs, list)
    assert len(configs) == 2
    assert configs[0]["scorer_type"] == "rule"
    assert configs[1]["scorer_type"] == "reference"


def test_run_definition_cases_count_matches_cases_list() -> None:
    """RunDefinition 用例数必须与 cases 列表一致。"""
    definition = make_run_definition()
    assert len(definition.cases) == 2
    assert definition.cases[0].name == "greeting test"


# ── Worker 载荷构建测试 ────────────────────────────────────────────────


def test_payload_includes_scorer_configs_for_worker() -> None:
    """_payload 将 scorer_configs 传递到 Worker 载荷中。"""
    definition = make_run_definition(
        scorer_configs=[
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "rule",
                "weight": 1.0,
                "threshold": None,
                "config": {"rule_type": "contains", "expected": "ok"},
            }
        ]
    )
    run = make_run(definition)
    run_cases = make_cases(run, definition)
    payload = _payload(
        run,
        run_cases,
        control_api_base_url="https://control.example",
        internal_api_token="secret-token",
    )

    assert "scorer_configs" in payload
    assert isinstance(payload["scorer_configs"], list)
    assert len(payload["scorer_configs"]) == 1
    assert payload["scorer_configs"][0]["scorer_type"] == "rule"


def test_payload_includes_execution_policy_from_config_snapshot() -> None:
    """_payload 将 config_snapshot 作为 execution_policy 传递给 Worker。"""
    definition = make_run_definition(
        config_snapshot={
            "timeout": 120,
            "max_retries": 3,
            "concurrency": 2,
        }
    )
    run = make_run(definition)
    run_cases = make_cases(run, definition)
    payload = _payload(
        run,
        run_cases,
        control_api_base_url="https://control.example",
        internal_api_token="secret-token",
    )

    assert payload["execution_policy"] == {
        "timeout": 120,
        "max_retries": 3,
        "concurrency": 2,
    }


def test_payload_includes_callback_when_url_and_token_provided() -> None:
    """_payload 在提供 URL 和 Token 时才包含 callback。"""
    definition = make_run_definition()
    run = make_run(definition)
    run_cases = make_cases(run, definition)

    # 提供 callback 参数
    payload_with = _payload(
        run,
        run_cases,
        control_api_base_url="https://control.example",
        internal_api_token="secret-token",
    )
    assert "callback" in payload_with
    assert payload_with["callback"]["base_url"] == "https://control.example"
    assert payload_with["callback"]["internal_token"] == "secret-token"

    # 不提供 callback 参数
    payload_without = _payload(
        run,
        run_cases,
        control_api_base_url=None,
        internal_api_token=None,
    )
    assert "callback" not in payload_without


def test_payload_cases_preserve_input_and_assertions() -> None:
    """_payload 构建的用例载荷保留完整 input 和 assertions。"""
    definition = make_run_definition()
    run = make_run(definition)
    run_cases = make_cases(run, definition)
    payload = _payload(
        run,
        run_cases,
        control_api_base_url="https://control.example",
        internal_api_token="secret-token",
    )

    assert len(payload["cases"]) == 2
    case = payload["cases"][0]
    assert case["input"] == {"message": "hello"}
    assert case["assertions"] == [{"type": "contains", "value": "hello"}]


def test_payload_includes_environment_config_from_plugin_snapshot() -> None:
    """_payload 将 plugin_snapshot 的 environment_config 传递为 environment。"""
    definition = make_run_definition(
        environment_config={
            "variables": {"STAGE": "test"},
            "headers": {"Accept": "application/json"},
        }
    )
    run = make_run(definition)
    run_cases = make_cases(run, definition)
    payload = _payload(
        run,
        run_cases,
        control_api_base_url="https://control.example",
        internal_api_token="secret-token",
    )

    assert payload["environment"] == {
        "variables": {"STAGE": "test"},
        "headers": {"Accept": "application/json"},
    }


def test_payload_includes_browser_profile_reference_without_auth_material() -> None:
    definition = make_run_definition()
    definition.plugin_snapshot["browser_profile_snapshot"] = {
        "browser_profile_id": str(uuid4()),
        "auth_state_version": 3,
        "auth_state_sha256": "b" * 64,
    }
    run = make_run(definition)

    payload = _payload(
        run,
        make_cases(run, definition),
        control_api_base_url="https://control.example",
        internal_api_token="secret-token",
    )

    assert (
        payload["browser_profile_snapshot"]
        == definition.plugin_snapshot["browser_profile_snapshot"]
    )
    assert "cookie" not in repr(payload).lower()
    assert "auth_state_envelope" not in repr(payload)


# ── 协议兼容性测试 ─────────────────────────────────────────────────────


def test_invocation_from_stored_config_handles_legacy_api_url() -> None:
    """旧版 api_url 格式可正确转换为 endpoint_url。"""
    legacy_config: dict[str, object] = {
        "api_url": "https://legacy.example/api",
        "protocol": "sync_json",
        "request_template": {"input": "{{input}}"},
        "response_path": "data.result",
        "timeout": 45,
    }
    config = invocation_from_stored_config(legacy_config)
    assert str(config.endpoint_url) == "https://legacy.example/api"
    assert config.protocol == InvocationProtocol.SYNC_JSON
    assert config.timeout_seconds == 45


def test_invocation_from_stored_config_prefers_new_endpoint_url() -> None:
    """新版 endpoint_url 格式直接通过验证。"""
    new_config: dict[str, object] = {
        "endpoint_url": "https://new.example/api",
        "protocol": "openai_chat",
        "request_template": {"messages": [{"role": "user", "content": "{{input}}"}]},
        "response_path": "choices.0.message.content",
        "timeout_seconds": 60,
        "credential_binding_ids": [str(uuid4())],
    }
    config = invocation_from_stored_config(new_config)
    assert str(config.endpoint_url) == "https://new.example/api"
    assert config.protocol == InvocationProtocol.OPENAI_CHAT
    assert config.credential_binding_ids is not None
