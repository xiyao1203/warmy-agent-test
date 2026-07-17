"""运行快照使用的环境 Application 契约。"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentRuntimeSnapshot(BaseModel):
    """嵌入 Run 快照的不可变、无秘密环境数据。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    environment_version_id: UUID | None = None
    variables: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    credential_binding_ids: list[UUID] = Field(default_factory=list)
    initial_state: dict[str, object] = Field(default_factory=dict)
