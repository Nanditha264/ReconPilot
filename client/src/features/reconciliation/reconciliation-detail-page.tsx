import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { PageHeader } from '@/components/layout/page-header';
import { EmptyState } from '@/components/feedback/empty-state';
import { Button } from '@/components/ui/button';
import { ArrowLeft, GitCompare } from 'lucide-react';

export const ReconciliationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <Link to="/reconciliation">
          <Button variant="ghost" size="sm" className="gap-1 text-finance-600">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Batches
          </Button>
        </Link>
      </div>

      <PageHeader
        title={`Reconciliation Batch: ${id || 'Unknown'}`}
        description="Detailed record breakdown and deterministic rule verification."
        badgeText="Batch Detail"
        badgeVariant="neutral"
      />

      <EmptyState
        title="Batch Record View"
        description={`Detailed discrepancy analysis for batch #${id} will be populated once the reconciliation engine executes.`}
        icon={GitCompare}
        phaseNotice="Phase 02/03 will connect this view to PostgreSQL batch tables."
      />
    </div>
  );
};
