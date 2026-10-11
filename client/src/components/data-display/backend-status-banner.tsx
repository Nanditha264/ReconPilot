import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/services/health';
import { Activity, Database, CheckCircle2, AlertTriangle, XCircle, RefreshCw, Bot } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const BackendStatusBanner: React.FC = () => {
  const {
    data: liveness,
    isError: livenessError,
    isLoading: livenessLoading,
    refetch: refetchLiveness,
  } = useQuery({
    queryKey: ['health', 'liveness'],
    queryFn: healthApi.getLiveness,
    refetchInterval: 15000,
  });

  const {
    data: readiness,
    isError: readinessError,
    isLoading: readinessLoading,
    refetch: refetchReadiness,
  } = useQuery({
    queryKey: ['health', 'readiness'],
    queryFn: healthApi.getReadiness,
    refetchInterval: 15000,
    retry: false,
  });

  const handleRefresh = () => {
    refetchLiveness();
    refetchReadiness();
  };

  const isLivenessOk = Boolean(liveness && !livenessError);
  const isDbOk = Boolean(readiness?.database?.connected && !readinessError);

  return (
    <div className="bg-finance-900 border-b border-finance-700/80 px-4 py-1.5 text-xs text-finance-300 flex flex-wrap items-center justify-between gap-3 shrink-0">
      <div className="flex items-center gap-3.5 flex-wrap">
        {/* API Liveness */}
        <div className="flex items-center gap-1.5 font-medium text-[11px]">
          <Activity className="w-3 h-3 text-finance-400" />
          <span className="text-finance-400">API Service:</span>
          {livenessLoading ? (
            <Badge variant="neutral" size="sm" className="text-[10px] py-0">Checking...</Badge>
          ) : isLivenessOk ? (
            <Badge variant="success" size="sm" className="gap-1 text-[10px] py-0 font-medium">
              <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
              Healthy ({liveness?.environment})
            </Badge>
          ) : (
            <Badge variant="danger" size="sm" className="gap-1 text-[10px] py-0 font-medium">
              <XCircle className="w-2.5 h-2.5 text-rose-400" />
              Offline
            </Badge>
          )}
        </div>

        {/* PostgreSQL Readiness */}
        <div className="flex items-center gap-1.5 font-medium text-[11px]">
          <Database className="w-3 h-3 text-finance-400" />
          <span className="text-finance-400">PostgreSQL:</span>
          {readinessLoading ? (
            <Badge variant="neutral" size="sm" className="text-[10px] py-0">Checking...</Badge>
          ) : isDbOk ? (
            <Badge variant="success" size="sm" className="gap-1 text-[10px] py-0 font-medium">
              <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
              Connected
            </Badge>
          ) : (
            <Badge variant="warning" size="sm" className="gap-1 text-[10px] py-0 font-medium" title={readiness?.database?.message || 'Database not reachable'}>
              <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
              Unconnected
            </Badge>
          )}
        </div>

        {/* AI Provider Mode */}
        {liveness && (
          <div className="hidden md:flex items-center gap-1.5 text-finance-400 font-mono text-[11px]">
            <Bot className="w-3 h-3 text-brand-primary" />
            <span>AI Reasoner:</span>
            <span className={`font-semibold px-1 py-0.5 rounded text-[10px] ${
              liveness.integrations.ai_provider === 'mock' 
                ? 'bg-finance-800 text-finance-300 border border-finance-700' 
                : 'bg-brand-primary/20 text-brand-accent border border-brand-primary/40'
            }`}>
              {liveness.integrations.ai_provider === 'mock' ? 'Deterministic Mock' : liveness.integrations.ai_provider}
            </span>
          </div>
        )}
      </div>

      <button
        onClick={handleRefresh}
        className="text-finance-400 hover:text-finance-200 flex items-center gap-1 hover:underline transition-colors ml-auto font-medium text-[11px]"
        title="Check backend status now"
      >
        <RefreshCw className="w-2.5 h-2.5" />
        <span>Check Health</span>
      </button>
    </div>
  );
};
