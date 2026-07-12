from __future__ import annotations

from dataclasses import dataclass

from agenttest.modules.test_missions.domain.completeness import evaluate_completeness
from agenttest.modules.test_missions.domain.entities import TestMission

_MISSING_REASONS = {
    "target": "请选择平台 Agent 版本或提供目标 URL",
    "access": "请选择有效浏览器实例、项目凭证或确认目标无需登录",
    "test_goal": "请说明最需要验证的业务任务",
    "safety_scope": "请确认只读或草稿写入测试范围",
}


@dataclass(frozen=True, slots=True)
class MissingInput:
    key: str
    reason: str


@dataclass(frozen=True, slots=True)
class MissionPreview:
    ready: bool
    missing_inputs: tuple[MissingInput, ...]
    execution_channels: tuple[str, ...]
    action_allowlist: tuple[str, ...]
    inferred_scenarios: tuple[str, ...]


class MissionPreflight:
    def evaluate(self, mission: TestMission) -> MissionPreview:
        completeness = evaluate_completeness(mission.facts)
        missing = tuple(MissingInput(key, _MISSING_REASONS[key]) for key in completeness.missing)
        discovery_fact = mission.facts.get("discovery")
        discovery = (
            discovery_fact.value
            if discovery_fact and isinstance(discovery_fact.value, dict)
            else {}
        )
        if (
            discovery
            and discovery.get("login_valid") is False
            and "access" not in completeness.missing
        ):
            missing = (*missing, MissingInput("access", _MISSING_REASONS["access"]))
        channels: list[str] = []
        if discovery.get("api_available") or mission.facts.get("api_available"):
            channels.append("api")
        if discovery.get("browser_available", True):
            channels.append("browser")
        channels.append("security")
        safety_fact = mission.facts.get("safety_scope")
        actions = ["read"]
        if safety_fact and safety_fact.value == "draft_write":
            actions.append("draft")
        scenario_fact = mission.facts.get("scenario_hints")
        raw_scenarios = scenario_fact.value if scenario_fact else ()
        scenarios = (
            tuple(str(item) for item in raw_scenarios)
            if isinstance(raw_scenarios, (list, tuple))
            else ()
        )
        return MissionPreview(
            ready=completeness.complete and not missing,
            missing_inputs=missing,
            execution_channels=tuple(dict.fromkeys(channels)),
            action_allowlist=tuple(actions),
            inferred_scenarios=scenarios,
        )
