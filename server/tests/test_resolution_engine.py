"""
Focused test suite for ReconPilot Human Approval & Exception Resolution Engine (Phase 07).
Validates proposals, evidence verification, separation of duties, RBAC,
state machine transitions, immutable audit history, tenant isolation, and non-mutation guarantees.
"""

import uuid
from datetime import timedelta

import pytest
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.enums import (
    ExceptionStatus,
    ProposalStatus,
    ResolutionCategory,
    ResolutionEventType,
    ResolutionStatus,
    UserRole,
    UserStatus,
)
from app.models.exception import ExceptionRecord
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.resolution_history import ResolutionHistory
from app.models.resolution_proposal import ResolutionProposal
from app.models.settlement import Settlement
from app.models.settlement_item import SettlementItem
from app.models.user import User
from app.modules.evidence.service import EvidenceCollector, EvidenceCorrelator
from app.modules.resolution.schemas import (
    CreateProposalRequest,
    DecisionRequest,
    ReopenExceptionRequest,
    ResolveExceptionRequest,
)
from app.modules.resolution.service import ResolutionService
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_resolution_test_data():
    """Cleans up test resolution data and resets tested exception status."""
    yield
    db = SessionLocal()
    try:
        db.query(ResolutionHistory).delete(synchronize_session=False)
        db.query(ResolutionProposal).delete(synchronize_session=False)
        db.query(User).filter(User.email.like("res_test_%")).delete(synchronize_session=False)
        db.query(Merchant).filter(Merchant.name.like("Res Test Merchant%")).delete(
            synchronize_session=False
        )
        # Reset any exceptions resolution status back to OPEN
        db.query(ExceptionRecord).update(
            {"resolution_status": ResolutionStatus.OPEN.value, "status": ExceptionStatus.OPEN},
            synchronize_session=False,
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def test_proposal_creation_and_evidence_validation():
    """Verify proposal creation with verified evidence references and rejection of hallucinated IDs."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        assert merchant is not None

        operator = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.FINANCE_OPERATOR)
            .first()
        )
        assert operator is not None

        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        assert exc is not None

        # Collect verified evidence IDs from dossier
        collector = EvidenceCollector(db=db, merchant_id=merchant.id)
        raw = collector.collect(exception_id=exc.id)
        assert raw is not None
        dossier = EvidenceCorrelator.correlate(raw)
        valid_ev_id = dossier.evidence_items[0].evidence_id

        service = ResolutionService(db=db, merchant_id=merchant.id)

        # 1. Proposal with verified evidence succeeds
        valid_req = CreateProposalRequest(
            category=ResolutionCategory.FEE_DISCREPANCY_REVIEW,
            explanation="Fee deduction variance matches scheduled tier discrepancy.",
            proposed_action="Request gateway ledger credit note.",
            supporting_evidence_ids=[valid_ev_id],
            auto_submit=False,
        )
        proposal = service.create_proposal(
            exception_id=exc.id, request=valid_req, current_user=operator
        )
        assert proposal is not None
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.category == ResolutionCategory.FEE_DISCREPANCY_REVIEW
        assert valid_ev_id in proposal.supporting_evidence_ids

        # 2. Proposal with fake/hallucinated evidence ID is rejected with 400
        invalid_req = CreateProposalRequest(
            category=ResolutionCategory.DATA_CORRECTION_REQUIRED,
            explanation="Hallucinated claim.",
            proposed_action="Do nothing.",
            supporting_evidence_ids=["fake_hallucinated_evidence_id_999"],
            auto_submit=False,
        )
        with pytest.raises(Exception) as exc_info:
            service.create_proposal(exception_id=exc.id, request=invalid_req, current_user=operator)
        assert "not recognized in the verified dossier" in str(exc_info.value)
    finally:
        db.close()


def test_proposal_submission_and_separation_of_duties():
    """Verify proposal submission and ensure creator cannot approve their own proposal."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        assert exc is not None

        # Operator (creator)
        operator = User(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            email=f"res_test_op_{uuid.uuid4().hex[:6]}@reconpilot.local",
            password_hash="test_hash",
            full_name="Operator Alice",
            role=UserRole.FINANCE_OPERATOR,
            status=UserStatus.ACTIVE,
        )
        # Reviewer Bob
        reviewer = User(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            email=f"res_test_rev_{uuid.uuid4().hex[:6]}@reconpilot.local",
            password_hash="test_hash",
            full_name="Reviewer Bob",
            role=UserRole.REVIEWER,
            status=UserStatus.ACTIVE,
        )
        db.add_all([operator, reviewer])
        db.commit()

        service = ResolutionService(db=db, merchant_id=merchant.id)

        # 1. Create DRAFT proposal by Operator
        create_req = CreateProposalRequest(
            category=ResolutionCategory.SETTLEMENT_DELAY_CONFIRMED,
            explanation="Bank settlement batch delayed due to weekend clearing cycle.",
            proposed_action="Allow 24h grace period for gateway deposit.",
            supporting_evidence_ids=[],
            auto_submit=False,
        )
        draft = service.create_proposal(
            exception_id=exc.id, request=create_req, current_user=operator
        )
        assert draft.status == ProposalStatus.DRAFT

        # 2. Submit proposal
        submitted = service.submit_proposal(
            exception_id=exc.id, proposal_id=draft.id, current_user=operator
        )
        assert submitted.status == ProposalStatus.PENDING_APPROVAL

        # 3. RBAC check: Operator Alice cannot approve proposals (only Reviewer/Admin can)
        with pytest.raises(Exception) as exc_info:
            service.approve_proposal(
                exception_id=exc.id,
                proposal_id=draft.id,
                request=DecisionRequest(rationale="Operator attempting to approve"),
                current_user=operator,
            )
        assert "only authorized reviewers" in str(exc_info.value).lower()

        # 4. Separation of duties check: Reviewer Bob creates a proposal, but CANNOT approve his own proposal
        rev2 = User(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            email=f"res_test_rev2_{uuid.uuid4().hex[:6]}@reconpilot.local",
            password_hash="test_hash",
            full_name="Reviewer Carol",
            role=UserRole.REVIEWER,
            status=UserStatus.ACTIVE,
        )
        db.add(rev2)
        db.commit()

        bob_proposal = service.create_proposal(
            exception_id=exc.id,
            request=CreateProposalRequest(
                category=ResolutionCategory.DATA_CORRECTION_REQUIRED,
                explanation="Need adjustment ledger entry for currency rounding.",
                proposed_action="Flag for data engineering sync.",
                auto_submit=True,
            ),
            current_user=reviewer,
        )
        with pytest.raises(Exception) as exc_info:
            service.approve_proposal(
                exception_id=exc.id,
                proposal_id=bob_proposal.id,
                request=DecisionRequest(rationale="I approve my own proposal"),
                current_user=reviewer,
            )
        assert "separation of duties" in str(exc_info.value).lower()

        # 5. Reviewer Carol approves Bob's proposal
        approved_bob = service.approve_proposal(
            exception_id=exc.id,
            proposal_id=bob_proposal.id,
            request=DecisionRequest(rationale="Peer review verified and accepted."),
            current_user=rev2,
        )
        assert approved_bob.status == ProposalStatus.APPROVED
        assert approved_bob.decision_by_user_id == rev2.id
        assert approved_bob.decision_rationale == "Peer review verified and accepted."

        # Verify exception resolution status
        summary = service.get_resolution_summary(exception_id=exc.id, current_user=reviewer)
        assert summary.resolution_status == ResolutionStatus.APPROVED
    finally:
        db.close()


def test_rejection_mandates_reason_and_does_not_resolve():
    """Verify reviewer rejection requires non-empty reason and leaves exception unresolved."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        assert exc is not None

        operator = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.FINANCE_OPERATOR)
            .first()
        )
        reviewer = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.REVIEWER)
            .first()
        )
        assert operator is not None and reviewer is not None

        service = ResolutionService(db=db, merchant_id=merchant.id)

        # Create & auto-submit proposal
        req = CreateProposalRequest(
            category=ResolutionCategory.NO_SUPPORTED_RESOLUTION,
            explanation="Unable to determine variance.",
            proposed_action="Write off variance.",
            supporting_evidence_ids=[],
            auto_submit=True,
        )
        proposal = service.create_proposal(exception_id=exc.id, request=req, current_user=operator)
        assert proposal.status == ProposalStatus.PENDING_APPROVAL

        # Reject with valid reason
        rejected = service.reject_proposal(
            exception_id=exc.id,
            proposal_id=proposal.id,
            request=DecisionRequest(
                rationale="Write-offs not permitted for variances over 50 INR without manager review."
            ),
            current_user=reviewer,
        )
        assert rejected.status == ProposalStatus.REJECTED
        assert rejected.decision_by_user_id == reviewer.id

        # Check exception state: must be REJECTED, NOT RESOLVED!
        summary = service.get_resolution_summary(exception_id=exc.id, current_user=reviewer)
        assert summary.resolution_status == ResolutionStatus.REJECTED
        assert summary.can_resolve is False
    finally:
        db.close()


def test_duplicate_decision_attempts():
    """Verify that an already decided proposal cannot be decided again (conflict)."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        operator = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.FINANCE_OPERATOR)
            .first()
        )
        reviewer = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.REVIEWER)
            .first()
        )

        service = ResolutionService(db=db, merchant_id=merchant.id)

        proposal = service.create_proposal(
            exception_id=exc.id,
            request=CreateProposalRequest(
                category=ResolutionCategory.OTHER,
                explanation="Testing duplicate decision handling.",
                proposed_action="Action test.",
                auto_submit=True,
            ),
            current_user=operator,
        )

        # First approval succeeds
        service.approve_proposal(
            exception_id=exc.id,
            proposal_id=proposal.id,
            request=DecisionRequest(rationale="First approval."),
            current_user=reviewer,
        )

        # Second decision fails with 409 Conflict
        with pytest.raises(Exception) as exc_info:
            service.approve_proposal(
                exception_id=exc.id,
                proposal_id=proposal.id,
                request=DecisionRequest(rationale="Second approval."),
                current_user=reviewer,
            )
        assert "not pending approval" in str(exc_info.value).lower()
    finally:
        db.close()


