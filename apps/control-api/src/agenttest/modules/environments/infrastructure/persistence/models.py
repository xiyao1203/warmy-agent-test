from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.shared.infrastructure.database import Base


class EnvironmentTemplateModel(Base):
    __tablename__ = "environment_templates"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_environment_templates_project_name"),
        Index(
            "ix_environment_templates_project",
            "project_id",
            text("created_at DESC"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(String(32))
    config: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class EnvironmentVersionModel(Base):
    __tablename__ = "environment_versions"
    __table_args__ = (
        UniqueConstraint(
            "environment_template_id", "version_number", name="uq_environment_versions_number"
        ),
        UniqueConstraint("project_id", "id", name="uq_environment_versions_project_id"),
        Index(
            "ix_environment_versions_project_template",
            "project_id",
            "environment_template_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    environment_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("environment_templates.id", ondelete="CASCADE")
    )
    version_number: Mapped[int]
    status: Mapped[str] = mapped_column(String(32))
    config: Mapped[dict] = mapped_column(JSON)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CredentialBindingModel(Base):
    __tablename__ = "credential_bindings"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_credential_bindings_project_id"),
        UniqueConstraint("project_id", "alias", name="uq_credential_bindings_alias"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(32))
    injection_location: Mapped[str] = mapped_column(String(32))
    injection_name: Mapped[str] = mapped_column(String(200))
    encrypted_value: Mapped[str] = mapped_column(Text)
    masked_hint: Mapped[str] = mapped_column(String(32))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
