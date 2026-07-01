from agenttest_api_runner.activities import build_agent_request


def test_worker_consumes_typed_invocation_contract() -> None:
    request = build_agent_request(
        {
            "endpoint_url": "https://agent.example/run",
            "protocol": "sse",
            "timeout_seconds": 17,
        },
        {"message": "hello"},
    )

    assert request.url == "https://agent.example/run"
    assert request.mode == "stream"
    assert request.timeout_seconds == 17


def test_worker_keeps_legacy_payload_compatibility() -> None:
    request = build_agent_request(
        {"url": "https://agent.example/run", "mode": "poll"},
        {"message": "hello"},
    )

    assert request.mode == "poll"
