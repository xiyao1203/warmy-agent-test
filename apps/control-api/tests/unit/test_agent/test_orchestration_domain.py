from uuid import uuid4

import pytest
from agenttest.modules.test_agent.domain import entities


def test_new_session_has_history_metadata_and_can_be_archived() -> None:
    session = entities.ChatSession.create(project_id=uuid4(), created_by=uuid4())

    assert session.title == "新对话"
    assert session.protocol_version == 2
    assert session.archived_at is None

    session.archive()

    assert session.archived_at is not None


def test_task_requires_confirmation_before_high_impact_execution() -> None:
    task = entities.AgentTask.create(
        project_id=uuid4(),
        session_id=uuid4(),
        child_agent="execution",
        capability="runs.start",
        risk_level=entities.RiskLevel.HIGH_IMPACT,
        idempotency_key="start:run-1",
        input={"run_id": "run-1"},
    )

    assert task.status is entities.TaskStatus.WAITING_CONFIRMATION
    with pytest.raises(ValueError, match="confirmation"):
        task.start()

    task.approve()
    task.start()
    task.complete({"run_id": "run-1"})

    assert task.status is entities.TaskStatus.COMPLETED


def test_confirmation_can_only_be_decided_once() -> None:
    confirmation = entities.AgentConfirmation.create(
        project_id=uuid4(),
        task_id=uuid4(),
        preview={"action": "publish"},
    )
    confirmation.approve(uuid4())

    with pytest.raises(ValueError, match="already decided"):
        confirmation.reject(uuid4())


def test_waiting_task_can_be_rejected_without_running() -> None:
    task = entities.AgentTask.create(
        project_id=uuid4(),
        session_id=uuid4(),
        child_agent="security",
        capability="security_scans.start",
        risk_level=entities.RiskLevel.HIGH_IMPACT,
        idempotency_key="security:1",
        input={"target_url": "https://example.com"},
    )

    task.reject()

    assert task.status is entities.TaskStatus.CANCELLED
    assert task.error == {"type": "Rejected", "message": "User rejected operation"}
