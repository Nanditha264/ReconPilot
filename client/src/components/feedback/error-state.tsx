import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Service Error',
  message,
  onRetry,
  className,
}) => {
  return (
    <div className={cn('p-6 bg-rose-50/50 border border-rose-200 rounded-lg text-left', className)}>
      <div className="flex items-start gap-3">
        <div className="p-2 bg-rose-100 rounded-full text-rose-600 shrink-0">
          <AlertCircle className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-rose-900">{title}</h3>
          <p className="mt-1 text-sm text-rose-700 font-mono break-all">{message}</p>
          {onRetry && (
            <div className="mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="border-rose-300 text-rose-800 hover:bg-rose-100 bg-white"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                Retry Request
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
