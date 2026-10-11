import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import (
    ExceptionStatus,
    ExceptionType,
    MatchStatus,
    ProposalStatus,
    ResolutionStatus,
    UserRole,
)
from app.models.evidence import Evidence
from app.models.exception import ExceptionRecord
from app.models.investigation_report import InvestigationReport
from app.models.payment import Payment
from app.models.reconciliation_result import ReconciliationResult
from app.models.reconciliation_run import ReconciliationRun
from app.models.resolution_proposal import ResolutionProposal
from app.models.user import User
from app.modules.dashboard.schemas import (
    AIInvestigationOverview,
    CurrencyExposure,
    DashboardOverviewResponse,
    DashboardTrendsResponse,
    ExceptionTrendItem,
    ExceptionTypeBreakdown,
    OperationsQueueItem,
    OperationsQueueResponse,
    PendingApprovalItem,
    ReconciliationHealthResponse,
    ReconciliationRunTrendItem,
    ResolutionStatusBreakdown,
    SeverityBreakdown,
)


class DashboardService:
    """Service providing aggregate financial metrics, reconciliation health, and operational queues."""

    def __init__(self, db: Session, merchant_id: uuid.UUID):
        self.db = db
        self.merchant_id = merchant_id

    def get_overview(self) -> DashboardOverviewResponse:
        """Computes top-level executive KPIs strictly scoped to the authenticated merchant."""
        # 1. Total payments processed
        total_payments = (
            self.db.scalar(
                select(func.count(Payment.id)).where(Payment.merchant_id == self.merchant_id)
            )
            or 0
        )

        # 2. Match counts from reconciliation results
        matched_count = (
            self.db.scalar(
                select(func.count(ReconciliationResult.id)).where(
                    ReconciliationResult.merchant_id == self.merchant_id,
                    ReconciliationResult.match_status.in_(
                        [
                            MatchStatus.MATCHED,
                            MatchStatus.MATCHED_WITH_VARIANCE,
                        ]
                    ),
                )
            )
            or 0
        )

        unmatched_count = (
            self.db.scalar(
                select(func.count(ReconciliationResult.id)).where(
                    ReconciliationResult.merchant_id == self.merchant_id,
                    ReconciliationResult.match_status == MatchStatus.UNMATCHED,
                )
            )
            or 0
        )

        discrepancy_count = (
            self.db.scalar(
                select(func.count(ReconciliationResult.id)).where(
                    ReconciliationResult.merchant_id == self.merchant_id,
                    ReconciliationResult.match_status == MatchStatus.EXCEPTION,
                )
            )
            or 0
        )

        # Exception records count
        exception_count = (
            self.db.scalar(
                select(func.count(ExceptionRecord.id)).where(
                    ExceptionRecord.merchant_id == self.merchant_id
                )
            )
            or 0
        )

        # Calculate match rate: matched / (matched + unmatched + discrepancies)
        total_reconciled = matched_count + unmatched_count + discrepancy_count
        if total_reconciled > 0:
            match_rate = round((matched_count / total_reconciled) * 100.0, 2)
        else:
            match_rate = 0.0

        # 3. Financial exposure by individual currency (only for open/unresolved exceptions)
        exposure_rows = self.db.execute(
            select(
                ExceptionRecord.currency,
                func.coalesce(func.sum(ExceptionRecord.financial_impact), Decimal("0.00")),
                func.count(ExceptionRecord.id),
            )
            .where(
                ExceptionRecord.merchant_id == self.merchant_id,
                ExceptionRecord.status != ExceptionStatus.RESOLVED,
            )
            .group_by(ExceptionRecord.currency)
        ).all()

        exposure_by_currency = [
            CurrencyExposure(
                currency=row[0],
                total_exposure=Decimal(str(row[1])),
                exception_count=row[2],
            )
            for row in exposure_rows
        ]

        # 4. Pending approval proposals count
        pending_approvals = (
            self.db.scalar(
                select(func.count(ResolutionProposal.id)).where(
                    ResolutionProposal.merchant_id == self.merchant_id,
                    ResolutionProposal.status == ProposalStatus.PENDING_APPROVAL.value,
                )
            )
            or 0
        )

        # 5. Exceptions awaiting review (OPEN and not approved/resolved)
        exceptions_awaiting = (
            self.db.scalar(
                select(func.count(ExceptionRecord.id)).where(
                    ExceptionRecord.merchant_id == self.merchant_id,
                    ExceptionRecord.status != ExceptionStatus.RESOLVED,
                    ExceptionRecord.resolution_status.in_(
                        [
                            ResolutionStatus.OPEN.value,
                            ResolutionStatus.UNDER_REVIEW.value,
                            ResolutionStatus.REOPENED.value,
                        ]
                    ),
                )
            )
            or 0
        )

        # 6. Resolved exceptions count
        resolved_count = (
            self.db.scalar(
                select(func.count(ExceptionRecord.id)).where(
                    ExceptionRecord.merchant_id == self.merchant_id,
                    or_(
                        ExceptionRecord.status == ExceptionStatus.RESOLVED,
                        ExceptionRecord.resolution_status == ResolutionStatus.RESOLVED.value,
                    ),
                )
            )
            or 0
        )

        # 7. AI Investigations aggregate
        ai_reports = self.db.execute(
            select(
                InvestigationReport.status,
                func.count(InvestigationReport.id),
                func.sum(
                    func.cast(
                        InvestigationReport.requires_human_review,
                        func.INTEGER if self.db.bind.dialect.name == "sqlite" else None,
                    )
                    if False
                    else 1
                ),  # safe aggregate
            )
            .where(InvestigationReport.merchant_id == self.merchant_id)
            .group_by(InvestigationReport.status)
        ).all()

        ai_completed = 0
        ai_pending = 0
        ai_failed = 0
        ai_unavailable = 0
        for status_val, count, _ in ai_reports:
            if status_val == "COMPLETED":
                ai_completed = count
            elif status_val == "PENDING":
                ai_pending = count
            elif status_val == "FAILED":
                ai_failed = count
            elif status_val == "UNAVAILABLE":
                ai_unavailable = count

        ai_human_review_count = (
            self.db.scalar(
                select(func.count(InvestigationReport.id)).where(
                    InvestigationReport.merchant_id == self.merchant_id,
                    InvestigationReport.requires_human_review.is_(True),
                )
            )
            or 0
        )

        # 8. Last reconciliation run timestamp
        last_run_time = self.db.scalar(
            select(func.max(ReconciliationRun.started_at)).where(
                ReconciliationRun.merchant_id == self.merchant_id
            )
        )

        return DashboardOverviewResponse(
            merchant_id=self.merchant_id,
            total_payments_processed=total_payments,
            matched_records=matched_count,
            unmatched_records=unmatched_count,
            exception_records=exception_count,
            match_rate_percentage=match_rate,
            total_exposure_by_currency=exposure_by_currency,
            pending_approvals_count=pending_approvals,
            exceptions_awaiting_review=exceptions_awaiting,
            resolved_exceptions_count=resolved_count,
            ai_investigations=AIInvestigationOverview(
                completed_count=ai_completed,
                pending_count=ai_pending,
                failed_count=ai_failed,
                unavailable_count=ai_unavailable,
                requires_human_review_count=ai_human_review_count,
            ),
            last_reconciliation_at=last_run_time,
        )

    def get_reconciliation_health(self) -> ReconciliationHealthResponse:
        """Computes categorical distributions for matching, exception types, exposure, and resolution states."""
        # 1. Match distribution
        matched = (
            self.db.scalar(
                select(func.count(ReconciliationResult.id)).where(
                    ReconciliationResult.merchant_id == self.merchant_id,
                    ReconciliationResult.match_status.in_(
                        [
                            MatchStatus.MATCHED,
                            MatchStatus.MATCHED_WITH_VARIANCE,
                        ]
                    ),
                )
            )
            or 0
        )

        unmatched = (
            self.db.scalar(
                select(func.count(ReconciliationResult.id)).where(
                    ReconciliationResult.merchant_id == self.merchant_id,
                    ReconciliationResult.match_status == MatchStatus.UNMATCHED,
                )
            )
            or 0
        )

        exceptions = (
            self.db.scalar(
                select(func.count(ExceptionRecord.id)).where(
                    ExceptionRecord.merchant_id == self.merchant_id
                )
            )
            or 0
        )

        # 2. Exceptions by type
        type_rows = self.db.execute(
            select(
                ExceptionRecord.exception_type,
                ExceptionRecord.currency,
                func.count(ExceptionRecord.id),
                func.coalesce(func.sum(ExceptionRecord.financial_impact), Decimal("0.00")),
            )
            .where(ExceptionRecord.merchant_id == self.merchant_id)
            .group_by(ExceptionRecord.exception_type, ExceptionRecord.currency)
        ).all()

        type_breakdowns = [
            ExceptionTypeBreakdown(
                exception_type=row[0].value if hasattr(row[0], "value") else str(row[0]),
                currency=row[1],
                count=row[2],
                total_exposure=Decimal(str(row[3])),
            )
            for row in type_rows
        ]

        # 3. Outstanding exposure by currency
        exposure_rows = self.db.execute(
            select(
                ExceptionRecord.currency,
                func.coalesce(func.sum(ExceptionRecord.financial_impact), Decimal("0.00")),
                func.count(ExceptionRecord.id),
            )
            .where(
                ExceptionRecord.merchant_id == self.merchant_id,
                ExceptionRecord.status != ExceptionStatus.RESOLVED,
            )
            .group_by(ExceptionRecord.currency)
        ).all()

        exposure_by_curr = [
            CurrencyExposure(
                currency=r[0],
                total_exposure=Decimal(str(r[1])),
                exception_count=r[2],
            )
            for r in exposure_rows
        ]

        # 4. Resolution status breakdown
        res_rows = self.db.execute(
            select(
                ExceptionRecord.resolution_status,
                func.count(ExceptionRecord.id),
            )
            .where(ExceptionRecord.merchant_id == self.merchant_id)
            .group_by(ExceptionRecord.resolution_status)
        ).all()

        res_breakdowns = [
            ResolutionStatusBreakdown(status=str(r[0] or "OPEN"), count=r[1]) for r in res_rows
        ]

        # 5. Severity breakdown
        sev_rows = self.db.execute(
            select(ExceptionRecord.severity, func.count(ExceptionRecord.id))
            .where(ExceptionRecord.merchant_id == self.merchant_id)
            .group_by(ExceptionRecord.severity)
        ).all()

        sev_breakdowns = [
            SeverityBreakdown(
                severity=r[0].value if hasattr(r[0], "value") else str(r[0]),
                count=r[1],
            )
            for r in sev_rows
        ]

        return ReconciliationHealthResponse(
            merchant_id=self.merchant_id,
            match_distribution={
                "matched": matched,
                "unmatched": unmatched,
                "exceptions": exceptions,
            },
            exceptions_by_type=type_breakdowns,
            exposure_by_currency=exposure_by_curr,
            resolution_status_distribution=res_breakdowns,
            severity_distribution=sev_breakdowns,
        )

    def get_exception_trends(self) -> DashboardTrendsResponse:
        """Returns reconciliation runs history and daily detected exception trends."""
        # 1. Historical runs
        runs = self.db.scalars(
            select(ReconciliationRun)
            .where(ReconciliationRun.merchant_id == self.merchant_id)
            .order_by(desc(ReconciliationRun.started_at))
            .limit(15)
        ).all()

        runs_history = []
        for r in runs:
            total = r.matched_records + r.unmatched_records + r.exception_records
            rate = round((r.matched_records / total * 100.0), 2) if total > 0 else 0.0
            runs_history.append(
                ReconciliationRunTrendItem(
                    run_id=r.id,
                    started_at=r.started_at,
                    completed_at=r.completed_at,
                    status=r.status.value if hasattr(r.status, "value") else str(r.status),
                    total_records=r.total_records,
                    matched_records=r.matched_records,
                    unmatched_records=r.unmatched_records,
                    exception_records=r.exception_records,
                    match_rate_percentage=rate,
                )
            )

        # 2. Daily exception detections
        day_expr = func.to_char(ExceptionRecord.first_detected_at, "YYYY-MM-DD")
        trend_rows = self.db.execute(
            select(
                day_expr.label("day"),
                ExceptionRecord.currency,
                func.count(ExceptionRecord.id),
                func.coalesce(func.sum(ExceptionRecord.financial_impact), Decimal("0.00")),
            )
            .where(ExceptionRecord.merchant_id == self.merchant_id)
            .group_by(day_expr, ExceptionRecord.currency)
            .order_by(day_expr)
            .limit(30)
        ).all()

        exception_trends = [
            ExceptionTrendItem(
                date=str(row[0]),
                currency=row[1],
                count=row[2],
                total_exposure=Decimal(str(row[3])),
            )
            for row in trend_rows
        ]

        return DashboardTrendsResponse(
            merchant_id=self.merchant_id,
            runs_history=runs_history,
            exception_trends=exception_trends,
        )

    def get_pending_approvals(self, current_user: User) -> list[PendingApprovalItem]:
        """
        Returns resolution proposals awaiting reviewer approval,
        properly evaluating separation-of-duties and reviewer authorization for current_user.
        """
        proposals = (
            self.db.query(ResolutionProposal, ExceptionRecord, User)
            .join(ExceptionRecord, ResolutionProposal.exception_id == ExceptionRecord.id)
            .outerjoin(User, ResolutionProposal.created_by_user_id == User.id)
            .filter(
                ResolutionProposal.merchant_id == self.merchant_id,
                ResolutionProposal.status == ProposalStatus.PENDING_APPROVAL.value,
            )
            .order_by(desc(ResolutionProposal.created_at))
            .all()
        )

        items = []
        is_reviewer_or_admin = current_user.role in (UserRole.REVIEWER, UserRole.ADMIN)

        for prop, exc, author in proposals:
            is_author = prop.created_by_user_id == current_user.id
            can_approve = is_reviewer_or_admin and not is_author

            items.append(
                PendingApprovalItem(
                    proposal_id=prop.id,
                    exception_id=exc.id,
                    exception_type=exc.exception_type,
                    severity=exc.severity,
                    proposal_category=prop.category,
                    proposed_action=prop.proposed_action,
                    explanation=prop.explanation,
                    financial_impact=exc.financial_impact,
                    currency=exc.currency,
                    created_by_user_id=prop.created_by_user_id,
                    created_by_user_name=author.full_name if author else None,
                    submitted_at=prop.created_at,
                    is_current_user_author=is_author,
                    can_current_user_approve=can_approve,
                )
            )

        return items

    def get_operations_queue(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        exception_type: str | None = None,
        currency: str | None = None,
        min_impact: Decimal | None = None,
        max_impact: Decimal | None = None,
        search: str | None = None,
        sort_by: str = "detected_at",
        sort_order: str = "desc",
    ) -> OperationsQueueResponse:
        """
        Returns a paginated list of exceptions for operational triage with linked investigation,
        evidence completeness, and proposal state.
        """
        query = select(ExceptionRecord).where(ExceptionRecord.merchant_id == self.merchant_id)

        # Apply filters
        if status:
            if status.upper() in [s.value for s in ExceptionStatus]:
                query = query.where(ExceptionRecord.status == ExceptionStatus(status.upper()))
            else:
                query = query.where(ExceptionRecord.resolution_status == status.upper())

        if exception_type and exception_type.upper() in [t.value for t in ExceptionType]:
            query = query.where(
                ExceptionRecord.exception_type == ExceptionType(exception_type.upper())
            )

        if currency:
            query = query.where(ExceptionRecord.currency == currency.upper())

        if min_impact is not None:
            query = query.where(ExceptionRecord.financial_impact >= min_impact)

        if max_impact is not None:
            query = query.where(ExceptionRecord.financial_impact <= max_impact)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    func.cast(ExceptionRecord.id, func.TEXT).ilike(search_pattern),
                    ExceptionRecord.description.ilike(search_pattern),
                )
            )

        # Total count
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0

        # Sort order
        order_col = ExceptionRecord.first_detected_at
        if sort_by == "impact":
            order_col = ExceptionRecord.financial_impact
        elif sort_by == "severity":
            order_col = ExceptionRecord.severity
        elif sort_by == "type":
            order_col = ExceptionRecord.exception_type
        elif sort_by == "status":
            order_col = ExceptionRecord.status

        if sort_order.lower() == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        # Pagination
        offset = (page - 1) * page_size
        exceptions = self.db.scalars(query.offset(offset).limit(page_size)).all()

        now = datetime.now(UTC)
        items = []

        for exc in exceptions:
            # Evidence count and strength
            ev_count = (
                self.db.scalar(
                    select(func.count(Evidence.id)).where(Evidence.exception_id == exc.id)
                )
                or 0
            )

            # Latest AI investigation
            report = self.db.scalar(
                select(InvestigationReport)
                .where(InvestigationReport.exception_id == exc.id)
                .order_by(desc(InvestigationReport.created_at))
            )

            # Active proposal
            active_prop = self.db.scalar(
                select(ResolutionProposal)
                .where(
                    ResolutionProposal.exception_id == exc.id,
                    ResolutionProposal.status == ProposalStatus.PENDING_APPROVAL.value,
                )
                .order_by(desc(ResolutionProposal.created_at))
            )

            age_days = max(0, (now - exc.first_detected_at).days) if exc.first_detected_at else 0

            items.append(
                OperationsQueueItem(
                    exception_id=exc.id,
                    exception_type=exc.exception_type,
                    severity=exc.severity,
                    status=exc.status,
                    resolution_status=exc.resolution_status or "OPEN",
                    financial_impact=exc.financial_impact,
                    currency=exc.currency,
                    first_detected_at=exc.first_detected_at,
                    age_days=age_days,
                    evidence_count=ev_count,
                    evidence_strength="CONFIRMED"
                    if ev_count >= 3
                    else ("CORROBORATED" if ev_count > 0 else None),
                    ai_investigation_status=report.status if report else None,
                    ai_requires_human_review=report.requires_human_review if report else None,
                    has_pending_proposal=active_prop is not None,
                    active_proposal_id=active_prop.id if active_prop else None,
                    active_proposal_category=active_prop.category.value if active_prop else None,
                )
            )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return OperationsQueueResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
