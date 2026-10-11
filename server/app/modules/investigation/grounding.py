"""
Evidence-grounding validator for ReconPilot AI Investigation Engine.
Ensures every evidence reference cited by the model strictly exists in the Phase 05 dossier.
Hallucinated or invalid evidence references are explicitly flagged, pruned, and reported.
"""

from app.modules.evidence.schemas import ExceptionEvidenceResponse
from app.modules.investigation.schemas import InvestigationReportData


class EvidenceGroundingValidator:
    """
    Validates that model citations exist within the closed universe of verified evidence items.
    Prevents hallucination of transaction identifiers, records, or facts.
    """

    @staticmethod
    def extract_valid_evidence_identifiers(dossier: ExceptionEvidenceResponse) -> set[str]:
        """
        Extracts all recognized reference identifiers from the Phase 05 evidence dossier:
        - evidence_id (e.g. 'ev_pay_001', 'ev_recon_001')
        - source_record_id (raw entity UUIDs or gateway IDs)
        - related records list
        """
        valid_ids: set[str] = set()

        for item in dossier.evidence_items:
            if item.evidence_id:
                valid_ids.add(item.evidence_id)
            if item.source_record_id:
                valid_ids.add(str(item.source_record_id))

        # Add reconciliation context IDs
        valid_ids.add(str(dossier.reconciliation.result_id))
        valid_ids.add(str(dossier.reconciliation.run_id))

        # Add related records
        for pid in dossier.related_records.payment_ids:
            valid_ids.add(str(pid))
        for si_id in dossier.related_records.settlement_item_ids:
            valid_ids.add(str(si_id))
        for s_id in dossier.related_records.settlement_ids:
            valid_ids.add(str(s_id))
        for ref_id in dossier.related_records.refund_ids:
            valid_ids.add(str(ref_id))
        for f_id in dossier.related_records.fee_ids:
            valid_ids.add(str(f_id))
        for adj_id in dossier.related_records.adjustment_ids:
            valid_ids.add(str(adj_id))

        return valid_ids

    @classmethod
    def validate_and_sanitize(
        cls, report_data: InvestigationReportData, dossier: ExceptionEvidenceResponse
    ) -> tuple[InvestigationReportData, list[str], list[str]]:
        """
        Sanitizes cited evidence in the report against valid dossier identifiers.

        Returns:
            sanitized_report: Report with pruned or flagged evidence citations.
            pruned_ids: List of invalid or hallucinated IDs that were rejected.
            valid_cited_ids: List of verified evidence IDs actually cited.
        """
        valid_ids = cls.extract_valid_evidence_identifiers(dossier)
        pruned_ids: list[str] = []
        valid_cited_ids: set[str] = set()

        def sanitize_id_list(id_list: list[str]) -> list[str]:
            sanitized: list[str] = []
            for eid in id_list:
                cleaned_id = str(eid).strip()
                if cleaned_id in valid_ids:
                    sanitized.append(cleaned_id)
                    valid_cited_ids.add(cleaned_id)
                else:
                    pruned_ids.append(cleaned_id)
            return sanitized

        # 1. Sanitize report top-level citations
        report_data.supporting_evidence = sanitize_id_list(report_data.supporting_evidence)
        report_data.contradicting_evidence = sanitize_id_list(report_data.contradicting_evidence)

        # 2. Sanitize likely causes citations
        for cause in report_data.likely_causes:
            cause.supporting_evidence = sanitize_id_list(cause.supporting_evidence)
            cause.contradicting_evidence = sanitize_id_list(cause.contradicting_evidence)

        # 3. Sanitize recommended actions citations
        for action in report_data.recommended_actions:
            action.supporting_evidence = sanitize_id_list(action.supporting_evidence)
            # Safe default: always require human approval
            action.requires_human_approval = True

        # 4. If invalid references were detected, document them in limitations
        if pruned_ids:
            unique_pruned = sorted(set(pruned_ids))
            report_data.limitations.append(
                f"[Evidence Policy Alert] The model cited {len(unique_pruned)} unrecognized or hallucinated "
                f"reference(s) which were stripped by the evidence grounding gate: {', '.join(unique_pruned)}."
            )

        # 5. Mirror missing information from authoritative evidence dossier if omitted
        for missing in dossier.summary.missing_information:
            if missing not in report_data.missing_information:
                report_data.missing_information.append(missing)

        # 6. Mirror conflicts from authoritative evidence dossier if omitted
        for conflict in dossier.summary.conflicts:
            conflict_note = f"[Deterministic Conflict] {conflict}"
            if (
                conflict_note not in report_data.limitations
                and conflict not in report_data.limitations
            ):
                report_data.limitations.append(conflict_note)

        return report_data, pruned_ids, sorted(valid_cited_ids)
