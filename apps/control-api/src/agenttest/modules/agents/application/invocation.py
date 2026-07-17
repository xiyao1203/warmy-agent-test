"""已发布 Agent 版本的运行时调用契约。"""

from __future__ import annotations

from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from agenttest.modules.agents.domain.invocation import InvocationProtocol


def _default_request_template() -> dict[str, object]:
    return {"input": "{{ input }}"}


class AgentInvocationConfig(BaseModel):
    """不包含秘密值的 Agent 运行时配置。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    endpoint_url: AnyHttpUrl
    protocol: InvocationProtocol = InvocationProtocol.SYNC_JSON
    request_template: dict[str, object] = Field(default_factory=_default_request_template)
    response_path: str = Field(default="output", min_length=1)
    timeout_seconds: int = Field(default=30, ge=1, le=600)
    credential_binding_ids: list[UUID] = Field(default_factory=list)
    target_config: dict[str, object] = Field(default_factory=dict)


def invocation_from_stored_config(config: dict[str, object]) -> AgentInvocationConfig:
    """读取当前调用契约，并兼容迁移前的 AgentConfig 结构。"""

    if "endpoint_url" in config:
        return AgentInvocationConfig.model_validate(config)
    legacy = {
        "endpoint_url": config.get("api_url"),
        "protocol": config.get("protocol", InvocationProtocol.SYNC_JSON),
        "request_template": config.get("request_template", _default_request_template()),
        "response_path": config.get("response_path", "output"),
        "timeout_seconds": config.get("timeout", 30),
        "credential_binding_ids": config.get("credential_binding_ids", []),
        "target_config": config.get("target_config", {}),
    }
    return AgentInvocationConfig.model_validate(legacy)
