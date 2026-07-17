"""PydanticAI 自定义 Model：通过 Temporal Model Runner 调用 LLM。

将 PydanticAI 的 Agent 消息格式转换为 OpenAI-Compatible JSON，
经 Temporal → Worker → Provider 管道执行真实调用，并回译为
PydanticAI ModelResponse（含 text + tool_calls）。

关键设计：
- 不直接连接 LLM Provider，保持 Temporal 安全边界
- 透传 tool_calls / tool_call_id / name 字段，支持原生 function calling
- model_name / system 属性由外部注入，与项目模型配置对齐
"""

from __future__ import annotations

import asyncio
import json
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelResponsePart,
    ModelResponseStreamEvent,
    PartDeltaEvent,
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    TextPartDelta,
    ToolCallPart,
    ToolCallPartDelta,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import Model, ModelRequestParameters, StreamedResponse
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import RequestUsage

from agenttest.modules.model_configs.public import (
    InvocationMessage,
    InvocationResult,
    ModelStreamCallback,
    StreamContext,
)


async def _handle_callback_stream(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    chunk_queue: asyncio.Queue[str],
    callback_token: str,
) -> None:
    """最小 HTTP 处理器：接收 Worker SSE chunk POST。

    解析原始 HTTP 请求（无框架依赖），验证 Internal-Token，
    提取 content 字段 push 到 chunk_queue。
    """
    try:
        raw = await asyncio.wait_for(reader.read(131072), timeout=15.0)
        text = raw.decode("utf-8", errors="replace")
        header_end = text.find("\r\n\r\n")
        if header_end < 0:
            return
        headers_section = text[:header_end]
        body_text = text[header_end + 4 :]

        if f"X-Internal-Token: {callback_token}" not in headers_section:
            writer.write(b"HTTP/1.1 401 Unauthorized\r\nContent-Length: 2\r\n\r\n{}")
            await writer.drain()
            return

        body = json.loads(body_text)
        content = body.get("content", "")
        if content:
            await chunk_queue.put(content)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}")
        await writer.drain()
    except Exception:
        try:
            writer.write(b"HTTP/1.1 500 Error\r\nContent-Length: 2\r\n\r\n{}")
            await writer.drain()
        except Exception:
            pass
    finally:
        writer.close()
        await writer.wait_closed()


