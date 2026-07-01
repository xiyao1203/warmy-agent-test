from uuid import uuid4

import pytest
from agenttest.modules.agents.domain.invocation import (
    AgentInvocationConfig,
    InvocationProtocol,
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
