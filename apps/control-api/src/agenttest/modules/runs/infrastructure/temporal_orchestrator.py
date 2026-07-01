from __future__ import annotations

from typing import Any

from temporalio.client import Client

from agenttest.modules.runs.application.ports import RunRuntimeUnavailableError
from agenttest.modules.runs.domain.entities import Run, RunCase

RUN_WORKFLOW_NAME = "RunWorkflow"


class TemporalRunOrchestrator:
    """通过 Temporal 启动 API Runner Workflow。

    控制面只发送 JSON 兼容载荷，避免直接依赖 Worker 包或业务数据库。
    """

    def __init__(
        self,
        *,
        task_queue: str,
        address: str | None = None,
        namespace: str = "default",
        control_api_base_url: str | None = None,
        internal_api_token: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._address = address
        self._namespace = namespace
        self._task_queue = task_queue
        self._control_api_base_url = control_api_base_url
        self._internal_api_token = internal_api_token
        self._client = client

    async def start(self, run: Run, cases: list[RunCase]) -> str:
        workflow_id = f"run-{run.run_id.value}"
        client = await self._get_client()
        await client.start_workflow(
            RUN_WORKFLOW_NAME,
            _payload(
                run,
                cases,
                control_api_base_url=self._control_api_base_url,
                internal_api_token=self._internal_api_token,
            ),
            id=workflow_id,
            task_queue=self._task_queue,
        )
        return workflow_id

    async def ensure_available(self) -> None:
        await self._get_client()

    async def cancel(self, run: Run) -> None:
        if run.workflow_id is None:
            return
        client = await self._get_client()
        handle = client.get_workflow_handle(run.workflow_id)
        await handle.signal("cancel")

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if self._address is None:
            raise RunRuntimeUnavailableError("Run execution runtime is unavailable")
        try:
            self._client = await Client.connect(
                self._address,
                namespace=self._namespace,
            )
        except Exception as error:
            raise RunRuntimeUnavailableError("Run execution runtime is unavailable") from error
        return self._client


def _payload(
    run: Run,
    cases: list[RunCase],
    *,
    control_api_base_url: str | None,
    internal_api_token: str | None,
) -> dict[str, object]:
    agent_config = run.plugin_snapshot.get("agent_config")
    if not isinstance(agent_config, dict):
        agent_config = run.config_snapshot.get("agent", run.config_snapshot)
    agent_type = str(run.plugin_snapshot.get("agent_type", "generic_http"))
    payload: dict[str, object] = {
        "run_id": str(run.run_id.value),
        "idempotency_key": run.idempotency_key,
        "agent_config": agent_config,
        "agent_type": agent_type,
        "environment": run.plugin_snapshot.get("environment_config", {}),
        "execution_policy": run.config_snapshot,
        "scorer_configs": run.plugin_snapshot.get("scorer_configs", []),
        "cases": [
            {
                "run_case_id": str(case.run_case_id.value),
                "input": case.input_snapshot,
                "assertions": case.assertion_snapshot,
                "execution_mode": case.execution_mode,
            }
            for case in cases
        ],
    }
    if control_api_base_url and internal_api_token:
        payload["callback"] = {
            "base_url": control_api_base_url,
            "internal_token": internal_api_token,
            "project_id": str(run.project_id.value),
        }
    return payload
