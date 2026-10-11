import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.adjustment import Adjustment
from app.models.audit_event import AuditEvent
from app.models.enums import (
    EvidenceCategory,
    EvidenceStrength,
    ExceptionType,
)
from app.models.exception import ExceptionRecord
from app.models.fee import Fee
from app.models.payment import Payment
from app.models.reconciliation_result import ReconciliationResult
from app.models.refund import Refund
from app.models.settlement import Settlement
from app.models.settlement_item import SettlementItem
from app.modules.evidence.schemas import (
    EvidenceItem,
    ExceptionEvidenceResponse,
    FinancialEvidenceSummary,
    ReconciliationContext,
    RelatedRecordsSummary,
)


@dataclass
class CollectedRawEvidence:
    exception: ExceptionRecord
    reconciliation_result: ReconciliationResult
    payment: Payment | None = None
    settlement_item: SettlementItem | None = None
    settlement: Settlement | None = None
    refunds: list[Refund] = field(default_factory=list)
    fees: list[Fee] = field(default_factory=list)
    adjustments: list[Adjustment] = field(default_factory=list)
    audit_events: list[AuditEvent] = field(default_factory=list)
    conflicting_payments: list[Payment] = field(default_factory=list)
    conflicting_items: list[SettlementItem] = field(default_factory=list)


