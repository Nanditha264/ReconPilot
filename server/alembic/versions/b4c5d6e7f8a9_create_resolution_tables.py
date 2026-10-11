"""create_resolution_tables

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-10-11 16:24:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b4c5d6e7f8a9"
down_revision: str | None = "a3b4c5d6e7f8"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add resolution_status column to exceptions table
    op.add_column(
        "exceptions",
        sa.Column(
            "resolution_status",
            sa.String(length=50),
            nullable=False,
            server_default="OPEN",
        ),
    )
    op.create_index(
        "ix_exceptions_resolution_status",
        "exceptions",
        ["resolution_status"],
        unique=False,
    )

    # 2. Create resolution_proposals table
    op.create_table(
        "resolution_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("exception_id", sa.Uuid(), nullable=False),
        sa.Column("investigation_report_id", sa.Uuid(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="OTHER"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("proposed_action", sa.Text(), nullable=False),
        sa.Column(
            "supporting_evidence_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("decision_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("decision_rationale", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_resolution_proposals_created_by_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["decision_by_user_id"],
            ["users.id"],
            name="fk_resolution_proposals_decision_by_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["exception_id"],
            ["exceptions.id"],
            name="fk_resolution_proposals_exception_id_exceptions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["investigation_report_id"],
            ["investigation_reports.id"],
            name="fk_resolution_proposals_report_id_investigation_reports",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name="fk_resolution_proposals_merchant_id_merchants",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resolution_proposals_merchant_id",
        "resolution_proposals",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_resolution_proposals_exception_id",
        "resolution_proposals",
        ["exception_id"],
        unique=False,
    )
    op.create_index(
        "ix_resolution_proposals_status",
        "resolution_proposals",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_resolution_proposals_created_at",
        "resolution_proposals",
        ["created_at"],
        unique=False,
    )

    # 3. Create resolution_history table
    op.create_table(
        "resolution_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("exception_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("previous_status", sa.String(length=50), nullable=False),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exception_id"],
            ["exceptions.id"],
            name="fk_resolution_history_exception_id_exceptions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name="fk_resolution_history_merchant_id_merchants",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["proposal_id"],
            ["resolution_proposals.id"],
            name="fk_resolution_history_proposal_id_proposals",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_resolution_history_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resolution_history_merchant_id",
        "resolution_history",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_resolution_history_exception_id",
        "resolution_history",
        ["exception_id"],
        unique=False,
    )
    op.create_index(
        "ix_resolution_history_created_at",
        "resolution_history",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_resolution_history_event_type",
        "resolution_history",
        ["event_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resolution_history_event_type", table_name="resolution_history")
    op.drop_index("ix_resolution_history_created_at", table_name="resolution_history")
    op.drop_index("ix_resolution_history_exception_id", table_name="resolution_history")
    op.drop_index("ix_resolution_history_merchant_id", table_name="resolution_history")
    op.drop_table("resolution_history")

    op.drop_index("ix_resolution_proposals_created_at", table_name="resolution_proposals")
    op.drop_index("ix_resolution_proposals_status", table_name="resolution_proposals")
    op.drop_index("ix_resolution_proposals_exception_id", table_name="resolution_proposals")
    op.drop_index("ix_resolution_proposals_merchant_id", table_name="resolution_proposals")
    op.drop_table("resolution_proposals")

    op.drop_index("ix_exceptions_resolution_status", table_name="exceptions")
    op.drop_column("exceptions", "resolution_status")
