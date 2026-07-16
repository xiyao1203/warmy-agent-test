"""Add professional project and test-case management fields.

Revision ID: 0027
Revises: 0026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(sa.Column("key", sa.String(length=12), nullable=True))
        batch_op.add_column(sa.Column("lead_user_id", sa.Uuid(), nullable=True))

    op.create_table(
        "project_sequences",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "resource_type"),
        sa.CheckConstraint("next_value >= 1", name="ck_project_sequences_next_value"),
    )

    with op.batch_alter_table("test_cases") as batch_op:
        batch_op.add_column(sa.Column("case_key", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("objective", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("case_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("template", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("case_type", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("automation_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("source", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("source_ref", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("component", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("requirement_refs", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("owner_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("preconditions", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("data_bindings", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("steps", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("artifact_requirements", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("postconditions", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("estimated_duration_seconds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("timeout_seconds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("retry_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("custom_fields", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("created_by", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("updated_by", sa.Uuid(), nullable=True))

    op.execute(
        """
        UPDATE projects
        SET key = 'P' || upper(substr(replace(CAST(id AS TEXT), '-', ''), 1, 8))
        WHERE key IS NULL
        """
    )
    op.execute(
        """
        UPDATE test_cases
        SET objective = COALESCE(NULLIF(trim(scenario), ''), name),
            case_status = 'ready',
            template = 'ai_eval',
            case_type = 'functional',
            automation_status = 'automated',
            source = 'manual',
            requirement_refs = '[]',
            preconditions = '[]',
            data_bindings = '[]',
            steps = '[]',
            artifact_requirements = '[]',
            postconditions = '[]',
            retry_count = 0,
            custom_fields = '{}',
            created_by = (
                SELECT dv.created_by
                FROM dataset_versions AS dv
                WHERE dv.id = test_cases.dataset_version_id
            ),
            updated_by = (
                SELECT dv.created_by
                FROM dataset_versions AS dv
                WHERE dv.id = test_cases.dataset_version_id
            )
        """
    )

    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        _backfill_case_keys_sqlite()
    else:
        _backfill_case_keys_postgresql()

    op.execute(
        """
        INSERT INTO project_sequences (
            project_id, resource_type, next_value, updated_at
        )
        SELECT p.id, 'test_case', COUNT(tc.id) + 1, CURRENT_TIMESTAMP
        FROM projects AS p
        LEFT JOIN datasets AS d ON d.project_id = p.id
        LEFT JOIN dataset_versions AS dv ON dv.dataset_id = d.id
        LEFT JOIN test_cases AS tc ON tc.dataset_version_id = dv.id
        GROUP BY p.id
        """
    )

    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column("key", existing_type=sa.String(length=12), nullable=False)
        batch_op.create_unique_constraint("uq_projects_key", ["key"])
        batch_op.create_foreign_key(
            "fk_projects_lead_user",
            "users",
            ["lead_user_id"],
            ["id"],
        )
        batch_op.create_check_constraint(
            "ck_projects_key_format",
            "length(key) BETWEEN 2 AND 12 AND key = upper(key)",
        )

    with op.batch_alter_table("test_cases") as batch_op:
        for column_name, column_type in (
            ("case_key", sa.String(length=40)),
            ("objective", sa.Text()),
            ("case_status", sa.String(length=32)),
            ("template", sa.String(length=32)),
            ("case_type", sa.String(length=32)),
            ("automation_status", sa.String(length=32)),
            ("source", sa.String(length=32)),
            ("requirement_refs", sa.JSON()),
            ("preconditions", sa.JSON()),
            ("data_bindings", sa.JSON()),
            ("steps", sa.JSON()),
            ("artifact_requirements", sa.JSON()),
            ("postconditions", sa.JSON()),
            ("retry_count", sa.Integer()),
            ("custom_fields", sa.JSON()),
            ("created_by", sa.Uuid()),
            ("updated_by", sa.Uuid()),
        ):
            batch_op.alter_column(
                column_name,
                existing_type=column_type,
                nullable=False,
            )
        batch_op.create_unique_constraint("uq_test_cases_case_key", ["case_key"])
        batch_op.create_foreign_key(
            "fk_test_cases_owner",
            "users",
            ["owner_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_test_cases_created_by",
            "users",
            ["created_by"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_test_cases_updated_by",
            "users",
            ["updated_by"],
            ["id"],
        )
        batch_op.create_check_constraint(
            "ck_test_cases_case_status",
            "case_status IN ('draft', 'ready', 'deprecated')",
        )
        batch_op.create_check_constraint(
            "ck_test_cases_template",
            "template IN ('step_by_step', 'text', 'bdd', 'ai_eval')",
        )
        batch_op.create_check_constraint(
            "ck_test_cases_case_type",
            "case_type IN ('functional', 'regression', 'smoke', 'integration', "
            "'e2e', 'security', 'performance', 'usability', 'exploratory')",
        )
        batch_op.create_check_constraint(
            "ck_test_cases_automation_status",
            "automation_status IN ('manual', 'candidate', 'automated')",
        )
        batch_op.create_check_constraint(
            "ck_test_cases_source",
            "source IN ('manual', 'agent_generated', 'imported', 'run_regression')",
        )
        batch_op.create_check_constraint(
            "ck_test_cases_duration",
            "estimated_duration_seconds IS NULL OR "
            "(estimated_duration_seconds BETWEEN 1 AND 86400)",
        )
        batch_op.create_check_constraint(
            "ck_test_cases_timeout",
            "timeout_seconds IS NULL OR (timeout_seconds BETWEEN 1 AND 86400)",
        )
        batch_op.create_check_constraint(
            "ck_test_cases_retry_count",
            "retry_count BETWEEN 0 AND 10",
        )

    op.create_index(
        "ix_test_cases_version_status",
        "test_cases",
        ["dataset_version_id", "case_status"],
    )
    op.create_index(
        "ix_test_cases_version_type",
        "test_cases",
        ["dataset_version_id", "case_type"],
    )
    op.create_index(
        "ix_test_cases_version_automation",
        "test_cases",
        ["dataset_version_id", "automation_status"],
    )


def _backfill_case_keys_sqlite() -> None:
    op.execute(
        """
        WITH ranked AS (
            SELECT
                tc.id AS case_id,
                p.key AS project_key,
                row_number() OVER (
                    PARTITION BY p.id
                    ORDER BY d.id, dv.version_number, tc.sort_order, tc.id
                ) AS sequence_number
            FROM test_cases AS tc
            JOIN dataset_versions AS dv ON dv.id = tc.dataset_version_id
            JOIN datasets AS d ON d.id = dv.dataset_id
            JOIN projects AS p ON p.id = d.project_id
        )
        UPDATE test_cases
        SET case_key = (
            SELECT project_key || '-TC-' || printf('%06d', sequence_number)
            FROM ranked
            WHERE ranked.case_id = test_cases.id
        )
        """
    )


def _backfill_case_keys_postgresql() -> None:
    op.execute(
        """
        WITH ranked AS (
            SELECT
                tc.id AS case_id,
                p.key AS project_key,
                row_number() OVER (
                    PARTITION BY p.id
                    ORDER BY d.id, dv.version_number, tc.sort_order, tc.id
                ) AS sequence_number
            FROM test_cases AS tc
            JOIN dataset_versions AS dv ON dv.id = tc.dataset_version_id
            JOIN datasets AS d ON d.id = dv.dataset_id
            JOIN projects AS p ON p.id = d.project_id
        )
        UPDATE test_cases AS tc
        SET case_key = ranked.project_key || '-TC-' ||
            lpad(CAST(ranked.sequence_number AS TEXT), 6, '0')
        FROM ranked
        WHERE ranked.case_id = tc.id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_test_cases_version_automation", table_name="test_cases")
    op.drop_index("ix_test_cases_version_type", table_name="test_cases")
    op.drop_index("ix_test_cases_version_status", table_name="test_cases")

    with op.batch_alter_table("test_cases") as batch_op:
        for constraint_name, constraint_type in (
            ("ck_test_cases_retry_count", "check"),
            ("ck_test_cases_timeout", "check"),
            ("ck_test_cases_duration", "check"),
            ("ck_test_cases_source", "check"),
            ("ck_test_cases_automation_status", "check"),
            ("ck_test_cases_case_type", "check"),
            ("ck_test_cases_template", "check"),
            ("ck_test_cases_case_status", "check"),
            ("fk_test_cases_updated_by", "foreignkey"),
            ("fk_test_cases_created_by", "foreignkey"),
            ("fk_test_cases_owner", "foreignkey"),
            ("uq_test_cases_case_key", "unique"),
        ):
            batch_op.drop_constraint(constraint_name, type_=constraint_type)
        for column_name in (
            "updated_by",
            "created_by",
            "custom_fields",
            "retry_count",
            "timeout_seconds",
            "estimated_duration_seconds",
            "postconditions",
            "artifact_requirements",
            "steps",
            "data_bindings",
            "preconditions",
            "owner_id",
            "requirement_refs",
            "component",
            "source_ref",
            "source",
            "automation_status",
            "case_type",
            "template",
            "case_status",
            "objective",
            "case_key",
        ):
            batch_op.drop_column(column_name)

    op.drop_table("project_sequences")

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint("ck_projects_key_format", type_="check")
        batch_op.drop_constraint("fk_projects_lead_user", type_="foreignkey")
        batch_op.drop_constraint("uq_projects_key", type_="unique")
        batch_op.drop_column("lead_user_id")
        batch_op.drop_column("key")
