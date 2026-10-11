"""create_investigation_reports_table

Revision ID: a3b4c5d6e7f8
Revises: 92fa468ac738
Create Date: 2026-10-11 16:03:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: str | None = "92fa468ac738"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investigation_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("exception_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="COMPLETED"),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="mock"),
        sa.Column(
            "model_name", sa.String(length=100), nullable=False, server_default="gemini-1.5-pro"
        ),
        sa.Column("prompt_version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("observed_discrepancy", sa.Text(), nullable=False),
        sa.Column("report_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "cited_evidence_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "policy_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exception_id"],
            ["exceptions.id"],
            name="fk_investigation_reports_exception_id_exceptions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name="fk_investigation_reports_merchant_id_merchants",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_investigation_reports_merchant_id",
        "investigation_reports",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_investigation_reports_exception_id",
        "investigation_reports",
        ["exception_id"],
        unique=False,
    )
    op.create_index(
        "ix_investigation_reports_status", "investigation_reports", ["status"], unique=False
    )
    op.create_index(
        "ix_investigation_reports_created_at", "investigation_reports", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_investigation_reports_created_at", table_name="investigation_reports")
    op.drop_index("ix_investigation_reports_status", table_name="investigation_reports")
    op.drop_index("ix_investigation_reports_exception_id", table_name="investigation_reports")
    op.drop_index("ix_investigation_reports_merchant_id", table_name="investigation_reports")
    op.drop_table("investigation_reports")
