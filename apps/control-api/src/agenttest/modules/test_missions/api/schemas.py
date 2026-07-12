from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class UpsertMissionRequest(BaseModel):
    session_id: UUID
    facts: dict[str, object] = Field(default_factory=dict)


class ConfirmMissionRequest(BaseModel):
    revision_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    idempotency_key: str = Field(min_length=1, max_length=200)
