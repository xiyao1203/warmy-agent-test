"""project model configurations and defaults

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-29 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建项目模型配置和三类默认模型映射。"""

    op.create_table(
        "model_configurations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("provider_type", sa.String(32), nullable=False),
        sa.Column("base_url", sa.String(2048), nullable=False),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False),
        sa.Column("api_key_hint", sa.String(16), nullable=False),
        sa.Column("supports_text", sa.Boolean(), nullable=False),
        sa.Column("supports_vision", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "id", name="uq_model_configs_project_id_id"),
        sa.UniqueConstraint("project_id", "name", name="uq_model_configs_project_name"),
    )
    op.create_index(
        "ix_model_configs_project_created_at",
        "model_configurations",
        ["project_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "project_model_defaults",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("model_config_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "purpose IN ('test_agent_chat', 'text_judge', 'vision_judge')",
            name="ck_project_model_defaults_purpose",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["project_id", "model_config_id"],
            ["model_configurations.project_id", "model_configurations.id"],
            ondelete="RESTRICT",
            name="fk_project_model_defaults_project_model",
        ),
        sa.PrimaryKeyConstraint("project_id", "purpose"),
        sa.UniqueConstraint(
            "project_id",
            "purpose",
            name="uq_project_model_defaults_project_purpose",
        ),
    )


def downgrade() -> None:
    """删除项目模型默认映射和配置。"""

    op.drop_table("project_model_defaults")
    op.drop_index("ix_model_configs_project_created_at", table_name="model_configurations")
    op.drop_table("model_configurations")
