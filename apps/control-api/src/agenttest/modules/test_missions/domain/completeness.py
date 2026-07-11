from __future__ import annotations

from dataclasses import dataclass

from agenttest.modules.test_missions.domain.value_objects import MissionFact

REQUIRED_FACT_KEYS = ("target", "access", "test_goal", "safety_scope")


@dataclass(frozen=True, slots=True)
class MissionCompleteness:
    complete: bool
    missing: tuple[str, ...]


def evaluate_completeness(facts: dict[str, MissionFact]) -> MissionCompleteness:
    missing = tuple(key for key in REQUIRED_FACT_KEYS if not _is_usable(facts.get(key)))
    return MissionCompleteness(complete=not missing, missing=missing)


def _is_usable(fact: MissionFact | None) -> bool:
    if fact is None or not fact.verified:
        return False
    value = fact.value
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list, tuple, set)):
        return bool(value)
    return True
