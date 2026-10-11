import logging
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ExceptionType
from app.models.exception import ExceptionRecord
from app.modules.demo.schemas import DemoScenarioItem, DemoScenariosResponse
from app.modules.evidence.service import EvidenceCollector, EvidenceCorrelator

logger = logging.getLogger(__name__)

SCENARIO_DEFINITIONS = [
    {
        "scenario_key": "AMOUNT_MISMATCH",
        "title": "Discrepancy: Amount Mismatch",
        "description": "Expected net settlement does not match actual amount credited by payment processor.",
        "exception_type": ExceptionType.AMOUNT_MISMATCH,
        "tags": ["Variance", "Ledger Mismatch", "Settlement Difference"],
    },
    {
        "scenario_key": "MISSING_PAYMENT",
        "title": "Discrepancy: Missing Payment Record",
        "description": "Processor settlement line references an external payment order missing from internal ledger.",
        "exception_type": ExceptionType.MISSING_PAYMENT,
        "tags": ["Orphan Settlement", "Missing Ingestion", "Internal Ledger"],
    },
    {
        "scenario_key": "MISSING_SETTLEMENT",
        "title": "Discrepancy: Missing Settlement Record",
        "description": "Payment was captured internally but no bank or gateway settlement batch has credited it.",
        "exception_type": ExceptionType.MISSING_SETTLEMENT,
        "tags": ["Unsettled Payment", "Delayed Payout", "Gateway Drop"],
    },
    {
        "scenario_key": "REFUND_MISMATCH",
        "title": "Discrepancy: Refund Variance",
        "description": "Customer refund deduction differs between internal ledger calculations and processor statement.",
        "exception_type": ExceptionType.REFUND_MISMATCH,
        "tags": ["Refund", "Reversal", "Partial Refund"],
    },
    {
        "scenario_key": "FEE_MISMATCH",
        "title": "Discrepancy: Fee / MDR Variance",
        "description": "Assessed gateway MDR fees or GST exceed agreed contractual fee schedule.",
        "exception_type": ExceptionType.FEE_MISMATCH,
        "tags": ["MDR Fees", "Contract Variance", "Gateway Commission"],
    },
    {
        "scenario_key": "DELAYED_SETTLEMENT",
        "title": "Discrepancy: Delayed Settlement / SLA Breach",
        "description": "Payment settlement exceeded processor SLA cycle (T+2/T+3 days).",
        "exception_type": ExceptionType.DELAYED_SETTLEMENT,
        "tags": ["SLA Breach", "Aging", "Cycle Delay"],
    },
]


class DemoService:
    def __init__(self, db: Session, merchant_id: uuid.UUID):
        self.db = db
        self.merchant_id = merchant_id

    def get_scenarios(self) -> DemoScenariosResponse:
        """
        Derives real demo scenarios from actual accessible database records.
        Does NOT hardcode IDs or fabricate synthetic exceptions.
        Guarantees strict tenant isolation by querying only the authenticated merchant_id.
        """
        items: list[DemoScenarioItem] = []

        # 1. Evaluate standard exception-type scenarios
        for defn in SCENARIO_DEFINITIONS:
            exc = self.db.scalar(
                select(ExceptionRecord)
                .where(
                    ExceptionRecord.merchant_id == self.merchant_id,
                    ExceptionRecord.exception_type == defn["exception_type"],
                )
                .order_by(ExceptionRecord.created_at.desc())
                .limit(1)
            )

            if exc:
                items.append(
                    DemoScenarioItem(
                        scenario_key=defn["scenario_key"],
                        title=defn["title"],
                        description=defn["description"],
                        exception_type=defn["exception_type"].value,
                        available=True,
                        exception_id=exc.id,
                        financial_impact=f"{Decimal(exc.financial_impact):.2f}",
                        currency=exc.currency,
                        reference_id=str(exc.id)[:8].upper(),
                        tags=defn["tags"],
                    )
                )
            else:
                items.append(
                    DemoScenarioItem(
                        scenario_key=defn["scenario_key"],
                        title=defn["title"],
                        description=defn["description"],
                        exception_type=defn["exception_type"].value,
                        available=False,
                        tags=defn["tags"],
                    )
                )

        # 2. Evaluate Conflicting Evidence scenario
        # Query exceptions for this merchant to find one with correlated evidence conflicts
        conflict_scenario = self._find_conflicting_evidence_scenario()
        items.append(conflict_scenario)

        total_avail = sum(1 for item in items if item.available)

        return DemoScenariosResponse(
            merchant_id=self.merchant_id,
            is_demo_mode=True,
            scenarios=items,
            total_available=total_avail,
        )

    def _find_conflicting_evidence_scenario(self) -> DemoScenarioItem:
        """
        Finds a real exception for this merchant that exhibits contradictory evidence.
        """
        collector = EvidenceCollector(db=self.db, merchant_id=self.merchant_id)

        # Candidates: DUPLICATE_SETTLEMENT or DUPLICATE_PAYMENT usually have contradictory records
        candidates = self.db.scalars(
            select(ExceptionRecord)
            .where(
                ExceptionRecord.merchant_id == self.merchant_id,
                ExceptionRecord.exception_type.in_(
                    [
                        ExceptionType.DUPLICATE_SETTLEMENT,
                        ExceptionType.DUPLICATE_PAYMENT,
                        ExceptionType.AMOUNT_MISMATCH,
                    ]
                ),
            )
            .order_by(ExceptionRecord.created_at.desc())
            .limit(20)
        ).all()

        for exc in candidates:
            raw = collector.collect(exc.id)
            if raw:
                corr = EvidenceCorrelator.correlate(raw)
                if corr.summary.conflicts:
                    return DemoScenarioItem(
                        scenario_key="CONFLICTING_EVIDENCE",
                        title="Discrepancy: Conflicting Evidence Records",
                        description="Correlated dossier contains direct contradictory records (e.g. duplicate settlement references).",
                        exception_type=exc.exception_type.value,
                        available=True,
                        exception_id=exc.id,
                        financial_impact=f"{Decimal(exc.financial_impact):.2f}",
                        currency=exc.currency,
                        reference_id=str(exc.id)[:8].upper(),
                        tags=["Contradictory Evidence", "Duplicate Reference", "Audit Flag"],
                    )

        return DemoScenarioItem(
            scenario_key="CONFLICTING_EVIDENCE",
            title="Discrepancy: Conflicting Evidence Records",
            description="Correlated dossier contains direct contradictory records.",
            exception_type="CONFLICTING_EVIDENCE",
            available=False,
            tags=["Contradictory Evidence", "Audit Flag"],
        )
