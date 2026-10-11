export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiErrorDetail;
}

export interface HealthLivenessData {
  status: string;
  service: string;
  version: string;
  environment: string;
  integrations: {
    razorpay_configured: boolean;
    ai_provider: string;
    llm_configured: boolean;
  };
}

export interface HealthReadinessData {
  status: 'ready' | 'not_ready';
  service: string;
  database: {
    type: string;
    connected: boolean;
    message: string;
  };
  config: {
    environment: string;
    amount_tolerance: number;
    ai_auto_classify_threshold: number;
    ai_review_threshold: number;
  };
}

export type ConnectionState = 'connected' | 'degraded' | 'disconnected' | 'checking';

export type UserRole = 'ADMIN' | 'FINANCE_OPERATOR' | 'REVIEWER';
export type UserStatus = 'ACTIVE' | 'DISABLED';

export interface UserProfile {
  id: string;
  merchant_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  last_login_at: string | null;
  created_at: string;
}

export interface MerchantInfo {
  id: string;
  name: string;
  currency: string;
  timezone: string;
}

export interface LoginResponseData {
  access_token: string;
  token_type: string;
  user: UserProfile;
  merchant: MerchantInfo;
}

export interface CurrentUserResponseData {
  user: UserProfile;
  merchant: MerchantInfo;
}

export interface PaginatedMeta {
  total_items: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginatedMeta;
}

export interface ReconciliationRun {
  id: string;
  merchant_id: string;
  run_type: 'DAILY_SCHEDULED' | 'MANUAL_TRIGGER' | 'RE_RUN' | 'BENCHMARK';
  status: 'STARTED' | 'COMPLETED' | 'FAILED' | 'PARTIAL';
  started_at: string;
  completed_at: string | null;
  total_records: number;
  matched_records: number;
  unmatched_records: number;
  exception_records: number;
  auto_classified_records: number;
  review_required_records: number;
  processing_duration_ms: number | null;
  error_summary: string | null;
  configuration_snapshot: Record<string, unknown> | null;
  created_at: string;
}

export interface ReconciliationResultItem {
  id: string;
  run_id: string;
  merchant_id: string;
  payment_id: string | null;
  settlement_id: string | null;
  match_type: string;
  match_status: string;
  expected_amount: string;
  actual_amount: string;
  difference: string;
  tolerance: string;
  confidence: string;
  explanation: string | null;
  matching_fields: Record<string, unknown> | null;
  created_at: string;
}

export interface TransactionSummary {
  id: string;
  merchant_id: string;
  external_id: string;
  external_order_id: string | null;
  amount: string;
  currency: string;
  status: string;
  payment_method: string;
  captured_at: string | null;
  source_created_at: string;
}

export interface ExceptionSummary {
  id: string;
  merchant_id: string;
  reconciliation_result_id: string;
  exception_type: string;
  severity: string;
  status: string;
  financial_impact: string;
  currency: string;
  description: string;
  created_at: string;
}

export interface IngestionSummary {
  total_records_processed: number;
  inserted_payments: number;
  inserted_settlements: number;
  inserted_items: number;
  inserted_refunds: number;
  inserted_fees: number;
  inserted_adjustments: number;
  skipped_records: number;
  duration_ms: number;
}

export type EvidenceCategory =
  | 'PAYMENT'
  | 'SETTLEMENT'
  | 'REFUND'
  | 'FEE'
  | 'ADJUSTMENT'
  | 'RECONCILIATION'
  | 'AUDIT'
  | 'RELATED_RECORD';

export type EvidenceStrength =
  | 'CONFIRMED'
  | 'CORROBORATED'
  | 'INCOMPLETE'
  | 'CONFLICTING';

export interface EvidenceItem {
  evidence_id: string;
  category: EvidenceCategory;
  source_type: string;
  source_record_id: string | null;
  strength: EvidenceStrength;
  attributes: Record<string, unknown>;
  limitations: string[];
  timestamp: string | null;
}

export interface ReconciliationContext {
  result_id: string;
  run_id: string;
  match_status: string;
  exception_type: string;
  severity: string;
  exception_status: string;
  expected_amount: string;
  actual_amount: string;
  variance: string;
  currency: string;
  tolerance: string;
  explanation: string | null;
  created_at: string;
}

