from __future__ import annotations

import httpx
import pytest
from agenttest_api_runner.callback import ControlPlaneCallback, ResultCallbackTask
from agenttest_api_runner.contracts import RunCaseResult, RunResult
from temporalio.converter import DataConverter


@pytest.mark.asyncio
async def test_callback_posts_run_result_to_control_plane_with_internal_token() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"status": "passed"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    callback = ControlPlaneCallback(client=client)

    await callback.post_result(
        ResultCallbackTask(
            base_url="https://control.example",
            internal_token="secret-token",
            project_id="project-1",
            result=RunResult(
                run_id="run-1",
                status="passed",
                cases=[
                    RunCaseResult(
                        run_case_id="case-1",
                        status="passed",
                        output={"message": "ok"},
                        trace=[{"name": "http.request"}],
                        duration_ms=12,
                    )
                ],
            ),
        )
    )

    assert requests[0].url == (
        "https://control.example/api/v1/projects/project-1/runs/run-1/result"
    )
    assert requests[0].headers["x-internal-token"] == "secret-token"
    assert requests[0].headers["authorization"] == "***"
    assert requests[0].read() == (
        b'{"cases":[{"run_case_id":"case-1","status":"passed",'
        b'"output":{"message":"ok"},"trace":[{"name":"http.request"}],'
        b'"error_type":null,"error_message":null,"duration_ms":12,"scores":[]}]}'
    )
    await client.aclose()


@pytest.mark.asyncio
async def test_callback_raises_for_control_plane_error() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "denied"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    callback = ControlPlaneCallback(client=client)

    with pytest.raises(httpx.HTTPStatusError):
        await callback.post_result(
            ResultCallbackTask(
                base_url="https://control.example",
                internal_token="bad-token",
                project_id="project-1",
                result=RunResult(run_id="run-1", status="error", cases=[]),
            )
        )
    await client.aclose()


@pytest.mark.asyncio
async def test_temporal_callback_payload_allows_nested_case_output() -> None:
    task = ResultCallbackTask(
        base_url="https://control.example",
        internal_token="secret-token",
        project_id="project-1",
        result=RunResult(
            run_id="run-1",
            status="passed",
            cases=[
                RunCaseResult(
                    run_case_id="case-1",
                    status="passed",
                    output={
                        "status": "passed",
                        "steps": [{"action": "open", "result": "planned"}],
                        "metadata": {"screenshot_count": 1},
                    },
                )
            ],
        ),
    )

    payloads = await DataConverter.default.encode([task])
    decoded = await DataConverter.default.decode(payloads, [ResultCallbackTask])

    assert decoded[0] == task
