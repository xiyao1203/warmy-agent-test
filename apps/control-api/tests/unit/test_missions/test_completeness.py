from uuid import uuid4

from agenttest.modules.test_missions.domain.completeness import evaluate_completeness
from agenttest.modules.test_missions.domain.entities import TestMission as Mission
from agenttest.modules.test_missions.domain.value_objects import MissionFact


def test_mission_requires_target_access_goal_and_safety_scope() -> None:
    mission = Mission.create(
        project_id=uuid4(),
        session_id=uuid4(),
        created_by=uuid4(),
    )

    result = evaluate_completeness(mission.facts)

    assert result.complete is False
    assert result.missing == ("target", "access", "test_goal", "safety_scope")


def test_unverified_or_blank_fact_remains_missing() -> None:
    facts = {
        "target": MissionFact.inferred("target", {"url": "https://agent.example"}, 0.8),
        "access": MissionFact.user("access", {"strategy": "none"}),
        "test_goal": MissionFact.user("test_goal", "  "),
        "safety_scope": MissionFact.user("safety_scope", "read_only"),
    }

    result = evaluate_completeness(facts)

    assert result.missing == ("target", "test_goal")


def test_complete_result_preserves_only_current_blockers() -> None:
    facts = {
        "target": MissionFact.user("target", {"url": "https://agent.example"}),
        "access": MissionFact.platform("access", {"browser_profile_id": str(uuid4())}),
        "test_goal": MissionFact.user("test_goal", "验证工单创建草稿"),
        "safety_scope": MissionFact.user("safety_scope", "draft_write"),
    }

    result = evaluate_completeness(facts)

    assert result.complete is True
    assert result.missing == ()
