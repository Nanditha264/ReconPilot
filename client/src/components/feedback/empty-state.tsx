import React from 'react';
import { LucideIcon, Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  phaseNotice?: string;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = Inbox,
  action,
  phaseNotice = 'Planned for subsequent phases. No dummy data generated.',
  className,
}) => {
  return (
    <div className={cn('p-12 text-center border-2 border-dashed border-finance-300 rounded-lg bg-finance-50/50', className)}>
      <div className="mx-auto w-12 h-12 rounded-full bg-white border border-finance-200 flex items-center justify-center text-finance-400 mb-4 shadow-sm">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-finance-800">{title}</h3>
      <p className="mt-1 text-sm text-finance-500 max-w-md mx-auto">{description}</p>
      
      {phaseNotice && (
        <div className="mt-3 inline-block bg-finance-100 text-finance-600 px-3 py-1 rounded text-xs font-mono">
          ℹ️ {phaseNotice}
        </div>
      )}

      {action && (
        <div className="mt-6">
          {action}
        </div>
      )}
    </div>
  );
};
