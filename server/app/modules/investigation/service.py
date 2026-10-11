"""
Core orchestration service for ReconPilot AI Investigation Engine.
Coordinates evidence retrieval, LLM analysis, grounding validation, policy enforcement,
and database persistence.
"""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import InvestigationStatus
from app.models.exception import ExceptionRecord
from app.models.investigation_report import InvestigationReport
from app.modules.evidence.schemas import ExceptionEvidenceResponse
from app.modules.evidence.service import EvidenceCollector, EvidenceCorrelator
from app.modules.investigation.grounding import EvidenceGroundingValidator
from app.modules.investigation.policy import DeterministicPolicyGate
from app.modules.investigation.providers import (
    InvestigationProviderError,
    ProviderExecutionError,
    ProviderUnavailableError,
    get_investigation_provider,
)
from app.modules.investigation.schemas import (
    InvestigationReportData,
    InvestigationResponse,
    StartInvestigationRequest,
)

logger = logging.getLogger(__name__)


class InvestigationService:
    """
    Coordinates AI investigations for exceptions under strict tenant isolation.
    """

    def __init__(self, db: Session, merchant_id: uuid.UUID):
        self.db = db
        self.merchant_id = merchant_id
        self.settings = get_settings()

    async def run_investigation(
        self,
        exception_id: uuid.UUID,
        request: StartInvestigationRequest | None = None,
    ) -> InvestigationResponse:
        """
        Executes an investigation for the specified exception.
        Adheres to non-mutation rules, evidence grounding, and tenant isolation.
        """
        force_refresh = request.force_refresh if request else False
        notes = request.notes if request else None

        # 1. Enforce tenant isolation: verify exception exists for merchant
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

        # 2. Check for recent existing completed investigation to avoid duplicate runs
        if not force_refresh:
            existing = self.db.scalar(
                select(InvestigationReport)
                .where(
                    InvestigationReport.exception_id == exception_id,
                    InvestigationReport.merchant_id == self.merchant_id,
                    InvestigationReport.status == InvestigationStatus.COMPLETED,
                )
                .order_by(InvestigationReport.created_at.desc())
            )
            if existing:
                return self._to_response(existing)

        # 3. Retrieve Phase 05 evidence dossier
        collector = EvidenceCollector(db=self.db, merchant_id=self.merchant_id)
        raw_evidence = collector.collect(exception_id=exception_id)
        if not raw_evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Authoritative reconciliation result or evidence missing for exception {exception_id}.",
            )
        dossier = EvidenceCorrelator.correlate(raw_evidence)

        # 4. Resolve provider
        provider_name = (self.settings.AI_PROVIDER or "mock").lower()
        model_name = self.settings.LLM_MODEL or "gemini-1.5-pro"
        prompt_version = "v1.0"

        try:
            provider = get_investigation_provider(self.settings)
        except ProviderUnavailableError as err:
            logger.warning(f"AI Provider unavailable for exception {exception_id}: {err}")
            return self._record_unavailable_investigation(
                exception_id=exception_id,
                dossier=dossier,
                provider_name=provider_name,
                model_name=model_name,
                prompt_version=prompt_version,
                error_msg=str(err),
            )

        # 5. Execute analysis
        try:
            report_data = await provider.investigate(dossier=dossier, notes=notes)
        except ProviderUnavailableError as err:
            logger.warning(f"Provider unavailable during call: {err}")
            return self._record_unavailable_investigation(
                exception_id=exception_id,
                dossier=dossier,
                provider_name=provider_name,
                model_name=model_name,
                prompt_version=prompt_version,
                error_msg=str(err),
            )
        except (ProviderExecutionError, InvestigationProviderError, Exception) as err:
            logger.error(f"Provider execution failure: {err}")
            return self._record_failed_investigation(
                exception_id=exception_id,
                dossier=dossier,
                provider_name=provider_name,
                model_name=model_name,
                prompt_version=prompt_version,
                error_msg=str(err),
            )

        # 6. Apply evidence grounding checks
        sanitized_report, pruned_ids, valid_cited_ids = (
            EvidenceGroundingValidator.validate_and_sanitize(report_data, dossier)
        )

        # 7. Apply deterministic policy gate
        enforced_report, policy_flags = DeterministicPolicyGate.evaluate(
            sanitized_report, dossier, pruned_ids
        )

        # 8. Persist report record in PostgreSQL
        record = InvestigationReport(
            merchant_id=self.merchant_id,
            exception_id=exception_id,
            status=InvestigationStatus.COMPLETED,
            provider=provider_name,
            model_name=model_name,
            prompt_version=prompt_version,
            observed_discrepancy=enforced_report.observed_discrepancy,
            report_data=enforced_report.model_dump(mode="json"),
            cited_evidence_ids=valid_cited_ids,
            requires_human_review=enforced_report.requires_human_review,
            policy_flags=policy_flags,
            error_message=None,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return self._to_response(record)

    def get_latest_investigation(
        self,
        exception_id: uuid.UUID,
    ) -> InvestigationResponse | None:
        """
        Retrieves the most recent investigation report for this exception.
        Enforces tenant isolation.
        """
        # Verify exception belongs to merchant
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

        record = self.db.scalar(
            select(InvestigationReport)
            .where(
                InvestigationReport.exception_id == exception_id,
                InvestigationReport.merchant_id == self.merchant_id,
            )
            .order_by(InvestigationReport.created_at.desc())
        )
        if not record:
            return None

        return self._to_response(record)

    def _record_unavailable_investigation(
        self,
        exception_id: uuid.UUID,
        dossier: ExceptionEvidenceResponse,
        provider_name: str,
        model_name: str,
        prompt_version: str,
        error_msg: str,
    ) -> InvestigationResponse:
        empty_report = InvestigationReportData(
            exception_id=exception_id,
            investigation_status=InvestigationStatus.UNAVAILABLE,
            observed_discrepancy=dossier.summary.observed_discrepancy,
            likely_causes=[],
            supporting_evidence=[],
            contradicting_evidence=[],
            missing_information=list(dossier.summary.missing_information),
            recommended_actions=[],
            requires_human_review=True,
            limitations=[f"Investigation provider unavailable: {error_msg}"],
            generated_at=datetime.now(UTC),
        )
        record = InvestigationReport(
            merchant_id=self.merchant_id,
            exception_id=exception_id,
            status=InvestigationStatus.UNAVAILABLE,
            provider=provider_name,
            model_name=model_name,
            prompt_version=prompt_version,
            observed_discrepancy=dossier.summary.observed_discrepancy,
            report_data=empty_report.model_dump(mode="json"),
            cited_evidence_ids=[],
            requires_human_review=True,
            policy_flags=[
                DeterministicPolicyGate.POLICY_NON_MUTATION,
                DeterministicPolicyGate.POLICY_HUMAN_REVIEW_REQUIRED,
            ],
            error_message=error_msg,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def _record_failed_investigation(
        self,
        exception_id: uuid.UUID,
        dossier: ExceptionEvidenceResponse,
        provider_name: str,
        model_name: str,
        prompt_version: str,
        error_msg: str,
    ) -> InvestigationResponse:
        failed_report = InvestigationReportData(
            exception_id=exception_id,
            investigation_status=InvestigationStatus.FAILED,
            observed_discrepancy=dossier.summary.observed_discrepancy,
            likely_causes=[],
            supporting_evidence=[],
            contradicting_evidence=[],
            missing_information=list(dossier.summary.missing_information),
            recommended_actions=[],
            requires_human_review=True,
            limitations=[f"Investigation execution failed: {error_msg}"],
            generated_at=datetime.now(UTC),
        )
        record = InvestigationReport(
            merchant_id=self.merchant_id,
            exception_id=exception_id,
            status=InvestigationStatus.FAILED,
            provider=provider_name,
            model_name=model_name,
            prompt_version=prompt_version,
            observed_discrepancy=dossier.summary.observed_discrepancy,
            report_data=failed_report.model_dump(mode="json"),
            cited_evidence_ids=[],
            requires_human_review=True,
            policy_flags=[
                DeterministicPolicyGate.POLICY_NON_MUTATION,
                DeterministicPolicyGate.POLICY_HUMAN_REVIEW_REQUIRED,
            ],
            error_message=error_msg,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def _to_response(self, record: InvestigationReport) -> InvestigationResponse:
        report_data = InvestigationReportData.model_validate(record.report_data)
        return InvestigationResponse(
            id=record.id,
            exception_id=record.exception_id,
            merchant_id=record.merchant_id,
            status=InvestigationStatus(record.status),
            provider=record.provider,
            model_name=record.model_name,
            prompt_version=record.prompt_version,
            report=report_data,
            policy_flags=record.policy_flags or [],
            requires_human_review=record.requires_human_review,
            error_message=record.error_message,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
