import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  FileText,
  CreditCard,
  Building,
  RotateCcw,
  Receipt,
  Scale,
  ShieldCheck,
  HelpCircle,
  Clock,
  Layers,
  Sparkles,
  RefreshCw,
  UserCheck,
  AlertCircle,
  ShieldAlert,
  Bot,
  Check,
  X,
  Send,
  ThumbsUp,
  ThumbsDown,
  History,
  Shield,
  Lock,
  ArrowRight,
  FileCheck2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';
import { exceptionService, resolutionService } from '@/services/reconciliation';
import {
  EvidenceCategory,
  EvidenceStrength,
  EvidenceItem,
  CauseAssessment,
  InvestigationStatus,
  ResolutionStatus,
  ResolutionCategory,
  ResolutionHistoryItem,
} from '@/types/api';

const categoryIcons: Record<EvidenceCategory, React.ReactNode> = {
  PAYMENT: <CreditCard className="w-4 h-4 text-emerald-600" />,
  SETTLEMENT: <Building className="w-4 h-4 text-blue-600" />,
  REFUND: <RotateCcw className="w-4 h-4 text-purple-600" />,
  FEE: <Receipt className="w-4 h-4 text-amber-600" />,
  ADJUSTMENT: <Scale className="w-4 h-4 text-indigo-600" />,
  RECONCILIATION: <ShieldCheck className="w-4 h-4 text-slate-700" />,
  AUDIT: <Clock className="w-4 h-4 text-cyan-600" />,
  RELATED_RECORD: <Layers className="w-4 h-4 text-rose-600" />,
};

const renderStrengthBadge = (strength: EvidenceStrength) => {
  switch (strength) {
    case 'CONFIRMED':
      return (
        <Badge variant="success" size="sm" className="gap-1 font-semibold">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          Confirmed
        </Badge>
      );
    case 'CORROBORATED':
      return (
        <Badge variant="info" size="sm" className="gap-1 font-semibold">
          <CheckCircle2 className="w-3 h-3 text-blue-600" />
          Corroborated
        </Badge>
      );
    case 'CONFLICTING':
      return (
        <Badge variant="danger" size="sm" className="gap-1 font-semibold">
          <AlertTriangle className="w-3 h-3 text-rose-600" />
          Conflicting
        </Badge>
      );
    case 'INCOMPLETE':
    default:
      return (
        <Badge variant="warning" size="sm" className="gap-1 font-semibold">
          <HelpCircle className="w-3 h-3 text-amber-600" />
          Incomplete
        </Badge>
      );
  }
};

const renderInvestigationStatusBadge = (status?: InvestigationStatus) => {
  switch (status) {
    case 'COMPLETED':
      return (
        <Badge variant="success" size="sm" className="gap-1 font-semibold">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          Analysis Complete
        </Badge>
      );
    case 'PENDING':
      return (
        <Badge variant="info" size="sm" className="gap-1 font-semibold">
          <Clock className="w-3 h-3 text-blue-600 animate-spin" />
          Analyzing
        </Badge>
      );
    case 'FAILED':
      return (
        <Badge variant="danger" size="sm" className="gap-1 font-semibold">
          <AlertTriangle className="w-3 h-3 text-rose-600" />
          Analysis Failed
        </Badge>
      );
    case 'UNAVAILABLE':
    default:
      return (
        <Badge variant="neutral" size="sm" className="gap-1 font-semibold">
          <HelpCircle className="w-3 h-3 text-slate-500" />
          Not Investigated
        </Badge>
      );
  }
};

const renderCauseAssessmentBadge = (assessment: CauseAssessment) => {
  switch (assessment) {
    case 'SUPPORTED':
      return (
        <Badge variant="success" size="sm" className="gap-1 font-semibold">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          Supported by Evidence
        </Badge>
      );
    case 'PLAUSIBLE':
      return (
        <Badge variant="info" size="sm" className="gap-1 font-semibold">
          <HelpCircle className="w-3 h-3 text-blue-600" />
          Plausible Hypothesis
        </Badge>
      );
    case 'UNDETERMINED':
    default:
      return (
        <Badge variant="warning" size="sm" className="gap-1 font-semibold">
          <AlertTriangle className="w-3 h-3 text-amber-600" />
          Cause Undetermined
        </Badge>
      );
  }
};

const renderResolutionStatusBadge = (status?: ResolutionStatus) => {
  switch (status) {
    case 'RESOLVED':
      return (
        <Badge variant="success" size="sm" className="gap-1 font-semibold">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          Resolved
        </Badge>
      );
    case 'APPROVED':
      return (
        <Badge variant="success" size="sm" className="gap-1 font-semibold">
          <ThumbsUp className="w-3 h-3 text-emerald-600" />
          Proposal Approved
        </Badge>
      );
    case 'PENDING_APPROVAL':
      return (
        <Badge variant="warning" size="sm" className="gap-1 font-semibold">
          <Clock className="w-3 h-3 text-amber-600 animate-pulse" />
          Pending Approval
        </Badge>
      );
    case 'UNDER_REVIEW':
      return (
        <Badge variant="info" size="sm" className="gap-1 font-semibold">
          <UserCheck className="w-3 h-3 text-blue-600" />
          Under Review
        </Badge>
      );
    case 'REJECTED':
      return (
        <Badge variant="danger" size="sm" className="gap-1 font-semibold">
          <ThumbsDown className="w-3 h-3 text-rose-600" />
          Proposal Rejected
        </Badge>
      );
    case 'REOPENED':
      return (
        <Badge variant="warning" size="sm" className="gap-1 font-semibold">
          <RotateCcw className="w-3 h-3 text-orange-600" />
          Reopened
        </Badge>
      );
    case 'OPEN':
    default:
      return (
        <Badge variant="neutral" size="sm" className="gap-1 font-semibold">
          <AlertCircle className="w-3 h-3 text-slate-500" />
          Open
        </Badge>
      );
  }
};

