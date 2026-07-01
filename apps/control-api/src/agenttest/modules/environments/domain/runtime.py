"""Immutable, secret-free Environment data embedded in a Run snapshot."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentRuntimeSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    environment_version_id: UUID | None = None
    variables: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    credential_binding_ids: list[UUID] = Field(default_factory=list)
    initial_state: dict[str, object] = Field(default_factory=dict)
