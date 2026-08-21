"""add ai feedback fields to submissions

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-03

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column("ai_feedback_status", sa.String(20), nullable=False, server_default="pending"),
    )
    op.add_column(
        "submissions",
        sa.Column("ai_feedback_text", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("submissions", "ai_feedback_text")
    op.drop_column("submissions", "ai_feedback_status")
