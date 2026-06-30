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


class TaskStatus(StrEnum):
    PENDING = "pending"
    WAITING_CONFIRMATION = "waiting_confirmation"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(StrEnum):
    READ = "read"
    DRAFT_WRITE = "draft_write"
    HIGH_IMPACT = "high_impact"


class ConfirmationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ChatSessionId:
    value: UUID

    @classmethod
    def new(cls) -> ChatSessionId:
        return cls(uuid4())


@dataclass(slots=True)
class ChatMessage:
    """单条对话消息。"""

    message_id: UUID
    sequence: int
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime


@dataclass(slots=True)
class ChatSession:
    """测试 Agent 对话会话实体。

    用户通过自然语言描述测试需求，Agent 生成结构化测试计划草稿，
    用户确认后可保存为正式测试计划；确认本身不伪装成运行启动。

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
    created_by: UUID
    messages: list[ChatMessage]
    plan_draft: dict[str, object]
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    title: str = "新对话"
    protocol_version: int = 2
    archived_at: datetime | None = None

    @classmethod
    def create(cls, *, project_id: UUID, created_by: UUID) -> ChatSession:
        now = datetime.now(UTC)
        return cls(
            session_id=ChatSessionId.new(),
            project_id=project_id,
            created_by=created_by,
            messages=[],
            plan_draft={},
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def archive(self) -> None:
        now = datetime.now(UTC)
        self.archived_at = now
        self.updated_at = now

    def add_user_message(self, content: str) -> None:
        """添加用户消息。"""
        self.messages.append(
            ChatMessage(
                message_id=uuid4(),
                sequence=len(self.messages) + 1,
                role="user",
                content=content,
                timestamp=datetime.now(UTC),
            )
        )
        self.updated_at = datetime.now(UTC)

    def add_assistant_message(
        self,
        content: str,
        plan_draft: dict[str, object] | None = None,
    ) -> None:
        """添加 Agent 回复，可附带计划草稿。"""
        self.messages.append(
            ChatMessage(
                message_id=uuid4(),
                sequence=len(self.messages) + 1,
                role="assistant",
                content=content,
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


@dataclass(slots=True)
class AgentTask:
    task_id: UUID
    project_id: UUID
    session_id: UUID
    parent_task_id: UUID | None
    child_agent: str
    capability: str
    risk_level: RiskLevel
    idempotency_key: str
    input: dict[str, object]
    status: TaskStatus
    output: dict[str, object] | None
    error: dict[str, object] | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID,
        session_id: UUID,
        child_agent: str,
        capability: str,
        risk_level: RiskLevel,
        idempotency_key: str,
        input: dict[str, object],
        parent_task_id: UUID | None = None,
    ) -> AgentTask:
        if not idempotency_key.strip():
            raise ValueError("Task idempotency key is required")
        now = datetime.now(UTC)
        return cls(
            task_id=uuid4(),
            project_id=project_id,
            session_id=session_id,
            parent_task_id=parent_task_id,
            child_agent=child_agent,
            capability=capability,
            risk_level=risk_level,
            idempotency_key=idempotency_key.strip(),
            input=input,
            status=(
                TaskStatus.PENDING
                if risk_level is RiskLevel.READ
                else TaskStatus.WAITING_CONFIRMATION
            ),
            output=None,
            error=None,
            created_at=now,
            updated_at=now,
        )

    def approve(self) -> None:
        if self.status is not TaskStatus.WAITING_CONFIRMATION:
            raise ValueError("Task is not waiting for confirmation")
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now(UTC)

    def start(self) -> None:
        if self.status is TaskStatus.WAITING_CONFIRMATION:
            raise ValueError("Task requires confirmation")
        if self.status is not TaskStatus.PENDING:
            raise ValueError("Task cannot start from current status")
        self.status = TaskStatus.RUNNING
        self.updated_at = datetime.now(UTC)

    def complete(self, output: dict[str, object]) -> None:
        if self.status is not TaskStatus.RUNNING:
            raise ValueError("Only a running task can complete")
        self.output = output
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now(UTC)

    def fail(self, error: dict[str, object]) -> None:
        if self.status not in {TaskStatus.PENDING, TaskStatus.RUNNING}:
            raise ValueError("Task cannot fail from current status")
        self.error = error
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now(UTC)

    def reject(self) -> None:
        if self.status is not TaskStatus.WAITING_CONFIRMATION:
            raise ValueError("Only a task waiting for confirmation can be rejected")
        self.error = {"type": "Rejected", "message": "User rejected operation"}
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class AgentConfirmation:
    confirmation_id: UUID
    project_id: UUID
    task_id: UUID
    status: ConfirmationStatus
    preview: dict[str, object]
    decided_by: UUID | None
    decided_at: datetime | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID,
        task_id: UUID,
        preview: dict[str, object],
    ) -> AgentConfirmation:
        return cls(
            confirmation_id=uuid4(),
            project_id=project_id,
            task_id=task_id,
            status=ConfirmationStatus.PENDING,
            preview=preview,
            decided_by=None,
            decided_at=None,
            created_at=datetime.now(UTC),
        )

    def approve(self, actor_id: UUID) -> None:
        self._decide(ConfirmationStatus.APPROVED, actor_id)

    def reject(self, actor_id: UUID) -> None:
        self._decide(ConfirmationStatus.REJECTED, actor_id)

    def _decide(self, status: ConfirmationStatus, actor_id: UUID) -> None:
        if self.status is not ConfirmationStatus.PENDING:
            raise ValueError("Confirmation already decided")
        self.status = status
        self.decided_by = actor_id
        self.decided_at = datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class AgentEvent:
    event_id: UUID
    project_id: UUID
    session_id: UUID
    sequence: int
    event_type: str
    payload: dict[str, object]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ArtifactLink:
    link_id: UUID
    project_id: UUID
    session_id: UUID
    task_id: UUID
    artifact_type: str
    artifact_id: UUID
    relation: str
    created_at: datetime
