from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class MissionStatus(StrEnum):
    COLLECTING = "collecting"
    NEEDS_INPUT = "needs_input"
    DISCOVERING = "discovering"
    READY_FOR_CONFIRMATION = "ready_for_confirmation"
    CONFIRMED = "confirmed"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    NEEDS_ATTENTION = "needs_attention"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FactSource(StrEnum):
    SYSTEM_INFERRED = "system_inferred"
    TARGET_DISCOVERED = "target_discovered"
    PLATFORM_RESOLVED = "platform_resolved"
    USER_PROVIDED = "user_provided"


_SOURCE_PRIORITY = {
    FactSource.SYSTEM_INFERRED: 1,
    FactSource.TARGET_DISCOVERED: 2,
    FactSource.PLATFORM_RESOLVED: 3,
    FactSource.USER_PROVIDED: 4,
}


@dataclass(frozen=True, slots=True)
class MissionFact:
    key: str
    value: object
    source: FactSource
    confidence: float
    verified: bool
    sensitive: bool = False

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Mission fact key is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Mission fact confidence must be between 0 and 1")

    @property
    def source_priority(self) -> int:
        return _SOURCE_PRIORITY[self.source]

    @classmethod
    def user(cls, key: str, value: object, *, sensitive: bool = False) -> MissionFact:
        return cls(key, value, FactSource.USER_PROVIDED, 1.0, True, sensitive)

    @classmethod
    def platform(cls, key: str, value: object) -> MissionFact:
        return cls(key, value, FactSource.PLATFORM_RESOLVED, 1.0, True)

    @classmethod
    def discovered(cls, key: str, value: object, confidence: float) -> MissionFact:
        return cls(key, value, FactSource.TARGET_DISCOVERED, confidence, confidence >= 0.9)

    @classmethod
    def inferred(cls, key: str, value: object, confidence: float) -> MissionFact:
        return cls(key, value, FactSource.SYSTEM_INFERRED, confidence, False)

    def public_snapshot(self) -> dict[str, object]:
        if self.sensitive:
            raise ValueError("Sensitive mission facts cannot enter revision snapshots")
        return {
            "value": _json_value(self.value),
            "source": self.source.value,
            "confidence": self.confidence,
            "verified": self.verified,
        }


@dataclass(frozen=True, slots=True)
class MissionRevision:
    revision_id: UUID
    project_id: UUID
    mission_id: UUID
    revision_number: int
    snapshot: dict[str, Any]
    content_hash: str
    confirmed_by: UUID
    confirmed_at: datetime


@dataclass(frozen=True, slots=True)
class MissionEvent:
    event_id: UUID
    project_id: UUID
    mission_id: UUID
    sequence: int
    event_type: str
    payload: dict[str, Any]
    created_at: datetime


def canonical_snapshot_hash(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_value(value: object) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))