class TemporalModel(Model):
    """通过 Temporal 管道调用真实 LLM 的 PydanticAI Model 适配器。

    使用方式：
        model = TemporalModel(
            invoker=temporal_invoker,
            config=model_config,
            model_name="gpt-4o",
        )
        agent = Agent(model, system_prompt="...", tools=[...])
        result = await agent.run("用户消息")
    """

    def __init__(
        self,
        *,
        invoker,  # ModelInvoker
        config,  # ModelConfiguration
        display_name: str = "temporal-model",
    ) -> None:
        super().__init__()
        self._invoker = invoker
        self._config = config
        self._display_name = display_name

    @property
    def model_name(self) -> str:
        return self._display_name

    @property
    def system(self) -> str:
        return "temporal"

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """执行一次模型调用并返回 PydanticAI 兼容响应。"""
        invocation_messages = _to_invocation_messages(messages)
        tools = _build_tools_payload(model_request_parameters)

        response_format = None
        if tools:
            response_format = None  # tool calling 不需要 json_object
        elif model_request_parameters.output_mode != "text":
            response_format = {"type": "json_object"}

        result = await self._invoker.invoke(
            self._config,
            invocation_messages,
            response_format=response_format,
            timeout_seconds=_model_setting_int(model_settings, "timeout", 60),
            max_tokens=_model_setting_int(model_settings, "max_tokens", 2048),
        )

        parts = _parse_response_parts(result.content, tools)
        usage = RequestUsage(
            input_tokens=result.prompt_tokens,
            output_tokens=result.completion_tokens,
        )
        return ModelResponse(
            parts=parts,
            usage=usage,
            model_name=self._display_name,
            timestamp=datetime.now(UTC),
            provider_name=self.system,
        )

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        """流式调用：通过 in-process 回调接收 Worker SSE 增量。

        启动本地 HTTP server 作为回调端点，Worker 逐 chunk POST，
        Agent 通过 asyncio.Queue 实时产出 PydanticAI delta 事件。
        支持 Temporal Workflow 取消信号传播。

        安全设计：
        - Callback token 每次请求随机生成（per-request rotation）
        - 服务器仅绑定 127.0.0.1，不暴露到外部网络
        - Worker 仅通过 callback URL 单向推送，无法访问任何 Control API 资源
        """
        invocation_messages = _to_invocation_messages(messages)
        tools = _build_tools_payload(model_request_parameters)

        timeout = _model_setting_int(model_settings, "timeout", 60)
        max_tokens = _model_setting_int(model_settings, "max_tokens", 2048)

        # ── 启动本地回调服务器 ──
        chunk_queue: asyncio.Queue[str] = asyncio.Queue()
        callback_token = secrets.token_hex(16)

        server = await asyncio.start_server(
            lambda r, w: _handle_callback_stream(
                r,
                w,
                chunk_queue=chunk_queue,
                callback_token=callback_token,
            ),
            host="127.0.0.1",
            port=0,
        )
        port = server.sockets[0].getsockname()[1] if server.sockets else 0
        callback = ModelStreamCallback(
            url=f"http://127.0.0.1:{port}/callback",
            internal_token=callback_token,
        )

        # ── 可取消的流式上下文 ──
        stream_ctx = StreamContext()

        # ── 后台启动流式 Workflow ──
        stream_result: list[InvocationResult | None] = [None]
        stream_error: list[Exception | None] = [None]

        async def _run_stream() -> None:
            try:
                result = await self._invoker.stream(
                    self._config,
                    invocation_messages,
                    callback=callback,
                    timeout_seconds=timeout,
                    max_tokens=max_tokens,
                    stream_ctx=stream_ctx,
                )
                stream_result[0] = result
            except Exception as exc:
                stream_error[0] = exc
            finally:
                await chunk_queue.put("")  # sentinel

        stream_task = asyncio.ensure_future(_run_stream())

        model_name = self._display_name
        ts = datetime.now(UTC)

        class _IncrementalStreamedResponse(StreamedResponse):
            def __init__(self) -> None:
                super().__init__(model_request_parameters=model_request_parameters)
                self._model = model_name
                self._ts = ts

            @property
            def model_name(self) -> str:
                return self._model

            @property
            def provider_name(self) -> str:
                return "temporal"

            @property
            def provider_url(self) -> None:
                return None

            @property
            def timestamp(self) -> datetime:
                return self._ts

            async def _get_event_iterator(
                self,
            ) -> AsyncIterator[ModelResponseStreamEvent]:
                text_chunks: list[str] = []

                # Phase A: 实时流式文本增量（Worker SSE → 本地 callback → queue）
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            chunk_queue.get(),
                            timeout=timeout + 15,
                        )
                    except TimeoutError:
                        break
                    if chunk == "":  # sentinel
                        break
                    text_chunks.append(chunk)
                    yield _text_delta_event(chunk)

                # Phase B: 收尾 — 错误传播 + tool calls
                err = stream_error[0]
                if err:
                    raise err

                final = stream_result[0]
                all_parts: list[ModelResponsePart] = []
                if final:
                    self._usage = RequestUsage(
                        input_tokens=final.prompt_tokens,
                        output_tokens=final.completion_tokens,
                    )
                    all_parts = _parse_response_parts(final.content, tools)

                # 回退：如果流式 chunks 为空，用完整响应做句子分块
                if not text_chunks and final:
                    for tp in [p for p in all_parts if isinstance(p, TextPart)]:
                        for sent in _split_sentences(tp.content):
                            if sent:
                                yield _text_delta_event(sent)

                # Tool calls（流式无 tool_call chunk，从最终结果解析）
                tool_call_parts = [p for p in all_parts if isinstance(p, ToolCallPart)]
                for i, tc in enumerate(tool_call_parts):
                    yield _tool_call_delta_event(
                        index=i,
                        tool_name=tc.tool_name,
                        tool_call_id=tc.tool_call_id,
                        args=tc.args if isinstance(tc.args, str) else "{}",
                    )

                # PydanticAI 要求至少一个事件
                if not text_chunks and not all_parts:
                    yield _text_delta_event("")

        try:
            yield _IncrementalStreamedResponse()
        finally:
            # 取消顺序：先取消 Temporal workflow → 关闭本地 server → 取消本地 task
            if stream_ctx.workflow_id:
                await self._invoker.cancel_workflow(stream_ctx.workflow_id)
            server.close()
            await server.wait_closed()
            if not stream_task.done():
                stream_task.cancel()


# ── 流式辅助 ───────────────────────────────────────────────────────


def _split_sentences(text: str) -> list[str]:
    """按句子边界拆分文本，最小 chunk 不低于 8 个字符。"""
    if not text:
        return [text]
    import re

    # 按句号/换行/问号/感叹号切分，保留分隔符
    parts = re.split(r"(?<=[。！？\n])", text)
    chunks: list[str] = []
    for part in parts:
        if not part:
            continue
        if len(part) <= 80:
            chunks.append(part)
        else:
            # 对长句再按逗号分
            sub = re.split(r"(?<=[，,;；])", part)
            for s in sub:
                if s:
                    chunks.append(s)
    # 确保至少有一个 chunk
    return chunks if chunks else [text]


def _model_setting_int(
    settings: ModelSettings | None,
    key: str,
    default: int,
) -> int:
    """Return integer model setting values while ignoring provider-specific objects."""
    if settings is None:
        return default
    value = settings.get(key, default)
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return int(value)
    return default


# ── 消息转换 ───────────────────────────────────────────────────────


