"""user_settings and feedback tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-29 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### 用户设置表 ###
    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("theme", sa.String(20), nullable=False, server_default="system"),
        sa.Column("language", sa.String(10), nullable=False, server_default="zh-CN"),
        sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("push_notifications", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "test_complete_notifications",
            sa.Boolean(),
            nullable=False,
            server_default="1",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # ### 反馈表 ###
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("contact", sa.String(320), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedbacks_user_id", "feedbacks", ["user_id"], unique=False)
    op.create_index("ix_feedbacks_created_at", "feedbacks", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_feedbacks_created_at", table_name="feedbacks")
    op.drop_index("ix_feedbacks_user_id", table_name="feedbacks")
    op.drop_table("feedbacks")
    op.drop_table("user_settings")
