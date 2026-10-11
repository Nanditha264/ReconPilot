import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import { EmptyState } from '@/components/feedback/empty-state';
import { dashboardService } from '@/services/dashboard';
import { resolutionService } from '@/services/reconciliation';
import { useAuth } from '@/hooks/use-auth';
import {
  UserCheck,
  ShieldCheck,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Lock,
  ArrowUpRight,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { PendingApprovalItem } from '@/types/api';

export const ReviewPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [actionError, setActionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectedProposal, setSelectedProposal] = useState<PendingApprovalItem | null>(null);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [isRejectModalOpen, setIsRejectModalOpen] = useState<boolean>(false);

  const {
    data: pendingApprovals = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['dashboard', 'pending-approvals'],
    queryFn: dashboardService.getPendingApprovals,
    staleTime: 10000,
  });

  const approveMutation = useMutation({
    mutationFn: async ({ exceptionId, proposalId }: { exceptionId: string; proposalId: string }) => {
      setActionError(null);
      return resolutionService.approveProposal(exceptionId, proposalId, {
        rationale: 'Approved via Human Review Queue with verified dual-control sign-off.',
      });
    },
    onSuccess: () => {
      setSuccessMessage('Resolution proposal approved successfully. Decision recorded in audit log.');
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['exceptions'] });
      setTimeout(() => setSuccessMessage(null), 5000);
    },
    onError: (err: Error) => {
      setActionError(err.message || 'Failed to approve proposal. Verify separation-of-duties permissions.');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({
      exceptionId,
      proposalId,
      reason,
    }: {
      exceptionId: string;
      proposalId: string;
      reason: string;
    }) => {
      setActionError(null);
      return resolutionService.rejectProposal(exceptionId, proposalId, {
        rationale: reason,
      });
    },
    onSuccess: () => {
      setSuccessMessage('Resolution proposal rejected. Explanation recorded in audit trail.');
      setIsRejectModalOpen(false);
      setRejectReason('');
      setSelectedProposal(null);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['exceptions'] });
      setTimeout(() => setSuccessMessage(null), 5000);
    },
    onError: (err: Error) => {
      setActionError(err.message || 'Failed to reject proposal.');
    },
  });

  const handleApprove = (item: PendingApprovalItem) => {
    if (!item.can_current_user_approve) return;
    if (window.confirm(`Approve resolution proposal (${item.proposed_action}) for ${item.currency} ${item.financial_impact}?`)) {
      approveMutation.mutate({
        exceptionId: item.exception_id,
        proposalId: item.proposal_id,
      });
    }
  };

  const handleOpenReject = (item: PendingApprovalItem) => {
    setSelectedProposal(item);
    setRejectReason('');
    setIsRejectModalOpen(true);
  };

  const handleConfirmReject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProposal || !rejectReason.trim()) return;
    rejectMutation.mutate({
      exceptionId: selectedProposal.exception_id,
      proposalId: selectedProposal.proposal_id,
      reason: rejectReason.trim(),
    });
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <PageHeader
        title="Human Review & Approval Queue"
        description="Dual-control governance for exception resolutions. Proposers cannot self-approve; reviewer sign-off required."
        badgeText={`Active User: ${user?.role || 'REVIEWER'}`}
        badgeVariant="info"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="gap-1.5 text-xs text-finance-300"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Queue
          </Button>
        }
      />

      {/* Success / Error Banners */}
      {successMessage && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-800 text-emerald-300 rounded-md text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {actionError && (
        <div className="p-3 bg-rose-950/40 border border-rose-800 text-rose-300 rounded-md text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Governance Explanation Notice */}
      <Card className="p-3.5 bg-finance-800 border-finance-700/80 shadow-sm flex items-start gap-3">
        <div className="p-1.5 bg-amber-500/20 text-amber-400 rounded-md border border-amber-500/30 shrink-0 mt-0.5">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="text-xs space-y-0.5">
          <div className="font-bold text-finance-100 uppercase tracking-wide text-[11px]">
            Enterprise Separation of Duties (SoD) Active
          </div>
          <p className="text-finance-400 leading-relaxed">
            Financial resolution proposals require dual-control authorization. A user who submits a proposal cannot approve it. Only authorized reviewers or leads distinct from the author can record approval decisions.
          </p>
        </div>
      </Card>

      {/* Main Content Area */}
      {isLoading && <LoadingState message="Loading pending review proposals..." />}

      {isError && (
        <ErrorState
          title="Review Queue Unreachable"
          message={error instanceof Error ? error.message : 'Failed to query pending approvals'}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && pendingApprovals.length === 0 && (
        <EmptyState
          title="Review Queue Clear"
          description="There are currently no exception resolution proposals awaiting human reviewer sign-off. When operators submit proposals for amount write-offs, manual ledger matches, or gateway escalations, they will appear here."
          icon={UserCheck}
        />
      )}

      {!isLoading && pendingApprovals.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-finance-400 font-mono">
            <span>{pendingApprovals.length} Proposals Awaiting Human Review</span>
            <span>Signed-in as: {user?.full_name || user?.email}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {pendingApprovals.map((item: PendingApprovalItem) => (
              <Card
                key={item.proposal_id}
                className="p-4 bg-finance-800 border-finance-700 hover:border-finance-600 transition-all flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-1.5">
                    <span className="font-bold text-finance-100 text-xs uppercase tracking-wide">
                      {item.proposal_category.replace(/_/g, ' ')}
                    </span>
                    <Badge variant="warning" size="sm" className="font-mono text-[9px] py-0 px-1">
                      {item.severity}
                    </Badge>
                  </div>

                  <div className="text-xs text-finance-200">
                    <span className="text-finance-400 font-semibold">Action: </span>
                    {item.proposed_action}
                  </div>

                  <p className="text-[11px] text-finance-400 line-clamp-3 leading-relaxed bg-finance-850 p-2 rounded border border-finance-700/60">
                    {item.explanation}
                  </p>

                  <div className="pt-1 flex items-center justify-between text-[11px] font-mono text-finance-400">
                    <span>Impact: <strong className="text-rose-400 font-bold">{item.currency} {parseFloat(item.financial_impact).toFixed(2)}</strong></span>
                    <span>Proposer: <strong className="text-finance-300">{item.created_by_user_name || 'Operator'}</strong></span>
                  </div>

                  <div className="text-[10px] text-finance-500 font-mono flex items-center gap-1">
                    <Clock className="w-3 h-3 text-finance-500" />
                    <span>Submitted: {new Date(item.submitted_at).toLocaleString()}</span>
                  </div>
                </div>

                {/* Actions & Separation of Duties Controls */}
                <div className="pt-3 border-t border-finance-700/80 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    {item.is_current_user_author ? (
                      <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 font-semibold bg-amber-950/60 border border-amber-800/80 px-2 py-0.5 rounded">
                        <Lock className="w-3 h-3" /> Author (Cannot Self-Approve)
                      </span>
                    ) : item.can_current_user_approve ? (
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-semibold bg-emerald-950/60 border border-emerald-800/80 px-2 py-0.5 rounded">
                        <ThumbsUp className="w-3 h-3" /> Reviewer Eligible
                      </span>
                    ) : (
                      <span className="text-[10px] text-finance-500 font-mono">Reviewer role required</span>
                    )}

                    <Link to={`/exceptions/${item.exception_id}`}>
                      <Button variant="ghost" size="sm" className="h-6 text-[10px] gap-1 px-1.5 text-brand-accent">
                        <span>Dossier</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Button>
                    </Link>
                  </div>

                  {/* Decision Buttons */}
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!item.can_current_user_approve || approveMutation.isPending}
                      onClick={() => handleApprove(item)}
                      className="h-7 text-[11px] gap-1 font-medium bg-emerald-950/40 text-emerald-300 border-emerald-800 hover:bg-emerald-900/60 hover:text-emerald-100"
                    >
                      <ThumbsUp className="w-3 h-3" />
                      <span>Approve</span>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!item.can_current_user_approve || rejectMutation.isPending}
                      onClick={() => handleOpenReject(item)}
                      className="h-7 text-[11px] gap-1 font-medium bg-rose-950/40 text-rose-300 border-rose-800 hover:bg-rose-900/60 hover:text-rose-100"
                    >
                      <ThumbsDown className="w-3 h-3" />
                      <span>Reject</span>
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {isRejectModalOpen && selectedProposal && (
        <div className="fixed inset-0 bg-finance-950/80 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <Card className="max-w-md w-full bg-finance-800 border-finance-700 shadow-xl p-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-finance-700">
              <h4 className="text-sm font-bold text-finance-100 flex items-center gap-2">
                <XCircle className="w-4 h-4 text-rose-400" />
                <span>Reject Resolution Proposal</span>
              </h4>
              <Badge variant="danger" size="sm" className="text-[10px]">
                Audit Logged
              </Badge>
            </div>

            <p className="text-xs text-finance-300 leading-relaxed">
              Provide an official business explanation for rejecting this proposal. The explanation will be permanently recorded in the PostgreSQL audit log.
            </p>

            <form onSubmit={handleConfirmReject} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-finance-400 uppercase tracking-wide mb-1">
                  Rejection Reason (Required)
                </label>
                <textarea
                  required
                  rows={3}
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g. Insufficient gateway chargeback documentation provided..."
                  className="w-full p-2.5 text-xs bg-finance-850 border border-finance-700 rounded-md text-finance-100 placeholder-finance-500 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsRejectModalOpen(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="danger"
                  size="sm"
                  disabled={!rejectReason.trim() || rejectMutation.isPending}
                  className="text-xs gap-1"
                >
                  <ThumbsDown className="w-3 h-3" />
                  <span>Confirm Rejection</span>
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
