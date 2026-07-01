"""Typed, secret-free contract used to invoke a published Agent version."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class InvocationProtocol(StrEnum):
    SYNC_JSON = "sync_json"
    OPENAI_CHAT = "openai_chat"
    SSE = "sse"
    ASYNC_POLL = "async_poll"


def _default_request_template() -> dict[str, object]:
    return {"input": "{{ input }}"}


class AgentInvocationConfig(BaseModel):
    """Runtime configuration. Secret values are deliberately not representable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    endpoint_url: AnyHttpUrl
    protocol: InvocationProtocol = InvocationProtocol.SYNC_JSON
    request_template: dict[str, object] = Field(default_factory=_default_request_template)
    response_path: str = Field(default="output", min_length=1)
    timeout_seconds: int = Field(default=30, ge=1, le=600)
    credential_binding_ids: list[UUID] = Field(default_factory=list)
