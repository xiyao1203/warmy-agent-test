from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base


class BrowserProfileModel(Base):
    __tablename__ = "browser_profiles"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_browser_profiles_project_name"),
        CheckConstraint(
            "status IN ('stopped', 'starting', 'running', 'error')",
            name="ck_browser_profiles_status",
        ),
        CheckConstraint(
            "auth_state_status IN ('missing', 'ready', 'expired', 'error')",
            name="ck_browser_profiles_auth_state_status",
        ),
        Index("ix_browser_profiles_project_updated", "project_id", "updated_at"),
        Index("ix_browser_profiles_project_status", "project_id", "auth_state_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    target_domain: Mapped[str] = mapped_column(String(500))
    user_data_dir: Mapped[str] = mapped_column(String(1000))
    cdp_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    auth_state_status: Mapped[str] = mapped_column(String(32))
    auth_state_envelope: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_state_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auth_state_version: Mapped[int] = mapped_column(Integer)
    auth_state_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locked_by_run_case_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("run_cases.id", ondelete="SET NULL"), nullable=True
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
