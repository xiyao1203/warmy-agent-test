"""Agent 版本字段扩展 + 基线标记。

新增 agent_versions 的扩展字段和 agents 表的版本追踪列。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # agents 表新增基线版本追踪列
    # 注意：SQLite 不支持 ALTER TABLE ADD CONSTRAINT，外键约束仅在 PostgreSQL 中添加
    op.add_column("agents", sa.Column("current_version_id", sa.Uuid(), nullable=True))
    op.add_column("agents", sa.Column("baseline_version_id", sa.Uuid(), nullable=True))

    # SQLite 不支持添加外键约束，仅在 PostgreSQL 中执行
    if op.get_bind().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_agents_current_version",
            "agents",
            "agent_versions",
            ["current_version_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_agents_baseline_version",
            "agents",
            "agent_versions",
            ["baseline_version_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    op.drop_constraint("fk_agents_baseline_version", "agents", type_="foreignkey")
    op.drop_constraint("fk_agents_current_version", "agents", type_="foreignkey")
    op.drop_column("agents", "baseline_version_id")
    op.drop_column("agents", "current_version_id")
