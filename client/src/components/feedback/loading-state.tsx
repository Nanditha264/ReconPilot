import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading operational data...',
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-12 text-center', className)}>
      <div className="relative flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-finance-200 border-t-brand-primary rounded-full animate-spin"></div>
      </div>
      <p className="mt-4 text-sm font-medium text-finance-600">{message}</p>
    </div>
  );
};
