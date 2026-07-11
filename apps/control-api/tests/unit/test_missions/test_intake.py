from uuid import uuid4

import pytest
from agenttest.modules.test_missions.application.intake import (
    FactProposal,
    MissionIntake,
)
from agenttest.modules.test_missions.domain.entities import TestMission as Mission
from agenttest.modules.test_missions.domain.value_objects import FactSource, MissionFact


def _mission() -> Mission:
    return Mission.create(project_id=uuid4(), session_id=uuid4(), created_by=uuid4())


def test_intake_extracts_explicit_user_facts_and_drops_secret_fields() -> None:
    mission = _mission()
    proposal = FactProposal.model_validate(
        {
            "target_url": "https://agent.example/chat",
            "test_goal": "验证多轮客服问答",
            "safety_scope": "read_only",
            "scenario_hints": ["退款政策", "上下文记忆"],
            "password": "must-not-survive",
        }
    )

    changed = MissionIntake().merge(mission, proposal)

    assert set(changed) == {"target", "test_goal", "safety_scope", "scenario_hints"}
    assert mission.facts["target"].source is FactSource.USER_PROVIDED
    assert "password" not in mission.facts


def test_intake_does_not_replace_explicit_user_goal_with_inference() -> None:
    mission = _mission()
    mission.merge_fact(MissionFact.user("test_goal", "用户明确目标"))

    MissionIntake().merge(
        mission,
        FactProposal(test_goal="模型推断目标", inferred_fields={"test_goal"}),
    )

    assert mission.facts["test_goal"].value == "用户明确目标"


def test_intake_rejects_direct_credential_material() -> None:
    with pytest.raises(ValueError, match="credential material"):
        MissionIntake().merge_raw(
            _mission(),
            {"target_url": "https://agent.example", "token": "secret"},
        )
