"""OpenAI-Compatible Chat Completions HTTP 适配器。"""

from __future__ import annotations

from ipaddress import ip_address
from time import monotonic
from urllib.parse import urlsplit

import httpx

from .contracts import ModelInvocationRequest, ModelInvocationResult


class ModelInvocationError(Exception):
    """可安全返回给控制面的模型调用错误。"""


class ModelPermissionError(ModelInvocationError):
    """供应商拒绝模型凭证。"""


class ModelTransientError(ModelInvocationError):
    """可按策略重试的上游或网络错误。"""


class ModelProtocolError(ModelInvocationError):
    """上游成功响应不符合 OpenAI-Compatible 契约。"""


class OpenAICompatibleAdapter:
    """通过真实 HTTP 请求调用 OpenAI-Compatible 服务。"""

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport

    async def invoke(self, request: ModelInvocationRequest) -> ModelInvocationResult:
        """执行 Chat Completions，并返回结构化用量与延迟。"""

        _validate_target(request.base_url, request.allow_private_network)
        payload: dict[str, object] = {
            "model": request.model_name,
            "messages": [{"role": item.role, "content": item.content} for item in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.response_format is not None:
            payload["response_format"] = request.response_format
        started = monotonic()
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=httpx.Timeout(request.timeout_seconds),
                follow_redirects=False,
            ) as client:
                response = await client.post(
                    f"{request.base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {request.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise ModelTransientError("模型服务网络连接或响应超时") from error
        latency_ms = round((monotonic() - started) * 1000)
        if response.status_code in {401, 403}:
            raise ModelPermissionError("模型服务拒绝了项目凭证")
        if response.status_code == 429 or response.status_code >= 500:
            raise ModelTransientError(f"模型服务暂时不可用（HTTP {response.status_code}）")
        if response.status_code >= 400:
            raise ModelProtocolError(f"模型服务返回不支持的状态（HTTP {response.status_code}）")
        try:
            body = response.json()
            message = body["choices"][0]["message"]
            # 优先使用 content，如果为空则尝试 reasoning_content（如 MIMO 模型）
            content = message.get("content") or ""
            if not content:
                content = message.get("reasoning_content") or ""
            if not isinstance(content, str):
                raise ValueError
            usage = body.get("usage") or {}
            return ModelInvocationResult(
                content=content,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                total_tokens=int(usage.get("total_tokens", 0)),
                latency_ms=latency_ms,
                response_id=body.get("id") if isinstance(body.get("id"), str) else None,
            )
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ModelProtocolError("模型服务响应不符合 OpenAI-Compatible 契约") from error


def _validate_target(base_url: str, allow_private_network: bool) -> None:
    """阻止模型配置直接访问元数据和未授权私网地址。"""

    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ModelProtocolError("模型服务 URL 无效")
    try:
        address = ip_address(parsed.hostname)
    except ValueError:
        return
    if address.is_link_local or address.is_multicast or address.is_unspecified:
        raise ModelProtocolError("模型服务 URL 命中禁止的网络地址")
    if (address.is_private or address.is_loopback) and not allow_private_network:
        raise ModelProtocolError("模型服务 URL 命中未授权的私有网络地址")
