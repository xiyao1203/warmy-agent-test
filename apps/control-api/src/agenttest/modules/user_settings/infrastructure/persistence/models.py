"""用户设置数据库模型。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.persistence.base import Base


class UserSettingsModel(Base):
    """用户设置数据库表。"""

    __tablename__ = "user_settings"

    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    theme: Mapped[str] = mapped_column(String(20), default="system")
    language: Mapped[str] = mapped_column(String(10), default="zh-CN")
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    test_complete_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
