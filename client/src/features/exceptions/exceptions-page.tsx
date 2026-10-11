import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import { Search } from 'lucide-react';
import { exceptionService } from '@/services/reconciliation';
import { DemoScenarioSelector } from '@/components/data-display/demo-scenario-selector';

export const ExceptionsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['exceptions', page, searchTerm],
    queryFn: () => exceptionService.listExceptions(page, 15, searchTerm),
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <PageHeader
          title="Exceptions Queue"
          description="Classified discrepancies detected by the deterministic engine requiring review or automated resolution."
          badgeText="Active Exceptions"
          badgeVariant="danger"
        />

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-finance-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search exception description..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 text-xs bg-finance-900 border border-finance-700/80 rounded-md text-finance-200 placeholder:text-finance-500 focus:outline-none focus:ring-1 focus:ring-brand-accent"
          />
        </div>
      </div>

      {/* Presenter Demo Scenario Selector */}
      <DemoScenarioSelector />

      {isLoading && <LoadingState message="Loading detected exceptions..." />}

      {isError && (
        <ErrorState
          title="Failed to Load Exceptions"
          message={error instanceof Error ? error.message : 'Network error'}
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-finance-700/60 flex items-center justify-between">
            <h3 className="text-sm font-bold text-finance-100">Detected Financial Discrepancies</h3>
            <span className="text-xs text-finance-400 font-mono">
              Total Exceptions: {data.meta.total_items}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-finance-900 border-b border-finance-700/80 text-finance-300 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Financial Impact</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Detected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-finance-700/50 font-mono">
                {data.items.map((ex) => (
                  <tr
                    key={ex.id}
                    onClick={() => (window.location.href = `/exceptions/${ex.id}`)}
                    className="hover:bg-finance-700/30 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4">
                      <span className="font-semibold text-finance-200 text-[11px]">
                        {ex.exception_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans">
                      {ex.severity === 'CRITICAL' ? (
                        <Badge variant="danger" size="sm">Critical</Badge>
                      ) : ex.severity === 'HIGH' ? (
                        <Badge variant="warning" size="sm">High</Badge>
                      ) : (
                        <Badge variant="neutral" size="sm">{ex.severity}</Badge>
                      )}
                    </td>
                    <td className="py-3 px-4 font-sans">
                      <Badge variant="info" size="sm">{ex.status}</Badge>
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-rose-400">
                      ₹{parseFloat(ex.financial_impact).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 font-sans text-finance-300 max-w-xs truncate">
                      {ex.description}
                    </td>
                    <td className="py-3 px-4 text-finance-400 font-sans flex items-center justify-between">
                      <span>{new Date(ex.created_at).toLocaleDateString()}</span>
                      <span className="text-[11px] text-brand-accent font-medium hover:underline">
                        View Evidence &rarr;
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-3 border-t border-finance-700/80 flex items-center justify-between text-xs text-finance-400">
            <span>
              Page <strong className="text-finance-200">{data.meta.current_page}</strong> of <strong className="text-finance-200">{data.meta.total_pages}</strong>
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!data.meta.has_previous}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!data.meta.has_next}
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
