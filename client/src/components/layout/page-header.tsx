import React from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface PageHeaderProps {
  title: string;
  description?: string;
  badgeText?: string;
  badgeVariant?: 'neutral' | 'success' | 'warning' | 'danger' | 'info';
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badgeText,
  badgeVariant = 'neutral',
  actions,
  className,
}) => {
  return (
    <div className={cn('mb-6 pb-4 border-b border-finance-700/80 flex flex-col md:flex-row md:items-center md:justify-between gap-4', className)}>
      <div className="min-w-0">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-finance-100">{title}</h1>
          {badgeText && (
            <Badge variant={badgeVariant} size="sm">{badgeText}</Badge>
          )}
        </div>
        {description && (
          <p className="mt-1 text-xs md:text-sm text-finance-400 max-w-3xl leading-relaxed">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
};
