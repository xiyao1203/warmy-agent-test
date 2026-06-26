from __future__ import annotations

from dataclasses import dataclass

import httpx

from agenttest_api_runner.contracts import RunResult


@dataclass(frozen=True, slots=True)
class ResultCallbackTask:
    base_url: str
    internal_token: str
    project_id: str
    result: RunResult


class ControlPlaneCallback:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def post_result(self, task: ResultCallbackTask) -> None:
        client = self._client or httpx.AsyncClient(timeout=30)
        should_close = self._client is None
        try:
            response = await client.post(
                _result_url(task),
                headers={
                    "X-Internal-Token": task.internal_token,
                    "Authorization": "***",
                },
                json={
                    "cases": [
                        {
                            "run_case_id": case.run_case_id,
                            "status": case.status,
                            "output": case.output,
                            "trace": case.trace,
                            "error_type": case.error_type,
                            "error_message": case.error_message,
                            "duration_ms": case.duration_ms,
                        }
                        for case in task.result.cases
                    ]
                },
            )
            response.raise_for_status()
        finally:
            if should_close:
                await client.aclose()


def _result_url(task: ResultCallbackTask) -> str:
    base = task.base_url.rstrip("/")
    return (
        f"{base}/api/v1/projects/{task.project_id}/runs/"
        f"{task.result.run_id}/result"
    )
