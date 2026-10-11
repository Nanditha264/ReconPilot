import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  CheckSquare,
  Square,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

interface ChecklistItem {
  id: string;
  label: string;
  description: string;
  targetRoute: string;
}

const CHECKLIST_ITEMS: ChecklistItem[] = [
  {
    id: 'env',
    label: '1. Confirm Demo Environment & Integrity',
    description: 'Verify live PostgreSQL connectivity, seeded demo records, and zero automated ledger mutations.',
    targetRoute: '/dashboard',
  },
  {
    id: 'dashboard',
    label: '2. Review Reconciliation Health & KPIs',
    description: 'Inspect executive KPI cards, currency-separated exposures (INR/USD), and 14-day exception trends.',
    targetRoute: '/dashboard',
  },
  {
    id: 'scenario',
    label: '3. Select Representative Discrepancy Scenario',
    description: 'Use Demo Scenario Selector to locate an actual exception (e.g. Amount Mismatch or Missing Payment).',
    targetRoute: '/exceptions',
  },
  {
    id: 'evidence',
    label: '4. Audit Correlated Financial Evidence Dossier',
    description: 'Inspect verified gateway ledger lines, processor settlement records, and corroborated facts.',
    targetRoute: '/exceptions',
  },
  {
    id: 'ai',
    label: '5. Inspect AI Root Cause Investigation',
    description: 'Review schema-constrained diagnostic hypotheses citing real evidence IDs and operator warnings.',
    targetRoute: '/exceptions',
  },
  {
    id: 'approval',
    label: '6. Demonstrate Human Approval Governance',
    description: 'Show resolution proposal submission, reviewer separation of duties, and rejection/approval logging.',
    targetRoute: '/review',
  },
  {
    id: 'command_center',
    label: '7. Revisit Operations Queue & Telemetry',
    description: 'Verify queue filtering, status updates, and operational analytics in the Command Center.',
    targetRoute: '/dashboard',
  },
];

export const DemoChecklist: React.FC<{ className?: string }> = ({ className = '' }) => {
  const navigate = useNavigate();
  const [completedItems, setCompletedItems] = useState<Record<string, boolean>>(() => {
    const saved = localStorage.getItem('reconpilot_demo_checklist');
    return saved ? JSON.parse(saved) : {};
  });
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  const toggleItem = (id: string) => {
    setCompletedItems((prev) => {
      const updated = { ...prev, [id]: !prev[id] };
      localStorage.setItem('reconpilot_demo_checklist', JSON.stringify(updated));
      return updated;
    });
  };

  const completedCount = Object.values(completedItems).filter(Boolean).length;
  const progressPercent = Math.round((completedCount / CHECKLIST_ITEMS.length) * 100);

  return (
    <Card className={`p-0 overflow-hidden bg-finance-800 border-finance-700/80 shadow-sm ${className}`}>
      {/* Header */}
      <div
        className="p-3.5 bg-gradient-to-r from-emerald-950/40 via-finance-800 to-finance-800 border-b border-finance-700/80 flex items-center justify-between cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <div className="p-1 bg-emerald-500/20 text-emerald-400 rounded-md border border-emerald-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-finance-100 uppercase tracking-wider">
                Presenter Demo Readiness Checklist
              </h3>
              <Badge variant="success" size="sm" className="font-mono text-[9px] py-0 px-1">
                {completedCount}/{CHECKLIST_ITEMS.length} Completed ({progressPercent}%)
              </Badge>
            </div>
            <p className="text-[11px] text-finance-400">
              Interactive preparation workflow for evaluators and judges.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-finance-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-finance-400" />
          )}
        </div>
      </div>

      {/* Checklist items */}
      {isExpanded && (
        <div className="p-3.5 space-y-2">
          {/* Progress bar */}
          <div className="w-full bg-finance-700/80 rounded-full h-1 mb-2 overflow-hidden">
            <div
              className="bg-emerald-500 h-1 transition-all duration-300 rounded-full"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            {CHECKLIST_ITEMS.map((item) => {
              const isDone = Boolean(completedItems[item.id]);
              return (
                <div
                  key={item.id}
                  className={`p-2.5 rounded-md border transition-all flex items-start gap-2 min-w-0 ${
                    isDone
                      ? 'bg-emerald-950/20 border-emerald-800/60 text-finance-300'
                      : 'bg-finance-850 border-finance-700/80 text-finance-300 hover:bg-finance-750'
                  }`}
                >
                  <button
                    onClick={() => toggleItem(item.id)}
                    className="mt-0.5 text-finance-500 hover:text-finance-300 transition-colors shrink-0"
                    title={isDone ? 'Mark as incomplete' : 'Mark as complete'}
                  >
                    {isDone ? (
                      <CheckSquare className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Square className="w-3.5 h-3.5 text-finance-500" />
                    )}
                  </button>

                  <div className="flex-1 space-y-0.5 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className={`font-semibold text-xs truncate ${isDone ? 'line-through text-finance-500' : 'text-finance-100'}`}>
                        {item.label}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate(item.targetRoute)}
                        className="h-5 px-1.5 text-[9px] gap-0.5 font-normal text-finance-400 hover:text-white shrink-0"
                      >
                        <span>Jump</span>
                        <ArrowRight className="w-2.5 h-2.5" />
                      </Button>
                    </div>
                    <p className="text-[11px] text-finance-400 leading-snug">
                      {item.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
};
