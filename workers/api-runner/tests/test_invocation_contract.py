from agenttest_api_runner.activities import build_agent_request


def test_worker_consumes_typed_invocation_contract() -> None:
    request = build_agent_request(
        {
            "endpoint_url": "https://agent.example/run",
            "protocol": "sse",
            "timeout_seconds": 17,
        },
        {"message": "hello"},
        environment={"headers": {"x-tenant": "demo"}, "variables": {"tenant": "staging"}},
    )

    assert request.url == "https://agent.example/run"
    assert request.mode == "stream"
    assert request.timeout_seconds == 17
    assert request.headers == {"x-tenant": "demo"}
    assert request.variables == {"tenant": "staging"}


def test_worker_keeps_legacy_payload_compatibility() -> None:
    request = build_agent_request(
        {"url": "https://agent.example/run", "mode": "poll"},
        {"message": "hello"},
    )

    assert request.mode == "poll"


def test_worker_injects_redeemed_credentials_only_in_activity() -> None:
    request = build_agent_request(
        {"endpoint_url": "https://agent.example/run"},
        {"message": "hello"},
        environment={
            "credential_bindings": [
                {
                    "kind": "bearer",
                    "injection_location": "header",
                    "injection_name": "Authorization",
                }
            ]
        },
        credential_values={"Authorization": "secret-token"},
    )

    assert request.headers["Authorization"] == "Bearer secret-token"
