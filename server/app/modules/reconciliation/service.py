import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.adjustment import Adjustment
from app.models.audit_event import AuditEvent
from app.models.enums import (
    ActorType,
    RunStatus,
    RunType,
)
from app.models.exception import ExceptionRecord
from app.models.fee import Fee
from app.models.payment import Payment
from app.models.reconciliation_result import ReconciliationResult
from app.models.reconciliation_run import ReconciliationRun
from app.models.refund import Refund
from app.models.settlement_item import SettlementItem
from app.modules.reconciliation.constants import (
    DEFAULT_AMOUNT_TOLERANCE,
    DEFAULT_SETTLEMENT_DELAY_DAYS,
    MAX_CANDIDATE_DATE_WINDOW_DAYS,
)
from app.modules.reconciliation.engine import execute_reconciliation_plan
from app.modules.reconciliation.normalization import (
    NormalizedAdjustment,
    NormalizedFee,
    NormalizedPayment,
    NormalizedRefund,
    NormalizedSettlementItem,
)


def run_reconciliation(
    db: Session,
    merchant_id: uuid.UUID,
    actor_id: str | None = None,
    run_type: RunType = RunType.MANUAL_TRIGGER,
    tolerance: Decimal | None = None,
    settlement_delay_days: int | None = None,
) -> ReconciliationRun:
    """
    Executes a complete, repeatable reconciliation run within managed database transaction boundaries.
    Reads current source records for the given merchant, calculates deterministic matches and exceptions,
    persists new run records, and writes full audit trail.
    """
    settings = get_settings()
    effective_tolerance = (
        tolerance
        if tolerance is not None
        else Decimal(str(settings.AMOUNT_TOLERANCE or DEFAULT_AMOUNT_TOLERANCE))
    )
    effective_delay_days = (
        settlement_delay_days
        if settlement_delay_days is not None
        else DEFAULT_SETTLEMENT_DELAY_DAYS
    )

    start_time = time.perf_counter()
    now_utc = datetime.now(UTC)

    config_snapshot: dict[str, Any] = {
        "amount_tolerance": str(effective_tolerance),
        "settlement_delay_days": effective_delay_days,
        "date_window_days": MAX_CANDIDATE_DATE_WINDOW_DAYS,
        "environment": settings.APP_ENV,
        "run_type": run_type.value,
    }

    # 1. Create ReconciliationRun header in STARTED status
    run_record = ReconciliationRun(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        run_type=run_type,
        status=RunStatus.STARTED,
        started_at=now_utc,
        configuration_snapshot=config_snapshot,
    )
    db.add(run_record)
    db.flush()

    # Audit event: RECONCILIATION_RUN_STARTED
    audit_start = AuditEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        reconciliation_run_id=run_record.id,
        actor_type=ActorType.HUMAN_CONTROLLER if actor_id else ActorType.SYSTEM,
        actor_id=actor_id,
        event_type="RECONCILIATION_RUN_STARTED",
        new_state=RunStatus.STARTED.value,
        event_metadata=config_snapshot,
    )
    db.add(audit_start)

    try:
        # 2. Select eligible source records for this merchant
        payments_orm = db.scalars(select(Payment).where(Payment.merchant_id == merchant_id)).all()
        settlement_items_orm = db.scalars(
            select(SettlementItem).where(SettlementItem.merchant_id == merchant_id)
        ).all()
        refunds_orm = db.scalars(select(Refund).where(Refund.merchant_id == merchant_id)).all()
        fees_orm = db.scalars(select(Fee).where(Fee.merchant_id == merchant_id)).all()
        adjustments_orm = db.scalars(
            select(Adjustment).where(Adjustment.merchant_id == merchant_id)
        ).all()

        # 3. Normalize into typed internal models
        norm_payments = [NormalizedPayment.model_validate(p) for p in payments_orm]
        norm_items = [NormalizedSettlementItem.model_validate(si) for si in settlement_items_orm]
        norm_refunds = [NormalizedRefund.model_validate(r) for r in refunds_orm]
        norm_fees = [NormalizedFee.model_validate(f) for f in fees_orm]
        norm_adjustments = [NormalizedAdjustment.model_validate(a) for a in adjustments_orm]

        # 4. Execute deterministic calculation & matching plan
        plan = execute_reconciliation_plan(
            merchant_id=merchant_id,
            payments=norm_payments,
            settlement_items=norm_items,
            refunds=norm_refunds,
            fees=norm_fees,
            adjustments=norm_adjustments,
            tolerance=effective_tolerance,
            settlement_delay_days=effective_delay_days,
            current_time=now_utc,
        )

        # 5. Persist reconciliation results and exceptions
        for item in plan.results:
            result_record = ReconciliationResult(
                id=uuid.uuid4(),
                run_id=run_record.id,
                merchant_id=merchant_id,
                payment_id=item.payment_id,
                settlement_id=item.settlement_id,
                match_type=item.match_type,
                match_status=item.match_status,
                expected_amount=item.expected_amount,
                actual_amount=item.actual_amount,
                difference=item.difference,
                tolerance=item.tolerance,
                confidence=item.confidence,
                explanation=item.explanation,
                matching_fields=item.matching_fields,
            )
            db.add(result_record)
            db.flush()

            # If result is an EXCEPTION, persist ExceptionRecord
            if item.classification:
                cls_info = item.classification
                exc_record = ExceptionRecord(
                    id=uuid.uuid4(),
                    merchant_id=merchant_id,
                    reconciliation_result_id=result_record.id,
                    exception_type=cls_info.exception_type,  # type: ignore[arg-type]
                    severity=cls_info.severity,  # type: ignore[arg-type]
                    status=cls_info.exception_status,  # type: ignore[arg-type]
                    financial_impact=cls_info.financial_impact,
                    currency="INR",
                    description=cls_info.description,
                )
                db.add(exc_record)

        # 6. Update run record counters and mark COMPLETED
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        run_record.status = RunStatus.COMPLETED
        run_record.completed_at = datetime.now(UTC)
        run_record.total_records = plan.total_records
        run_record.matched_records = plan.matched_records
        run_record.unmatched_records = plan.unmatched_records
        run_record.exception_records = plan.exception_records
        run_record.auto_classified_records = plan.auto_classified_records
        run_record.review_required_records = plan.review_required_records
        run_record.processing_duration_ms = duration_ms

        # Audit event: RECONCILIATION_RUN_COMPLETED
        audit_completed = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            reconciliation_run_id=run_record.id,
            actor_type=ActorType.HUMAN_CONTROLLER if actor_id else ActorType.SYSTEM,
            actor_id=actor_id,
            event_type="RECONCILIATION_RUN_COMPLETED",
            previous_state=RunStatus.STARTED.value,
            new_state=RunStatus.COMPLETED.value,
            event_metadata={
                "total_records": plan.total_records,
                "matched_records": plan.matched_records,
                "exception_records": plan.exception_records,
                "duration_ms": duration_ms,
            },
        )
        db.add(audit_completed)

        db.commit()
        db.refresh(run_record)
        return run_record

    except Exception as exc:
        db.rollback()
        # Mark run failed in new transaction
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        try:
            failed_run = ReconciliationRun(
                id=run_record.id,
                merchant_id=merchant_id,
                run_type=run_type,
                status=RunStatus.FAILED,
                started_at=now_utc,
                completed_at=datetime.now(UTC),
                processing_duration_ms=duration_ms,
                error_summary=str(exc)[:500],
                configuration_snapshot=config_snapshot,
            )
            db.add(failed_run)
            db.commit()
        except Exception:
            db.rollback()
        raise exc
