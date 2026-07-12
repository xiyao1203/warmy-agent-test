from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import MissionFact

_SECRET_KEYS = {
    "password",
    "credential",
    "token",
    "cookie",
    "storage_state",
    "auth_state",
    "api_key",
    "secret",
}


class FactProposal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    target_url: AnyHttpUrl | None = None
    agent_version_id: UUID | None = None
    browser_profile_id: UUID | None = None
    access_strategy: Literal["none", "browser_profile", "credential"] | None = None
    credential_binding_id: UUID | None = None
    test_goal: str | None = Field(default=None, min_length=1, max_length=4000)
    safety_scope: Literal["read_only", "draft_write"] | None = None
    scenario_hints: list[str] = Field(default_factory=list, max_length=20)
    inferred_fields: set[str] = Field(default_factory=set, exclude=True)


class MissionIntake:
    def merge_raw(self, mission: TestMission, values: dict[str, object]) -> tuple[str, ...]:
        if any(key.lower() in _SECRET_KEYS for key in values):
            raise ValueError("Mission intake cannot accept credential material")
        return self.merge(mission, FactProposal.model_validate(values))

    def merge(self, mission: TestMission, proposal: FactProposal) -> tuple[str, ...]:
        candidates: dict[str, object] = {}
        if proposal.target_url is not None or proposal.agent_version_id is not None:
            target: dict[str, object] = {}
            if proposal.target_url is not None:
                target["url"] = str(proposal.target_url)
            if proposal.agent_version_id is not None:
                target["agent_version_id"] = str(proposal.agent_version_id)
            candidates["target"] = target
        if proposal.access_strategy is not None:
            access: dict[str, object] = {"strategy": proposal.access_strategy}
            if proposal.browser_profile_id is not None:
                access["browser_profile_id"] = str(proposal.browser_profile_id)
            if proposal.credential_binding_id is not None:
                access["credential_binding_id"] = str(proposal.credential_binding_id)
            candidates["access"] = access
        elif proposal.browser_profile_id is not None:
            candidates["access"] = {
                "strategy": "browser_profile",
                "browser_profile_id": str(proposal.browser_profile_id),
            }
        if proposal.test_goal is not None:
            candidates["test_goal"] = proposal.test_goal
        if proposal.safety_scope is not None:
            candidates["safety_scope"] = proposal.safety_scope
        if proposal.scenario_hints:
            candidates["scenario_hints"] = proposal.scenario_hints

        changed: list[str] = []
        for key, value in candidates.items():
            fact = (
                MissionFact.inferred(key, value, confidence=0.7)
                if key in proposal.inferred_fields
                else MissionFact.user(key, value)
            )
            if mission.merge_fact(fact):
                changed.append(key)
        return tuple(changed)
