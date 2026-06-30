from agenttest.modules.test_agent.infrastructure import models


def test_super_agent_orchestration_tables_are_project_scoped() -> None:
    expected = {
        "test_agent_tasks": models.TestAgentTaskModel,
        "test_agent_events": models.TestAgentEventModel,
        "test_agent_confirmations": models.TestAgentConfirmationModel,
        "test_agent_artifact_links": models.TestAgentArtifactLinkModel,
        "target_agent_chat_sessions": models.TargetAgentChatSessionModel,
        "target_agent_chat_turns": models.TargetAgentChatTurnModel,
    }

    for table_name, model in expected.items():
        assert model.__table__.name == table_name
        assert "project_id" in model.__table__.columns


def test_session_supports_history_and_protocol_versioning() -> None:
    columns = models.TestAgentSessionModel.__table__.columns

    assert "title" in columns
    assert "archived_at" in columns
    assert "protocol_version" in columns