def _to_invocation_messages(messages: list[ModelMessage]) -> list[InvocationMessage]:
    """将 PydanticAI ModelMessage 列表转为平台 InvocationMessage。"""
    result: list[InvocationMessage] = []
    for msg in messages:
        if isinstance(msg, ModelRequest):
            # 处理 instructions（system prompt）
            if msg.instructions:
                result.append(
                    InvocationMessage(
                        role="system",
                        content=msg.instructions,
                    )
                )
            for request_part in msg.parts:
                if isinstance(request_part, SystemPromptPart):
                    result.append(
                        InvocationMessage(
                            role="system",
                            content=request_part.content,
                        )
                    )
                elif isinstance(request_part, UserPromptPart):
                    result.append(
                        InvocationMessage(
                            role="user",
                            content=_content_to_string(request_part.content),
                        )
                    )
                elif isinstance(request_part, ToolReturnPart):
                    result.append(
                        InvocationMessage(
                            role="tool",
                            content=_tool_return_content(request_part),
                            tool_call_id=request_part.tool_call_id,
                            name=request_part.tool_name,
                        )
                    )
                elif isinstance(request_part, RetryPromptPart):
                    result.append(
                        InvocationMessage(
                            role="user",
                            content=_content_to_string(request_part.content),
                        )
                    )
        elif isinstance(msg, ModelResponse):
            for response_part in msg.parts:
                if isinstance(response_part, TextPart):
                    result.append(
                        InvocationMessage(
                            role="assistant",
                            content=response_part.content,
                        )
                    )
                elif isinstance(response_part, ToolCallPart):
                    args = response_part.args
                    arguments = (
                        args
                        if isinstance(args, str)
                        else json.dumps(args or {}, ensure_ascii=False)
                    )
                    result.append(
                        InvocationMessage(
                            role="assistant",
                            content=arguments,
                            tool_calls=[
                                {
                                    "id": response_part.tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": response_part.tool_name,
                                        "arguments": arguments,
                                    },
                                }
                            ]
                            if response_part.tool_name
                            else None,
                        )
                    )
    return result


def _content_to_string(content: object) -> str:
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(content)


def _tool_return_content(part: ToolReturnPart) -> str:
    """序列化 tool return 内容为字符串。"""
    content = part.content
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(content)


def _build_tools_payload(params: ModelRequestParameters) -> list[dict] | None:
    """从 ModelRequestParameters 构建 OpenAI tools 数组。"""
    if not params.function_tools:
        return None
    tools = []
    for td in params.function_tools:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": td.name,
                    "description": td.description or "",
                    "parameters": td.parameters_json_schema,
                },
            }
        )
    return tools if tools else None


def _parse_response_parts(content: str, tools: list[dict] | None) -> list[ModelResponsePart]:
    """解析 LLM 响应为 PydanticAI parts（text + tool_calls）。

    优先尝试解析为带 tool_calls 的 JSON，失败则作为纯文本处理。
    """
    # 尝试解析为 tool call 响应
    if tools and content.strip().startswith("{"):
        try:
            data = json.loads(content)
            if "tool_calls" in data:
                parts: list[ModelResponsePart] = []
                for tc in data["tool_calls"]:
                    func = tc.get("function", {})
                    parts.append(
                        ToolCallPart(
                            tool_name=func.get("name", ""),
                            args=func.get("arguments", "{}"),
                            tool_call_id=tc.get("id", ""),
                        )
                    )
                if parts:
                    return parts
            # 如果 LLM 直接返回了 text + tool_calls
            text = data.get("content", "")
            tcs = data.get("tool_calls", [])
            if not tcs and text:
                return [TextPart(content=text)]
        except (json.JSONDecodeError, KeyError):
            pass

    # 尝试解析 OpenAI 原生 tool_calls 格式（choices[0].message.tool_calls）
    if content.strip().startswith("{"):
        try:
            data = json.loads(content)
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                text = msg.get("content", "")
                tcs = msg.get("tool_calls", [])
                response_parts: list[ModelResponsePart] = []
                if text:
                    response_parts.append(TextPart(content=text))
                for tc in tcs:
                    func = tc.get("function", {})
                    response_parts.append(
                        ToolCallPart(
                            tool_name=func.get("name", ""),
                            args=func.get("arguments", "{}"),
                            tool_call_id=tc.get("id", ""),
                        )
                    )
                if response_parts:
                    return response_parts
        except (json.JSONDecodeError, KeyError):
            pass

    return [TextPart(content=content)]


def _text_delta_event(text: str) -> ModelResponseStreamEvent:
    """构造文本增量事件。"""
    return PartDeltaEvent(
        index=0,
        delta=TextPartDelta(content_delta=text),
    )


def _tool_call_delta_event(
    *,
    index: int,
    tool_name: str,
    tool_call_id: str,
    args: str,
) -> ModelResponseStreamEvent:
    """构造 tool call 增量事件。

    Args:
        index: tool call 在 parts 列表中的索引。
        tool_name: 工具名称。
        tool_call_id: LLM 返回的 tool call ID。
        args: JSON 字符串形式的工具参数。
    """
    return PartDeltaEvent(
        index=index,
        delta=ToolCallPartDelta(
            tool_name_delta=tool_name,
            args_delta=args,
            tool_call_id=tool_call_id,
        ),
    )
