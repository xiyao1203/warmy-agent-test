from uuid import uuid4

import pytest
from agenttest.modules.agents.api.schemas import AgentConfigRequest
from agenttest.modules.agents.public import (
    AgentInvocationConfig,
    InvocationProtocol,
    invocation_from_stored_config,
)
from pydantic import ValidationError


def test_invocation_config_exposes_only_credential_references() -> None:
    credential_id = uuid4()

    config = AgentInvocationConfig(
        endpoint_url="https://agent.example/v1/chat",
        protocol=InvocationProtocol.OPENAI_CHAT,
        request_template={"messages": "{{ input.messages }}"},
        response_path="choices.0.message.content",
        timeout_seconds=45,
        credential_binding_ids=[credential_id],
    )

    assert config.credential_binding_ids == [credential_id]
    assert "api_key" not in config.model_dump(mode="json")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("endpoint_url", "not-a-url"),
        ("timeout_seconds", 0),
        ("response_path", ""),
    ],
)
def test_invocation_config_rejects_invalid_runtime_fields(field: str, value: object) -> None:
    payload: dict[str, object] = {
        "endpoint_url": "https://agent.example/run",
        "response_path": "output",
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        AgentInvocationConfig.model_validate(payload)


def test_invocation_config_rejects_unknown_or_secret_fields() -> None:
    with pytest.raises(ValidationError):
        AgentInvocationConfig.model_validate(
            {
                "endpoint_url": "https://agent.example/run",
                "response_path": "output",
                "api_key": "must-not-be-stored-here",
            }
        )


def test_legacy_agent_config_is_normalized_without_inventing_credentials() -> None:
    config = invocation_from_stored_config({"api_url": "https://agent.example/run", "timeout": 18})

    assert config.endpoint_url.unicode_string() == "https://agent.example/run"
    assert config.timeout_seconds == 18
    assert config.protocol is InvocationProtocol.SYNC_JSON
    assert config.credential_binding_ids == []


def test_invocation_config_carries_secret_free_target_config() -> None:
    config = invocation_from_stored_config(
        {
            "api_url": "https://app.tapnow.ai/canvas/demo",
            "target_config": {
                "browser_profile_id": "profile-1",
                "entry_url": "https://app.tapnow.ai/canvas/demo",
                "login": {
                    "credential_binding_id": "credential-1",
                    "strategy": "credential",
                },
                "plugin_id": "tapnow-canvas-agent",
            },
        }
    )

    assert config.target_config["entry_url"] == "https://app.tapnow.ai/canvas/demo"
    assert config.target_config["browser_profile_id"] == "profile-1"
    assert "secret-password" not in str(config.model_dump(mode="json"))


def test_api_agent_config_persists_full_invocation_contract() -> None:
    credential_id = uuid4()
    request = AgentConfigRequest(
        api_url="https://agent.example/v1/chat",
        protocol="openai_chat",
        request_template={"messages": "{{ input.messages }}"},
        response_path="choices.0.message.content",
        credential_binding_ids=[credential_id],
        timeout=42,
    )

    stored = request.to_domain().to_dict()

    assert stored["protocol"] == "openai_chat"
    assert stored["request_template"] == {"messages": "{{ input.messages }}"}
    assert stored["response_path"] == "choices.0.message.content"
    assert stored["credential_binding_ids"] == [str(credential_id)]