export interface RelatedRecordsSummary {
  payment_ids: string[];
  settlement_item_ids: string[];
  settlement_ids: string[];
  refund_ids: string[];
  fee_ids: string[];
  adjustment_ids: string[];
  audit_event_ids: string[];
}

export interface FinancialEvidenceSummary {
  observed_discrepancy: string;
  expected_amount: string;
  actual_amount: string;
  variance: string;
  currency: string;
  overall_strength: EvidenceStrength;
  cause_established: boolean;
  supported_findings: string[];
  missing_information: string[];
  conflicts: string[];
}

export interface ExceptionEvidenceResponse {
  exception_id: string;
  merchant_id: string;
  reconciliation: ReconciliationContext;
  evidence_items: EvidenceItem[];
  related_records: RelatedRecordsSummary;
  summary: FinancialEvidenceSummary;
}

export type InvestigationStatus = 'COMPLETED' | 'PENDING' | 'FAILED' | 'UNAVAILABLE';

export type CauseAssessment = 'SUPPORTED' | 'PLAUSIBLE' | 'UNDETERMINED';

export interface LikelyCause {
  explanation: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  assessment: CauseAssessment;
}

export interface RecommendedAction {
  action: string;
  reason: string;
  supporting_evidence: string[];
  requires_human_approval: boolean;
}

export interface InvestigationReportData {
  exception_id: string;
  investigation_status: InvestigationStatus;
  observed_discrepancy: string;
  likely_causes: LikelyCause[];
  supporting_evidence: string[];
  contradicting_evidence: string[];
  missing_information: string[];
  recommended_actions: RecommendedAction[];
  requires_human_review: boolean;
  limitations: string[];
  generated_at: string;
}

