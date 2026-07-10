from __future__ import annotations

import pytest


def test_worker_settings_require_temporal_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTTEST_TEMPORAL_ADDRESS", raising=False)

    from agenttest_api_runner.main import WorkerSettings

    with pytest.raises(RuntimeError, match="Temporal address"):
        WorkerSettings.from_environment()


def test_worker_settings_use_control_plane_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTEST_TEMPORAL_ADDRESS", "temporal.example:7233")
    monkeypatch.delenv("AGENTTEST_TEMPORAL_NAMESPACE", raising=False)
    monkeypatch.delenv("AGENTTEST_TEMPORAL_TASK_QUEUE", raising=False)

    from agenttest_api_runner.main import WorkerSettings

    settings = WorkerSettings.from_environment()

    assert settings.address == "temporal.example:7233"
    assert settings.namespace == "default"
    assert settings.task_queue == "agenttest-api-runner"


@pytest.mark.asyncio
async def test_run_registers_run_workflow_and_all_activities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENTTEST_TEMPORAL_ADDRESS", "temporal.example:7233")

    from agenttest_api_runner import main

    connected: dict[str, object] = {}
    worker_options: dict[str, object] = {}

    async def connect(address: str, *, namespace: str) -> object:
        connected.update(address=address, namespace=namespace)
        return object()

    class FakeWorker:
        def __init__(self, client: object, **options: object) -> None:
            worker_options.update(client=client, **options)

        async def run(self) -> None:
            worker_options["ran"] = True

    monkeypatch.setattr(main.Client, "connect", connect)
    monkeypatch.setattr(main, "Worker", FakeWorker)

    await main.run()

    assert connected == {
        "address": "temporal.example:7233",
        "namespace": "default",
    }
    assert worker_options["task_queue"] == "agenttest-api-runner"
    assert worker_options["workflows"] == [main.RunWorkflow, main.TargetAgentChatWorkflow]
    assert worker_options["activities"] == [
        main.execute_agent_case,
        main.post_run_result,
        main.capture_page_snapshot,
        main.run_playwright_case,
        main.run_codex_browser_case,
        main.execute_target_chat,
        main.run_tapnow_case,
    ]
    assert worker_options["ran"] is True
