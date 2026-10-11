import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import { Search } from 'lucide-react';
import { transactionService } from '@/services/reconciliation';

export const TransactionsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['transactions', page, searchTerm],
    queryFn: () => transactionService.listTransactions(page, 15, searchTerm),
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <PageHeader
          title="Financial Transactions"
          description="Normalized ledger of payment captures, provider identifiers, and monetary status."
          badgeText="PostgreSQL Ledger"
          badgeVariant="info"
        />

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-finance-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search external ID or order..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 text-xs bg-finance-900 border border-finance-700/80 rounded-md text-finance-200 placeholder:text-finance-500 focus:outline-none focus:ring-1 focus:ring-brand-accent"
          />
        </div>
      </div>

      {isLoading && <LoadingState message="Loading persisted transactions..." />}

      {isError && (
        <ErrorState
          title="Failed to Load Transactions"
          message={error instanceof Error ? error.message : 'Network error'}
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <Card className="bg-finance-800 border-finance-700/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-finance-700/60 flex items-center justify-between">
            <h3 className="text-sm font-bold text-finance-100">Captured Payments</h3>
            <span className="text-xs text-finance-400 font-mono">
              Total Records: {data.meta.total_items}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-finance-900 border-b border-finance-700/80 text-finance-300 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">External ID</th>
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4">Method</th>
                  <th className="py-3 px-4">Created Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-finance-700/50 font-mono">
                {data.items.map((tx) => (
                  <tr key={tx.id} className="hover:bg-finance-700/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-finance-200">{tx.external_id}</td>
                    <td className="py-3 px-4 text-finance-400">{tx.external_order_id || '—'}</td>
                    <td className="py-3 px-4 font-sans">
                      {tx.status === 'CAPTURED' ? (
                        <Badge variant="success" size="sm">Captured</Badge>
                      ) : tx.status === 'REFUNDED' ? (
                        <Badge variant="warning" size="sm">Refunded</Badge>
                      ) : (
                        <Badge variant="neutral" size="sm">{tx.status}</Badge>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-finance-100">
                      ₹{parseFloat(tx.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 font-sans uppercase text-[11px] text-finance-400">
                      {tx.payment_method}
                    </td>
                    <td className="py-3 px-4 text-finance-400 font-sans">
                      {new Date(tx.source_created_at).toLocaleDateString()}
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
