import React from 'react';
import { PageHeader } from '@/components/layout/page-header';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sliders, Database, KeyRound, Cpu } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="System Settings & Policy Thresholds"
        description="Configuration parameters for financial tolerance limits, AI autonomy gates, and integrations."
        badgeText="Configuration"
        badgeVariant="neutral"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-finance-800 border-finance-700/80 shadow-sm">
          <div className="flex items-center gap-2 mb-4 text-finance-200 font-semibold">
            <Sliders className="w-5 h-5 text-brand-accent" />
            <h3>Financial Tolerance & Policy Bounds</h3>
          </div>
          <div className="space-y-4 text-sm">
            <div className="flex justify-between items-center py-2 border-b border-finance-700/60">
              <span className="text-finance-400">Amount Tolerance Limit</span>
              <span className="font-mono font-semibold text-finance-100">₹ 1.00</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-finance-700/60">
              <span className="text-finance-400">AI Auto-Classify Confidence Gate</span>
              <span className="font-mono font-semibold text-finance-100">≥ 0.90 (90%)</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-finance-700/60">
              <span className="text-finance-400">AI Flagged for Review Gate</span>
              <span className="font-mono font-semibold text-finance-100">≥ 0.75 (75%)</span>
            </div>
          </div>
        </Card>

        <Card className="bg-finance-800 border-finance-700/80 shadow-sm">
          <div className="flex items-center gap-2 mb-4 text-finance-200 font-semibold">
            <KeyRound className="w-5 h-5 text-brand-accent" />
            <h3>Integration Credentials</h3>
          </div>
          <div className="space-y-4 text-sm">
            <div className="flex justify-between items-center py-2 border-b border-finance-700/60">
              <span className="text-finance-400">Razorpay API Credentials</span>
              <Badge variant="warning" size="sm">Configured (.env)</Badge>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-finance-700/60">
              <span className="text-finance-400">AI Engine Provider</span>
              <Badge variant="neutral" size="sm" className="font-mono">mock (Safe Development)</Badge>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-finance-700/60">
              <span className="text-finance-400">Database Driver</span>
              <div className="flex items-center gap-1 font-mono text-xs font-semibold text-finance-200">
                <Database className="w-3.5 h-3.5 text-finance-400" />
                <span>PostgreSQL (psycopg3)</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="p-4 rounded-lg bg-finance-900 border border-finance-700/80 text-finance-400 text-xs font-mono">
        <Cpu className="w-4 h-4 inline-block mr-1 text-finance-400 -mt-0.5" />
        Note: Financial tolerance limits and deterministic reconciliation parameters are strictly configured via server environment settings to guarantee audit compliance.
      </div>
    </div>
  );
};
