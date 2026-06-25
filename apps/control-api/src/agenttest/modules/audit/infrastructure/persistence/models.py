from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, event, text
from sqlalchemy.orm import Mapped, Mapper, mapped_column

from agenttest.shared.infrastructure.database import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index(
            "ix_audit_logs_project_created_at_desc",
            "project_id",
            text("created_at DESC"),
        ),
        {"info": {"append_only": True}},
    )
    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(100))
    object_type: Mapped[str] = mapped_column(String(100))
    object_id: Mapped[UUID | None] = mapped_column(nullable=True)
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id"),
        nullable=True,
    )
    changes: Mapped[dict[str, Any]] = mapped_column(JSON)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def prevent_audit_mutation(_mapper: Mapper[Any], _connection: Any, _target: Any) -> None:
    raise ValueError("Audit logs are append-only")


event.listen(AuditLogModel, "before_update", prevent_audit_mutation)
event.listen(AuditLogModel, "before_delete", prevent_audit_mutation)
