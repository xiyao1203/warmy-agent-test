"""Executable asset versions and evidence persistence.

Revision ID: 0013
Revises: 0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _project_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
    ]


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.add_column(
        "agent_versions",
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("agent_versions", sa.Column("invocation_config", sa.JSON(), nullable=True))
    op.add_column(
        "agent_versions",
        sa.Column("readiness_status", sa.String(32), nullable=False, server_default="ready"),
    )
    if op.get_bind().dialect.name == "sqlite":
        op.execute(
            """UPDATE agent_versions
            SET invocation_config = json_object(
                'endpoint_url', json_extract(config, '$.api_url'),
                'protocol', 'sync_json',
                'request_template', json_object('input', '{{ input }}'),
                'response_path', 'output',
                'timeout_seconds', COALESCE(json_extract(config, '$.timeout'), 30),
                'credential_binding_ids', json_array()
            ), readiness_status = CASE
                WHEN COALESCE(json_extract(config, '$.api_url'), '') = ''
                    THEN 'needs_configuration'
                ELSE 'ready' END
            """
        )
    else:
        op.execute(
            """UPDATE agent_versions
            SET invocation_config = json_build_object(
                'endpoint_url', config->>'api_url',
                'protocol', 'sync_json',
                'request_template', json_build_object('input', '{{ input }}'),
                'response_path', 'output',
                'timeout_seconds', COALESCE((config->>'timeout')::integer, 30),
                'credential_binding_ids', json_build_array()
            ), readiness_status = CASE
                WHEN COALESCE(config->>'api_url', '') = '' THEN 'needs_configuration'
                ELSE 'ready' END
            """
        )
    op.add_column("security_scans", sa.Column("run_id", sa.Uuid(), nullable=True))
    op.add_column("security_scans", sa.Column("agent_version_id", sa.Uuid(), nullable=True))
    op.add_column("security_scans", sa.Column("environment_version_id", sa.Uuid(), nullable=True))
    op.add_column("security_scans", sa.Column("security_profile_id", sa.Uuid(), nullable=True))
    if op.get_bind().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_security_scans_run",
            "security_scans",
            "runs",
            ["run_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_security_scans_project_run", "security_scans", ["project_id", "run_id", "status"]
    )

    op.create_table(
        "environment_versions",
        *_project_columns(),
        sa.Column(
            "environment_template_id",
            sa.Uuid(),
            sa.ForeignKey("environment_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint(
            "environment_template_id", "version_number", name="uq_environment_versions_number"
        ),
        sa.UniqueConstraint("project_id", "id", name="uq_environment_versions_project_id"),
    )
    op.create_index(
        "ix_environment_versions_project_template",
        "environment_versions",
        ["project_id", "environment_template_id", "status"],
    )

    op.create_table(
        "credential_bindings",
        *_project_columns(),
        sa.Column("alias", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("injection_location", sa.String(32), nullable=False),
        sa.Column("injection_name", sa.String(200), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("masked_hint", sa.String(32), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "id", name="uq_credential_bindings_project_id"),
        sa.UniqueConstraint("project_id", "alias", name="uq_credential_bindings_alias"),
    )

    op.create_table(
        "scorer_versions",
        *_project_columns(),
        sa.Column(
            "scorer_id", sa.Uuid(), sa.ForeignKey("scorers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("scorer_id", "version_number", name="uq_scorer_versions_number"),
        sa.UniqueConstraint("project_id", "id", name="uq_scorer_versions_project_id"),
    )

    op.create_table(
        "security_profiles",
        *_project_columns(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "name", name="uq_security_profiles_name"),
    )

    op.create_table(
        "review_policies",
        *_project_columns(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "name", name="uq_review_policies_name"),
    )

    op.create_table(
        "run_evaluations",
        *_project_columns(),
        sa.Column(
            "run_id", sa.Uuid(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("aggregate_score", sa.Float(), nullable=True),
        sa.Column("pass_rate", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=True),
        sa.Column("token_usage", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "run_id", name="uq_run_evaluations_project_run"),
        sa.UniqueConstraint("project_id", "id", name="uq_run_evaluations_project_id"),
    )

    op.create_table(
        "scores",
        *_project_columns(),
        sa.Column(
            "evaluation_id",
            sa.Uuid(),
            sa.ForeignKey("run_evaluations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_case_id",
            sa.Uuid(),
            sa.ForeignKey("run_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scorer_version_id", sa.Uuid(), sa.ForeignKey("scorer_versions.id"), nullable=True
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint(
            "evaluation_id", "run_case_id", "scorer_version_id", name="uq_scores_source"
        ),
    )
    op.create_index("ix_scores_project_case", "scores", ["project_id", "run_case_id"])

    op.create_table(
        "release_decisions",
        *_project_columns(),
        sa.Column("gate_id", sa.Uuid(), sa.ForeignKey("release_gates.id"), nullable=False),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), sa.ForeignKey("experiments.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("facts", sa.JSON(), nullable=False),
        sa.Column("failures", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("evaluated_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        *_timestamps(),
    )
    op.create_index(
        "ix_release_decisions_project_run",
        "release_decisions",
        ["project_id", "run_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_release_decisions_project_run", table_name="release_decisions")
    op.drop_table("release_decisions")
    op.drop_index("ix_scores_project_case", table_name="scores")
    op.drop_table("scores")
    op.drop_table("run_evaluations")
    op.drop_table("review_policies")
    op.drop_table("security_profiles")
    op.drop_table("scorer_versions")
    op.drop_table("credential_bindings")
    op.drop_index("ix_environment_versions_project_template", table_name="environment_versions")
    op.drop_table("environment_versions")
    op.drop_index("ix_security_scans_project_run", table_name="security_scans")
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint("fk_security_scans_run", "security_scans", type_="foreignkey")
    op.drop_column("security_scans", "security_profile_id")
    op.drop_column("security_scans", "environment_version_id")
    op.drop_column("security_scans", "agent_version_id")
    op.drop_column("security_scans", "run_id")
    op.drop_column("agent_versions", "readiness_status")
    op.drop_column("agent_versions", "invocation_config")
    op.drop_column("agent_versions", "schema_version")
