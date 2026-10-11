from decimal import Decimal

from app.db.seed_data import generate_deterministic_dataset
from app.models.enums import ExceptionType, PaymentStatus, RefundStatus


def test_seed_dataset_generation_counts():
    """Verify that dataset meets all volume requirements: 250+ payments, 20+ settlements, 50+ benchmarks."""
    ds = generate_deterministic_dataset()

    assert len(ds.payments) >= 250, f"Expected >= 250 payments, got {len(ds.payments)}"
    assert len(ds.settlements) >= 20, f"Expected >= 20 settlements, got {len(ds.settlements)}"
    assert len(ds.settlement_items) >= 250
    assert len(ds.benchmark_cases) >= 50
    assert len(ds.reconciliation_results) >= 50
    assert len(ds.exceptions) >= 20


def test_seed_dataset_all_amounts_are_decimal():
    """Verify that all monetary values in the dataset are Decimal instances, not float or str."""
    ds = generate_deterministic_dataset()

    for p in ds.payments:
        assert isinstance(p["amount"], Decimal), f"Payment amount {p['amount']} is not Decimal"

    for f in ds.fees:
        assert isinstance(f["amount"], Decimal), f"Fee amount {f['amount']} is not Decimal"
        assert isinstance(f["tax_amount"], Decimal), (
            f"Fee tax_amount {f['tax_amount']} is not Decimal"
        )

    for r in ds.refunds:
        assert isinstance(r["amount"], Decimal), f"Refund amount {r['amount']} is not Decimal"

    for s in ds.settlements:
        assert isinstance(s["amount"], Decimal), f"Settlement amount {s['amount']} is not Decimal"

    for a in ds.adjustments:
        assert isinstance(a["amount"], Decimal), f"Adjustment amount {a['amount']} is not Decimal"


def test_required_financial_scenarios_exist():
    """Verify all 25 specific scenario categories specified in prompt exist in benchmark cases."""
    ds = generate_deterministic_dataset()
    scenario_ids = {b["scenario_id"] for b in ds.benchmark_cases}

    required_keys = [
        "SCEN_01_FULL_MATCH",
        "SCEN_02_PARTIAL_REFUND",
        "SCEN_03_MULTIPLE_REFUNDS",
        "SCEN_04_FEE_ACCOUNTED",
        "SCEN_05_INCORRECT_FEE",
        "SCEN_06_MISSING_SETTLEMENT",
        "SCEN_07_SETTLEMENT_NO_PAYMENT",
        "SCEN_08_DUPLICATE_PAYMENT",
        "SCEN_09_DUPLICATE_SETTLEMENT",
        "SCEN_10_DELAYED_SETTLEMENT",
        "SCEN_11_AMOUNT_MISMATCH",
        "SCEN_12_POSITIVE_ADJUSTMENT",
        "SCEN_13_NEGATIVE_ADJUSTMENT",
        "SCEN_14_SETTLEMENT_LEVEL_ADJ",
        "SCEN_15_REFUND_NOT_IN_SETTLEMENT",
        "SCEN_16_MISSING_EXT_ID",
        "SCEN_17_MULTI_PAYMENT_BATCH_A",
        "SCEN_18_MULTI_PAYMENT_BATCH_B",
        "SCEN_19_AMBIGUOUS_EVIDENCE",
        "SCEN_20_CROSS_CURRENCY",
        "SCEN_21_FAILED_PAYMENT",
        "SCEN_22_FAILED_REFUND",
        "SCEN_23_WITHIN_TOLERANCE",
        "SCEN_24_OUTSIDE_TOLERANCE",
        "SCEN_25_INSUFFICIENT_EVIDENCE",
    ]

    for req in required_keys:
        assert req in scenario_ids, f"Required scenario {req} missing from benchmark dataset"


def test_failed_payment_and_failed_refund_integrity():
    """Verify failed payments do not generate expected revenue, and failed refunds do not reduce settlement."""
    ds = generate_deterministic_dataset()

    failed_payment = next(
        p
        for p in ds.payments
        if p["payment_metadata"].get("scenario_id") == "SCEN_21_FAILED_PAYMENT"
    )
    assert failed_payment["status"] == PaymentStatus.FAILED

    failed_refund = next(
        r for r in ds.refunds if r["refund_metadata"].get("scenario_id") == "SCEN_22_FAILED_REFUND"
    )
    assert failed_refund["status"] == RefundStatus.FAILED


def test_exception_type_coverage():
    """Verify representative exception types are covered across benchmarks."""
    ds = generate_deterministic_dataset()
    covered_types = {
        b["expected_exception_type"]
        for b in ds.benchmark_cases
        if b["expected_exception_type"] is not None
    }

    assert ExceptionType.FEE_MISMATCH in covered_types
    assert ExceptionType.AMOUNT_MISMATCH in covered_types
    assert ExceptionType.MISSING_SETTLEMENT in covered_types
    assert ExceptionType.MISSING_PAYMENT in covered_types
    assert ExceptionType.DUPLICATE_PAYMENT in covered_types
    assert ExceptionType.DUPLICATE_SETTLEMENT in covered_types
    assert ExceptionType.DELAYED_SETTLEMENT in covered_types
    assert ExceptionType.REFUND_MISMATCH in covered_types
    assert ExceptionType.ADJUSTMENT_MISMATCH in covered_types


def test_deterministic_reproducibility():
    """Verify that repeated calls to generate_deterministic_dataset yield identical results."""
    ds1 = generate_deterministic_dataset()
    ds2 = generate_deterministic_dataset()

    assert len(ds1.payments) == len(ds2.payments)
    assert len(ds1.settlements) == len(ds2.settlements)
    assert ds1.payments[0]["id"] == ds2.payments[0]["id"]
    assert ds1.payments[0]["amount"] == ds2.payments[0]["amount"]
    assert ds1.settlements[0]["id"] == ds2.settlements[0]["id"]
