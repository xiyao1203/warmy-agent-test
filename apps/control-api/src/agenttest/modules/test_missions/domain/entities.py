from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from agenttest.modules.test_missions.domain.completeness import evaluate_completeness
from agenttest.modules.test_missions.domain.value_objects import (
    MissionFact,
    MissionRevision,
    MissionStatus,
    canonical_snapshot_hash,
)


class ConfirmedMissionMutationError(ValueError):
    pass


@dataclass(slots=True)
class TestMission:
    mission_id: UUID
    project_id: UUID
    session_id: UUID
    created_by: UUID
    status: MissionStatus
    facts: dict[str, MissionFact]
    revisions: list[MissionRevision]
    active_revision_id: UUID | None
    lock_version: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def create(cls, *, project_id: UUID, session_id: UUID, created_by: UUID) -> TestMission:
        now = datetime.now(UTC)
        return cls(
            mission_id=uuid4(),
            project_id=project_id,
            session_id=session_id,
            created_by=created_by,
            status=MissionStatus.COLLECTING,
            facts={},
            revisions=[],
            active_revision_id=None,
            lock_version=0,
            created_at=now,
            updated_at=now,
        )

    def merge_fact(self, candidate: MissionFact) -> bool:
        if self.status not in {
            MissionStatus.COLLECTING,
            MissionStatus.NEEDS_INPUT,
            MissionStatus.DISCOVERING,
            MissionStatus.READY_FOR_CONFIRMATION,
        }:
            raise ConfirmedMissionMutationError("Confirmed mission facts require a new revision")
        current = self.facts.get(candidate.key)
        if current is not None and not _supersedes(candidate, current):
            return False
        self.facts[candidate.key] = candidate
        self.updated_at = datetime.now(UTC)
        self.lock_version += 1
        if self.status is MissionStatus.DISCOVERING:
            return True
        completeness = evaluate_completeness(self.facts)
        self.status = (
            MissionStatus.READY_FOR_CONFIRMATION
            if completeness.complete
            else MissionStatus.NEEDS_INPUT
        )
        return True

    def confirm(
        self,
        *,
        confirmed_by: UUID,
        execution: dict[str, Any] | None = None,
        budget: dict[str, Any] | None = None,
        action_allowlist: list[str] | None = None,
    ) -> MissionRevision:
        completeness = evaluate_completeness(self.facts)
        if not completeness.complete:
            missing = ", ".join(completeness.missing)
            raise ValueError(f"Mission is missing required facts: {missing}")
        snapshot: dict[str, Any] = {
            "facts": {key: fact.public_snapshot() for key, fact in sorted(self.facts.items())},
            "execution": dict(execution or {}),
            "budget": dict(budget or {}),
            "action_allowlist": list(action_allowlist or ["read"]),
        }
        now = datetime.now(UTC)
        revision = MissionRevision(
            revision_id=uuid4(),
            project_id=self.project_id,
            mission_id=self.mission_id,
            revision_number=len(self.revisions) + 1,
            snapshot=snapshot,
            content_hash=canonical_snapshot_hash(snapshot),
            confirmed_by=confirmed_by,
            confirmed_at=now,
        )
        self.revisions.append(revision)
        self.active_revision_id = revision.revision_id
        self.status = MissionStatus.CONFIRMED
        self.updated_at = now
        self.lock_version += 1
        return revision

    def begin_discovery(self) -> None:
        if self.status not in {
            MissionStatus.COLLECTING,
            MissionStatus.NEEDS_INPUT,
            MissionStatus.READY_FOR_CONFIRMATION,
        }:
            raise ValueError("Mission cannot start discovery from current status")
        self.status = MissionStatus.DISCOVERING
        self.updated_at = datetime.now(UTC)
        self.lock_version += 1

    def finish_discovery(self) -> None:
        if self.status is not MissionStatus.DISCOVERING:
            raise ValueError("Mission discovery is not running")
        completeness = evaluate_completeness(self.facts)
        self.status = (
            MissionStatus.READY_FOR_CONFIRMATION
            if completeness.complete
            else MissionStatus.NEEDS_INPUT
        )
        self.updated_at = datetime.now(UTC)
        self.lock_version += 1

    def reopen_for_revision(self) -> None:
        if self.status not in {
            MissionStatus.CONFIRMED,
            MissionStatus.COMPLETED,
            MissionStatus.FAILED,
            MissionStatus.CANCELLED,
        }:
            raise ValueError("Mission is already editable")
        self.status = MissionStatus.COLLECTING
        self.active_revision_id = None
        self.updated_at = datetime.now(UTC)
        self.lock_version += 1


def _supersedes(candidate: MissionFact, current: MissionFact) -> bool:
    if candidate.source_priority != current.source_priority:
        return candidate.source_priority > current.source_priority
    if candidate.verified != current.verified:
        return candidate.verified
    return candidate.confidence >= current.confidence
