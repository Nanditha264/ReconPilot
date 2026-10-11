import React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'neutral' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'neutral',
  size = 'md',
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full';

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  }[size];

  const variantStyles = {
    neutral: 'bg-finance-700/60 text-finance-300 border border-finance-600',
    success: 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/80',
    warning: 'bg-amber-950/70 text-amber-400 border border-amber-800/80',
    danger: 'bg-rose-950/70 text-rose-400 border border-rose-800/80',
    info: 'bg-sky-950/70 text-sky-400 border border-sky-800/80',
  }[variant];

  return (
    <span className={cn(baseStyles, sizeStyles, variantStyles, className)} {...props}>
      {children}
    </span>
  );
};
