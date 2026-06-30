"""Unit tests for ChatSession domain entity."""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.test_agent.domain.entities import (
    ChatSession,
    SessionStatus,
)


def test_session_create() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    assert s.status is SessionStatus.ACTIVE
    assert s.messages == []
    assert s.plan_draft == {}


def test_session_add_user_message() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    s.add_user_message("测试登录流程")
    assert len(s.messages) == 1
    assert s.messages[0].role == "user"
    assert s.messages[0].content == "测试登录流程"


def test_session_add_assistant_message() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    s.add_assistant_message("我将为您创建测试计划")
    assert len(s.messages) == 1
    assert s.messages[0].role == "assistant"
    assert s.status is SessionStatus.ACTIVE


def test_session_add_assistant_with_plan() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    plan = {
        "agent_id": "agent-1",
        "dataset_id": "ds-1",
        "scorer": "exact_match",
    }
    s.add_assistant_message("已生成测试计划", plan_draft=plan)
    assert s.status is SessionStatus.PLAN_DRAFTED
    assert s.plan_draft == plan


def test_session_confirm_plan() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    plan = {"agent_id": "agent-1", "dataset_id": "ds-1"}
    s.add_assistant_message("计划已生成", plan_draft=plan)
    result = s.confirm_plan()
    assert s.status is SessionStatus.CONFIRMED
    assert result == plan


def test_session_confirm_empty_plan_raises() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    with pytest.raises(ValueError, match="Plan draft is empty"):
        s.confirm_plan()


def test_session_confirm_wrong_status_raises() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    s.add_assistant_message("hi", plan_draft={"a": 1})
    s.confirm_plan()
    with pytest.raises(ValueError, match="No plan to confirm"):
        s.confirm_plan()


def test_session_complete() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    s.add_assistant_message("hi", plan_draft={"a": 1})
    s.confirm_plan()
    s.complete()
    assert s.status is SessionStatus.COMPLETED


def test_session_status_values() -> None:
    assert SessionStatus.ACTIVE == "active"
    assert SessionStatus.PLAN_DRAFTED == "plan_drafted"
    assert SessionStatus.CONFIRMED == "confirmed"
    assert SessionStatus.COMPLETED == "completed"


def test_session_multi_turn() -> None:
    s = ChatSession.create(project_id=uuid4(), created_by=uuid4())
    s.add_user_message("测试登录")
    s.add_assistant_message("好的，我来规划")
    s.add_user_message("使用 admin 账号")
    s.add_assistant_message(
        "已生成计划",
        plan_draft={"agent": "login-agent", "cases": ["test_login"]},
    )
    assert len(s.messages) == 4
    assert s.status is SessionStatus.PLAN_DRAFTED