class EvidenceCollector:
    """
    Safely retrieves relevant financial records scoped strictly to the merchant tenant.
    Never modifies records. Enforces tenant boundaries on every query.
    """

    def __init__(self, db: Session, merchant_id: uuid.UUID):
        self.db = db
        self.merchant_id = merchant_id

    def collect(self, exception_id: uuid.UUID) -> CollectedRawEvidence | None:
        # 1. Retrieve exception record for tenant
        exc = self.db.scalar(
            select(ExceptionRecord).where(
                ExceptionRecord.id == exception_id,
                ExceptionRecord.merchant_id == self.merchant_id,
            )
        )
        if not exc:
            return None

        # 2. Retrieve authoritative reconciliation result
        res = self.db.scalar(
            select(ReconciliationResult).where(
                ReconciliationResult.id == exc.reconciliation_result_id,
                ReconciliationResult.merchant_id == self.merchant_id,
            )
        )
        if not res:
            return None

        # 3. Retrieve payment if payment_id is known
        payment: Payment | None = None
        if res.payment_id:
            payment = self.db.scalar(
                select(Payment).where(
                    Payment.id == res.payment_id,
                    Payment.merchant_id == self.merchant_id,
                )
            )

        # 4. Retrieve settlement item if settlement_item_id or settlement_id is available
        settlement_item: SettlementItem | None = None
        settlement_item_id_str = (
            res.matching_fields.get("settlement_item_id")
            if res.matching_fields and isinstance(res.matching_fields, dict)
            else None
        )

        if settlement_item_id_str:
            try:
                si_uuid = uuid.UUID(settlement_item_id_str)
                settlement_item = self.db.scalar(
                    select(SettlementItem).where(
                        SettlementItem.id == si_uuid,
                        SettlementItem.merchant_id == self.merchant_id,
                    )
                )
            except (ValueError, TypeError):
                settlement_item = None

        # Fallback settlement item lookup via settlement_id and payment_id
        if not settlement_item and res.settlement_id:
            if payment:
                settlement_item = self.db.scalar(
                    select(SettlementItem).where(
                        SettlementItem.settlement_id == res.settlement_id,
                        SettlementItem.merchant_id == self.merchant_id,
                        SettlementItem.payment_id == payment.id,
                    )
                )
            if not settlement_item:
                settlement_item = self.db.scalar(
                    select(SettlementItem).where(
                        SettlementItem.settlement_id == res.settlement_id,
                        SettlementItem.merchant_id == self.merchant_id,
                    )
                )

        # If payment is missing on the result but settlement_item has payment_id, correlate payment
        if not payment and settlement_item and settlement_item.payment_id:
            payment = self.db.scalar(
                select(Payment).where(
                    Payment.id == settlement_item.payment_id,
                    Payment.merchant_id == self.merchant_id,
                )
            )

        # 5. Retrieve parent settlement batch if settlement_id or item is available
        settlement: Settlement | None = None
        settlement_id = res.settlement_id or (
            settlement_item.settlement_id if settlement_item else None
        )
        if settlement_id:
            settlement = self.db.scalar(
                select(Settlement).where(
                    Settlement.id == settlement_id,
                    Settlement.merchant_id == self.merchant_id,
                )
            )

        # 6. Retrieve related refunds, fees, and adjustments for payment
        refunds: list[Refund] = []
        fees: list[Fee] = []
        adjustments: list[Adjustment] = []

        if payment:
            refunds = list(
                self.db.scalars(
                    select(Refund)
                    .where(
                        Refund.payment_id == payment.id,
                        Refund.merchant_id == self.merchant_id,
                    )
                    .order_by(Refund.created_at.asc())
                ).all()
            )

            fees = list(
                self.db.scalars(
                    select(Fee)
                    .where(
                        Fee.payment_id == payment.id,
                        Fee.merchant_id == self.merchant_id,
                    )
                    .order_by(Fee.created_at.asc())
                ).all()
            )

            adjustments = list(
                self.db.scalars(
                    select(Adjustment)
                    .where(
                        Adjustment.payment_id == payment.id,
                        Adjustment.merchant_id == self.merchant_id,
                    )
                    .order_by(Adjustment.created_at.asc())
                ).all()
            )

        # If settlement batch is linked, also check settlement-level adjustments
        if settlement:
            batch_adjs = list(
                self.db.scalars(
                    select(Adjustment)
                    .where(
                        Adjustment.settlement_id == settlement.id,
                        Adjustment.merchant_id == self.merchant_id,
                    )
                    .order_by(Adjustment.created_at.asc())
                ).all()
            )
            # Avoid duplicating adjustments already captured
            existing_adj_ids = {a.id for a in adjustments}
            for ba in batch_adjs:
                if ba.id not in existing_adj_ids:
                    adjustments.append(ba)

        # 7. Retrieve related audit events specifically for this exception
        audit_events = list(
            self.db.scalars(
                select(AuditEvent)
                .where(
                    AuditEvent.merchant_id == self.merchant_id,
                    AuditEvent.exception_id == exc.id,
                )
                .order_by(AuditEvent.created_at.asc())
            ).all()
        )

        # 8. Check for conflicting or duplicate records
        conflicting_payments: list[Payment] = []
        if payment and payment.external_id:
            all_with_ext_id = list(
                self.db.scalars(
                    select(Payment).where(
                        Payment.merchant_id == self.merchant_id,
                        Payment.external_id == payment.external_id,
                    )
                ).all()
            )
            conflicting_payments = [p for p in all_with_ext_id if p.id != payment.id]

        conflicting_items: list[SettlementItem] = []
        if settlement_item and settlement_item.external_payment_id:
            all_with_item_ext = list(
                self.db.scalars(
                    select(SettlementItem).where(
                        SettlementItem.merchant_id == self.merchant_id,
                        SettlementItem.external_payment_id == settlement_item.external_payment_id,
                    )
                ).all()
            )
            conflicting_items = [i for i in all_with_item_ext if i.id != settlement_item.id]

        return CollectedRawEvidence(
            exception=exc,
            reconciliation_result=res,
            payment=payment,
            settlement_item=settlement_item,
            settlement=settlement,
            refunds=refunds,
            fees=fees,
            adjustments=adjustments,
            audit_events=audit_events,
            conflicting_payments=conflicting_payments,
            conflicting_items=conflicting_items,
        )


