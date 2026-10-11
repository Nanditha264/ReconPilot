"""
Core service for ReconPilot Human Approval & Exception Resolution Engine (Phase 07).
Enforces auditable resolution lifecycle, evidence grounding, RBAC, separation of duties,
concurrency safety, and zero financial mutation guarantees.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.enums import (
    ActorType,
    ExceptionStatus,
    ProposalStatus,
    ResolutionEventType,
    ResolutionStatus,
    UserRole,
)
from app.models.exception import ExceptionRecord
from app.models.investigation_report import InvestigationReport
from app.models.resolution_history import ResolutionHistory
from app.models.resolution_proposal import ResolutionProposal
from app.models.user import User
from app.modules.evidence.service import EvidenceCollector, EvidenceCorrelator
from app.modules.investigation.grounding import EvidenceGroundingValidator
from app.modules.resolution.schemas import (
    CreateProposalRequest,
    DecisionRequest,
    ProposalResponse,
    ReopenExceptionRequest,
    ResolutionHistoryItem,
    ResolutionSummaryResponse,
    ResolveExceptionRequest,
)

logger = logging.getLogger(__name__)

# Valid lifecycle state transitions map
LEGAL_TRANSITIONS: dict[ResolutionStatus, set[ResolutionStatus]] = {
    ResolutionStatus.OPEN: {ResolutionStatus.UNDER_REVIEW, ResolutionStatus.PENDING_APPROVAL},
    ResolutionStatus.UNDER_REVIEW: {ResolutionStatus.PENDING_APPROVAL, ResolutionStatus.OPEN},
    ResolutionStatus.PENDING_APPROVAL: {
        ResolutionStatus.APPROVED,
        ResolutionStatus.REJECTED,
        ResolutionStatus.UNDER_REVIEW,
    },
    ResolutionStatus.APPROVED: {ResolutionStatus.RESOLVED, ResolutionStatus.UNDER_REVIEW},
    ResolutionStatus.REJECTED: {
        ResolutionStatus.UNDER_REVIEW,
        ResolutionStatus.PENDING_APPROVAL,
        ResolutionStatus.OPEN,
    },
    ResolutionStatus.RESOLVED: {ResolutionStatus.REOPENED},
    ResolutionStatus.REOPENED: {
        ResolutionStatus.UNDER_REVIEW,
        ResolutionStatus.PENDING_APPROVAL,
    },
}


class ResolutionService:
    """
    Manages exception resolution proposals, approvals, rejections, and lifecycle events.
    """

    def __init__(self, db: Session, merchant_id: uuid.UUID):
        self.db = db
        self.merchant_id = merchant_id

    def get_resolution_summary(
        self, exception_id: uuid.UUID, current_user: User
    ) -> ResolutionSummaryResponse:
        """
        Retrieves the current resolution status, active proposal, and allowable actions
        for the current authenticated user.
        """
        exc = self._get_exception(exception_id)
        current_res_status = ResolutionStatus(exc.resolution_status or ResolutionStatus.OPEN.value)

        # Get latest proposal for this exception
        latest_proposal = self.db.scalar(
            select(ResolutionProposal)
            .where(
                ResolutionProposal.exception_id == exception_id,
                ResolutionProposal.merchant_id == self.merchant_id,
            )
            .order_by(desc(ResolutionProposal.created_at))
        )

        proposals_total = len(
            self.db.scalars(
                select(ResolutionProposal).where(
                    ResolutionProposal.exception_id == exception_id,
                    ResolutionProposal.merchant_id == self.merchant_id,
                )
            ).all()
        )

        history_total = len(
            self.db.scalars(
                select(ResolutionHistory).where(
                    ResolutionHistory.exception_id == exception_id,
                    ResolutionHistory.merchant_id == self.merchant_id,
                )
            ).all()
        )

        # Determine capabilities based on user role and separation of duties
        is_reviewer = current_user.role in (UserRole.REVIEWER, UserRole.ADMIN)
        is_author = (
            latest_proposal is not None and latest_proposal.created_by_user_id == current_user.id
        )

        can_approve = (
            is_reviewer
            and not is_author
            and latest_proposal is not None
            and latest_proposal.status == ProposalStatus.PENDING_APPROVAL.value
        )
        can_reject = (
            is_reviewer
            and not is_author
            and latest_proposal is not None
            and latest_proposal.status == ProposalStatus.PENDING_APPROVAL.value
        )
        can_resolve = (
            is_reviewer
            and current_res_status == ResolutionStatus.APPROVED
            and latest_proposal is not None
            and latest_proposal.status == ProposalStatus.APPROVED.value
        )
        can_reopen = current_res_status == ResolutionStatus.RESOLVED
        can_submit = current_res_status != ResolutionStatus.RESOLVED

        allowed_next = sorted(list(LEGAL_TRANSITIONS.get(current_res_status, set())))

        return ResolutionSummaryResponse(
            exception_id=exc.id,
            resolution_status=current_res_status,
            active_proposal=self._to_proposal_response(latest_proposal)
            if latest_proposal
            else None,
            proposals_count=proposals_total,
            history_events_count=history_total,
            can_submit_proposal=can_submit,
            can_approve=can_approve,
            can_reject=can_reject,
            can_resolve=can_resolve,
            can_reopen=can_reopen,
            allowed_transitions=allowed_next,
        )

    def get_history(self, exception_id: uuid.UUID) -> list[ResolutionHistoryItem]:
        """
        Retrieves the complete, ordered history of resolution events for this exception.
        """
        self._get_exception(exception_id)

        history_records = self.db.scalars(
            select(ResolutionHistory)
            .where(
                ResolutionHistory.exception_id == exception_id,
                ResolutionHistory.merchant_id == self.merchant_id,
            )
            .order_by(ResolutionHistory.created_at.asc())
        ).all()

        results: list[ResolutionHistoryItem] = []
        for h in history_records:
            results.append(
                ResolutionHistoryItem(
                    id=h.id,
                    merchant_id=h.merchant_id,
                    exception_id=h.exception_id,
                    proposal_id=h.proposal_id,
                    user_id=h.user_id,
                    user_name=h.user.full_name if h.user else None,
                    user_role=h.user.role.value if h.user else None,
                    event_type=ResolutionEventType(h.event_type),
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    reason=h.reason,
                    metadata=h.event_metadata,
                    created_at=h.created_at,
                )
            )
        return results

    def create_proposal(
        self,
        exception_id: uuid.UUID,
        request: CreateProposalRequest,
        current_user: User,
    ) -> ProposalResponse:
        """
        Creates a new resolution proposal. Validates all cited evidence against the dossier.
        """
        exc = self._get_exception(exception_id)
        current_status = ResolutionStatus(exc.resolution_status or ResolutionStatus.OPEN.value)

        if current_status == ResolutionStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a proposal for an already resolved exception. Reopen it first.",
            )

        # 1. Validate all cited evidence IDs against the verified dossier
        self._validate_evidence_references(exception_id, request.supporting_evidence_ids)

        # 2. Validate investigation report if linked
        if request.investigation_report_id:
            report = self.db.scalar(
                select(InvestigationReport).where(
                    InvestigationReport.id == request.investigation_report_id,
                    InvestigationReport.exception_id == exception_id,
                    InvestigationReport.merchant_id == self.merchant_id,
                )
            )
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Investigation report {request.investigation_report_id} does not exist or belong to this exception.",
                )

        initial_proposal_status = (
            ProposalStatus.PENDING_APPROVAL if request.auto_submit else ProposalStatus.DRAFT
        )

        proposal = ResolutionProposal(
            merchant_id=self.merchant_id,
            exception_id=exception_id,
            investigation_report_id=request.investigation_report_id,
            category=request.category.value,
            status=initial_proposal_status.value,
            explanation=request.explanation,
            proposed_action=request.proposed_action,
            supporting_evidence_ids=request.supporting_evidence_ids,
            created_by_user_id=current_user.id,
            decision_by_user_id=None,
            decision_rationale=None,
            decided_at=None,
        )
        self.db.add(proposal)
        self.db.flush()

        # Update exception resolution status
        new_exception_status = (
            ResolutionStatus.PENDING_APPROVAL
            if request.auto_submit
            else (
                ResolutionStatus.UNDER_REVIEW
                if current_status == ResolutionStatus.OPEN
                else current_status
            )
        )

        if new_exception_status != current_status:
            self._validate_transition(current_status, new_exception_status)
            exc.resolution_status = new_exception_status.value

        # Record History Event
        self._record_history_event(
            exception_id=exception_id,
            proposal_id=proposal.id,
            user_id=current_user.id,
            event_type=ResolutionEventType.PROPOSAL_CREATED,
            previous_status=current_status.value,
            new_status=new_exception_status.value,
            reason=f"Proposal created ({request.category.value}): {request.proposed_action[:100]}",
            metadata={
                "category": request.category.value,
                "evidence_count": len(request.supporting_evidence_ids),
                "auto_submit": request.auto_submit,
            },
        )

        if request.auto_submit:
            self._record_history_event(
                exception_id=exception_id,
                proposal_id=proposal.id,
                user_id=current_user.id,
                event_type=ResolutionEventType.PROPOSAL_SUBMITTED,
                previous_status=current_status.value,
                new_status=new_exception_status.value,
                reason="Submitted for reviewer approval",
                metadata={"category": request.category.value},
            )

        self.db.commit()
        self.db.refresh(proposal)
        return self._to_proposal_response(proposal)

    def submit_proposal(
        self,
        exception_id: uuid.UUID,
        proposal_id: uuid.UUID,
        current_user: User,
    ) -> ProposalResponse:
        """
        Submits an existing DRAFT proposal for reviewer approval.
        """
        exc = self._get_exception(exception_id)
        current_status = ResolutionStatus(exc.resolution_status or ResolutionStatus.OPEN.value)

        proposal = self._get_proposal(proposal_id, exception_id)
        if proposal.status != ProposalStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only DRAFT proposals can be submitted. Current status: {proposal.status}",
            )

        new_status = ResolutionStatus.PENDING_APPROVAL
        self._validate_transition(current_status, new_status)

        proposal.status = ProposalStatus.PENDING_APPROVAL.value
        exc.resolution_status = new_status.value

        self._record_history_event(
            exception_id=exception_id,
            proposal_id=proposal.id,
            user_id=current_user.id,
            event_type=ResolutionEventType.PROPOSAL_SUBMITTED,
            previous_status=current_status.value,
            new_status=new_status.value,
            reason="Proposal submitted for human approval",
            metadata={"category": proposal.category},
        )

        self.db.commit()
        self.db.refresh(proposal)
        return self._to_proposal_response(proposal)

    def approve_proposal(
        self,
        exception_id: uuid.UUID,
        proposal_id: uuid.UUID,
        request: DecisionRequest,
        current_user: User,
    ) -> ProposalResponse:
        """
        Approves a submitted proposal.
        Enforces reviewer role, separation of duties, and optimistic concurrency locks.
        """
        # 1. RBAC check
        if current_user.role not in (UserRole.REVIEWER, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authorized Reviewers or Admins can approve resolution proposals.",
            )

        # 2. Concurrency lock
        exc = self.db.scalar(
            select(ExceptionRecord)
            .where(
                ExceptionRecord.id == exception_id,
                ExceptionRecord.merchant_id == self.merchant_id,
            )
            .with_for_update()
        )
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found."
            )

        proposal = self.db.scalar(
            select(ResolutionProposal)
            .where(
                ResolutionProposal.id == proposal_id,
                ResolutionProposal.exception_id == exception_id,
                ResolutionProposal.merchant_id == self.merchant_id,
            )
            .with_for_update()
        )
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found.")

        # 3. Separation of duties
        if proposal.created_by_user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Separation of duties policy violation: The proposal author cannot approve their own proposal.",
            )

        # 4. State validation
        if proposal.status != ProposalStatus.PENDING_APPROVAL.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Proposal is not pending approval. Current proposal status: {proposal.status}",
            )

        current_res_status = ResolutionStatus(exc.resolution_status or ResolutionStatus.OPEN.value)
        new_res_status = ResolutionStatus.APPROVED
        self._validate_transition(current_res_status, new_res_status)

        # 5. Apply decision
        now = datetime.now(UTC)
        proposal.status = ProposalStatus.APPROVED.value
        proposal.decision_by_user_id = current_user.id
        proposal.decision_rationale = request.rationale
        proposal.decided_at = now
        exc.resolution_status = new_res_status.value

        self._record_history_event(
            exception_id=exception_id,
            proposal_id=proposal.id,
            user_id=current_user.id,
            event_type=ResolutionEventType.PROPOSAL_APPROVED,
            previous_status=current_res_status.value,
            new_status=new_res_status.value,
            reason=f"Approved: {request.rationale}",
            metadata={
                "reviewer_name": current_user.full_name,
                "reviewer_role": current_user.role.value,
            },
        )

        self.db.commit()
        self.db.refresh(proposal)
        return self._to_proposal_response(proposal)

    def reject_proposal(
        self,
        exception_id: uuid.UUID,
        proposal_id: uuid.UUID,
        request: DecisionRequest,
        current_user: User,
    ) -> ProposalResponse:
        """
        Rejects a submitted proposal. Requires mandatory non-empty reason.
        Rejection does NOT resolve the exception.
        """
        if not request.rationale or len(request.rationale.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A valid explanation reason is mandatory when rejecting a resolution proposal.",
            )

        if current_user.role not in (UserRole.REVIEWER, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authorized Reviewers or Admins can reject resolution proposals.",
            )

        exc = self.db.scalar(
            select(ExceptionRecord)
            .where(
                ExceptionRecord.id == exception_id,
                ExceptionRecord.merchant_id == self.merchant_id,
            )
            .with_for_update()
        )
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found."
            )

        proposal = self.db.scalar(
            select(ResolutionProposal)
            .where(
                ResolutionProposal.id == proposal_id,
                ResolutionProposal.exception_id == exception_id,
                ResolutionProposal.merchant_id == self.merchant_id,
            )
            .with_for_update()
        )
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found.")

        if proposal.created_by_user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Separation of duties policy violation: The proposal author cannot reject their own proposal.",
            )

        if proposal.status != ProposalStatus.PENDING_APPROVAL.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Proposal is not pending approval. Current proposal status: {proposal.status}",
            )

        current_res_status = ResolutionStatus(exc.resolution_status or ResolutionStatus.OPEN.value)
        new_res_status = ResolutionStatus.REJECTED
        self._validate_transition(current_res_status, new_res_status)

        now = datetime.now(UTC)
        proposal.status = ProposalStatus.REJECTED.value
        proposal.decision_by_user_id = current_user.id
        proposal.decision_rationale = request.rationale.strip()
        proposal.decided_at = now
        exc.resolution_status = new_res_status.value

        self._record_history_event(
            exception_id=exception_id,
            proposal_id=proposal.id,
            user_id=current_user.id,
            event_type=ResolutionEventType.PROPOSAL_REJECTED,
            previous_status=current_res_status.value,
            new_status=new_res_status.value,
            reason=f"Rejected: {request.rationale.strip()}",
            metadata={
                "reviewer_name": current_user.full_name,
                "reviewer_role": current_user.role.value,
            },
        )

        self.db.commit()
        self.db.refresh(proposal)
        return self._to_proposal_response(proposal)

    def resolve_exception(
        self,
        exception_id: uuid.UUID,
        request: ResolveExceptionRequest,
        current_user: User,
    ) -> ResolutionSummaryResponse:
        """
        Explicitly marks the exception as RESOLVED.
        Requires reviewer role, explicit operator confirmation, and an approved proposal.
        """
        if current_user.role not in (UserRole.REVIEWER, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Reviewers or Admins can mark exceptions as resolved.",
            )

        if not request.confirmation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explicit confirmation is required before marking this exception resolved.",
            )

        exc = self.db.scalar(
            select(ExceptionRecord)
            .where(
                ExceptionRecord.id == exception_id,
                ExceptionRecord.merchant_id == self.merchant_id,
            )
            .with_for_update()
        )
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found."
            )

        current_res_status = ResolutionStatus(exc.resolution_status or ResolutionStatus.OPEN.value)
        if current_res_status != ResolutionStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exception must have an approved resolution proposal before being resolved. Current: {current_res_status}",
            )

        new_res_status = ResolutionStatus.RESOLVED
        self._validate_transition(current_res_status, new_res_status)

        now = datetime.now(UTC)
        exc.resolution_status = new_res_status.value
        exc.status = ExceptionStatus.RESOLVED
        exc.resolved_at = now

        self._record_history_event(
            exception_id=exception_id,
            proposal_id=None,
            user_id=current_user.id,
            event_type=ResolutionEventType.EXCEPTION_RESOLVED,
            previous_status=current_res_status.value,
            new_status=new_res_status.value,
            reason=request.notes
            or "Exception marked resolved following approved proposal verification.",
            metadata={"resolver": current_user.full_name},
        )

        self.db.commit()
        return self.get_resolution_summary(exception_id, current_user)

    def reopen_exception(
        self,
        exception_id: uuid.UUID,
        request: ReopenExceptionRequest,
        current_user: User,
    ) -> ResolutionSummaryResponse:
        """
        Reopens a resolved exception. Requires mandatory non-empty business justification.
        """
        if not request.reason or len(request.reason.strip()) < 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A clear business reason of at least 5 characters is mandatory when reopening an exception.",
            )

        exc = self.db.scalar(
            select(ExceptionRecord)
            .where(
                ExceptionRecord.id == exception_id,
                ExceptionRecord.merchant_id == self.merchant_id,
            )
            .with_for_update()
        )
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found."
            )

        current_res_status = ResolutionStatus(exc.resolution_status or ResolutionStatus.OPEN.value)
        if current_res_status != ResolutionStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only RESOLVED exceptions can be reopened. Current status: {current_res_status}",
            )

        new_res_status = ResolutionStatus.REOPENED
        self._validate_transition(current_res_status, new_res_status)

        exc.resolution_status = new_res_status.value
        exc.status = ExceptionStatus.OPEN
        exc.resolved_at = None

        self._record_history_event(
            exception_id=exception_id,
            proposal_id=None,
            user_id=current_user.id,
            event_type=ResolutionEventType.EXCEPTION_REOPENED,
            previous_status=current_res_status.value,
            new_status=new_res_status.value,
            reason=request.reason.strip(),
            metadata={"reopened_by": current_user.full_name},
        )

        self.db.commit()
        return self.get_resolution_summary(exception_id, current_user)

    def _get_exception(self, exception_id: uuid.UUID) -> ExceptionRecord:
        exc = self.db.scalar(
            select(ExceptionRecord).where(
                ExceptionRecord.id == exception_id,
                ExceptionRecord.merchant_id == self.merchant_id,
            )
        )
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exception record {exception_id} not found.",
            )
        return exc

    def _get_proposal(self, proposal_id: uuid.UUID, exception_id: uuid.UUID) -> ResolutionProposal:
        proposal = self.db.scalar(
            select(ResolutionProposal).where(
                ResolutionProposal.id == proposal_id,
                ResolutionProposal.exception_id == exception_id,
                ResolutionProposal.merchant_id == self.merchant_id,
            )
        )
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resolution proposal {proposal_id} not found.",
            )
        return proposal

    def _validate_evidence_references(
        self, exception_id: uuid.UUID, evidence_ids: list[str]
    ) -> None:
        if not evidence_ids:
            return

        collector = EvidenceCollector(db=self.db, merchant_id=self.merchant_id)
        raw_evidence = collector.collect(exception_id=exception_id)
        if not raw_evidence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to verify evidence references because the exception has no evidence dossier.",
            )

        dossier = EvidenceCorrelator.correlate(raw_evidence)
        valid_ids = EvidenceGroundingValidator.extract_valid_evidence_identifiers(dossier)

        invalid_citations = [eid for eid in evidence_ids if eid not in valid_ids]
        if invalid_citations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evidence reference(s) {invalid_citations} are not recognized in the verified dossier for this exception.",
            )

    def _validate_transition(self, current: ResolutionStatus, target: ResolutionStatus) -> None:
        allowed = LEGAL_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal resolution status transition from '{current.value}' to '{target.value}'. Allowed transitions: {[s.value for s in allowed]}.",
            )

    def _record_history_event(
        self,
        exception_id: uuid.UUID,
        proposal_id: uuid.UUID | None,
        user_id: uuid.UUID,
        event_type: ResolutionEventType,
        previous_status: str,
        new_status: str,
        reason: str | None,
        metadata: dict[str, Any] | None,
    ) -> None:
        # 1. Append to resolution_history
        hist = ResolutionHistory(
            merchant_id=self.merchant_id,
            exception_id=exception_id,
            proposal_id=proposal_id,
            user_id=user_id,
            event_type=event_type.value,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            event_metadata=metadata,
        )
        self.db.add(hist)

        # 2. Append to central audit_events
        audit = AuditEvent(
            merchant_id=self.merchant_id,
            exception_id=exception_id,
            reconciliation_run_id=None,
            actor_type=ActorType.HUMAN_CONTROLLER,
            actor_id=str(user_id),
            event_type=f"RESOLUTION_{event_type.value}",
            previous_state=previous_status,
            new_state=new_status,
            event_metadata={
                "proposal_id": str(proposal_id) if proposal_id else None,
                "reason": reason,
                **(metadata or {}),
            },
        )
        self.db.add(audit)

    def _to_proposal_response(self, proposal: ResolutionProposal) -> ProposalResponse:
        return ProposalResponse(
            id=proposal.id,
            merchant_id=proposal.merchant_id,
            exception_id=proposal.exception_id,
            investigation_report_id=proposal.investigation_report_id,
            category=proposal.category,
            status=proposal.status,
            explanation=proposal.explanation,
            proposed_action=proposal.proposed_action,
            supporting_evidence_ids=proposal.supporting_evidence_ids or [],
            created_by_user_id=proposal.created_by_user_id,
            created_by_user_name=proposal.created_by_user.full_name
            if proposal.created_by_user
            else None,
            created_by_user_email=proposal.created_by_user.email
            if proposal.created_by_user
            else None,
            decision_by_user_id=proposal.decision_by_user_id,
            decision_by_user_name=proposal.decision_by_user.full_name
            if proposal.decision_by_user
            else None,
            decision_rationale=proposal.decision_rationale,
            decided_at=proposal.decided_at,
            created_at=proposal.created_at,
            updated_at=proposal.updated_at,
        )
