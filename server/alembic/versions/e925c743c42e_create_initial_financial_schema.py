"""create_initial_financial_schema

Revision ID: e925c743c42e
Revises: None
Create Date: 2026-10-11 08:53:11.769006

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e925c743c42e"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. benchmark_cases
    op.create_table(
        "benchmark_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_version", sa.String(length=50), nullable=False),
        sa.Column("scenario_id", sa.String(length=100), nullable=False),
        sa.Column("source_reference", sa.String(length=100), nullable=True),
        sa.Column("expected_match_status", sa.String(length=50), nullable=False),
        sa.Column("expected_exception_type", sa.String(length=50), nullable=True),
        sa.Column("expected_root_cause", sa.Text(), nullable=True),
        sa.Column("expected_financial_impact", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("expected_policy_outcome", sa.String(length=50), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_id", name="uq_benchmark_cases_scenario_id"),
    )
    op.create_index(
        "ix_benchmark_cases_dataset_scenario",
        "benchmark_cases",
        ["dataset_version", "scenario_id"],
        unique=False,
    )
    op.create_index(
        "ix_benchmark_cases_expected_type",
        "benchmark_cases",
        ["expected_exception_type"],
        unique=False,
    )

    # 2. merchants
    op.create_table(
        "merchants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("external_reference", sa.String(length=100), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(currency) = 3", name="ck_merchant_currency_length"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_merchants_email"),
        sa.UniqueConstraint("external_reference", name="uq_merchants_external_reference"),
    )
    op.create_index("ix_merchants_status", "merchants", ["status"], unique=False)

    # 3. source_integrations
    op.create_table(
        "source_integrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_source_integrations_merchant_provider",
        "source_integrations",
        ["merchant_id", "provider"],
        unique=False,
    )

    # 4. payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("source_integration_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.Column("external_order_id", sa.String(length=100), nullable=True),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        sa.CheckConstraint("length(currency) = 3", name="ck_payments_currency_length"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["source_integration_id"], ["source_integrations.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "external_id", name="uq_payments_merchant_external_id"),
    )
    op.create_index(
        "ix_payments_external_order_id",
        "payments",
        ["merchant_id", "external_order_id"],
        unique=False,
    )
    op.create_index(
        "ix_payments_merchant_source_created",
        "payments",
        ["merchant_id", "source_created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payments_merchant_status",
        "payments",
        ["merchant_id", "status"],
        unique=False,
    )

    # 5. reconciliation_runs
    op.create_table(
        "reconciliation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("source_integration_id", sa.Uuid(), nullable=True),
        sa.Column("run_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_records", sa.Integer(), nullable=False),
        sa.Column("matched_records", sa.Integer(), nullable=False),
        sa.Column("unmatched_records", sa.Integer(), nullable=False),
        sa.Column("exception_records", sa.Integer(), nullable=False),
        sa.Column("auto_classified_records", sa.Integer(), nullable=False),
        sa.Column("review_required_records", sa.Integer(), nullable=False),
        sa.Column("processing_duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("configuration_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["source_integration_id"], ["source_integrations.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reconciliation_runs_merchant_status",
        "reconciliation_runs",
        ["merchant_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_runs_started_at",
        "reconciliation_runs",
        ["started_at"],
        unique=False,
    )

    # 6. settlements
    op.create_table(
        "settlements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("source_integration_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("initiated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(currency) = 3", name="ck_settlements_currency_length"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["source_integration_id"], ["source_integrations.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "merchant_id", "external_id", name="uq_settlements_merchant_external_id"
        ),
    )
    op.create_index(
        "ix_settlements_merchant_date",
        "settlements",
        ["merchant_id", "settlement_date"],
        unique=False,
    )
    op.create_index(
        "ix_settlements_merchant_status",
        "settlements",
        ["merchant_id", "status"],
        unique=False,
    )

    # 7. adjustments (signed numeric amount)
    op.create_table(
        "adjustments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("settlement_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("adjustment_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(currency) = 3", name="ck_adjustments_currency_length"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_adjustments_merchant_type",
        "adjustments",
        ["merchant_id", "adjustment_type"],
        unique=False,
    )
    op.create_index("ix_adjustments_payment_id", "adjustments", ["payment_id"], unique=False)
    op.create_index("ix_adjustments_settlement_id", "adjustments", ["settlement_id"], unique=False)

    # 8. fees
    op.create_table(
        "fees",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("fee_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("tax_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_fees_amount_non_negative"),
        sa.CheckConstraint("tax_amount >= 0", name="ck_fees_tax_amount_non_negative"),
        sa.CheckConstraint("length(currency) = 3", name="ck_fees_currency_length"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fees_fee_type", "fees", ["fee_type"], unique=False)
    op.create_index("ix_fees_merchant_payment", "fees", ["merchant_id", "payment_id"], unique=False)

    # 9. reconciliation_results
    op.create_table(
        "reconciliation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("settlement_id", sa.Uuid(), nullable=True),
        sa.Column("match_type", sa.String(length=50), nullable=False),
        sa.Column("match_status", sa.String(length=50), nullable=False),
        sa.Column("expected_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("actual_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("difference", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("tolerance", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("matching_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_reconciliation_results_confidence_range",
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["run_id"], ["reconciliation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reconciliation_results_payment_id",
        "reconciliation_results",
        ["payment_id"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_results_run_status",
        "reconciliation_results",
        ["run_id", "match_status"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_results_settlement_id",
        "reconciliation_results",
        ["settlement_id"],
        unique=False,
    )

    # 10. refunds
    op.create_table(
        "refunds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_refunds_amount_positive"),
        sa.CheckConstraint("length(currency) = 3", name="ck_refunds_currency_length"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "external_id", name="uq_refunds_merchant_external_id"),
    )
    op.create_index(
        "ix_refunds_merchant_status", "refunds", ["merchant_id", "status"], unique=False
    )
    op.create_index("ix_refunds_payment_id", "refunds", ["payment_id"], unique=False)

    # 11. settlement_items
    op.create_table(
        "settlement_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("settlement_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("external_payment_id", sa.String(length=100), nullable=True),
        sa.Column("gross_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("fee_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("refund_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("adjustment_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("net_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(currency) = 3", name="ck_settlement_items_currency_length"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlements.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_settlement_items_external_payment_id",
        "settlement_items",
        ["merchant_id", "external_payment_id"],
        unique=False,
    )
    op.create_index(
        "ix_settlement_items_payment_id", "settlement_items", ["payment_id"], unique=False
    )
    op.create_index(
        "ix_settlement_items_settlement_id",
        "settlement_items",
        ["settlement_id"],
        unique=False,
    )

    # 12. exceptions
    op.create_table(
        "exceptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("reconciliation_result_id", sa.Uuid(), nullable=False),
        sa.Column("exception_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("financial_impact", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("first_detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_exceptions_confidence_range",
        ),
        sa.CheckConstraint("length(currency) = 3", name="ck_exceptions_currency_length"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["reconciliation_result_id"],
            ["reconciliation_results.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reconciliation_result_id", name="uq_exceptions_reconciliation_result_id"
        ),
    )
    op.create_index(
        "ix_exceptions_merchant_status",
        "exceptions",
        ["merchant_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_exceptions_type_severity",
        "exceptions",
        ["exception_type", "severity"],
        unique=False,
    )

    # 13. ai_investigations
    op.create_table(
        "ai_investigations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exception_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("classification", sa.String(length=50), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("recommended_action", sa.String(length=255), nullable=False),
        sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validation_status", sa.String(length=50), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_ai_investigations_confidence_range",
        ),
        sa.ForeignKeyConstraint(["exception_id"], ["exceptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_investigations_classification",
        "ai_investigations",
        ["classification"],
        unique=False,
    )
    op.create_index(
        "ix_ai_investigations_exception_id",
        "ai_investigations",
        ["exception_id"],
        unique=False,
    )

    # 14. audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("exception_id", sa.Uuid(), nullable=True),
        sa.Column("reconciliation_run_id", sa.Uuid(), nullable=True),
        sa.Column("actor_type", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("previous_state", sa.String(length=100), nullable=True),
        sa.Column("new_state", sa.String(length=100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exception_id"], ["exceptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["reconciliation_run_id"],
            ["reconciliation_runs.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"], unique=False)
    op.create_index("ix_audit_events_exception_id", "audit_events", ["exception_id"], unique=False)
    op.create_index(
        "ix_audit_events_merchant_created",
        "audit_events",
        ["merchant_id", "created_at"],
        unique=False,
    )

    # 15. evidence
    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exception_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("source_table", sa.String(length=100), nullable=False),
        sa.Column("source_record_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exception_id"], ["exceptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_exception_id", "evidence", ["exception_id"], unique=False)
    op.create_index(
        "ix_evidence_source_record",
        "evidence",
        ["source_table", "source_record_id"],
        unique=False,
    )

    # 16. reviews
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exception_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.String(length=100), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("previous_status", sa.String(length=50), nullable=False),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exception_id"], ["exceptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_exception_id", "reviews", ["exception_id"], unique=False)
    op.create_index("ix_reviews_reviewer_id", "reviews", ["reviewer_id"], unique=False)


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("evidence")
    op.drop_table("audit_events")
    op.drop_table("ai_investigations")
    op.drop_table("exceptions")
    op.drop_table("settlement_items")
    op.drop_table("refunds")
    op.drop_table("reconciliation_results")
    op.drop_table("fees")
    op.drop_table("adjustments")
    op.drop_table("settlements")
    op.drop_table("reconciliation_runs")
    op.drop_table("payments")
    op.drop_table("source_integrations")
    op.drop_table("merchants")
    op.drop_table("benchmark_cases")
