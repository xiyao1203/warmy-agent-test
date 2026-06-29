"""项目级大模型配置 SQLAlchemy 模型。"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base


class ModelConfigurationModel(Base):
    """项目模型配置持久化模型。"""

    __tablename__ = "model_configurations"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_model_configs_project_id_id"),
        UniqueConstraint("project_id", "name", name="uq_model_configs_project_name"),
        Index("ix_model_configs_project_created_at", "project_id", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    provider_type: Mapped[str] = mapped_column(String(32))
    base_url: Mapped[str] = mapped_column(String(2048))
    model_name: Mapped[str] = mapped_column(String(200))
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    api_key_hint: Mapped[str] = mapped_column(String(16))
    supports_text: Mapped[bool] = mapped_column(Boolean)
    supports_vision: Mapped[bool] = mapped_column(Boolean)
    enabled: Mapped[bool] = mapped_column(Boolean)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProjectModelDefaultModel(Base):
    """项目默认模型持久化模型。"""

    __tablename__ = "project_model_defaults"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_id", "model_config_id"],
            ["model_configurations.project_id", "model_configurations.id"],
            ondelete="RESTRICT",
            name="fk_project_model_defaults_project_model",
        ),
        UniqueConstraint(
            "project_id",
            "purpose",
            name="uq_project_model_defaults_project_purpose",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    purpose: Mapped[str] = mapped_column(String(32), primary_key=True)
    model_config_id: Mapped[UUID]
    updated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
