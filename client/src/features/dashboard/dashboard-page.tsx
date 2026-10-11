import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import {
  GitCompare,
  AlertTriangle,
  UserCheck,
  ShieldCheck,
  RefreshCw,
  Search,
  ArrowUpRight,
  Clock,
  Bot,
  ShieldAlert,
  CreditCard,
  ChevronLeft,
  ChevronRight,
  Lock,
  ThumbsUp,
  ExternalLink,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
} from 'recharts';
import { dashboardService } from '@/services/dashboard';
import {
  CurrencyExposure,
  OperationsQueueItem,
  PendingApprovalItem,
} from '@/types/api';
import { DemoChecklist } from '@/components/data-display/demo-checklist';
import { DemoScenarioSelector } from '@/components/data-display/demo-scenario-selector';

const PIE_COLORS = ['#10b981', '#3b82f6', '#f43f5e', '#8b5cf6'];

export const DashboardPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Filters & Pagination for Operations Queue
  const [queuePage, setQueuePage] = useState(1);
  const [queueSearch, setQueueSearch] = useState('');
  const [queueStatusFilter, setQueueStatusFilter] = useState('');
  const [queueTypeFilter, setQueueTypeFilter] = useState('');
  const [queueSortBy, setQueueSortBy] = useState('detected_at');
  const [queueSortOrder, setQueueSortOrder] = useState<'asc' | 'desc'>('desc');

  // Queries
  const {
    data: overview,
    isLoading: isOverviewLoading,
    isError: isOverviewError,
    error: overviewError,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: () => dashboardService.getOverview(),
  });

  const { data: health } = useQuery({
    queryKey: ['dashboard-health'],
    queryFn: () => dashboardService.getReconciliationHealth(),
  });

  const { data: trends } = useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: () => dashboardService.getExceptionTrends(),
  });

  const { data: pendingApprovals = [] } = useQuery({
    queryKey: ['dashboard-pending-approvals'],
    queryFn: () => dashboardService.getPendingApprovals(),
  });

  const {
    data: queueResponse,
    isLoading: isQueueLoading,
  } = useQuery({
    queryKey: [
      'dashboard-operations-queue',
      queuePage,
      queueSearch,
      queueStatusFilter,
      queueTypeFilter,
      queueSortBy,
      queueSortOrder,
    ],
    queryFn: () =>
      dashboardService.getOperationsQueue({
        page: queuePage,
        pageSize: 10,
        search: queueSearch || undefined,
        status: queueStatusFilter || undefined,
        exceptionType: queueTypeFilter || undefined,
        sortBy: queueSortBy,
        sortOrder: queueSortOrder,
      }),
  });

  const handleRefreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard-overview'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-health'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-trends'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-pending-approvals'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-operations-queue'] });
  };

  if (isOverviewLoading) {
    return <LoadingState message="Aggregating financial operations metrics and reconciliation telemetry..." />;
  }

  if (isOverviewError) {
    return (
      <ErrorState
        title="Failed to Load Operations Dashboard"
        message={overviewError instanceof Error ? overviewError.message : 'Error retrieving metrics'}
        onRetry={() => refetchOverview()}
      />
    );
  }

  // Formatting helpers
  const formatCurrencyAmount = (amountStr: string, curr: string) => {
    const val = parseFloat(amountStr) || 0;
    return `${curr} ${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  };

  // Pie chart data
  const matchPieData = health
    ? [
        { name: 'Matched', value: health.match_distribution.matched || 0 },
        { name: 'Unmatched', value: health.match_distribution.unmatched || 0 },
        { name: 'Exceptions', value: health.match_distribution.exceptions || 0 },
      ].filter((d) => d.value > 0)
    : [];

  // Bar chart data for exception types
  const typeBarData = health
    ? health.exceptions_by_type.map((t) => ({
        type: t.exception_type.replace(/_/g, ' '),
        count: t.count,
        exposure: parseFloat(t.total_exposure),
      }))
    : [];

  // Runs trend line chart data
  const runsTrendData = trends
    ? [...trends.runs_history].reverse().map((r, i) => ({
        run: `Run ${i + 1}`,
        matchRate: r.match_rate_percentage,
        total: r.total_records,
      }))
    : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Finance Operations Command Center"
          description="Real-time reconciliation intelligence, financial exposure telemetry, AI investigations, and human approval queue."
          badgeText="Production Operations"
          badgeVariant="success"
        />

        <div className="flex items-center gap-2 self-start sm:self-center">
          {overview?.last_reconciliation_at && (
            <span className="text-[11px] font-mono text-finance-500 hidden md:inline">
              Last reconciled: {new Date(overview.last_reconciliation_at).toLocaleTimeString()}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshAll}
            className="gap-1.5 text-xs text-finance-700 hover:text-finance-900"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
          <Link to="/reconciliation">
            <Button size="sm" variant="primary" className="gap-1.5 text-xs">
              <GitCompare className="w-3.5 h-3.5" />
              Run Reconciliation
            </Button>
          </Link>
        </div>
      </div>

      {/* Presenter Demo Experience Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DemoChecklist />
        <DemoScenarioSelector />
      </div>

      {/* 1. EXECUTIVE KPI HIERARCHY CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Payments Processed */}
        <Card className="border-l-4 border-l-brand-primary p-4 bg-finance-800 border-finance-700/80 shadow-sm">
          <div className="flex items-center justify-between text-finance-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Payments Processed</span>
            <CreditCard className="w-4 h-4 text-brand-accent" />
          </div>
          <div className="text-2xl font-bold font-mono text-finance-100">
            {overview?.total_payments_processed.toLocaleString() || '0'}
          </div>
          <div className="mt-2 text-[11px] text-finance-400">
            Internal merchant ledger entries
          </div>
        </Card>

        {/* Matched Records & Rate */}
        <Card className="border-l-4 border-l-emerald-500 p-4 bg-finance-800 border-finance-700/80 shadow-sm">
          <div className="flex items-center justify-between text-finance-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Deterministic Match Rate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-bold font-mono text-finance-100">
              {overview?.match_rate_percentage || 0}%
            </div>
            <span className="text-xs text-emerald-400 font-semibold font-mono">
              ({overview?.matched_records || 0} matched)
            </span>
          </div>
          <div className="mt-2 text-[11px] text-finance-400">
            Exact & tolerance matched records
          </div>
        </Card>

        {/* Total Outstanding Exposure */}
        <Card className="border-l-4 border-l-rose-500 p-4 bg-finance-800 border-finance-700/80 shadow-sm">
          <div className="flex items-center justify-between text-finance-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Outstanding Exposure</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          {overview?.total_exposure_by_currency && overview.total_exposure_by_currency.length > 0 ? (
            <div className="space-y-1">
              {overview.total_exposure_by_currency.map((exp: CurrencyExposure) => (
                <div key={exp.currency} className="text-xl font-bold font-mono text-rose-400">
                  {formatCurrencyAmount(exp.total_exposure, exp.currency)}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-2xl font-bold font-mono text-finance-100">₹0.00</div>
          )}
          <div className="mt-2 text-[11px] text-finance-400">
            Across {overview?.exceptions_awaiting_review || 0} open exceptions
          </div>
        </Card>

        {/* Pending Approvals & Resolved */}
        <Card className="border-l-4 border-l-amber-500 p-4 bg-finance-800 border-finance-700/80 shadow-sm">
          <div className="flex items-center justify-between text-finance-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Pending Approvals</span>
            <UserCheck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-bold font-mono text-amber-400">
              {overview?.pending_approvals_count || 0}
            </div>
            <span className="text-xs text-finance-400">
              awaiting reviewer
            </span>
          </div>
          <div className="mt-2 text-[11px] text-finance-400 flex items-center justify-between">
            <span>Resolved tickets:</span>
            <span className="font-semibold text-emerald-400 font-mono">
              {overview?.resolved_exceptions_count || 0}
            </span>
          </div>
        </Card>
      </div>

      {/* 2. PENDING APPROVALS ALERT PANEL (IF ANY) */}
      {pendingApprovals.length > 0 && (
        <Card className="border-amber-500/40 bg-amber-950/20 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-amber-900/40 rounded text-amber-400">
                <Clock className="w-4 h-4 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-amber-300">
                  Resolution Proposals Awaiting Human Review ({pendingApprovals.length})
                </h3>
                <p className="text-xs text-amber-400/80">
                  Decisions require separation of duties. Proposal authors cannot approve their own submissions.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
            {pendingApprovals.map((prop: PendingApprovalItem) => (
              <div
                key={prop.proposal_id}
                className="p-3.5 bg-finance-900 rounded-lg border border-finance-700/80 shadow-xs space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-finance-200 uppercase text-[11px]">
                    {prop.proposal_category.replace(/_/g, ' ')}
                  </span>
                  <Badge variant="warning" size="sm" className="text-[10px]">
                    {prop.severity}
                  </Badge>
                </div>

                <div className="text-finance-300 line-clamp-2">
                  <span className="font-semibold text-finance-200">Action: </span>
                  {prop.proposed_action}
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-finance-400 pt-1 border-t border-finance-800">
                  <span>Impact: <strong className="text-rose-400">{prop.currency} {parseFloat(prop.financial_impact).toFixed(2)}</strong></span>
                  <span>By: {prop.created_by_user_name || 'Operator'}</span>
                </div>

                {/* Separation of Duties & Decision Action */}
                <div className="flex items-center justify-between pt-1">
                  {prop.is_current_user_author ? (
                    <span className="inline-flex items-center gap-1 text-[10px] text-amber-300 font-semibold bg-amber-950/60 border border-amber-800/40 px-2 py-0.5 rounded">
                      <Lock className="w-3 h-3" /> Author (Cannot Self-Approve)
                    </span>
                  ) : prop.can_current_user_approve ? (
                    <span className="inline-flex items-center gap-1 text-[10px] text-emerald-300 font-semibold bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded">
                      <ThumbsUp className="w-3 h-3" /> Reviewer Action Ready
                    </span>
                  ) : (
                    <span className="text-[10px] text-finance-400">Reviewer required</span>
                  )}

                  <Link to={`/exceptions/${prop.exception_id}`}>
                    <Button variant="outline" size="sm" className="h-7 text-[11px] gap-1">
                      <span>Review Dossier</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 3. RECONCILIATION HEALTH & VISUALIZATIONS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Match Distribution Pie Chart */}
        <Card className="p-5 bg-finance-800 border-finance-700/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-finance-100">Reconciliation Match Distribution</h3>
              <Badge variant="neutral" size="sm">Deterministic</Badge>
            </div>
            <p className="text-xs text-finance-400 mb-4">
              Relative proportion of matched versus exceptional records.
            </p>
          </div>

          <div className="h-52 flex items-center justify-center">
            {matchPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={matchPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {matchPieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: number) => [`${val} records`, 'Count']}
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#F3F4F6', fontSize: '11px', borderRadius: '6px' }}
                    itemStyle={{ color: '#F3F4F6' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-finance-400 italic">No reconciliation data available</div>
            )}
          </div>

          <div className="flex justify-center gap-4 text-xs font-mono pt-2 border-t border-finance-700/60 text-finance-300">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>Matched: {health?.match_distribution.matched || 0}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
              <span>Unmatched: {health?.match_distribution.unmatched || 0}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span>Exceptions: {health?.match_distribution.exceptions || 0}</span>
            </div>
          </div>
        </Card>

        {/* Exception Types Bar Chart */}
        <Card className="p-5 bg-finance-800 border-finance-700/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-finance-100">Exceptions by Anomaly Type</h3>
              <Badge variant="warning" size="sm">Triage</Badge>
            </div>
            <p className="text-xs text-finance-400 mb-4">
              Breakdown of financial exception counts by detected anomaly.
            </p>
          </div>

          <div className="h-52 flex items-center justify-center">
            {typeBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={typeBarData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <XAxis dataKey="type" stroke="#64748B" tick={{ fontSize: 9, fill: '#94A3B8' }} interval={0} angle={-25} textAnchor="end" />
                  <YAxis stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <Tooltip
                    formatter={(val: number) => [`${val} cases`, 'Exceptions']}
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#F3F4F6', fontSize: '11px', borderRadius: '6px' }}
                    itemStyle={{ color: '#F3F4F6' }}
                  />
                  <Bar dataKey="count" fill="#38BDF8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-finance-400 italic">No exceptions recorded</div>
            )}
          </div>

          <div className="text-right text-[11px] text-finance-400 font-mono pt-2 border-t border-finance-700/60">
            Total Exception Types: {typeBarData.length}
          </div>
        </Card>

        {/* Runs History Trend */}
        <Card className="p-5 bg-finance-800 border-finance-700/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-finance-100">Reconciliation Match Trend</h3>
              <Badge variant="info" size="sm">History</Badge>
            </div>
            <p className="text-xs text-finance-400 mb-4">
              Match rate progression across sequential batch reconciliation runs.
            </p>
          </div>

          <div className="h-52 flex items-center justify-center">
            {runsTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={runsTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                  <XAxis dataKey="run" stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <YAxis domain={[0, 100]} stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} unit="%" />
                  <Tooltip
                    formatter={(val: number) => [`${val}%`, 'Match Rate']}
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#F3F4F6', fontSize: '11px', borderRadius: '6px' }}
                    itemStyle={{ color: '#F3F4F6' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="matchRate"
                    stroke="#10B981"
                    strokeWidth={2}
                    dot={{ r: 3, fill: '#10B981' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-finance-400 italic">No past runs recorded</div>
            )}
          </div>

          <div className="text-right text-[11px] text-finance-400 font-mono pt-2 border-t border-finance-700/60">
            Tracked Runs: {runsTrendData.length}
          </div>
        </Card>
      </div>

      {/* 4. AI INVESTIGATION OVERVIEW CARD */}
      <Card className="p-5 bg-finance-800 border-finance-700/80 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-finance-700/60">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-primary/10 text-brand-accent rounded-lg border border-brand-primary/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-finance-100">AI Investigation Telemetry</h3>
              <p className="text-xs text-finance-400">
                Assistive root-cause diagnostics and evidence-grounded hypotheses for finance teams.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="text-center">
              <div className="font-bold text-emerald-400 text-base">
                {overview?.ai_investigations.completed_count || 0}
              </div>
              <span className="text-[10px] text-finance-400 uppercase">Completed</span>
            </div>
            <div className="text-center">
              <div className="font-bold text-sky-400 text-base">
                {overview?.ai_investigations.pending_count || 0}
              </div>
              <span className="text-[10px] text-finance-400 uppercase">Pending</span>
            </div>
            <div className="text-center">
              <div className="font-bold text-amber-400 text-base">
                {overview?.ai_investigations.requires_human_review_count || 0}
              </div>
              <span className="text-[10px] text-finance-400 uppercase">Human Review</span>
            </div>
            <div className="text-center">
              <div className="font-bold text-rose-400 text-base">
                {overview?.ai_investigations.failed_count || 0}
              </div>
              <span className="text-[10px] text-finance-400 uppercase">Failed</span>
            </div>
          </div>
        </div>

        <div className="pt-3 flex items-center justify-between text-[11px] text-finance-400">
          <div className="flex items-center gap-1.5 text-finance-300">
            <ShieldAlert className="w-3.5 h-3.5 text-finance-400 flex-shrink-0" />
            <span>
              Deterministic ledger arithmetic is strictly separated from AI generated diagnostics. AI cannot approve financial resolutions.
            </span>
          </div>
          <Link to="/exceptions" className="text-brand-accent hover:underline font-semibold flex items-center gap-1">
            <span>View All Exceptions</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </Card>

      {/* 5. EXCEPTION OPERATIONS QUEUE */}
      <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-finance-700/60 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-finance-100">
              Exception Operations Queue ({queueResponse?.total || 0} Total)
            </h3>
            <p className="text-xs text-finance-400">
              Live operational triage queue with evidence strength, AI status, and lifecycle stage.
            </p>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-finance-400" />
              <input
                type="text"
                value={queueSearch}
                onChange={(e) => {
                  setQueueSearch(e.target.value);
                  setQueuePage(1);
                }}
                placeholder="Search ID or description..."
                className="pl-8 pr-3 py-1.5 text-xs bg-finance-900 border border-finance-700/80 rounded-md w-44 text-finance-200 placeholder:text-finance-500 focus:ring-1 focus:ring-brand-accent focus:outline-none"
              />
            </div>

            <select
              value={queueStatusFilter}
              onChange={(e) => {
                setQueueStatusFilter(e.target.value);
                setQueuePage(1);
              }}
              className="py-1.5 px-2 text-xs bg-finance-900 border border-finance-700/80 rounded-md text-finance-200 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="RESOLVED">Resolved</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="REOPENED">Reopened</option>
            </select>

            <select
              value={queueTypeFilter}
              onChange={(e) => {
                setQueueTypeFilter(e.target.value);
                setQueuePage(1);
              }}
              className="py-1.5 px-2 text-xs bg-finance-900 border border-finance-700/80 rounded-md text-finance-200 focus:outline-none"
            >
              <option value="">All Types</option>
              <option value="MISSING_PAYMENT">Missing Payment</option>
              <option value="MISSING_SETTLEMENT">Missing Settlement</option>
              <option value="AMOUNT_MISMATCH">Amount Mismatch</option>
              <option value="FEE_MISMATCH">Fee Mismatch</option>
              <option value="REFUND_MISMATCH">Refund Mismatch</option>
              <option value="DUPLICATE_PAYMENT">Duplicate Payment</option>
              <option value="DELAYED_SETTLEMENT">Delayed Settlement</option>
            </select>

            <select
              value={`${queueSortBy}:${queueSortOrder}`}
              onChange={(e) => {
                const [sb, so] = e.target.value.split(':');
                setQueueSortBy(sb);
                setQueueSortOrder(so as 'asc' | 'desc');
                setQueuePage(1);
              }}
              className="py-1.5 px-2 text-xs bg-finance-900 border border-finance-700/80 rounded-md text-finance-200 focus:outline-none"
            >
              <option value="detected_at:desc">Newest First</option>
              <option value="detected_at:asc">Oldest First</option>
              <option value="impact:desc">Highest Financial Impact</option>
              <option value="impact:asc">Lowest Financial Impact</option>
              <option value="severity:desc">Severity</option>
            </select>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-finance-900 border-b border-finance-700/80 text-finance-300 font-semibold uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-4">Exception Reference</th>
                <th className="py-2.5 px-4">Type</th>
                <th className="py-2.5 px-4">Severity</th>
                <th className="py-2.5 px-4">Financial Impact</th>
                <th className="py-2.5 px-4">Age</th>
                <th className="py-2.5 px-4">Evidence</th>
                <th className="py-2.5 px-4">AI Diagnosis</th>
                <th className="py-2.5 px-4">Resolution State</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-finance-700/50">
              {isQueueLoading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-finance-400">
                    <LoadingState message="Loading operations queue..." />
                  </td>
                </tr>
              ) : queueResponse?.items && queueResponse.items.length > 0 ? (
                queueResponse.items.map((item: OperationsQueueItem) => (
                  <tr key={item.exception_id} className="hover:bg-finance-700/30 transition-colors">
                    {/* Exception Reference */}
                    <td className="py-3 px-4 font-mono text-[11px] text-finance-200 font-semibold">
                      <Link
                        to={`/exceptions/${item.exception_id}`}
                        className="text-brand-accent hover:underline"
                      >
                        {item.exception_id.slice(0, 8)}...
                      </Link>
                    </td>

                    {/* Type */}
                    <td className="py-3 px-4 font-semibold text-finance-200">
                      {item.exception_type.replace(/_/g, ' ')}
                    </td>

                    {/* Severity */}
                    <td className="py-3 px-4">
                      <Badge
                        variant={
                          item.severity === 'CRITICAL' || item.severity === 'HIGH'
                            ? 'danger'
                            : item.severity === 'MEDIUM'
                            ? 'warning'
                            : 'neutral'
                        }
                        size="sm"
                        className="text-[10px]"
                      >
                        {item.severity}
                      </Badge>
                    </td>

                    {/* Financial Impact */}
                    <td className="py-3 px-4 font-mono font-bold text-rose-400">
                      {item.currency} {parseFloat(item.financial_impact).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>

                    {/* Age */}
                    <td className="py-3 px-4 text-finance-400 font-mono text-[11px]">
                      {item.age_days === 0 ? 'Today' : `${item.age_days}d ago`}
                    </td>

                    {/* Evidence Strength */}
                    <td className="py-3 px-4">
                      {item.evidence_strength ? (
                        <Badge
                          variant={item.evidence_strength === 'CONFIRMED' ? 'success' : 'info'}
                          size="sm"
                          className="text-[10px]"
                        >
                          {item.evidence_strength} ({item.evidence_count})
                        </Badge>
                      ) : (
                        <span className="text-finance-500 text-[11px]">No proof</span>
                      )}
                    </td>

                    {/* AI Diagnosis */}
                    <td className="py-3 px-4">
                      {item.ai_investigation_status === 'COMPLETED' ? (
                        <Badge variant="success" size="sm" className="text-[10px] gap-1">
                          <Bot className="w-3 h-3" /> Ready
                        </Badge>
                      ) : item.ai_investigation_status === 'PENDING' ? (
                        <Badge variant="info" size="sm" className="text-[10px] gap-1 animate-pulse">
                          <Clock className="w-3 h-3" /> In Progress
                        </Badge>
                      ) : (
                        <span className="text-finance-500 text-[11px]">—</span>
                      )}
                    </td>

                    {/* Resolution State */}
                    <td className="py-3 px-4">
                      <Badge
                        variant={
                          item.resolution_status === 'RESOLVED'
                            ? 'success'
                            : item.resolution_status === 'PENDING_APPROVAL'
                            ? 'warning'
                            : item.resolution_status === 'APPROVED'
                            ? 'success'
                            : item.resolution_status === 'REOPENED'
                            ? 'warning'
                            : 'neutral'
                        }
                        size="sm"
                        className="text-[10px]"
                      >
                        {item.resolution_status}
                      </Badge>
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right">
                      <Link to={`/exceptions/${item.exception_id}`}>
                        <Button variant="ghost" size="sm" className="h-7 text-xs text-brand-accent hover:text-brand-accent/80 gap-1">
                          <span>Dossier</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-finance-400 italic">
                    No exceptions match the selected filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {queueResponse && queueResponse.total_pages > 1 && (
          <div className="p-3 bg-finance-900 border-t border-finance-700/80 flex items-center justify-between text-xs text-finance-400">
            <div>
              Showing page <span className="font-semibold text-finance-200">{queueResponse.page}</span> of{' '}
              <span className="font-semibold text-finance-200">{queueResponse.total_pages}</span> ({queueResponse.total} items)
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={queuePage <= 1}
                onClick={() => setQueuePage((prev) => Math.max(1, prev - 1))}
                className="h-7 w-7 p-0"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={queuePage >= queueResponse.total_pages}
                onClick={() => setQueuePage((prev) => Math.min(queueResponse.total_pages, prev + 1))}
                className="h-7 w-7 p-0"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
