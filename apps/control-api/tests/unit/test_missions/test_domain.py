from uuid import uuid4

import pytest
from agenttest.modules.test_missions.domain.entities import (
    ConfirmedMissionMutationError,
)
from agenttest.modules.test_missions.domain.entities import (
    TestMission as Mission,
)
from agenttest.modules.test_missions.domain.value_objects import (
    FactSource,
    MissionFact,
    MissionStatus,
    canonical_snapshot_hash,
)


def _complete_mission() -> Mission:
    mission = Mission.create(
        project_id=uuid4(),
        session_id=uuid4(),
        created_by=uuid4(),
    )
    mission.merge_fact(MissionFact.user("target", {"url": "https://agent.example"}))
    mission.merge_fact(MissionFact.user("access", {"strategy": "none"}))
    mission.merge_fact(MissionFact.user("test_goal", "验证客服问答"))
    mission.merge_fact(MissionFact.user("safety_scope", "read_only"))
    return mission


def test_user_fact_has_precedence_over_system_inference() -> None:
    mission = Mission.create(
        project_id=uuid4(),
        session_id=uuid4(),
        created_by=uuid4(),
    )
    mission.merge_fact(MissionFact.inferred("test_goal", "推断目标", confidence=0.95))
    mission.merge_fact(MissionFact.user("test_goal", "用户明确目标"))
    mission.merge_fact(MissionFact.discovered("test_goal", "探测目标", confidence=1.0))

    assert mission.facts["test_goal"].value == "用户明确目标"
    assert mission.facts["test_goal"].source is FactSource.USER_PROVIDED


def test_confirmation_freezes_canonical_snapshot_hash() -> None:
    mission = _complete_mission()

    revision = mission.confirm(
        confirmed_by=uuid4(),
        execution={"channels": ["api", "browser", "security"]},
        budget={"max_cases": 50, "hard_cost": 20},
        action_allowlist=["read", "draft"],
    )

    assert mission.status is MissionStatus.CONFIRMED
    assert revision.content_hash == canonical_snapshot_hash(revision.snapshot)
    assert revision.revision_number == 1
    assert revision.snapshot["facts"]["target"]["value"] == {"url": "https://agent.example"}
    with pytest.raises(ConfirmedMissionMutationError):
        mission.merge_fact(MissionFact.user("test_goal", "篡改运行范围"))


def test_new_revision_requires_reopening_instead_of_mutating_confirmed_snapshot() -> None:
    mission = _complete_mission()
    first = mission.confirm(confirmed_by=uuid4())

    mission.reopen_for_revision()
    mission.merge_fact(MissionFact.user("test_goal", "增加多轮上下文测试"))
    second = mission.confirm(confirmed_by=uuid4())

    assert first.revision_number == 1
    assert second.revision_number == 2
    assert first.content_hash != second.content_hash
    assert first.snapshot["facts"]["test_goal"]["value"] == "验证客服问答"