class EvidenceCorrelator:
    """
    Correlates collected records into deterministic EvidenceItems, assesses evidence strength,
    and produces a concise financial evidence summary.
    """

    @staticmethod
    def correlate(raw: CollectedRawEvidence) -> ExceptionEvidenceResponse:
        res = raw.reconciliation_result
        exc = raw.exception

        evidence_items: list[EvidenceItem] = []
        supported_findings: list[str] = []
        missing_info: list[str] = []
        conflicts: list[str] = []

        # 1. Reconciliation Result Evidence Item
        recon_evidence = EvidenceItem(
            evidence_id=f"ev_recon_{res.id.hex[:8]}",
            category=EvidenceCategory.RECONCILIATION,
            source_type="reconciliation_result",
            source_record_id=str(res.id),
            strength=EvidenceStrength.CONFIRMED,
            attributes={
                "match_type": res.match_type.value,
                "match_status": res.match_status.value,
                "expected_amount": str(res.expected_amount),
                "actual_amount": str(res.actual_amount),
                "variance": str(res.difference),
                "tolerance": str(res.tolerance),
                "confidence": str(res.confidence),
                "explanation": res.explanation or "",
            },
            limitations=[],
            timestamp=res.created_at,
        )
        evidence_items.append(recon_evidence)

        # 2. Payment Evidence
        if raw.payment:
            p = raw.payment
            p_limitations = []
            if p.captured_at is None and p.status.value == "CAPTURED":
                p_limitations.append("Captured timestamp is not recorded on payment entity.")

            payment_strength = (
                EvidenceStrength.CONFLICTING
                if raw.conflicting_payments
                else EvidenceStrength.CONFIRMED
            )

            payment_evidence = EvidenceItem(
                evidence_id=f"ev_pay_{p.id.hex[:8]}",
                category=EvidenceCategory.PAYMENT,
                source_type="payment",
                source_record_id=str(p.id),
                strength=payment_strength,
                attributes={
                    "external_id": p.external_id,
                    "external_order_id": p.external_order_id,
                    "amount": str(p.amount),
                    "currency": p.currency,
                    "status": p.status.value,
                    "payment_method": p.payment_method,
                    "captured_at": p.captured_at.isoformat() if p.captured_at else None,
                    "source_created_at": p.source_created_at.isoformat(),
                },
                limitations=p_limitations,
                timestamp=p.source_created_at,
            )
            evidence_items.append(payment_evidence)
            supported_findings.append(
                f"Internal payment record found: ID {p.external_id} for {p.amount} {p.currency} (status: {p.status.value})."
            )
        else:
            missing_info.append(
                "Internal payment ledger record is missing or unlinked for this exception."
            )

        # Conflicting payments
        if raw.conflicting_payments:
            conflicts.append(
                f"Detected {len(raw.conflicting_payments)} duplicate payment record(s) sharing external ID '{raw.payment.external_id if raw.payment else 'unknown'}'."
            )
            for cp in raw.conflicting_payments:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"ev_pay_conflict_{cp.id.hex[:8]}",
                        category=EvidenceCategory.RELATED_RECORD,
                        source_type="payment_duplicate",
                        source_record_id=str(cp.id),
                        strength=EvidenceStrength.CONFLICTING,
                        attributes={
                            "external_id": cp.external_id,
                            "amount": str(cp.amount),
                            "status": cp.status.value,
                            "created_at": cp.source_created_at.isoformat(),
                        },
                        limitations=["Conflicting record with identical external reference."],
                        timestamp=cp.source_created_at,
                    )
                )

        # 3. Settlement Item Evidence
        if raw.settlement_item:
            si = raw.settlement_item
            si_limitations = []
            if not si.payment_id:
                si_limitations.append("Settlement line item has null internal payment_id.")

            si_strength = (
                EvidenceStrength.CONFLICTING
                if raw.conflicting_items
                else EvidenceStrength.CONFIRMED
            )

            settlement_item_evidence = EvidenceItem(
                evidence_id=f"ev_item_{si.id.hex[:8]}",
                category=EvidenceCategory.SETTLEMENT,
                source_type="settlement_item",
                source_record_id=str(si.id),
                strength=si_strength,
                attributes={
                    "settlement_id": str(si.settlement_id),
                    "external_payment_id": si.external_payment_id,
                    "gross_amount": str(si.gross_amount),
                    "fee_amount": str(si.fee_amount),
                    "refund_amount": str(si.refund_amount),
                    "adjustment_amount": str(si.adjustment_amount),
                    "net_amount": str(si.net_amount),
                    "currency": si.currency,
                    "source_created_at": si.source_created_at.isoformat(),
                },
                limitations=si_limitations,
                timestamp=si.source_created_at,
            )
            evidence_items.append(settlement_item_evidence)
            supported_findings.append(
                f"Bank settlement line item found: net credited amount {si.net_amount} {si.currency} (gross: {si.gross_amount})."
            )
        else:
            missing_info.append(
                "Settlement line item is missing in gateway/bank settlement reports."
            )

        # Conflicting settlement items
        if raw.conflicting_items:
            conflicts.append(
                f"Detected {len(raw.conflicting_items)} duplicate settlement line(s) referencing external payment '{raw.settlement_item.external_payment_id if raw.settlement_item else 'unknown'}'."
            )
            for csi in raw.conflicting_items:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"ev_item_conflict_{csi.id.hex[:8]}",
                        category=EvidenceCategory.RELATED_RECORD,
                        source_type="settlement_item_duplicate",
                        source_record_id=str(csi.id),
                        strength=EvidenceStrength.CONFLICTING,
                        attributes={
                            "settlement_id": str(csi.settlement_id),
                            "external_payment_id": csi.external_payment_id,
                            "net_amount": str(csi.net_amount),
                            "created_at": csi.source_created_at.isoformat(),
                        },
                        limitations=["Duplicate settlement report row."],
                        timestamp=csi.source_created_at,
                    )
                )

        # 4. Settlement Batch Evidence
        if raw.settlement:
            st = raw.settlement
            evidence_items.append(
                EvidenceItem(
                    evidence_id=f"ev_batch_{st.id.hex[:8]}",
                    category=EvidenceCategory.SETTLEMENT,
                    source_type="settlement",
                    source_record_id=str(st.id),
                    strength=EvidenceStrength.CONFIRMED,
                    attributes={
                        "external_id": st.external_id,
                        "settlement_date": st.settlement_date.isoformat(),
                        "total_batch_amount": str(st.amount),
                        "currency": st.currency,
                        "status": st.status.value,
                        "settled_at": st.settled_at.isoformat() if st.settled_at else None,
                    },
                    limitations=[],
                    timestamp=st.settled_at or st.source_created_at,
                )
            )

        # 5. Refund Evidence
        if raw.refunds:
            total_refunds = sum(
                (r.amount for r in raw.refunds if r.status.value == "PROCESSED"), Decimal("0.00")
            )
            supported_findings.append(
                f"Processed {len(raw.refunds)} refund record(s) totaling {total_refunds} {raw.payment.currency if raw.payment else 'INR'}."
            )
            for r in raw.refunds:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"ev_rfnd_{r.id.hex[:8]}",
                        category=EvidenceCategory.REFUND,
                        source_type="refund",
                        source_record_id=str(r.id),
                        strength=EvidenceStrength.CONFIRMED,
                        attributes={
                            "external_id": r.external_id,
                            "amount": str(r.amount),
                            "currency": r.currency,
                            "status": r.status.value,
                            "processed_at": r.processed_at.isoformat(),
                        },
                        limitations=[],
                        timestamp=r.processed_at,
                    )
                )

        # 6. Fee Evidence
        if raw.fees:
            total_fees = sum((f.amount + f.tax_amount for f in raw.fees), Decimal("0.00"))
            supported_findings.append(
                f"Assessed {len(raw.fees)} fee component(s) totaling {total_fees} {raw.payment.currency if raw.payment else 'INR'}."
            )
            for f in raw.fees:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"ev_fee_{f.id.hex[:8]}",
                        category=EvidenceCategory.FEE,
                        source_type="fee",
                        source_record_id=str(f.id),
                        strength=EvidenceStrength.CONFIRMED,
                        attributes={
                            "fee_type": f.fee_type.value,
                            "amount": str(f.amount),
                            "tax_amount": str(f.tax_amount),
                            "currency": f.currency,
                            "status": f.status.value,
                        },
                        limitations=[],
                        timestamp=f.created_at,
                    )
                )

        # 7. Adjustment Evidence
        if raw.adjustments:
            total_adjs = sum((a.amount for a in raw.adjustments), Decimal("0.00"))
            supported_findings.append(
                f"Found {len(raw.adjustments)} adjustment record(s) summing to signed {total_adjs} {raw.payment.currency if raw.payment else 'INR'}."
            )
            for a in raw.adjustments:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"ev_adj_{a.id.hex[:8]}",
                        category=EvidenceCategory.ADJUSTMENT,
                        source_type="adjustment",
                        source_record_id=str(a.id),
                        strength=EvidenceStrength.CONFIRMED,
                        attributes={
                            "adjustment_type": a.adjustment_type.value,
                            "amount": str(a.amount),
                            "currency": a.currency,
                            "status": a.status.value,
                            "reason": a.reason,
                        },
                        limitations=[],
                        timestamp=a.created_at,
                    )
                )

        # 8. Audit Trail Evidence
        for ae in raw.audit_events:
            evidence_items.append(
                EvidenceItem(
                    evidence_id=f"ev_audit_{ae.id.hex[:8]}",
                    category=EvidenceCategory.AUDIT,
                    source_type="audit_event",
                    source_record_id=str(ae.id),
                    strength=EvidenceStrength.CONFIRMED,
                    attributes={
                        "event_type": ae.event_type,
                        "actor_type": ae.actor_type.value,
                        "actor_id": ae.actor_id,
                        "previous_state": ae.previous_state,
                        "new_state": ae.new_state,
                    },
                    limitations=[],
                    timestamp=ae.created_at,
                )
            )

        # 9. Determine Overall Evidence Strength & Cause Established
        if conflicts:
            overall_strength = EvidenceStrength.CONFLICTING
            cause_established = True  # Established as collision/duplicate conflict
        elif missing_info:
            overall_strength = EvidenceStrength.INCOMPLETE
            # If the exception is specifically MISSING_PAYMENT or MISSING_SETTLEMENT,
            # the absence of the record is the direct cause
            if exc.exception_type in (
                ExceptionType.MISSING_PAYMENT,
                ExceptionType.MISSING_SETTLEMENT,
                ExceptionType.DELAYED_SETTLEMENT,
            ):
                cause_established = True
            else:
                cause_established = False
        elif len(evidence_items) >= 2:
            overall_strength = (
                EvidenceStrength.CORROBORATED
                if len(supported_findings) >= 2
                else EvidenceStrength.CONFIRMED
            )
            cause_established = True
        else:
            overall_strength = EvidenceStrength.INCOMPLETE
            cause_established = False

        observed_discrepancy = (
            exc.description
            or f"Recorded difference of {res.difference} {exc.currency} between expected ({res.expected_amount}) and actual ({res.actual_amount})."
        )

        summary = FinancialEvidenceSummary(
            observed_discrepancy=observed_discrepancy,
            expected_amount=res.expected_amount,
            actual_amount=res.actual_amount,
            variance=res.difference,
            currency=exc.currency,
            overall_strength=overall_strength,
            cause_established=cause_established,
            supported_findings=supported_findings,
            missing_information=missing_info,
            conflicts=conflicts,
        )

        reconciliation_ctx = ReconciliationContext(
            result_id=res.id,
            run_id=res.run_id,
            match_status=res.match_status,
            exception_type=exc.exception_type,
            severity=exc.severity,
            exception_status=exc.status,
            expected_amount=res.expected_amount,
            actual_amount=res.actual_amount,
            variance=res.difference,
            currency=exc.currency,
            tolerance=res.tolerance,
            explanation=res.explanation,
            created_at=res.created_at,
        )

        related_records = RelatedRecordsSummary(
            payment_ids=[str(raw.payment.id)] if raw.payment else [],
            settlement_item_ids=[str(raw.settlement_item.id)] if raw.settlement_item else [],
            settlement_ids=[str(raw.settlement.id)] if raw.settlement else [],
            refund_ids=[str(r.id) for r in raw.refunds],
            fee_ids=[str(f.id) for f in raw.fees],
            adjustment_ids=[str(a.id) for a in raw.adjustments],
            audit_event_ids=[str(ae.id) for ae in raw.audit_events],
        )

        return ExceptionEvidenceResponse(
            exception_id=exc.id,
            merchant_id=exc.merchant_id,
            reconciliation=reconciliation_ctx,
            evidence_items=evidence_items,
            related_records=related_records,
            summary=summary,
        )
