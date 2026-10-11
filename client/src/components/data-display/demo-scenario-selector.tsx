import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { demoService } from '@/services/demo';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Sparkles,
  ArrowRight,
  AlertTriangle,
  FileQuestion,
  HelpCircle,
  Clock,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { DemoScenarioItem } from '@/types/api';

const scenarioIcons: Record<string, React.ReactNode> = {
  AMOUNT_MISMATCH: <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />,
  MISSING_PAYMENT: <FileQuestion className="w-4 h-4 text-amber-400 shrink-0" />,
  MISSING_SETTLEMENT: <Clock className="w-4 h-4 text-sky-400 shrink-0" />,
  REFUND_MISMATCH: <RefreshCw className="w-4 h-4 text-purple-400 shrink-0" />,
  FEE_MISMATCH: <Layers className="w-4 h-4 text-indigo-400 shrink-0" />,
  DELAYED_SETTLEMENT: <Clock className="w-4 h-4 text-cyan-400 shrink-0" />,
  CONFLICTING_EVIDENCE: <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />,
};

interface DemoScenarioSelectorProps {
  onSelectScenario?: (scenario: DemoScenarioItem) => void;
  className?: string;
}

export const DemoScenarioSelector: React.FC<DemoScenarioSelectorProps> = ({
  onSelectScenario,
  className = '',
}) => {
  const navigate = useNavigate();

  const {
    data: demoData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['demo', 'scenarios'],
    queryFn: demoService.getScenarios,
    staleTime: 60000,
  });

  const handleLaunchScenario = (scenario: DemoScenarioItem) => {
    if (onSelectScenario) {
      onSelectScenario(scenario);
    }
    if (scenario.available && scenario.exception_id) {
      navigate(`/exceptions/${scenario.exception_id}`);
    }
  };

  return (
    <Card className={`p-0 overflow-hidden bg-finance-800 border-finance-700/80 shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-3.5 bg-gradient-to-r from-amber-950/40 via-finance-800 to-finance-800 border-b border-finance-700/80 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1 bg-amber-500/20 text-amber-400 rounded-md border border-amber-500/30">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-finance-100 uppercase tracking-wider flex items-center gap-2">
              <span>Demo Scenario Selector</span>
              <Badge variant="warning" size="sm" className="font-mono text-[9px] py-0 px-1">
                {demoData ? `${demoData.total_available} Scenarios Live` : 'Live Ground Truth'}
              </Badge>
            </h3>
            <p className="text-[11px] text-finance-400">
              Verified discrepancy scenarios derived from real accessible database records.
            </p>
          </div>
        </div>

        <button
          onClick={() => refetch()}
          className="text-finance-400 hover:text-finance-200 p-1 rounded transition-colors text-xs flex items-center gap-1 hover:bg-finance-700/60"
          title="Refresh scenario discovery"
        >
          <RefreshCw className="w-3 h-3" />
          <span className="text-[10px]">Refresh</span>
        </button>
      </div>

      {/* Scenarios Grid */}
      <div className="p-3.5">
        {isLoading && (
          <div className="py-8 text-center text-xs text-finance-400 space-y-2">
            <RefreshCw className="w-4 h-4 mx-auto animate-spin text-brand-primary" />
            <p>Discovering real exceptions in active database...</p>
          </div>
        )}

        {isError && (
          <div className="py-3 px-3 bg-rose-950/40 border border-rose-800/80 rounded-md text-xs text-rose-300">
            Could not retrieve demo scenarios. Please ensure backend is running.
          </div>
        )}

        {demoData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {demoData.scenarios.map((scenario) => {
              const icon = scenarioIcons[scenario.scenario_key] || <HelpCircle className="w-4 h-4 text-finance-400 shrink-0" />;
              return (
                <div
                  key={scenario.scenario_key}
                  className={`p-3 rounded-md border text-xs flex flex-col justify-between transition-all min-w-0 ${
                    scenario.available
                      ? 'border-finance-700 bg-finance-850 hover:bg-finance-750 hover:border-brand-primary/60 hover:shadow-sm'
                      : 'border-dashed border-finance-700/60 bg-finance-900/40 opacity-50'
                  }`}
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-start justify-between gap-1.5">
                      <div className="flex items-center gap-1.5 font-semibold text-finance-100 text-xs min-w-0">
                        {icon}
                        <span className="truncate">{scenario.title.replace('Discrepancy: ', '')}</span>
                      </div>
                      {scenario.available ? (
                        <Badge variant="success" size="sm" className="font-mono text-[9px] py-0 px-1 shrink-0">
                          Available
                        </Badge>
                      ) : (
                        <Badge variant="neutral" size="sm" className="font-mono text-[9px] py-0 px-1 shrink-0">
                          Unavailable
                        </Badge>
                      )}
                    </div>

                    <p className="text-[11px] text-finance-400 line-clamp-2 leading-relaxed">
                      {scenario.description}
                    </p>

                    {scenario.available && scenario.financial_impact && (
                      <div className="pt-1 flex items-center justify-between text-[11px] font-mono">
                        <span className="text-finance-500">Variance Impact:</span>
                        <span className="font-bold text-finance-100">
                          {scenario.currency || 'INR'} {parseFloat(scenario.financial_impact).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    )}

                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {scenario.tags.map((tag, i) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.2 rounded bg-finance-700/60 text-finance-300 text-[9px] font-medium"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2 mt-2 border-t border-finance-700/80 flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono text-finance-400 truncate">
                      {scenario.reference_id ? `Ref: ${scenario.reference_id}` : 'No Record'}
                    </span>

                    <Button
                      size="sm"
                      variant={scenario.available ? 'outline' : 'ghost'}
                      disabled={!scenario.available}
                      onClick={() => handleLaunchScenario(scenario)}
                      className="text-[10px] h-6 px-2 gap-1 font-medium shrink-0"
                    >
                      <span>Explore</span>
                      <ArrowRight className="w-2.5 h-2.5" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
};