const RESOLUTION_CATEGORIES: { id: ResolutionCategory; label: string; desc: string }[] = [
  {
    id: 'FEE_DISCREPANCY_REVIEW',
    label: 'Fee Discrepancy Review',
    desc: 'Contractual fee schedule variance or MDR tier disagreement with payment gateway.',
  },
  {
    id: 'SETTLEMENT_DELAY_CONFIRMED',
    label: 'Settlement Delay Confirmed',
    desc: 'Bank cutoff timing, holiday clearing lag, or acknowledged delayed settlement batch.',
  },
  {
    id: 'DATA_CORRECTION_REQUIRED',
    label: 'Data Correction Required',
    desc: 'Internal data pipeline format mismatch, rounding correction, or duplicate entry.',
  },
  {
    id: 'GATEWAY_INVESTIGATION_REQUESTED',
    label: 'Gateway Investigation Requested',
    desc: 'Official support ticket or dispute initiated with payment aggregator.',
  },
  {
    id: 'INTERNAL_CONFIG_FIX',
    label: 'Internal Config Fix',
    desc: 'Merchant ledger configuration, tolerance profile, or fee rule updated.',
  },
  {
    id: 'NO_SUPPORTED_RESOLUTION',
    label: 'No Supported Resolution',
    desc: 'Variance is unrecoverable or represents an accepted write-off variance.',
  },
  {
    id: 'OTHER',
    label: 'Other Operational Resolution',
    desc: 'Custom operator resolution with detailed business justification.',
  },
];