def test_resolution_confirmation_and_reopen_lifecycle():
    """Verify final resolution requires confirmation and can be reopened with mandatory reason."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        operator = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.FINANCE_OPERATOR)
            .first()
        )
        reviewer = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.REVIEWER)
            .first()
        )

        service = ResolutionService(db=db, merchant_id=merchant.id)

        # Create and approve proposal
        proposal = service.create_proposal(
            exception_id=exc.id,
            request=CreateProposalRequest(
                category=ResolutionCategory.SETTLEMENT_DELAY_CONFIRMED,
                explanation="Confirmed settlement funds arrived.",
                proposed_action="Close ticket.",
                auto_submit=True,
            ),
            current_user=operator,
        )
        service.approve_proposal(
            exception_id=exc.id,
            proposal_id=proposal.id,
            request=DecisionRequest(rationale="Bank credit confirmed."),
            current_user=reviewer,
        )

        # 1. Resolve without explicit confirmation fails
        with pytest.raises(Exception) as exc_info:
            service.resolve_exception(
                exception_id=exc.id,
                request=ResolveExceptionRequest(confirmation=False),
                current_user=reviewer,
            )
        assert "Explicit confirmation is required" in str(exc_info.value)

        # 2. Resolve with confirmation succeeds
        resolved_summary = service.resolve_exception(
            exception_id=exc.id,
            request=ResolveExceptionRequest(
                confirmation=True, notes="Verified credit in bank statement."
            ),
            current_user=reviewer,
        )
        assert resolved_summary.resolution_status == ResolutionStatus.RESOLVED
        assert resolved_summary.can_reopen is True

        # Check DB exception record
        db_exc = db.query(ExceptionRecord).filter(ExceptionRecord.id == exc.id).first()
        assert db_exc.resolution_status == ResolutionStatus.RESOLVED.value
        assert db_exc.resolved_at is not None

        # 3. Reopen without reason fails (Pydantic schema validation & service validation)
        with pytest.raises(Exception) as exc_info:
            ReopenExceptionRequest(reason="bad")
        assert "at least 5 characters" in str(exc_info.value).lower()

        with pytest.raises(Exception) as exc_info:
            service.reopen_exception(
                exception_id=exc.id,
                request=ReopenExceptionRequest(reason="     "),
                current_user=operator,
            )
        assert "clear business reason" in str(exc_info.value).lower()

        # 4. Reopen with reason succeeds
        reopened_summary = service.reopen_exception(
            exception_id=exc.id,
            request=ReopenExceptionRequest(
                reason="Subsequent bank statement showed a clawback on this transaction."
            ),
            current_user=operator,
        )
        assert reopened_summary.resolution_status == ResolutionStatus.REOPENED
        assert db_exc.resolved_at is None
    finally:
        db.close()


def test_immutable_history_and_audit_trail():
    """Verify that every lifecycle event creates an immutable record in resolution_history."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        operator = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.FINANCE_OPERATOR)
            .first()
        )
        reviewer = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.REVIEWER)
            .first()
        )

        service = ResolutionService(db=db, merchant_id=merchant.id)

        # Cycle: Create -> Approve -> Resolve -> Reopen
        p = service.create_proposal(
            exception_id=exc.id,
            request=CreateProposalRequest(
                category=ResolutionCategory.ESCALATE_TO_GATEWAY,
                explanation="Escalated to gateway support.",
                proposed_action="Awaiting ticket #12345.",
                auto_submit=True,
            ),
            current_user=operator,
        )
        service.approve_proposal(
            exception_id=exc.id,
            proposal_id=p.id,
            request=DecisionRequest(rationale="Escalation ticket approved."),
            current_user=reviewer,
        )
        service.resolve_exception(
            exception_id=exc.id,
            request=ResolveExceptionRequest(confirmation=True),
            current_user=reviewer,
        )
        service.reopen_exception(
            exception_id=exc.id,
            request=ReopenExceptionRequest(reason="Ticket reopened by payment gateway."),
            current_user=operator,
        )

        # Retrieve history
        history = service.get_history(exception_id=exc.id)
        event_types = [h.event_type for h in history]

        assert ResolutionEventType.PROPOSAL_CREATED in event_types
        assert ResolutionEventType.PROPOSAL_SUBMITTED in event_types
        assert ResolutionEventType.PROPOSAL_APPROVED in event_types
        assert ResolutionEventType.EXCEPTION_RESOLVED in event_types
        assert ResolutionEventType.EXCEPTION_REOPENED in event_types

        # Verify chronological ordering
        for i in range(len(history) - 1):
            assert history[i].created_at <= history[i + 1].created_at
    finally:
        db.close()


