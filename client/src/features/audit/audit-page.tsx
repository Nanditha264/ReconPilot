import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/feedback/loading-state';
import { ErrorState } from '@/components/feedback/error-state';
import { EmptyState } from '@/components/feedback/empty-state';
import { auditService } from '@/services/audit';
import {
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  Clock,
  User,
  Bot,
  Terminal,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { AuditEventItem } from '@/types/api';

const getActorIcon = (actorType: string) => {
  switch (actorType) {
    case 'SYSTEM':
      return <Terminal className="w-3.5 h-3.5 text-brand-accent" />;
    case 'AI_INVESTIGATOR':
      return <Bot className="w-3.5 h-3.5 text-purple-400" />;
    case 'USER':
    default:
      return <User className="w-3.5 h-3.5 text-emerald-400" />;
  }
};

const getStateBadge = (state: string | null) => {
  if (!state) return <span className="text-finance-500 font-mono text-[11px]">—</span>;
  if (state.includes('RESOLVED') || state === 'COMPLETED' || state === 'APPROVED') {
    return <Badge variant="success" size="sm" className="font-mono text-[10px]">{state}</Badge>;
  }
  if (state.includes('REVIEW') || state === 'PENDING') {
    return <Badge variant="warning" size="sm" className="font-mono text-[10px]">{state}</Badge>;
  }
  if (state.includes('REJECTED') || state === 'FAILED') {
    return <Badge variant="danger" size="sm" className="font-mono text-[10px]">{state}</Badge>;
  }
  return <Badge variant="neutral" size="sm" className="font-mono text-[10px]">{state}</Badge>;
};

export const AuditPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [search, setSearch] = useState('');
  const [actorType, setActorType] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['audit', 'events', page, pageSize, search, actorType],
    queryFn: () => auditService.listEvents(page, pageSize, search || undefined, undefined, actorType || undefined),
    staleTime: 30000,
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <PageHeader
        title="Audit Trail & Financial Governance"
        description="Immutable chronological ledger of all reconciliation runs, anomaly classifications, controller overrides, and policy evaluations."
        badgeText="PostgreSQL Audit Ledger"
        badgeVariant="success"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="gap-1.5 text-xs text-finance-300"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Log
          </Button>
        }
      />

      {/* Filter and Search Bar */}
      <Card className="p-3 bg-finance-800 border-finance-700/80 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-finance-500" />
            <input
              type="text"
              placeholder="Search event type, actor ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-finance-850 border border-finance-700 rounded-md text-finance-100 placeholder-finance-500 focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs text-finance-400">
            <Filter className="w-3.5 h-3.5" />
            <select
              value={actorType}
              onChange={(e) => {
                setActorType(e.target.value);
                setPage(1);
              }}
              className="py-1.5 px-2 text-xs bg-finance-850 border border-finance-700 rounded-md text-finance-200 focus:outline-none focus:border-brand-primary"
            >
              <option value="">All Actors</option>
              <option value="SYSTEM">System Engine</option>
              <option value="USER">Human Operator</option>
              <option value="AI_INVESTIGATOR">AI Investigator</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-finance-400 font-mono">
          {data ? `${data.meta.total_items} Total Audit Events` : 'Reading PostgreSQL Audit Ledger...'}
        </div>
      </Card>

      {/* Main Content Area */}
      {isLoading && <LoadingState message="Streaming audit records from PostgreSQL..." />}

      {isError && (
        <ErrorState
          title="Audit Trail Unreachable"
          message={error instanceof Error ? error.message : 'Failed to query audit_events table'}
          onRetry={() => refetch()}
        />
      )}

      {data && data.items.length === 0 && (
        <EmptyState
          title="No Audit Records Matching Filter"
          description="Adjust your search criteria or clear actor filters to inspect the complete governance trail."
          icon={ShieldCheck}
        />
      )}

      {data && data.items.length > 0 && (
        <Card className="p-0 overflow-hidden bg-finance-800 border-finance-700/80 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-finance-850 border-b border-finance-700/80 text-finance-400 font-semibold uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-4">Timestamp</th>
                  <th className="py-2.5 px-4">Event Category</th>
                  <th className="py-2.5 px-4">Actor</th>
                  <th className="py-2.5 px-4">State Transition</th>
                  <th className="py-2.5 px-4">Related Entity</th>
                  <th className="py-2.5 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-finance-700/60 font-mono">
                {data.items.map((event: AuditEventItem) => (
                  <tr key={event.id} className="hover:bg-finance-750/50 transition-colors">
                    <td className="py-3 px-4 text-finance-400 whitespace-nowrap text-[11px]">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-finance-500" />
                        <span>{new Date(event.created_at).toLocaleString()}</span>
                      </div>
                    </td>

                    <td className="py-3 px-4 font-bold text-finance-100 text-[11px]">
                      <span className="px-2 py-0.5 rounded bg-finance-700/80 border border-finance-600 text-finance-200">
                        {event.event_type}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-finance-300">
                      <div className="flex items-center gap-1.5 text-xs">
                        {getActorIcon(event.actor_type)}
                        <span className="font-semibold">{event.actor_type}</span>
                        {event.actor_id && (
                          <span className="text-[10px] text-finance-500 font-mono truncate max-w-[100px]">
                            ({event.actor_id})
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-xs whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        {getStateBadge(event.previous_state)}
                        <span className="text-finance-500">&rarr;</span>
                        {getStateBadge(event.new_state)}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-xs text-finance-300">
                      {event.exception_id ? (
                        <Link
                          to={`/exceptions/${event.exception_id}`}
                          className="text-brand-accent hover:underline flex items-center gap-1 text-[11px]"
                        >
                          <span>Exception {event.exception_id.slice(0, 8)}</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </Link>
                      ) : event.reconciliation_run_id ? (
                        <span className="text-finance-400 text-[11px]">
                          Run {event.reconciliation_run_id.slice(0, 8)}
                        </span>
                      ) : (
                        <span className="text-finance-500 text-[11px]">—</span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-right">
                      {event.event_metadata ? (
                        <span
                          className="text-[10px] text-finance-400 font-mono bg-finance-850 px-1.5 py-0.5 rounded border border-finance-700 cursor-help"
                          title={JSON.stringify(event.event_metadata, null, 2)}
                        >
                          {Object.keys(event.event_metadata).length} metadata keys
                        </span>
                      ) : (
                        <span className="text-[10px] text-finance-500 font-mono">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination bar */}
          <div className="p-3 border-t border-finance-700/80 bg-finance-850 flex items-center justify-between text-xs text-finance-400">
            <span>
              Page {data.meta.current_page} of {data.meta.total_pages} ({data.meta.total_items} Total Events)
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!data.meta.has_previous}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="h-7 px-2 text-xs gap-1"
              >
                <ChevronLeft className="w-3 h-3" />
                <span>Previous</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!data.meta.has_next}
                onClick={() => setPage((p) => p + 1)}
                className="h-7 px-2 text-xs gap-1"
              >
                <span>Next</span>
                <ChevronRight className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
