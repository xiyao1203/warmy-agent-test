"""ChatSession 领域实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class SessionStatus(StrEnum):
    ACTIVE = "active"
    PLAN_DRAFTED = "plan_drafted"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ChatSessionId:
    value: UUID

    @classmethod
    def new(cls) -> ChatSessionId:
        return cls(uuid4())


@dataclass(slots=True)
class ChatMessage:
    """单条对话消息。"""
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime


@dataclass(slots=True)
class ChatSession:
    """测试 Agent 对话会话实体。

    用户通过自然语言描述测试需求，Agent 生成结构化测试计划草稿，
    用户确认后触发执行。

    Attributes:
        session_id: 会话唯一标识。
        project_id: 所属项目 ID。
        messages: 对话历史。
        plan_draft: Agent 生成的计划草稿（JSON）。
        status: 会话状态。
        created_at: 创建时间。
        updated_at: 更新时间。
    """
    session_id: ChatSessionId
    project_id: UUID
    messages: list[ChatMessage]
    plan_draft: dict[str, object]
    status: SessionStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, *, project_id: UUID) -> ChatSession:
        now = datetime.now(UTC)
        return cls(
            session_id=ChatSessionId.new(),
            project_id=project_id,
            messages=[],
            plan_draft={},
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def add_user_message(self, content: str) -> None:
        """添加用户消息。"""
        self.messages.append(
            ChatMessage(role="user", content=content, timestamp=datetime.now(UTC))
        )
        self.updated_at = datetime.now(UTC)

    def add_assistant_message(
        self, content: str, plan_draft: dict[str, object] | None = None,
    ) -> None:
        """添加 Agent 回复，可附带计划草稿。"""
        self.messages.append(
            ChatMessage(
                role="assistant", content=content,
                timestamp=datetime.now(UTC),
            )
        )
        if plan_draft:
            self.plan_draft = plan_draft
            self.status = SessionStatus.PLAN_DRAFTED
        self.updated_at = datetime.now(UTC)

    def confirm_plan(self) -> dict[str, object]:
        """确认执行计划。返回确认后的计划。"""
        if self.status not in {
            SessionStatus.PLAN_DRAFTED,
            SessionStatus.ACTIVE,
        }:
            raise ValueError("No plan to confirm")
        if not self.plan_draft:
            raise ValueError("Plan draft is empty")
        self.status = SessionStatus.CONFIRMED
        self.updated_at = datetime.now(UTC)
        return self.plan_draft

    def complete(self) -> None:
        """标记会话完成。"""
        self.status = SessionStatus.COMPLETED
        self.updated_at = datetime.now(UTC)
