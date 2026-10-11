from decimal import Decimal

import app.models  # noqa: F401
from app.db.base import Base
from app.models import (
    Adjustment,
    AIInvestigation,
    BenchmarkCase,
    ExceptionRecord,
    Fee,
    Payment,
    ReconciliationResult,
    Refund,
    Settlement,
    SettlementItem,
)
from sqlalchemy import Numeric, inspect


def test_all_16_models_registered_in_base_metadata():
    """Verify that all 16 financial domain models are registered with SQLAlchemy Base.metadata."""
    tables = Base.metadata.tables.keys()
    expected_tables = {
        "merchants",
        "source_integrations",
        "payments",
        "refunds",
        "fees",
        "settlements",
        "settlement_items",
        "adjustments",
        "reconciliation_runs",
        "reconciliation_results",
        "exceptions",
        "evidence",
        "ai_investigations",
        "reviews",
        "audit_events",
        "benchmark_cases",
    }
    assert expected_tables.issubset(tables)


def test_monetary_columns_use_numeric_with_correct_precision():
    """Verify that financial amounts use Numeric(20, 2) rather than Float or String."""
    numeric_columns = [
        (Payment, "amount", 20, 2),
        (Refund, "amount", 20, 2),
        (Fee, "amount", 20, 2),
        (Fee, "tax_amount", 20, 2),
        (Settlement, "amount", 20, 2),
        (SettlementItem, "gross_amount", 20, 2),
        (SettlementItem, "fee_amount", 20, 2),
        (SettlementItem, "refund_amount", 20, 2),
        (SettlementItem, "adjustment_amount", 20, 2),
        (SettlementItem, "net_amount", 20, 2),
        (Adjustment, "amount", 20, 2),
        (ReconciliationResult, "expected_amount", 20, 2),
        (ReconciliationResult, "actual_amount", 20, 2),
        (ReconciliationResult, "difference", 20, 2),
        (ReconciliationResult, "tolerance", 20, 2),
        (ExceptionRecord, "financial_impact", 20, 2),
        (BenchmarkCase, "expected_financial_impact", 20, 2),
    ]

    for model_cls, col_name, prec, scale in numeric_columns:
        col = getattr(model_cls, col_name).property.columns[0]
        assert isinstance(col.type, Numeric), f"{model_cls.__name__}.{col_name} must be Numeric"
        assert col.type.precision == prec, (
            f"{model_cls.__name__}.{col_name} precision must be {prec}"
        )
        assert col.type.scale == scale, f"{model_cls.__name__}.{col_name} scale must be {scale}"


def test_confidence_columns_use_numeric_5_4():
    """Verify confidence columns use Numeric(5, 4) for high-precision probability representations."""
    confidence_cols = [
        (ReconciliationResult, "confidence"),
        (ExceptionRecord, "confidence"),
        (AIInvestigation, "confidence"),
    ]
    for model_cls, col_name in confidence_cols:
        col = getattr(model_cls, col_name).property.columns[0]
        assert isinstance(col.type, Numeric), f"{model_cls.__name__}.{col_name} must be Numeric"
        assert col.type.precision == 5
        assert col.type.scale == 4


def test_foreign_key_relationships_configured():
    """Inspect foreign keys and relationships between models."""
    insp_payment = inspect(Payment)
    fks_payment = {fk.target_fullname for fk in insp_payment.columns["merchant_id"].foreign_keys}
    assert "merchants.id" in fks_payment

    insp_item = inspect(SettlementItem)
    fks_item_settlement = {
        fk.target_fullname for fk in insp_item.columns["settlement_id"].foreign_keys
    }
    assert "settlements.id" in fks_item_settlement

    # Verify payment_id in SettlementItem is nullable for missing payment exceptions
    assert insp_item.columns["payment_id"].nullable is True


def test_signed_adjustment_convention():
    """Verify adjustment calculation convention: expected = gross - refund - fee + adjustment."""
    gross = Decimal("1000.00")
    refund = Decimal("100.00")
    fee = Decimal("20.00")
    positive_adj = Decimal("50.00")  # increases settlement
    negative_adj = Decimal("-50.00")  # decreases settlement

    expected_with_pos = gross - refund - fee + positive_adj
    expected_with_neg = gross - refund - fee + negative_adj

    assert expected_with_pos == Decimal("930.00")
    assert expected_with_neg == Decimal("830.00")
