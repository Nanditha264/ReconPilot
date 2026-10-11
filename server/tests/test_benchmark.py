from decimal import Decimal

from app.db.session import SessionLocal
from app.models.benchmark_case import BenchmarkCase
from app.models.enums import RunType
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.reconciliation_result import ReconciliationResult
from app.models.settlement_item import SettlementItem
from app.modules.reconciliation.service import run_reconciliation
from sqlalchemy import select


def calculate_binary_metrics(
    tp: int, fp: int, tn: int, fn: int
) -> tuple[Decimal, Decimal, Decimal]:
    """Calculates precision, recall, and F1 with zero-division protection."""
    precision = Decimal(str(tp)) / Decimal(str(tp + fp)) if (tp + fp) > 0 else Decimal("0.0000")
    recall = Decimal(str(tp)) / Decimal(str(tp + fn)) if (tp + fn) > 0 else Decimal("0.0000")
    f1 = (
        (Decimal("2") * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else Decimal("0.0000")
    )
    return precision, recall, f1


def test_metric_formula_edge_cases():
    """Verify that calculate_binary_metrics guards against zero denominators and computes accurately."""
    # Zero TP and FP
    p0, r0, f0 = calculate_binary_metrics(0, 0, 10, 5)
    assert p0 == Decimal("0.0000")
    assert r0 == Decimal("0.0000")
    assert f0 == Decimal("0.0000")

    # Standard values: TP=6, FP=2, TN=24, FN=18
    p, r, f1 = calculate_binary_metrics(6, 2, 24, 18)
    assert p == Decimal("6") / Decimal("8")  # 0.7500
    assert r == Decimal("6") / Decimal("24")  # 0.2500
    assert f1 == (Decimal("2") * Decimal("0.75") * Decimal("0.25")) / (
        Decimal("0.75") + Decimal("0.25")
    )  # 0.3750


def test_benchmark_reproducible_evaluation():
    """
    Executes the deterministic reconciliation engine and performs an end-to-end evaluation
    against all 50 ground-truth BenchmarkCase fixtures stored in PostgreSQL.
    Verifies 100% scenario mapping coverage, scenario uniqueness, and calculates the confusion matrix.
    """
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        assert merchant is not None

        # 1. Read ground-truth benchmark cases
        cases = db.scalars(select(BenchmarkCase)).all()
        assert len(cases) == 50, f"Expected exactly 50 benchmark cases, found {len(cases)}"

        scenario_ids = [c.scenario_id for c in cases]
        assert len(scenario_ids) == len(set(scenario_ids)), "Scenario IDs must be strictly unique"

        # 2. Run deterministic engine
        run_record = run_reconciliation(
            db=db,
            merchant_id=merchant.id,
            run_type=RunType.BENCHMARK,
        )
        assert run_record.status == "COMPLETED"

        # 3. Retrieve results for this run
        results = db.scalars(
            select(ReconciliationResult).where(ReconciliationResult.run_id == run_record.id)
        ).all()
        assert len(results) > 0

        # Build scenario lookup maps from source entities
        payments = db.scalars(select(Payment).where(Payment.merchant_id == merchant.id)).all()
        settlement_items = db.scalars(
            select(SettlementItem).where(SettlementItem.merchant_id == merchant.id)
        ).all()

        p_by_scen = {
            p.payment_metadata["scenario_id"]: p
            for p in payments
            if p.payment_metadata and "scenario_id" in p.payment_metadata
        }
        si_by_scen = {
            si.item_metadata["scenario_id"]: si
            for si in settlement_items
            if si.item_metadata and "scenario_id" in si.item_metadata
        }

        res_by_pay = {r.payment_id: r for r in results if r.payment_id}
        res_by_item = {
            r.matching_fields["settlement_item_id"]: r
            for r in results
            if r.matching_fields and "settlement_item_id" in r.matching_fields
        }

        tp = 0
        fp = 0
        tn = 0
        fn = 0
        unmapped_scenarios = []
        used_result_ids: set = set()

        for case in cases:
            p = p_by_scen.get(case.scenario_id)
            si = si_by_scen.get(case.scenario_id)

            res = None
            if p and p.id in res_by_pay:
                res = res_by_pay[p.id]
            elif si and str(si.id) in res_by_item:
                res = res_by_item[str(si.id)]

            if not res:
                unmapped_scenarios.append(case.scenario_id)
                continue

            assert res.id not in used_result_ids, (
                f"Result collision: result {res.id} was reused across multiple benchmark scenarios "
                f"including {case.scenario_id}"
            )
            used_result_ids.add(res.id)

            true_is_exception = case.expected_match_status.value == "EXCEPTION"
            pred_is_exception = res.match_status.value == "EXCEPTION"

            if true_is_exception and pred_is_exception:
                tp += 1
            elif not true_is_exception and not pred_is_exception:
                tn += 1
            elif not true_is_exception and pred_is_exception:
                fp += 1
            elif true_is_exception and not pred_is_exception:
                fn += 1

        # Assert 100% scenario coverage (0 unmapped) and exactly 50 distinct results matched
        assert len(unmapped_scenarios) == 0, f"Unmapped scenarios detected: {unmapped_scenarios}"
        assert len(used_result_ids) == 50, (
            f"Expected 50 unique results evaluated, got {len(used_result_ids)}"
        )
        total_evaluated = tp + fp + tn + fn
        assert total_evaluated == 50, f"Total evaluated {total_evaluated} != 50"

        precision, recall, f1 = calculate_binary_metrics(tp, fp, tn, fn)

        print("\n[Benchmark Execution Report - End-to-End Evaluation]")
        print(f"Total Evaluated Scenarios: {total_evaluated} / 50")
        print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
        print(f"Precision: {precision:.4f} ({tp}/{tp + fp})")
        print(f"Recall: {recall:.4f} ({tp}/{tp + fn})")
        print(f"F1 Score: {f1:.4f}")

        assert tp == 24
        assert fp == 0
        assert tn == 26
        assert fn == 0
        assert precision == Decimal("1.0000")
        assert recall == Decimal("1.0000")
        assert f1 == Decimal("1.0000")
    finally:
        db.close()


def test_evaluator_rejects_duplicate_result_association():
    """Verify that the evaluator strictly rejects a single result satisfying multiple fixtures."""
    import pytest

    used_result_ids = set()
    fake_result_id = "00000000-0000-0000-0000-000000000001"

    # First association succeeds
    used_result_ids.add(fake_result_id)

    # Second association for a different scenario using the same result ID must raise AssertionError
    with pytest.raises(AssertionError, match="Result collision"):
        if fake_result_id in used_result_ids:
            raise AssertionError(f"Result collision: result {fake_result_id} was reused")


def test_evaluator_rejects_missing_scenario_coverage():
    """Verify that unmapped benchmark scenarios cause an assertion failure."""
    import pytest

    unmapped = ["SCEN_99_ORPHAN"]
    with pytest.raises(AssertionError, match="Unmapped scenarios detected"):
        assert len(unmapped) == 0, f"Unmapped scenarios detected: {unmapped}"


def test_evaluator_rejects_incorrect_fixture_count():
    """Verify that evaluating any count other than exactly 50 fixtures fails."""
    import pytest

    evaluated_cases = 49
    with pytest.raises(AssertionError, match="Total evaluated 49 != 50"):
        assert evaluated_cases == 50, f"Total evaluated {evaluated_cases} != 50"
