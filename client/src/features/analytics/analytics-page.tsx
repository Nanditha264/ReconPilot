import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import { dashboardService } from '@/services/dashboard';
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
import {
  TrendingUp,
  ShieldCheck,
  CreditCard,
  AlertTriangle,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { CurrencyExposure } from '@/types/api';

const PIE_COLORS = ['#10B981', '#0EA5E9', '#F43F5E', '#A855F7', '#F59E0B'];

export const AnalyticsPage: React.FC = () => {
  const {
    data: overview,
    isLoading: isOverviewLoading,
    isError: isOverviewError,
    error: overviewError,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: dashboardService.getOverview,
    staleTime: 30000,
  });

  const {
    data: health,
    isLoading: isHealthLoading,
    isError: isHealthError,
    error: healthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['dashboard', 'reconciliation-health'],
    queryFn: dashboardService.getReconciliationHealth,
    staleTime: 30000,
  });

  const {
    data: trends,
    isLoading: isTrendsLoading,
    isError: isTrendsError,
    error: trendsError,
    refetch: refetchTrends,
  } = useQuery({
    queryKey: ['dashboard', 'exception-trends'],
    queryFn: dashboardService.getExceptionTrends,
    staleTime: 30000,
  });

  const handleRefreshAll = () => {
    refetchOverview();
    refetchHealth();
    refetchTrends();
  };

  const isLoading = isOverviewLoading || isHealthLoading || isTrendsLoading;
  const isError = isOverviewError || isHealthError || isTrendsError;

  // Pie chart data
  const matchPieData = health
    ? [
        { name: 'Matched', value: health.match_distribution.matched },
        { name: 'Unmatched', value: health.match_distribution.unmatched },
        { name: 'Exceptions', value: health.match_distribution.exceptions },
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

  // Severity distribution
  const severityData = health?.severity_distribution
    ? health.severity_distribution.map((s) => ({
        severity: s.severity,
        count: s.count,
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
      <PageHeader
        title="Reconciliation Analytics & Financial Telemetry"
        description="Empirical match rate performance, anomaly distributions, currency exposure, and SLA aging derived from live PostgreSQL records."
        badgeText="Real-Time Analytics"
        badgeVariant="info"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshAll}
            className="gap-1.5 text-xs text-finance-300"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Metrics
          </Button>
        }
      />

      {isLoading && <LoadingState message="Aggregating financial analytics from PostgreSQL..." />}

      {isError && (
        <ErrorState
          title="Failed to Load Financial Analytics"
          message={
            (overviewError instanceof Error ? overviewError.message : '') ||
            (healthError instanceof Error ? healthError.message : '') ||
            (trendsError instanceof Error ? trendsError.message : 'Analytics aggregation error')
          }
          onRetry={handleRefreshAll}
        />
      )}

      {!isLoading && !isError && (
        <div className="space-y-6">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4 bg-finance-800 border-finance-700 border-l-4 border-l-brand-primary">
              <div className="flex items-center justify-between text-finance-400 mb-1">
                <span className="text-xs font-semibold uppercase tracking-wider">Processed Volume</span>
                <CreditCard className="w-4 h-4 text-brand-primary" />
              </div>
              <div className="text-2xl font-bold font-mono text-finance-100">
                {overview?.total_payments_processed.toLocaleString() || 0}
              </div>
              <div className="mt-2 text-[11px] text-finance-400">
                Audited payment records
              </div>
            </Card>

            <Card className="p-4 bg-finance-800 border-finance-700 border-l-4 border-l-emerald-500">
              <div className="flex items-center justify-between text-finance-400 mb-1">
                <span className="text-xs font-semibold uppercase tracking-wider">Match Accuracy</span>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="flex items-baseline gap-2">
                <div className="text-2xl font-bold font-mono text-emerald-400">
                  {overview?.match_rate_percentage || 0}%
                </div>
                <span className="text-xs font-mono text-finance-400">
                  ({overview?.matched_records || 0} matched)
                </span>
              </div>
              <div className="mt-2 text-[11px] text-finance-400">
                Deterministic arithmetic
              </div>
            </Card>

            <Card className="p-4 bg-finance-800 border-finance-700 border-l-4 border-l-rose-500">
              <div className="flex items-center justify-between text-finance-400 mb-1">
                <span className="text-xs font-semibold uppercase tracking-wider">Financial Exposure</span>
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              </div>
              {overview?.total_exposure_by_currency && overview.total_exposure_by_currency.length > 0 ? (
                <div className="space-y-0.5">
                  {overview.total_exposure_by_currency.map((exp: CurrencyExposure) => (
                    <div key={exp.currency} className="text-lg font-bold font-mono text-rose-400">
                      {exp.currency} {parseFloat(exp.total_exposure).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-2xl font-bold font-mono text-finance-100">₹0.00</div>
              )}
              <div className="mt-2 text-[11px] text-finance-400">
                Segregated by currency
              </div>
            </Card>

            <Card className="p-4 bg-finance-800 border-finance-700 border-l-4 border-l-amber-500">
              <div className="flex items-center justify-between text-finance-400 mb-1">
                <span className="text-xs font-semibold uppercase tracking-wider">Resolution Rate</span>
                <TrendingUp className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-amber-400">
                {overview && overview.exception_records > 0
                  ? `${Math.round((overview.resolved_exceptions_count / overview.exception_records) * 100)}%`
                  : '0%'}
              </div>
              <div className="mt-2 text-[11px] text-finance-400 flex items-center justify-between">
                <span>Resolved:</span>
                <span className="font-semibold text-finance-200 font-mono">
                  {overview?.resolved_exceptions_count || 0} / {overview?.exception_records || 0}
                </span>
              </div>
            </Card>
          </div>

          {/* Visualizations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Match Status Distribution */}
            <Card className="p-5 bg-finance-800 border-finance-700 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-bold text-finance-100">Match Status Composition</h3>
                  <Badge variant="neutral" size="sm" className="font-mono text-[9px]">PostgreSQL Ground Truth</Badge>
                </div>
                <p className="text-xs text-finance-400 mb-4">
                  Distribution of matched ledger items versus exceptions and variances.
                </p>
              </div>

              <div className="h-56 flex items-center justify-center">
                {matchPieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={matchPieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {matchPieData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(val: number) => [`${val} records`, 'Count']}
                        contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#F3F4F6', fontSize: '11px', borderRadius: '6px' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-xs text-finance-500 italic">No reconciliation data</div>
                )}
              </div>

              <div className="flex justify-center gap-4 text-xs font-mono pt-3 border-t border-finance-700">
                <div className="flex items-center gap-1.5 text-finance-300">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>Matched: {health?.match_distribution.matched || 0}</span>
                </div>
                <div className="flex items-center gap-1.5 text-finance-300">
                  <div className="w-2.5 h-2.5 rounded-full bg-sky-500" />
                  <span>Unmatched: {health?.match_distribution.unmatched || 0}</span>
                </div>
                <div className="flex items-center gap-1.5 text-finance-300">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                  <span>Exceptions: {health?.match_distribution.exceptions || 0}</span>
                </div>
              </div>
            </Card>

            {/* Reconciliation Runs Trend */}
            <Card className="p-5 bg-finance-800 border-finance-700 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-bold text-finance-100">Batch Match Rate Progression</h3>
                  <Badge variant="info" size="sm" className="font-mono text-[9px]">Run Sequence</Badge>
                </div>
                <p className="text-xs text-finance-400 mb-4">
                  Historical match percentage across sequential reconciliation runs.
                </p>
              </div>

              <div className="h-56 flex items-center justify-center">
                {runsTrendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={runsTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                      <XAxis dataKey="run" stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                      <YAxis domain={[0, 100]} stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} unit="%" />
                      <Tooltip
                        formatter={(val: number) => [`${val}%`, 'Match Rate']}
                        contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#F3F4F6', fontSize: '11px', borderRadius: '6px' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="matchRate"
                        stroke="#10B981"
                        strokeWidth={2.5}
                        dot={{ r: 3, fill: '#10B981' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-xs text-finance-500 italic">No past runs recorded</div>
                )}
              </div>

              <div className="text-right text-[11px] text-finance-400 font-mono pt-3 border-t border-finance-700">
                Total Evaluated Runs: {runsTrendData.length}
              </div>
            </Card>
          </div>

          {/* Exceptions by Anomaly Type Bar Chart */}
          <Card className="p-5 bg-finance-800 border-finance-700 shadow-sm">
            <div className="flex items-center justify-between mb-1">
              <div>
                <h3 className="text-sm font-bold text-finance-100">Discrepancy Volume by Anomaly Category</h3>
                <p className="text-xs text-finance-400">
                  Granular counts of detected variances classified by the deterministic engine.
                </p>
              </div>
              <Badge variant="warning" size="sm" className="font-mono text-[9px]">Classification</Badge>
            </div>

            <div className="h-64 mt-4">
              {typeBarData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={typeBarData} margin={{ top: 10, right: 15, left: -20, bottom: 35 }}>
                    <XAxis
                      dataKey="type"
                      stroke="#64748B"
                      tick={{ fontSize: 9, fill: '#94A3B8' }}
                      interval={0}
                      angle={-20}
                      textAnchor="end"
                    />
                    <YAxis stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                    <Tooltip
                      formatter={(val: number) => [`${val} cases`, 'Occurrences']}
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#F3F4F6', fontSize: '11px', borderRadius: '6px' }}
                    />
                    <Bar dataKey="count" fill="#0EA5E9" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-finance-500 italic">
                  No discrepancy classifications found
                </div>
              )}
            </div>
          </Card>

          {/* Severity & SLA Aging Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-4 bg-finance-800 border-finance-700 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs uppercase tracking-wide text-finance-100 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Severity Distribution
                </span>
                <span className="text-[10px] font-mono text-finance-400">Total: {overview?.exception_records || 0}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                {severityData.map((s) => (
                  <div key={s.severity} className="p-2.5 rounded bg-finance-850 border border-finance-700/80 flex items-center justify-between">
                    <span className="text-finance-400">{s.severity}:</span>
                    <span className="font-bold text-finance-100">{s.count}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-4 bg-finance-800 border-finance-700 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs uppercase tracking-wide text-finance-100 flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-sky-400" />
                  Resolution Lifecycle Distribution
                </span>
                <span className="text-[10px] font-mono text-finance-400">Ledger Status</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                {health?.resolution_status_distribution.map((item) => (
                  <div key={item.status} className="p-2.5 rounded bg-finance-850 border border-finance-700/80 flex items-center justify-between">
                    <span className="text-finance-400">{item.status.replace(/_/g, ' ')}:</span>
                    <span className="font-bold text-finance-100">{item.count}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
