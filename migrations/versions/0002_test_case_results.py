"""bring test_case_results under alembic, add real FK to submissions

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drops the old hand-written table (schema.sql, never Alembic-
    # managed) -- this was a known, flagged piece of schema drift.
    # Existing rows are just leftover manual-test data, not real user
    # data, safe to drop.
    op.execute("DROP TABLE IF EXISTS test_case_results")

    op.create_table(
        "test_case_results",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("submissions.id"),
            nullable=False,
        ),
        sa.Column("test_case_index", sa.Integer, nullable=False),
        sa.Column("verdict", sa.String(30), nullable=False),
        sa.Column("stdout", sa.Text),
        sa.Column("stderr", sa.Text),
        sa.Column("exit_code", sa.Integer),
        sa.Column("runtime_seconds", sa.Float),
        sa.Column("timed_out", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("compile_error", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_test_case_results_submission_id", "test_case_results", ["submission_id"]
    )


def downgrade() -> None:
    op.drop_table("test_case_results")