export interface InvestigationResponse {
  id: string;
  exception_id: string;
  merchant_id: string;
  status: InvestigationStatus;
  provider: string;
  model_name: string;
  prompt_version: string;
  report: InvestigationReportData;
  policy_flags: string[];
  requires_human_review: boolean;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type ResolutionStatus =
  | 'OPEN'
  | 'UNDER_REVIEW'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'RESOLVED'
  | 'REOPENED';

export type ProposalStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'SUPERSEDED';

export type ResolutionCategory =
  | 'FEE_DISCREPANCY_REVIEW'
  | 'SETTLEMENT_DELAY_CONFIRMED'
  | 'DATA_CORRECTION_REQUIRED'
  | 'GATEWAY_INVESTIGATION_REQUESTED'
  | 'INTERNAL_CONFIG_FIX'
  | 'NO_SUPPORTED_RESOLUTION'
  | 'OTHER';

export type ResolutionEventType =
  | 'PROPOSAL_CREATED'
  | 'PROPOSAL_SUBMITTED'
  | 'PROPOSAL_APPROVED'
  | 'PROPOSAL_REJECTED'
  | 'EXCEPTION_RESOLVED'
  | 'EXCEPTION_REOPENED';

export interface ProposalResponse {
  id: string;
  exception_id: string;
  merchant_id: string;
  category: ResolutionCategory;
  explanation: string;
  proposed_action: string;
  supporting_evidence_ids: string[];
  investigation_report_id: string | null;
  status: ProposalStatus;
  created_by_user_id: string;
  created_by_user_name: string | null;
  decision_by_user_id: string | null;
  decision_by_user_name: string | null;
  decision_rationale: string | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResolutionHistoryItem {
  id: string;
  exception_id: string;
  proposal_id: string | null;
  user_id: string;
  user_name: string | null;
  user_role: string | null;
  event_type: ResolutionEventType;
  previous_status: string | null;
  new_status: string | null;
  reason: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ResolutionSummaryResponse {
  exception_id: string;
  merchant_id: string;
  resolution_status: ResolutionStatus;
  active_proposal: ProposalResponse | null;
  resolved_at: string | null;
  can_create_proposal: boolean;
  can_submit_proposal: boolean;
  can_approve_proposal: boolean;
  can_reject_proposal: boolean;
  can_resolve: boolean;
  can_reopen: boolean;
}

export interface CreateProposalPayload {
  category: ResolutionCategory;
  explanation: string;
  proposed_action: string;
  supporting_evidence_ids?: string[];
  investigation_report_id?: string | null;
  auto_submit?: boolean;
}

export interface DecisionPayload {
  rationale: string;
}

export interface ResolveExceptionPayload {
  confirmation: boolean;
  notes?: string;
}

export interface ReopenExceptionPayload {
  reason: string;
}

export interface CurrencyExposure {
  currency: string;
  total_exposure: string;
  exception_count: number;
}

export interface AIInvestigationOverview {
  completed_count: number;
  pending_count: number;
  failed_count: number;
  unavailable_count: number;
  requires_human_review_count: number;
}

export interface DashboardOverviewResponse {
  merchant_id: string;
  total_payments_processed: number;
  matched_records: number;
  unmatched_records: number;
  exception_records: number;
  match_rate_percentage: number;
  total_exposure_by_currency: CurrencyExposure[];
  pending_approvals_count: number;
  exceptions_awaiting_review: number;
  resolved_exceptions_count: number;
  ai_investigations: AIInvestigationOverview;
  last_reconciliation_at: string | null;
}

export interface ExceptionTypeBreakdown {
  exception_type: string;
  count: number;
  total_exposure: string;
  currency: string;
}

export interface ResolutionStatusBreakdown {
  status: string;
  count: number;
}

export interface SeverityBreakdown {
  severity: string;
  count: number;
}

export interface ReconciliationHealthResponse {
  merchant_id: string;
  match_distribution: Record<string, number>;
  exceptions_by_type: ExceptionTypeBreakdown[];
  exposure_by_currency: CurrencyExposure[];
  resolution_status_distribution: ResolutionStatusBreakdown[];
  severity_distribution: SeverityBreakdown[];
}

export interface ReconciliationRunTrendItem {
  run_id: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  total_records: number;
  matched_records: number;
  unmatched_records: number;
  exception_records: number;
  match_rate_percentage: number;
}

export interface ExceptionTrendItem {
  date: string;
  count: number;
  total_exposure: string;
  currency: string;
}

export interface DashboardTrendsResponse {
  merchant_id: string;
  runs_history: ReconciliationRunTrendItem[];
  exception_trends: ExceptionTrendItem[];
}

export interface PendingApprovalItem {
  proposal_id: string;
  exception_id: string;
  exception_type: string;
  severity: string;
  proposal_category: ResolutionCategory;
  proposed_action: string;
  explanation: string;
  financial_impact: string;
  currency: string;
  created_by_user_id: string;
  created_by_user_name: string | null;
  submitted_at: string;
  is_current_user_author: boolean;
  can_current_user_approve: boolean;
}

export interface OperationsQueueItem {
  exception_id: string;
  exception_type: string;
  severity: string;
  status: string;
  resolution_status: string;
  financial_impact: string;
  currency: string;
  first_detected_at: string;
  age_days: number;
  evidence_count: number;
  evidence_strength: string | null;
  ai_investigation_status: string | null;
  ai_requires_human_review: boolean | null;
  has_pending_proposal: boolean;
  active_proposal_id: string | null;
  active_proposal_category: string | null;
}

export interface OperationsQueueResponse {
  items: OperationsQueueItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DemoScenarioItem {
  scenario_key: string;
  title: string;
  description: string;
  exception_type: string;
  available: boolean;
  exception_id: string | null;
  financial_impact: string | null;
  currency: string | null;
  reference_id: string | null;
  tags: string[];
}

export interface DemoScenariosResponse {
  merchant_id: string;
  is_demo_mode: boolean;
  scenarios: DemoScenarioItem[];
  total_available: number;
}

export interface AuditEventItem {
  id: string;
  merchant_id: string;
  exception_id: string | null;
  reconciliation_run_id: string | null;
  actor_type: string;
  actor_id: string | null;
  event_type: string;
  previous_state: string | null;
  new_state: string | null;
  event_metadata: Record<string, unknown> | null;
  created_at: string;
}


