import pytest
from agenttest.modules.security.domain.targets import validate_agent_endpoint


def test_rejects_literal_private_target_by_default() -> None:
    with pytest.raises(ValueError, match="private network"):
        validate_agent_endpoint("http://127.0.0.1:8080/chat")


def test_allows_literal_private_target_only_when_enabled() -> None:
    validate_agent_endpoint(
        "http://10.0.0.8:8080/chat",
        allow_private_network=True,
    )


def test_accepts_public_https_target() -> None:
    validate_agent_endpoint("https://agent.example.com/chat")