def test_cross_tenant_resolution_access_denial():
    """Verify that operators from Merchant B cannot view or modify Merchant A's resolution."""
    db = SessionLocal()
    try:
        merchant_a = db.query(Merchant).first()
        exc_a = (
            db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant_a.id).first()
        )
        assert exc_a is not None

        # Create Merchant B and User B
        merchant_b = Merchant(
            id=uuid.uuid4(),
            name=f"Res Test Merchant B {uuid.uuid4().hex[:6]}",
            email=f"res_b_{uuid.uuid4().hex[:6]}@example.com",
            currency="INR",
            timezone="Asia/Kolkata",
        )
        user_b = User(
            id=uuid.uuid4(),
            merchant_id=merchant_b.id,
            email=f"res_test_user_b_{uuid.uuid4().hex[:6]}@example.com",
            password_hash="test_pw",
            full_name="Tenant B Reviewer",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        db.add_all([merchant_b, user_b])
        db.commit()

        token_b = create_access_token(
            data={
                "sub": str(user_b.id),
                "merchant_id": str(merchant_b.id),
                "role": user_b.role.value,
            },
            expires_delta=timedelta(minutes=30),
        )
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to access Merchant A's exception resolution
        get_resp = client.get(f"/api/v1/exceptions/{exc_a.id}/resolution", headers=headers_b)
        assert get_resp.status_code == 404

        post_resp = client.post(
            f"/api/v1/exceptions/{exc_a.id}/resolution/proposals",
            json={
                "category": "OTHER",
                "explanation": "Cross-tenant intrusion attempt.",
                "proposed_action": "Deny.",
            },
            headers=headers_b,
        )
        assert post_resp.status_code == 404
    finally:
        db.close()


def test_resolution_workflow_never_mutates_financial_records():
    """Verify that creating, approving, and resolving exceptions never mutates payments or settlements."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()
        operator = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.FINANCE_OPERATOR)
            .first()
        )
        reviewer = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.REVIEWER)
            .first()
        )

        # Baseline counts
        payments_before = db.query(Payment).count()
        settlements_before = db.query(Settlement).count()
        items_before = db.query(SettlementItem).count()

        service = ResolutionService(db=db, merchant_id=merchant.id)

        # Execute full lifecycle
        p = service.create_proposal(
            exception_id=exc.id,
            request=CreateProposalRequest(
                category=ResolutionCategory.DATA_CORRECTION_REQUIRED,
                explanation="Zero mutation verification.",
                proposed_action="Audit ledger manually.",
                auto_submit=True,
            ),
            current_user=operator,
        )
        service.approve_proposal(
            exception_id=exc.id,
            proposal_id=p.id,
            request=DecisionRequest(rationale="Approved zero-mutation."),
            current_user=reviewer,
        )
        service.resolve_exception(
            exception_id=exc.id,
            request=ResolveExceptionRequest(confirmation=True),
            current_user=reviewer,
        )

        # Verify baseline counts are identical
        assert db.query(Payment).count() == payments_before
        assert db.query(Settlement).count() == settlements_before
        assert db.query(SettlementItem).count() == items_before
    finally:
        db.close()


def test_api_resolution_endpoints_e2e():
    """Verify HTTP API endpoints for proposal creation, approval, resolution, and history."""
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.merchant_id == merchant.id).first()

        operator = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.FINANCE_OPERATOR)
            .first()
        )
        reviewer = (
            db.query(User)
            .filter(User.merchant_id == merchant.id, User.role == UserRole.REVIEWER)
            .first()
        )

        token_op = create_access_token(
            data={
                "sub": str(operator.id),
                "merchant_id": str(merchant.id),
                "role": operator.role.value,
            },
            expires_delta=timedelta(minutes=30),
        )
        token_rev = create_access_token(
            data={
                "sub": str(reviewer.id),
                "merchant_id": str(merchant.id),
                "role": reviewer.role.value,
            },
            expires_delta=timedelta(minutes=30),
        )

        headers_op = {"Authorization": f"Bearer {token_op}"}
        headers_rev = {"Authorization": f"Bearer {token_rev}"}

        # 1. GET resolution summary
        sum_resp = client.get(f"/api/v1/exceptions/{exc.id}/resolution", headers=headers_op)
        assert sum_resp.status_code == 200
        assert sum_resp.json()["data"]["resolution_status"] == "OPEN"

        # 2. POST create proposal
        prop_resp = client.post(
            f"/api/v1/exceptions/{exc.id}/resolution/proposals",
            json={
                "category": "SETTLEMENT_DELAY_CONFIRMED",
                "explanation": "E2E test proposal for settlement delay.",
                "proposed_action": "Wait for next batch cycle.",
                "auto_submit": True,
            },
            headers=headers_op,
        )
        assert prop_resp.status_code == 200
        prop_data = prop_resp.json()["data"]
        proposal_id = prop_data["id"]
        assert prop_data["status"] == "PENDING_APPROVAL"

        # 3. POST approve proposal by reviewer
        appr_resp = client.post(
            f"/api/v1/exceptions/{exc.id}/resolution/proposals/{proposal_id}/approve",
            json={"rationale": "E2E Reviewer approved delay."},
            headers=headers_rev,
        )
        assert appr_resp.status_code == 200
        assert appr_resp.json()["data"]["status"] == "APPROVED"

        # 4. POST resolve exception
        res_resp = client.post(
            f"/api/v1/exceptions/{exc.id}/resolution/resolve",
            json={"confirmation": True, "notes": "Resolved successfully."},
            headers=headers_rev,
        )
        assert res_resp.status_code == 200
        assert res_resp.json()["data"]["resolution_status"] == "RESOLVED"

        # 5. GET resolution history
        hist_resp = client.get(
            f"/api/v1/exceptions/{exc.id}/resolution/history", headers=headers_op
        )
        assert hist_resp.status_code == 200
        events = hist_resp.json()["data"]
        assert len(events) >= 3

        # 6. POST reopen exception
        reopen_resp = client.post(
            f"/api/v1/exceptions/{exc.id}/resolution/reopen",
            json={"reason": "Reopening for E2E verification test cycle."},
            headers=headers_op,
        )
        assert reopen_resp.status_code == 200
        assert reopen_resp.json()["data"]["resolution_status"] == "REOPENED"
    finally:
        db.close()
