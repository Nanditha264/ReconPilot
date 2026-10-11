import React from 'react';
import { useDemo } from '@/hooks/use-demo';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Eye, ShieldCheck, HelpCircle } from 'lucide-react';

export const DemoBanner: React.FC = () => {
  const { isDemoMode, toggleDemoMode, startWalkthrough, isWalkthroughActive } = useDemo();

  return (
    <div className="bg-gradient-to-r from-amber-950/40 via-finance-900 to-amber-950/30 border-b border-amber-900/60 px-4 py-1.5 flex flex-wrap items-center justify-between gap-2.5 text-xs text-amber-200/90 shrink-0">
      <div className="flex items-center gap-2 flex-wrap min-w-0">
        <Badge
          variant={isDemoMode ? 'warning' : 'neutral'}
          size="sm"
          className="font-bold gap-1 tracking-wide uppercase px-2 py-0 text-[10px]"
        >
          <Sparkles className="w-3 h-3 text-amber-400" />
          {isDemoMode ? 'Judge Demo Mode' : 'Production Mode'}
        </Badge>
        <span className="font-medium text-amber-100 text-[11px]">
          Seeded Financial Records:
        </span>
        <span className="text-finance-400 text-[11px] hidden md:inline truncate">
          Active Razorpay + Bank ledger audit. Zero automated financial mutation.
        </span>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {!isWalkthroughActive && (
          <button
            onClick={startWalkthrough}
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-600/90 hover:bg-amber-500 text-white font-medium text-[11px] shadow-xs transition-colors"
          >
            <Eye className="w-3 h-3" />
            <span>Start Guided Walkthrough</span>
          </button>
        )}

        <button
          onClick={toggleDemoMode}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-finance-700 bg-finance-800 hover:bg-finance-700 text-finance-300 font-medium text-[11px] transition-colors"
          title="Toggle visual demo indicators"
        >
          <ShieldCheck className="w-3 h-3 text-amber-400" />
          <span>{isDemoMode ? 'Demo Active' : 'Enable Demo'}</span>
        </button>

        <span
          className="text-finance-500 hover:text-finance-300 cursor-help"
          title="Demo Mode visual indicators clearly delineate seeded evaluation records from live customer production activity."
        >
          <HelpCircle className="w-3.5 h-3.5" />
        </span>
      </div>
    </div>
  );
};