export const ExceptionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Queries
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['exception-evidence', id],
    queryFn: () => (id ? exceptionService.getExceptionEvidence(id) : Promise.reject(new Error('No ID'))),
    enabled: !!id,
  });

  const {
    data: investigation,
    isLoading: isInvestigationLoading,
  } = useQuery({
    queryKey: ['exception-investigation', id],
    queryFn: () => (id ? exceptionService.getLatestInvestigation(id) : Promise.resolve(null)),
    enabled: !!id,
  });

  const {
    data: resolutionSummary,
  } = useQuery({
    queryKey: ['exception-resolution', id],
    queryFn: () => (id ? resolutionService.getResolutionSummary(id) : Promise.reject(new Error('No ID'))),
    enabled: !!id,
  });

  const {
    data: resolutionHistory = [],
  } = useQuery({
    queryKey: ['exception-resolution-history', id],
    queryFn: () => (id ? resolutionService.getResolutionHistory(id) : Promise.resolve([])),
    enabled: !!id,
  });

  // UI state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createCategory, setCreateCategory] = useState<ResolutionCategory>('FEE_DISCREPANCY_REVIEW');
  const [createExplanation, setCreateExplanation] = useState('');
  const [createProposedAction, setCreateProposedAction] = useState('');
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);
  const [autoSubmit, setAutoSubmit] = useState(true);

  const [isApproveOpen, setIsApproveOpen] = useState(false);
  const [approvalRationale, setApprovalRationale] = useState('Reviewed against verified ledger evidence. Approved.');

  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [rejectionRationale, setRejectionRationale] = useState('');

  const [isResolveOpen, setIsResolveOpen] = useState(false);
  const [resolveConfirmed, setResolveConfirmed] = useState(false);
  const [resolveNotes, setResolveNotes] = useState('');

  const [isReopenOpen, setIsReopenOpen] = useState(false);
  const [reopenReason, setReopenReason] = useState('');

  const [isHistoryExpanded, setIsHistoryExpanded] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const invalidateResolutionQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['exception-resolution', id] });
    queryClient.invalidateQueries({ queryKey: ['exception-resolution-history', id] });
    queryClient.invalidateQueries({ queryKey: ['exception-evidence', id] });
  };

  // Mutations
  const investigateMutation = useMutation({
    mutationFn: (forceRefresh: boolean = true) =>
      id ? exceptionService.startInvestigation(id, { force_refresh: forceRefresh }) : Promise.reject(new Error('No ID')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exception-investigation', id] });
    },
  });

  const createProposalMutation = useMutation({
    mutationFn: (payload: {
      category: ResolutionCategory;
      explanation: string;
      proposed_action: string;
      supporting_evidence_ids: string[];
      auto_submit: boolean;
    }) => {
      if (!id) throw new Error('Missing ID');
      return resolutionService.createProposal(id, payload);
    },
    onSuccess: () => {
      setActionError(null);
      setActionSuccess('Resolution proposal registered successfully.');
      setIsCreateOpen(false);
      invalidateResolutionQueries();
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : 'Failed to create proposal.');
    },
  });

  const submitProposalMutation = useMutation({
    mutationFn: (proposalId: string) => {
      if (!id) throw new Error('Missing ID');
      return resolutionService.submitProposal(id, proposalId);
    },
    onSuccess: () => {
      setActionError(null);
      setActionSuccess('Proposal submitted for peer review.');
      invalidateResolutionQueries();
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : 'Failed to submit proposal.');
    },
  });

  const approveProposalMutation = useMutation({
    mutationFn: (params: { proposalId: string; rationale: string }) => {
      if (!id) throw new Error('Missing ID');
      return resolutionService.approveProposal(id, params.proposalId, { rationale: params.rationale });
    },
    onSuccess: () => {
      setActionError(null);
      setActionSuccess('Proposal approved successfully.');
      setIsApproveOpen(false);
      invalidateResolutionQueries();
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : 'Failed to approve proposal.');
    },
  });

  const rejectProposalMutation = useMutation({
    mutationFn: (params: { proposalId: string; rationale: string }) => {
      if (!id) throw new Error('Missing ID');
      return resolutionService.rejectProposal(id, params.proposalId, { rationale: params.rationale });
    },
    onSuccess: () => {
      setActionError(null);
      setActionSuccess('Proposal rejected with recorded rationale.');
      setIsRejectOpen(false);
      invalidateResolutionQueries();
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : 'Failed to reject proposal.');
    },
  });

  const resolveExceptionMutation = useMutation({
    mutationFn: (params: { notes: string }) => {
      if (!id) throw new Error('Missing ID');
      return resolutionService.resolveException(id, {
        confirmation: true,
        notes: params.notes,
      });
    },
    onSuccess: () => {
      setActionError(null);
      setActionSuccess('Exception officially marked as Resolved.');
      setIsResolveOpen(false);
      invalidateResolutionQueries();
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : 'Failed to resolve exception.');
    },
  });

  const reopenExceptionMutation = useMutation({
    mutationFn: (params: { reason: string }) => {
      if (!id) throw new Error('Missing ID');
      return resolutionService.reopenException(id, { reason: params.reason });
    },
    onSuccess: () => {
      setActionError(null);
      setActionSuccess('Exception reopened with justification recorded.');
      setIsReopenOpen(false);
      invalidateResolutionQueries();
    },
    onError: (err: unknown) => {
      setActionError(err instanceof Error ? err.message : 'Failed to reopen exception.');
    },
  });

  // Pre-fill from AI Recommendation
  const handleImportFromAI = () => {
    if (investigation?.report.recommended_actions && investigation.report.recommended_actions.length > 0) {
      const rec = investigation.report.recommended_actions[0];
      setCreateProposedAction(rec.action);
      setCreateExplanation(rec.reason || 'Aligned with AI investigation findings.');
      if (rec.supporting_evidence && rec.supporting_evidence.length > 0) {
        setSelectedEvidenceIds(rec.supporting_evidence);
      }
    }
  };

  const toggleEvidenceSelection = (evId: string) => {
    setSelectedEvidenceIds((prev) =>
      prev.includes(evId) ? prev.filter((item) => item !== evId) : [...prev, evId]
    );
  };

  const activeProposal = resolutionSummary?.active_proposal;
  const isAuthor = Boolean(activeProposal && user?.id === activeProposal.created_by_user_id);
  const isReviewerOrAdmin = user?.role === 'REVIEWER' || user?.role === 'ADMIN';
  const canDecideProposal = isReviewerOrAdmin && !isAuthor;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Navigation */}
      <div className="flex items-center gap-2 mb-2">
        <Link to="/exceptions">
          <Button variant="ghost" size="sm" className="gap-1 text-finance-600 hover:text-finance-900">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Exceptions Queue
          </Button>
        </Link>
      </div>

      <PageHeader
        title="Financial Discrepancy Evidence Dossier"
        description={`Authoritative reconciliation result, linked source records, and correlation evidence for Exception #${id || 'Unknown'}.`}
        badgeText={data ? data.reconciliation.exception_type : 'Case File'}
        badgeVariant="warning"
      />

      {isLoading && <LoadingState message="Collecting and correlating financial evidence from PostgreSQL..." />}

      {isError && (
        <ErrorState
          title="Failed to Load Financial Evidence"
          message={error instanceof Error ? error.message : 'Error retrieving exception record'}
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <div className="space-y-6">
          {/* Action alerts */}
          {actionSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-xs text-emerald-800">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>{actionSuccess}</span>
              </div>
              <button onClick={() => setActionSuccess(null)} className="text-emerald-600 hover:text-emerald-900">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {actionError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center justify-between text-xs text-rose-800">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>{actionError}</span>
              </div>
              <button onClick={() => setActionError(null)} className="text-rose-600 hover:text-rose-900">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* 1. Primary Discrepancy Summary Card */}
          <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-finance-700/60">
              <div className="space-y-2 max-w-3xl">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-finance-400 uppercase tracking-wider">
                    Observed Discrepancy
                  </span>
                  {renderStrengthBadge(data.summary.overall_strength)}
                  {data.summary.cause_established && (
                    <Badge variant="neutral" size="sm" className="bg-emerald-950/60 text-emerald-300 border-emerald-800/40">
                      Cause Established
                    </Badge>
                  )}
                  {resolutionSummary && renderResolutionStatusBadge(resolutionSummary.resolution_status)}
                </div>
                <h3 className="text-base font-bold text-finance-100 leading-snug">
                  {data.summary.observed_discrepancy}
                </h3>
                <p className="text-xs text-finance-400 font-mono">
                  Exception Case ID: <span className="font-semibold text-finance-200">{data.exception_id}</span>
                </p>
              </div>

              {/* Financial Variance Pill Box */}
              <div className="grid grid-cols-3 gap-3 bg-finance-900 p-4 rounded-lg border border-finance-700/80 font-mono text-center">
                <div>
                  <div className="text-[10px] uppercase font-semibold text-finance-400">Expected Settlement</div>
                  <div className="text-sm font-bold text-finance-100">
                    ₹{parseFloat(data.reconciliation.expected_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-semibold text-finance-400">Actual Credit</div>
                  <div className="text-sm font-bold text-finance-100">
                    ₹{parseFloat(data.reconciliation.actual_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-semibold text-finance-400">Discrepancy Variance</div>
                  <div
                    className={`text-sm font-bold ${
                      parseFloat(data.reconciliation.variance) !== 0 ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    ₹{parseFloat(data.reconciliation.variance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>
            </div>

            {/* Findings & Information Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 text-xs">
              <div className="space-y-2">
                <h4 className="font-bold text-emerald-300 flex items-center gap-1.5 uppercase text-[11px] tracking-wide">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Corroborated Facts ({data.summary.supported_findings.length})
                </h4>
                {data.summary.supported_findings.length > 0 ? (
                  <ul className="space-y-1.5 text-finance-200">
                    {data.summary.supported_findings.map((f, i) => (
                      <li key={i} className="bg-emerald-950/30 p-2 rounded border border-emerald-800/40 leading-relaxed text-finance-200">
                        {f}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-finance-400 italic">No facts corroborated yet.</p>
                )}
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-amber-300 flex items-center gap-1.5 uppercase text-[11px] tracking-wide">
                  <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
                  Missing Information ({data.summary.missing_information.length})
                </h4>
                {data.summary.missing_information.length > 0 ? (
                  <ul className="space-y-1.5 text-finance-200">
                    {data.summary.missing_information.map((m, i) => (
                      <li key={i} className="bg-amber-950/30 p-2 rounded border border-amber-800/40 leading-relaxed text-finance-200">
                        {m}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-finance-400 italic">No missing information detected.</p>
                )}
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-rose-300 flex items-center gap-1.5 uppercase text-[11px] tracking-wide">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                  Direct Conflicts ({data.summary.conflicts.length})
                </h4>
                {data.summary.conflicts.length > 0 ? (
                  <ul className="space-y-1.5 text-finance-200">
                    {data.summary.conflicts.map((c, i) => (
                      <li key={i} className="bg-rose-950/30 p-2 rounded border border-rose-800/40 leading-relaxed text-finance-200">
                        {c}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-finance-400 italic">No contradictory records found.</p>
                )}
              </div>
            </div>
          </Card>

          {/* 2. AI Root Cause Investigation Card (Phase 06) */}
          <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-finance-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-finance-900/60">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-brand-primary/10 text-brand-accent rounded-lg border border-brand-primary/20">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-bold text-finance-100">
                      AI Root Cause Investigation Service
                    </h3>
                    {renderInvestigationStatusBadge(investigation?.status)}
                    {investigation && (
                      <Badge
                        variant={investigation.provider === 'mock' ? 'neutral' : 'info'}
                        size="sm"
                        className="font-mono text-[10px] py-0 px-1.5"
                      >
                        {investigation.provider === 'mock' ? 'Deterministic Mock Provider' : `Live Provider (${investigation.provider})`}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-finance-400">
                    Evidence-grounded, schema-constrained diagnostic report for finance operators. Zero automated mutations.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => investigateMutation.mutate(true)}
                  disabled={investigateMutation.isPending || isInvestigationLoading}
                  className="gap-1.5 text-xs text-finance-200"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${investigateMutation.isPending ? 'animate-spin' : ''}`} />
                  {investigation ? 'Re-run Investigation' : 'Run AI Investigation'}
                </Button>
              </div>
            </div>

            <div className="p-6">
              {isInvestigationLoading && (
                <div className="py-8 text-center text-xs text-finance-400">
                  <Clock className="w-5 h-5 mx-auto mb-2 animate-spin text-brand-accent" />
                  Loading investigation analysis...
                </div>
              )}

              {!isInvestigationLoading && !investigation && (
                <div className="py-8 text-center border-2 border-dashed border-finance-700/80 rounded-lg">
                  <Sparkles className="w-8 h-8 mx-auto mb-2 text-finance-500" />
                  <h4 className="text-sm font-semibold text-finance-200">No Investigation Report Yet</h4>
                  <p className="text-xs text-finance-400 max-w-md mx-auto mt-1 mb-4">
                    Trigger an automated diagnostic run to extract likely root causes and recommended resolutions grounded strictly in verified evidence.
                  </p>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => investigateMutation.mutate(false)}
                    disabled={investigateMutation.isPending}
                    className="gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    Generate Root Cause Investigation
                  </Button>
                </div>
              )}

              {!isInvestigationLoading && investigation && (
                <div className="space-y-6">
                  {/* Human review policy banner */}
                  {investigation.requires_human_review && (
                    <div className="p-3 bg-amber-950/40 rounded-lg border border-amber-800/50 flex items-start gap-2 text-xs text-amber-300">
                      <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-amber-200">Human Operator Review Required: </span>
                        AI analysis is assistive and advisory. Under financial governance rules, all proposed resolutions require human review and approval.
                      </div>
                    </div>
                  )}

                  {/* Likely Root Causes */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-finance-300 flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 text-brand-accent" />
                      Evaluated Hypotheses & Causes ({investigation.report.likely_causes.length})
                    </h4>
                    <div className="grid grid-cols-1 gap-3">
                      {investigation.report.likely_causes.map((cause, idx) => (
                        <div key={idx} className="p-3.5 rounded-lg border border-finance-700/80 bg-finance-900/60 space-y-2">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-semibold text-finance-200">
                              Hypothesis {idx + 1}: {cause.explanation}
                            </span>
                            {renderCauseAssessmentBadge(cause.assessment)}
                          </div>
                          {cause.supporting_evidence.length > 0 && (
                            <div className="text-[11px] text-finance-400 flex items-center gap-1.5 flex-wrap">
                              <span className="font-semibold text-finance-300">Citing Evidence:</span>
                              {cause.supporting_evidence.map((ev, i) => (
                                <Badge key={i} variant="neutral" size="sm" className="font-mono text-[10px] bg-finance-800 text-finance-300 border-finance-700">
                                  {ev}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommended Actions */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-finance-300 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Recommended Operational Next Steps ({investigation.report.recommended_actions.length})
                    </h4>
                    <div className="space-y-2">
                      {investigation.report.recommended_actions.map((act, idx) => (
                        <div key={idx} className="p-3 rounded-lg border border-emerald-900/50 bg-emerald-950/20 flex items-start justify-between gap-4">
                          <div className="space-y-1">
                            <div className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                              <ArrowRight className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                              {act.action}
                            </div>
                            <p className="text-xs text-finance-300 pl-5">{act.reason}</p>
                          </div>
                          {act.requires_human_approval && (
                            <Badge variant="warning" size="sm" className="flex-shrink-0 text-[10px]">
                              Review Required
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Metadata and provenance footer */}
                  <div className="pt-3 border-t border-finance-700/60 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-finance-500">
                    <div>
                      PROVIDER: <span className="font-semibold text-finance-400">{investigation.provider}</span> &bull; MODEL: <span className="font-semibold text-finance-400">{investigation.model_name}</span> &bull; PROMPT: <span className="font-semibold text-finance-400">{investigation.prompt_version}</span>
                    </div>
                    <div>ANALYZED: {new Date(investigation.created_at).toLocaleString()}</div>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* 3. HUMAN APPROVAL & EXCEPTION RESOLUTION WORKFLOW (PHASE 07) */}
          <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-finance-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-finance-900/60">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-finance-900 text-white rounded-lg border border-finance-700 shadow-sm">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-finance-100">
                      Human Approval & Exception Resolution Workflow
                    </h3>
                    {resolutionSummary && renderResolutionStatusBadge(resolutionSummary.resolution_status)}
                  </div>
                  <p className="text-xs text-finance-400">
                    Dual-control review governance with separation of duties and zero automated financial mutation.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsHistoryExpanded(!isHistoryExpanded)}
                  className="gap-1.5 text-xs text-finance-200"
                >
                  <History className="w-3.5 h-3.5 text-finance-400" />
                  Audit Trail ({resolutionHistory.length})
                  {isHistoryExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </Button>
              </div>
            </div>

            {/* Lifecycle Progression Stepper */}
            <div className="p-4 bg-finance-900/40 border-b border-finance-700/60">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                {/* Step 1: Open / Under Review */}
                <div
                  className={`p-2.5 rounded-md border flex items-center gap-2 ${
                    resolutionSummary?.resolution_status === 'OPEN' ||
                    resolutionSummary?.resolution_status === 'UNDER_REVIEW'
                      ? 'bg-blue-950/40 border-blue-800/60 text-blue-300 font-semibold'
                      : 'bg-finance-900 border-finance-700/80 text-finance-400'
                  }`}
                >
                  <div className="w-5 h-5 rounded-full bg-blue-900/60 text-blue-300 flex items-center justify-center font-bold text-[10px]">
                    1
                  </div>
                  <div>
                    <div className="text-[11px] font-bold">Investigation</div>
                    <div className="text-[10px] text-finance-400">Evidence assembled</div>
                  </div>
                </div>

                {/* Step 2: Resolution Proposed */}
                <div
                  className={`p-2.5 rounded-md border flex items-center gap-2 ${
                    resolutionSummary?.resolution_status === 'PENDING_APPROVAL'
                      ? 'bg-amber-950/40 border-amber-800/60 text-amber-300 font-semibold'
                      : activeProposal
                      ? 'bg-finance-900 border-finance-700/80 text-finance-200'
                      : 'bg-finance-900 border-finance-700/80 text-finance-500'
                  }`}
                >
                  <div className="w-5 h-5 rounded-full bg-amber-900/60 text-amber-300 flex items-center justify-center font-bold text-[10px]">
                    2
                  </div>
                  <div>
                    <div className="text-[11px] font-bold">Proposal Submitted</div>
                    <div className="text-[10px] text-finance-400">Awaiting reviewer</div>
                  </div>
                </div>

                {/* Step 3: Peer Approved */}
                <div
                  className={`p-2.5 rounded-md border flex items-center gap-2 ${
                    resolutionSummary?.resolution_status === 'APPROVED'
                      ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300 font-semibold'
                      : resolutionSummary?.resolution_status === 'REJECTED'
                      ? 'bg-rose-950/40 border-rose-800/60 text-rose-300'
                      : 'bg-finance-900 border-finance-700/80 text-finance-500'
                  }`}
                >
                  <div className="w-5 h-5 rounded-full bg-emerald-900/60 text-emerald-300 flex items-center justify-center font-bold text-[10px]">
                    3
                  </div>
                  <div>
                    <div className="text-[11px] font-bold">Reviewer Decision</div>
                    <div className="text-[10px] text-finance-400">Separation of duties</div>
                  </div>
                </div>

                {/* Step 4: Confirmed Resolved */}
                <div
                  className={`p-2.5 rounded-md border flex items-center gap-2 ${
                    resolutionSummary?.resolution_status === 'RESOLVED'
                      ? 'bg-emerald-950/50 border-emerald-600 text-emerald-200 font-bold'
                      : resolutionSummary?.resolution_status === 'REOPENED'
                      ? 'bg-orange-950/40 border-orange-800/60 text-orange-300 font-semibold'
                      : 'bg-finance-900 border-finance-700/80 text-finance-500'
                  }`}
                >
                  <div className="w-5 h-5 rounded-full bg-finance-800 text-finance-300 flex items-center justify-center font-bold text-[10px]">
                    4
                  </div>
                  <div>
                    <div className="text-[11px] font-bold">Final Resolution</div>
                    <div className="text-[10px] text-finance-400">Immutable sign-off</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Financial Non-Mutation Disclaimer Banner */}
              <div className="p-3 bg-finance-900 border border-finance-700/80 rounded-lg flex items-center justify-between text-[11px] text-finance-300 font-mono">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-finance-400 flex-shrink-0" />
                  <span>
                    GOVERNANCE GUARANTEE: Approving or resolving an exception records an authoritative operational decision. It does NOT initiate money movements, payout adjustments, or automated refund transactions.
                  </span>
                </div>
              </div>

              {/* Active Proposal Card (if one exists) */}
              {activeProposal && (
                <div className="border border-finance-700/80 rounded-lg p-5 space-y-4 bg-finance-900/80 shadow-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-finance-700/60 pb-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-finance-100 uppercase tracking-wide">
                          Active Resolution Proposal
                        </span>
                        <Badge
                          variant={
                            activeProposal.status === 'APPROVED'
                              ? 'success'
                              : activeProposal.status === 'REJECTED'
                              ? 'danger'
                              : 'warning'
                          }
                          size="sm"
                        >
                          {activeProposal.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-finance-300 font-semibold">
                        Category: {activeProposal.category.replace(/_/g, ' ')}
                      </p>
                    </div>

                    <div className="text-right text-[11px] text-finance-400 font-mono">
                      <div>Created by: <span className="font-semibold text-finance-200">{activeProposal.created_by_user_name || activeProposal.created_by_user_id}</span></div>
                      <div>{new Date(activeProposal.created_at).toLocaleString()}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="space-y-1">
                      <span className="font-bold text-finance-300 uppercase text-[10px]">Business Rationale & Explanation</span>
                      <p className="p-2.5 bg-finance-950 rounded border border-finance-800 text-finance-200 leading-relaxed">
                        {activeProposal.explanation}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <span className="font-bold text-finance-300 uppercase text-[10px]">Proposed Operational Action</span>
                      <p className="p-2.5 bg-finance-950 rounded border border-finance-800 text-finance-200 leading-relaxed">
                        {activeProposal.proposed_action}
                      </p>
                    </div>
                  </div>

                  {/* Supporting Evidence Citations */}
                  {activeProposal.supporting_evidence_ids.length > 0 && (
                    <div className="space-y-1 text-xs">
                      <span className="font-bold text-finance-300 uppercase text-[10px]">Cited Verified Evidence Items</span>
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {activeProposal.supporting_evidence_ids.map((evId) => (
                          <Badge key={evId} variant="neutral" size="sm" className="font-mono text-[10px] bg-finance-800 border-finance-700 text-finance-300">
                            {evId}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reviewer Decision Details if Decided */}
                  {activeProposal.decided_at && (
                    <div className="p-3 bg-finance-950/60 rounded-lg border border-finance-700/80 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-finance-200 flex items-center gap-1.5">
                          {activeProposal.status === 'APPROVED' ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                          )}
                          Reviewer Decision by {activeProposal.decision_by_user_name || activeProposal.decision_by_user_id}
                        </span>
                        <span className="text-[11px] font-mono text-finance-400">
                          {new Date(activeProposal.decided_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-finance-300 italic pl-5">
                        &ldquo;{activeProposal.decision_rationale}&rdquo;
                      </p>
                    </div>
                  )}

                  {/* SEPARATION OF DUTIES WARNING */}
                  {activeProposal.status === 'PENDING_APPROVAL' && isAuthor && (
                    <div className="p-3 bg-amber-950/40 rounded-lg border border-amber-800/50 flex items-start gap-2.5 text-xs text-amber-300">
                      <Lock className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-amber-200">Separation of Duties Policy Enforced: </span>
                        You authored this resolution proposal. Under accounting compliance controls, the proposal creator is strictly prohibited from approving or rejecting their own submission. An authorized peer Reviewer or Admin must perform the review.
                      </div>
                    </div>
                  )}

                  {/* Proposal Actions Bar */}
                  <div className="pt-2 border-t border-finance-700/60 flex flex-wrap items-center justify-between gap-3">
                    {/* Draft proposal submission */}
                    {activeProposal.status === 'DRAFT' && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => submitProposalMutation.mutate(activeProposal.id)}
                        disabled={submitProposalMutation.isPending}
                        className="gap-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        Submit Proposal for Peer Review
                      </Button>
                    )}

                    {/* Reviewer Decisions (Only enabled when user is not author and has role Reviewer/Admin) */}
                    {activeProposal.status === 'PENDING_APPROVAL' && (
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => setIsApproveOpen(true)}
                          disabled={!canDecideProposal || approveProposalMutation.isPending}
                          className="gap-1.5 bg-emerald-600 hover:bg-emerald-700"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                          Approve Proposal
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => setIsRejectOpen(true)}
                          disabled={!canDecideProposal || rejectProposalMutation.isPending}
                          className="gap-1.5"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                          Reject Proposal
                        </Button>
                      </div>
                    )}

                    {/* Final Resolution Confirmation (When Approved) */}
                    {resolutionSummary?.resolution_status === 'APPROVED' && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => setIsResolveOpen(true)}
                        disabled={resolveExceptionMutation.isPending}
                        className="gap-1.5 bg-emerald-700 hover:bg-emerald-800"
                      >
                        <FileCheck2 className="w-3.5 h-3.5" />
                        Confirm Final Resolution
                      </Button>
                    )}

                    {/* Option to create a revised proposal if rejected */}
                    {activeProposal.status === 'REJECTED' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setIsCreateOpen(true)}
                        className="gap-1.5 text-finance-200"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        Create Revised Proposal
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {/* No proposal yet - Prompt to create */}
              {!activeProposal && resolutionSummary?.resolution_status !== 'RESOLVED' && (
                <div className="py-8 text-center border-2 border-dashed border-finance-700/80 rounded-lg space-y-3 bg-finance-900/60">
                  <FileText className="w-8 h-8 mx-auto text-finance-500" />
                  <div>
                    <h4 className="text-sm font-semibold text-finance-200">No Resolution Proposal Submitted</h4>
                    <p className="text-xs text-finance-400 max-w-md mx-auto mt-1">
                      Finance operators can propose an evidence-backed resolution for reviewer approval.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => setIsCreateOpen(true)}
                    className="gap-1.5"
                  >
                    <FileText className="w-4 h-4" />
                    Propose Resolution
                  </Button>
                </div>
              )}

              {/* Resolved State Box */}
              {resolutionSummary?.resolution_status === 'RESOLVED' && (
                <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-emerald-600 text-white flex items-center justify-center">
                      <Check className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-emerald-950">Exception Formally Resolved</h4>
                      <p className="text-xs text-emerald-800">
                        Resolution verified and locked in immutable history on{' '}
                        {resolutionSummary.resolved_at ? new Date(resolutionSummary.resolved_at).toLocaleString() : 'N/A'}.
                      </p>
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setIsReopenOpen(true)}
                    className="gap-1.5 text-xs text-finance-700 hover:text-finance-900 border-emerald-300"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-orange-600" />
                    Reopen Exception
                  </Button>
                </div>
              )}

              {/* Reopened State Alert */}
              {resolutionSummary?.resolution_status === 'REOPENED' && (
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <RotateCcw className="w-6 h-6 text-orange-600 flex-shrink-0" />
                    <div>
                      <h4 className="text-sm font-bold text-orange-950">Exception Reopened for Re-evaluation</h4>
                      <p className="text-xs text-orange-800">
                        New financial discrepancy or ledger reversal reported. A new resolution proposal is required.
                      </p>
                    </div>
                  </div>

                  {!activeProposal && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => setIsCreateOpen(true)}
                      className="gap-1.5"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Draft New Proposal
                    </Button>
                  )}
                </div>
              )}

              {/* CREATE PROPOSAL MODAL / PANEL */}
              {isCreateOpen && (
                <div className="p-5 border-2 border-brand-primary/30 rounded-lg bg-finance-50/70 space-y-4">
                  <div className="flex items-center justify-between border-b border-finance-200 pb-2">
                    <h4 className="text-sm font-bold text-finance-900 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-brand-primary" />
                      Create Resolution Proposal
                    </h4>
                    <div className="flex items-center gap-2">
                      {investigation?.report.recommended_actions && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleImportFromAI}
                          className="text-xs text-brand-primary hover:text-brand-accent gap-1"
                        >
                          <Sparkles className="w-3 h-3" />
                          Import AI Recommendation
                        </Button>
                      )}
                      <button onClick={() => setIsCreateOpen(false)} className="text-finance-400 hover:text-finance-600">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4 text-xs">
                    {/* Category */}
                    <div>
                      <label className="block font-bold text-finance-300 mb-1">Resolution Category</label>
                      <select
                        value={createCategory}
                        onChange={(e) => setCreateCategory(e.target.value as ResolutionCategory)}
                        className="w-full p-2 bg-finance-900 border border-finance-700/80 rounded text-xs text-finance-200 focus:outline-none focus:ring-1 focus:ring-brand-accent"
                      >
                        {RESOLUTION_CATEGORIES.map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.label} — {cat.desc}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Explanation */}
                    <div>
                      <label className="block font-bold text-finance-300 mb-1">
                        Business Rationale & Explanation (min 5 chars)
                      </label>
                      <textarea
                        rows={3}
                        value={createExplanation}
                        onChange={(e) => setCreateExplanation(e.target.value)}
                        placeholder="Explain why this resolution is justified by the evidence..."
                        className="w-full p-2 bg-finance-900 border border-finance-700/80 rounded text-xs text-finance-200 placeholder:text-finance-500 focus:outline-none focus:ring-1 focus:ring-brand-accent"
                      />
                    </div>

                    {/* Proposed Action */}
                    <div>
                      <label className="block font-bold text-finance-300 mb-1">
                        Recommended Operational Next Step (min 5 chars)
                      </label>
                      <input
                        type="text"
                        value={createProposedAction}
                        onChange={(e) => setCreateProposedAction(e.target.value)}
                        placeholder="e.g. Request gateway credit note, adjust internal accounting schedule, etc."
                        className="w-full p-2 bg-finance-900 border border-finance-700/80 rounded text-xs text-finance-200 placeholder:text-finance-500 focus:outline-none focus:ring-1 focus:ring-brand-accent"
                      />
                    </div>

                    {/* Select Verified Evidence Items */}
                    <div>
                      <label className="block font-bold text-finance-300 mb-1">
                        Attach Supporting Evidence from Dossier ({data.evidence_items.length} available)
                      </label>
                      <div className="max-h-36 overflow-y-auto border border-finance-700/80 rounded p-2 bg-finance-900 space-y-1">
                        {data.evidence_items.map((ev: EvidenceItem) => {
                          const isSelected = selectedEvidenceIds.includes(ev.evidence_id);
                          return (
                            <label
                              key={ev.evidence_id}
                              className={`flex items-center gap-2 p-1.5 rounded cursor-pointer text-[11px] ${
                                isSelected ? 'bg-brand-primary/20 text-brand-accent font-semibold' : 'hover:bg-finance-800 text-finance-300'
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleEvidenceSelection(ev.evidence_id)}
                                className="rounded text-brand-accent"
                              />
                              <span className="font-mono text-[10px] uppercase font-bold text-finance-400">[{ev.category}]</span>
                              <span>{ev.evidence_id} &bull; {ev.source_type}</span>
                            </label>
                          );
                        })}
                      </div>
                    </div>

                    {/* Auto-submit checkbox */}
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="autoSubmitCheck"
                        checked={autoSubmit}
                        onChange={(e) => setAutoSubmit(e.target.checked)}
                        className="rounded text-brand-accent"
                      />
                      <label htmlFor="autoSubmitCheck" className="text-xs text-finance-300 cursor-pointer">
                        Submit immediately for peer reviewer approval (otherwise save as Draft)
                      </label>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-finance-700/60">
                    <Button variant="ghost" size="sm" onClick={() => setIsCreateOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={
                        createExplanation.trim().length < 5 ||
                        createProposedAction.trim().length < 5 ||
                        createProposalMutation.isPending
                      }
                      onClick={() =>
                        createProposalMutation.mutate({
                          category: createCategory,
                          explanation: createExplanation.trim(),
                          proposed_action: createProposedAction.trim(),
                          supporting_evidence_ids: selectedEvidenceIds,
                          auto_submit: autoSubmit,
                        })
                      }
                      className="gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                      {autoSubmit ? 'Submit Proposal' : 'Save as Draft'}
                    </Button>
                  </div>
                </div>
              )}

              {/* APPROVE PROPOSAL DIALOG */}
              {isApproveOpen && activeProposal && (
                <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-emerald-300 flex items-center gap-1.5">
                      <ThumbsUp className="w-4 h-4 text-emerald-400" />
                      Approve Resolution Proposal
                    </h4>
                    <button onClick={() => setIsApproveOpen(false)} className="text-emerald-400 hover:text-emerald-200">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-emerald-300/80">
                    As an authorized Reviewer, confirm that you have verified the supporting evidence.
                  </p>
                  <div>
                    <label className="block text-xs font-semibold text-emerald-200 mb-1">
                      Approval Rationale / Verification Notes:
                    </label>
                    <input
                      type="text"
                      value={approvalRationale}
                      onChange={(e) => setApprovalRationale(e.target.value)}
                      placeholder="e.g. Verified with gateway support portal..."
                      className="w-full p-2 bg-finance-900 border border-emerald-700/80 rounded text-xs text-finance-100 placeholder:text-finance-500 focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="ghost" onClick={() => setIsApproveOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={approvalRationale.trim().length < 3 || approveProposalMutation.isPending}
                      onClick={() =>
                        approveProposalMutation.mutate({
                          proposalId: activeProposal.id,
                          rationale: approvalRationale.trim(),
                        })
                      }
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      Confirm Approval
                    </Button>
                  </div>
                </div>
              )}

              {/* REJECT PROPOSAL DIALOG */}
              {isRejectOpen && activeProposal && (
                <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-rose-300 flex items-center gap-1.5">
                      <ThumbsDown className="w-4 h-4 text-rose-400" />
                      Reject Resolution Proposal
                    </h4>
                    <button onClick={() => setIsRejectOpen(false)} className="text-rose-400 hover:text-rose-200">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-rose-300/80">
                    A clear reason is mandatory when rejecting a proposal to inform the operator of required revisions.
                  </p>
                  <div>
                    <label className="block text-xs font-semibold text-rose-200 mb-1">
                      Mandatory Rejection Rationale (min 3 chars):
                    </label>
                    <textarea
                      rows={2}
                      value={rejectionRationale}
                      onChange={(e) => setRejectionRationale(e.target.value)}
                      placeholder="Explain why this proposal is rejected and what evidence or action is required..."
                      className="w-full p-2 bg-finance-900 border border-rose-700/80 rounded text-xs text-finance-100 placeholder:text-finance-500 focus:ring-1 focus:ring-rose-500"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="ghost" onClick={() => setIsRejectOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      disabled={rejectionRationale.trim().length < 3 || rejectProposalMutation.isPending}
                      onClick={() =>
                        rejectProposalMutation.mutate({
                          proposalId: activeProposal.id,
                          rationale: rejectionRationale.trim(),
                        })
                      }
                    >
                      Confirm Rejection
                    </Button>
                  </div>
                </div>
              )}

              {/* CONFIRM FINAL RESOLUTION DIALOG */}
              {isResolveOpen && (
                <div className="p-4 bg-emerald-950/40 border border-emerald-700/80 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-emerald-300 flex items-center gap-1.5">
                      <FileCheck2 className="w-4 h-4 text-emerald-400" />
                      Confirm Final Resolution
                    </h4>
                    <button onClick={() => setIsResolveOpen(false)} className="text-emerald-400 hover:text-emerald-200">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-emerald-300/80">
                    Final confirmation marks this exception resolved in the system ledger.
                  </p>
                  <label className="flex items-start gap-2 p-2 bg-finance-900 rounded border border-emerald-800/60 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={resolveConfirmed}
                      onChange={(e) => setResolveConfirmed(e.target.checked)}
                      className="rounded text-emerald-500 mt-0.5"
                    />
                    <span className="text-xs text-emerald-200 font-medium">
                      I confirm that all financial discrepancies have been verified against immutable evidence and approved by peer review. No automatic money movements will occur.
                    </span>
                  </label>
                  <div>
                    <label className="block text-xs font-semibold text-emerald-200 mb-1">
                      Optional Closing Operational Notes:
                    </label>
                    <input
                      type="text"
                      value={resolveNotes}
                      onChange={(e) => setResolveNotes(e.target.value)}
                      placeholder="e.g. Ledger discrepancy resolved with merchant finance confirmation."
                      className="w-full p-2 bg-finance-900 border border-emerald-700/80 rounded text-xs text-finance-100 placeholder:text-finance-500"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="ghost" onClick={() => setIsResolveOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={!resolveConfirmed || resolveExceptionMutation.isPending}
                      onClick={() => resolveExceptionMutation.mutate({ notes: resolveNotes })}
                      className="bg-emerald-700 hover:bg-emerald-800"
                    >
                      Confirm and Mark Resolved
                    </Button>
                  </div>
                </div>
              )}

              {/* REOPEN EXCEPTION DIALOG */}
              {isReopenOpen && (
                <div className="p-4 bg-orange-950/40 border border-orange-800/60 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-orange-300 flex items-center gap-1.5">
                      <RotateCcw className="w-4 h-4 text-orange-400" />
                      Reopen Resolved Exception
                    </h4>
                    <button onClick={() => setIsReopenOpen(false)} className="text-orange-400 hover:text-orange-200">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-orange-300/80">
                    Reopening moves this exception back to open investigation status. A mandatory business justification is required.
                  </p>
                  <div>
                    <label className="block text-xs font-semibold text-orange-200 mb-1">
                      Mandatory Business Reason (min 5 chars):
                    </label>
                    <textarea
                      rows={2}
                      value={reopenReason}
                      onChange={(e) => setReopenReason(e.target.value)}
                      placeholder="e.g. Bank statement reversal or delayed chargeback clawback detected..."
                      className="w-full p-2 bg-finance-900 border border-orange-700/80 rounded text-xs text-finance-100 placeholder:text-finance-500 focus:ring-1 focus:ring-orange-500"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="ghost" onClick={() => setIsReopenOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={reopenReason.trim().length < 5 || reopenExceptionMutation.isPending}
                      onClick={() => reopenExceptionMutation.mutate({ reason: reopenReason.trim() })}
                      className="bg-orange-600 hover:bg-orange-700"
                    >
                      Confirm Reopen
                    </Button>
                  </div>
                </div>
              )}

              {/* RESOLUTION HISTORY AUDIT TRAIL TIMELINE */}
              {isHistoryExpanded && (
                <div className="pt-4 border-t border-finance-700/60 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-finance-300 flex items-center gap-1.5">
                      <History className="w-3.5 h-3.5 text-finance-400" />
                      Immutable Resolution History Audit Trail ({resolutionHistory.length} events)
                    </h4>
                    <span className="text-[10px] text-finance-400 font-mono">Append-Only Postgres Ledger</span>
                  </div>

                  {resolutionHistory.length === 0 ? (
                    <p className="text-xs text-finance-400 italic">No lifecycle events recorded yet.</p>
                  ) : (
                    <div className="divide-y divide-finance-700/60 border border-finance-700/80 rounded-lg overflow-hidden bg-finance-900/60">
                      {resolutionHistory.map((hist: ResolutionHistoryItem) => (
                        <div key={hist.id} className="p-3 text-xs space-y-1 hover:bg-finance-800/80 transition-colors">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                            <div className="flex items-center gap-2">
                              <Badge variant="neutral" size="sm" className="font-mono text-[10px] font-bold">
                                {hist.event_type}
                              </Badge>
                              <span className="font-semibold text-finance-200">
                                {hist.user_name || hist.user_id}
                              </span>
                              {hist.user_role && (
                                <span className="text-[10px] text-finance-400 font-mono">
                                  ({hist.user_role})
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] font-mono text-finance-500">
                              {new Date(hist.created_at).toLocaleString()}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 text-[11px] text-finance-300">
                            {hist.previous_status && (
                              <span>
                                Status: <span className="font-mono text-finance-400">{hist.previous_status}</span> &rarr;{' '}
                                <span className="font-mono font-semibold text-emerald-400">{hist.new_status}</span>
                              </span>
                            )}
                          </div>

                          {hist.reason && (
                            <p className="text-finance-300 italic text-[11px] pl-3 border-l-2 border-finance-600">
                              &ldquo;{hist.reason}&rdquo;
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>

          {/* 4. Structured Evidence Items Breakdown (Phase 05) */}
          <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-finance-700/60 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-finance-100">
                  Supporting Financial Evidence Ledger ({data.evidence_items.length} Records)
                </h3>
                <p className="text-xs text-finance-400">
                  Direct database records and external ledger proofs supporting this discrepancy conclusion.
                </p>
              </div>
              <Badge variant="neutral" size="sm" className="font-mono">
                Merchant Tenant Isolated
              </Badge>
            </div>

            <div className="divide-y divide-finance-700/50">
              {data.evidence_items.map((item: EvidenceItem) => (
                <div key={item.evidence_id} className="p-4 hover:bg-finance-700/30 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-finance-900 rounded border border-finance-700/80">
                        {categoryIcons[item.category as EvidenceCategory] || <FileText className="w-4 h-4 text-finance-400" />}
                      </div>
                      <div>
                        <span className="text-xs font-bold text-finance-200 uppercase tracking-wide">
                          {item.category} &bull; {item.source_type}
                        </span>
                        <span className="ml-2 text-[11px] font-mono text-finance-400">
                          [{item.evidence_id}]
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {renderStrengthBadge(item.strength)}
                      {item.timestamp && (
                        <span className="text-[11px] font-mono text-finance-500">
                          {new Date(item.timestamp).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Attributes Key-Value Grid */}
                  <div className="mt-3 bg-finance-900 p-3 rounded-md border border-finance-700/80 font-mono text-[11px]">
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                      {item.source_record_id && (
                        <div>
                          <span className="text-finance-500 block text-[10px]">RECORD ID:</span>
                          <span className="font-semibold text-finance-200 break-all">{item.source_record_id}</span>
                        </div>
                      )}
                      {Object.entries(item.attributes).map(([key, val]) => (
                        <div key={key}>
                          <span className="text-finance-500 block text-[10px] uppercase">
                            {key.replace(/_/g, ' ')}:
                          </span>
                          <span className="font-semibold text-finance-200 break-all">
                            {val !== null && val !== undefined ? String(val) : '—'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Limitations / Notes */}
                  {item.limitations.length > 0 && (
                    <div className="mt-2 flex items-center gap-1.5 text-[11px] text-amber-300 bg-amber-950/40 p-2 rounded border border-amber-800/40">
                      <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-amber-400" />
                      <span>{item.limitations.join('; ')}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
