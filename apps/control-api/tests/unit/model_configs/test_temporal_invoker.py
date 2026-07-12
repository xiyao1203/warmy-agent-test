from datetime import timedelta
from types import SimpleNamespace

import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.model_configs.application.ports import (
    InvocationMessage,
    ModelStreamCallback,
    StreamContext,
)
from agenttest.modules.model_configs.domain.entities import (
    ModelConfiguration,
)
from agenttest.modules.model_configs.domain.value_objects import ProviderType
from agenttest.modules.model_configs.infrastructure.temporal_invoker import (
    TemporalModelInvoker,
)
from agenttest.modules.projects.public import ProjectId


def model_config() -> ModelConfiguration:
    return ModelConfiguration.create(
        project_id=ProjectId.new(),
        name="chat",
        provider_type=ProviderType.OPENAI_COMPATIBLE,
        base_url="https://model.example/v1",
        model_name="model",
        encrypted_api_key="encrypted",
        api_key_hint="...pted",
        supports_text=True,
        supports_vision=False,
        created_by=UserId.new(),
    )


@pytest.mark.asyncio
async def test_invoke_bounds_workflow_execution_time(monkeypatch) -> None:
    seen: dict[str, object] = {}

    class Client:
        async def execute_workflow(self, *_args, **kwargs):
            seen["execution_timeout"] = kwargs.get("execution_timeout")
            return {"content": "ok"}

    async def connect(*_args, **_kwargs):
        return Client()

    monkeypatch.setattr(
        "agenttest.modules.model_configs.infrastructure.temporal_invoker.Client.connect",
        connect,
    )
    invoker = TemporalModelInvoker(address="temporal", namespace="default", task_queue="models")

    await invoker.invoke(
        model_config(),
        [InvocationMessage(role="user", content="hi")],
        timeout_seconds=15,
    )

    assert seen["execution_timeout"] == timedelta(seconds=45)


@pytest.mark.asyncio
async def test_stream_uses_requested_workflow_id(monkeypatch) -> None:
    seen: dict[str, object] = {}

    class Handle:
        async def result(self):
            return {"content": "done", "cancelled": False}

    class Client:
        async def start_workflow(self, *_args, **kwargs):
            seen["workflow_id"] = kwargs["id"]
            return Handle()

    async def connect(*_args, **_kwargs):
        return Client()

    monkeypatch.setattr(
        "agenttest.modules.model_configs.infrastructure.temporal_invoker.Client.connect",
        connect,
    )
    config = model_config()
    invoker = TemporalModelInvoker(address="temporal", namespace="default", task_queue="models")
    context = StreamContext(workflow_id="chat-generation-123")

    result = await invoker.stream(
        config,
        [SimpleNamespace(role="user", content="hi", tool_calls=None, tool_call_id=None, name=None)],
        callback=ModelStreamCallback(url="http://callback", internal_token="token"),
        stream_ctx=context,
    )

    assert seen["workflow_id"] == "chat-generation-123"
    assert context.workflow_id == "chat-generation-123"
    assert result.cancelled is False
