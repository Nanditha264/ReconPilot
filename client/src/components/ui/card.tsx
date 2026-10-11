import React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'muted' | 'flat' | 'elevated';
}

export const Card: React.FC<CardProps> = ({
  className,
  variant = 'default',
  children,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-finance-800 border border-finance-600/70 shadow-sm text-finance-200',
    muted: 'bg-finance-850 border border-finance-700/80 text-finance-300',
    flat: 'bg-finance-800 border border-transparent text-finance-200',
    elevated: 'bg-finance-750 border border-finance-600 shadow-md text-finance-100',
  }[variant];

  return (
    <div className={cn('rounded-lg p-5 transition-colors', variantStyles, className)} {...props}>
      {children}
    </div>
  );
};
