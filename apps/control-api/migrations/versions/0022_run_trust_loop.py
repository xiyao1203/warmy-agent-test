"""Add durable Run trust-loop postprocessing records.

Revision ID: 0022
Revises: 0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _project_run_fk(name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["project_id", "run_id"],
        ["runs.project_id", "runs.id"],
        ondelete="CASCADE",
        name=name,
    )


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.create_unique_constraint("uq_runs_project_id", ["project_id", "id"])

    op.create_table(
        "run_postprocess_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_stage", sa.String(32), nullable=True),
        sa.Column("workflow_id", sa.String(255), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("warning_codes", sa.JSON(), nullable=False),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _project_run_fk("fk_run_postprocess_jobs_project_run"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "id", name="uq_run_postprocess_jobs_project_id"),
        sa.UniqueConstraint(
            "project_id",
            "run_id",
            "pipeline_version",
            name="uq_run_postprocess_jobs_project_run_pipeline",
        ),
    )
    op.create_index(
        "ix_run_postprocess_jobs_project_status_updated",
        "run_postprocess_jobs",
        ["project_id", "status", "updated_at"],
    )
    op.create_table(
        "run_postprocess_stage_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("warning_code", sa.String(100), nullable=True),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id", "job_id"],
            ["run_postprocess_jobs.project_id", "run_postprocess_jobs.id"],
            ondelete="CASCADE",
            name="fk_run_postprocess_stage_results_project_job",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "job_id", "stage", name="uq_run_postprocess_stage_results_job_stage"
        ),
    )
    op.create_index(
        "ix_run_postprocess_stage_results_project_job",
        "run_postprocess_stage_results",
        ["project_id", "job_id", "completed_at"],
    )
    op.create_table(
        "run_diagnostics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("run_case_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("failure_class", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("counterevidence", sa.JSON(), nullable=False),
        sa.Column("verification_steps", sa.JSON(), nullable=False),
        sa.Column("model_adapter_version", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _project_run_fk("fk_run_diagnostics_project_run"),
        sa.ForeignKeyConstraint(["run_case_id"], ["run_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "run_case_id",
            "pipeline_version",
            name="uq_run_diagnostics_project_case_pipeline",
        ),
    )
    op.create_index(
        "ix_run_diagnostics_project_run",
        "run_diagnostics",
        ["project_id", "run_id", "created_at"],
    )
    op.create_table(
        "run_regression_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("run_case_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_version", sa.String(64), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("input_reference", sa.JSON(), nullable=False),
        sa.Column("minimized_input", sa.JSON(), nullable=True),
        sa.Column("reproduction_run_case_ids", sa.JSON(), nullable=False),
        sa.Column("reproduction_count", sa.Integer(), nullable=False),
        sa.Column("target_dataset_version_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _project_run_fk("fk_run_regression_candidates_project_run"),
        sa.ForeignKeyConstraint(["run_case_id"], ["run_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "fingerprint",
            "pipeline_version",
            name="uq_run_regression_candidates_project_fingerprint_pipeline",
        ),
    )
    op.create_index(
        "ix_run_regression_candidates_project_status",
        "run_regression_candidates",
        ["project_id", "status", "updated_at"],
    )
    op.create_table(
        "run_calibrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("sample_set_version", sa.String(100), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("arbitration", sa.JSON(), nullable=False),
        sa.Column("evaluator_version", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        _project_run_fk("fk_run_calibrations_project_run"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "run_id",
            "pipeline_version",
            name="uq_run_calibrations_project_run_pipeline",
        ),
    )
    op.create_table(
        "run_joint_gate_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_version", sa.String(64), nullable=False),
        sa.Column("baseline_run_id", sa.Uuid(), nullable=True),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("input_facts", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        _project_run_fk("fk_run_joint_gate_decisions_project_run"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "run_id",
            "pipeline_version",
            name="uq_run_joint_gate_decisions_project_run_pipeline",
        ),
    )


def downgrade() -> None:
    op.drop_table("run_joint_gate_decisions")
    op.drop_table("run_calibrations")
    op.drop_index(
        "ix_run_regression_candidates_project_status", table_name="run_regression_candidates"
    )
    op.drop_table("run_regression_candidates")
    op.drop_index("ix_run_diagnostics_project_run", table_name="run_diagnostics")
    op.drop_table("run_diagnostics")
    op.drop_index(
        "ix_run_postprocess_stage_results_project_job",
        table_name="run_postprocess_stage_results",
    )
    op.drop_table("run_postprocess_stage_results")
    op.drop_index(
        "ix_run_postprocess_jobs_project_status_updated", table_name="run_postprocess_jobs"
    )
    op.drop_table("run_postprocess_jobs")
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_constraint("uq_runs_project_id", type_="unique")
