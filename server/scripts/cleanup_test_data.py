from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Delete child records first in proper dependency order
    db.execute(
        text(
            "DELETE FROM fees WHERE external_id LIKE 'fee_ev_test_%' OR payment_id IN (SELECT id FROM payments WHERE external_id LIKE 'pay_ev_test_%' OR external_id LIKE 'pay_collision_%')"
        )
    )
    db.execute(
        text(
            "DELETE FROM refunds WHERE external_id LIKE 'rfnd_ev_test_%' OR payment_id IN (SELECT id FROM payments WHERE external_id LIKE 'pay_ev_test_%' OR external_id LIKE 'pay_collision_%')"
        )
    )
    db.execute(
        text(
            "DELETE FROM adjustments WHERE external_id LIKE 'adj_ev_test_%' OR payment_id IN (SELECT id FROM payments WHERE external_id LIKE 'pay_ev_test_%' OR external_id LIKE 'pay_collision_%')"
        )
    )
    db.execute(
        text(
            "DELETE FROM exceptions WHERE description LIKE 'Recorded settlement amount differs by 32.00 INR' OR description LIKE 'Settlement item without matching payment in internal ledger' OR description LIKE 'Duplicate settlement line item detected in bank report'"
        )
    )
    db.execute(
        text(
            "DELETE FROM reconciliation_results WHERE explanation LIKE 'Amount variance exceeding tolerance' OR explanation LIKE 'Unmatched settlement line item without internal payment' OR explanation LIKE 'Duplicate settlement line item detected'"
        )
    )
    db.execute(
        text(
            "DELETE FROM reconciliation_runs WHERE total_records IN (1, 2) AND matched_records IN (0, 1) AND exception_records IN (1, 2) AND run_type = 'MANUAL_TRIGGER'"
        )
    )
    db.execute(
        text(
            "DELETE FROM settlement_items WHERE external_payment_id LIKE 'pay_ev_test_%' OR external_payment_id LIKE 'pay_unknown_%' OR external_payment_id LIKE 'pay_collision_%' OR external_payment_id = 'pay_unknown_ref'"
        )
    )
    db.execute(
        text(
            "DELETE FROM settlements WHERE external_id LIKE 'setl_ev_test_%' OR external_id LIKE 'setl_orphan_%' OR external_id LIKE 'setl_dup_batch_%'"
        )
    )
    db.execute(
        text(
            "DELETE FROM payments WHERE external_id LIKE 'pay_ev_test_%' OR external_id LIKE 'pay_collision_%'"
        )
    )
    db.execute(text("DELETE FROM users WHERE email LIKE 'operator_b_%'"))
    db.execute(text("DELETE FROM merchants WHERE name LIKE 'Isolated Merchant %'"))
    db.commit()
    print("Payments count:", db.execute(text("SELECT count(*) FROM payments")).scalar())
    print("Settlements count:", db.execute(text("SELECT count(*) FROM settlements")).scalar())
    print(
        "Settlement items count:",
        db.execute(text("SELECT count(*) FROM settlement_items")).scalar(),
    )
finally:
    db.close()
