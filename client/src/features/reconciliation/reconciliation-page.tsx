import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import { Play, CheckCircle, Database } from 'lucide-react';
import { reconciliationService, ingestionService } from '@/services/reconciliation';

export const ReconciliationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [ingestionMessage, setIngestionMessage] = useState<string | null>(null);

  const {
    data: runsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['reconciliation-runs', page],
    queryFn: () => reconciliationService.listRuns(page, 10),
  });

  const runMutation = useMutation({
    mutationFn: () => reconciliationService.triggerRun({ run_type: 'MANUAL_TRIGGER', tolerance: '1.00' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-runs'] });
    },
  });

  const ingestMutation = useMutation({
    mutationFn: () => ingestionService.ingestDemoData(),
    onSuccess: (data) => {
      setIngestionMessage(
        `Ingested ${data.total_records_processed} source records in ${data.duration_ms}ms (${data.skipped_records} preserved existing).`
      );
      queryClient.invalidateQueries({ queryKey: ['reconciliation-runs'] });
      setTimeout(() => setIngestionMessage(null), 6000);
    },
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <PageHeader
          title="Reconciliation Runs"
          description="Deterministic financial matching pipeline calculating expected settlements, tolerances, and exceptions."
          badgeText="Deterministic Engine"
          badgeVariant="success"
        />

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            onClick={() => ingestMutation.mutate()}
            disabled={ingestMutation.isPending}
            className="flex items-center gap-2 text-xs font-semibold py-2"
          >
            <Database className="w-3.5 h-3.5 text-finance-600" />
            <span>{ingestMutation.isPending ? 'Ingesting...' : 'Ingest Demo Data'}</span>
          </Button>

          <Button
            variant="primary"
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending}
            className="flex items-center gap-2 text-xs font-semibold py-2"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{runMutation.isPending ? 'Running Engine...' : 'Run Reconciliation'}</span>
          </Button>
        </div>
      </div>

      {ingestionMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{ingestionMessage}</span>
        </div>
      )}

      {isLoading && <LoadingState message="Loading historical reconciliation runs..." />}

      {isError && (
        <ErrorState
          title="Failed to Load Reconciliation Runs"
          message={error instanceof Error ? error.message : 'Network error'}
          onRetry={() => refetch()}
        />
      )}

      {runsData && (
        <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-finance-700/60 flex items-center justify-between">
            <h3 className="text-sm font-bold text-finance-100">Run History</h3>
            <span className="text-xs text-finance-400 font-mono">
              Total Runs: {runsData.meta.total_items}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-finance-900 border-b border-finance-700/80 text-finance-300 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Run ID / Type</th>
                  <th className="py-3 px-4">Started At</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Examined</th>
                  <th className="py-3 px-4 text-right">Matched</th>
                  <th className="py-3 px-4 text-right">Exceptions</th>
                  <th className="py-3 px-4 text-right">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-finance-700/50">
                {runsData.items.map((run) => (
                  <tr key={run.id} className="hover:bg-finance-700/30 transition-colors font-mono">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-finance-200">{run.id.slice(0, 8)}...</div>
                      <div className="text-[10px] text-finance-400 font-sans">{run.run_type}</div>
                    </td>
                    <td className="py-3 px-4 text-finance-300 font-sans">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-sans">
                      {run.status === 'COMPLETED' ? (
                        <Badge variant="success" size="sm">Completed</Badge>
                      ) : run.status === 'FAILED' ? (
                        <Badge variant="danger" size="sm">Failed</Badge>
                      ) : (
                        <Badge variant="info" size="sm">Running</Badge>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-finance-200">
                      {run.total_records}
                    </td>
                    <td className="py-3 px-4 text-right text-emerald-400 font-semibold">
                      {run.matched_records}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {run.exception_records > 0 ? (
                        <span className="text-rose-400 font-bold">{run.exception_records}</span>
                      ) : (
                        <span className="text-finance-500">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right text-finance-400 font-sans">
                      {run.processing_duration_ms ? `${run.processing_duration_ms}ms` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination bar */}
          <div className="p-3 border-t border-finance-700/80 flex items-center justify-between text-xs text-finance-400">
            <span>
              Page <strong className="text-finance-200">{runsData.meta.current_page}</strong> of <strong className="text-finance-200">{runsData.meta.total_pages}</strong>
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!runsData.meta.has_previous}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!runsData.meta.has_next}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
