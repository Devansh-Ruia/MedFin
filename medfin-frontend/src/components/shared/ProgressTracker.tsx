// src/components/shared/ProgressTracker.tsx

'use client';

import React from 'react';
import { cn, formatCurrency, calculateProgressPercent } from '@/lib/utils';

interface ProgressTrackerProps {
  label: string;
  used: number;
  total: number;
  showCurrency?: boolean;
  variant?: 'default' | 'gradient' | 'segmented';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ProgressTracker({
  label,
  used,
  total,
  showCurrency = true,
  variant = 'default',
  size = 'md',
  className,
}: ProgressTrackerProps) {
  const percent = calculateProgressPercent(used, total);
  const remaining = total - used;

  const heightClass = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  }[size];

  const getProgressColor = () => {
    if (percent >= 90) return 'bg-green-500';
    if (percent >= 70) return 'bg-yellow-500';
    if (percent >= 50) return 'bg-blue-500';
    return 'bg-gray-400';
  };

  const formatValue = (val: number) => 
    showCurrency ? formatCurrency(val) : val.toLocaleString();

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex justify-between items-baseline">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm text-gray-500">
          {formatValue(used)} / {formatValue(total)}
        </span>
      </div>

      <div className={cn('w-full bg-gray-200 rounded-full overflow-hidden', heightClass)}>
        {variant === 'gradient' ? (
          <div
            className={cn('h-full rounded-full transition-all duration-500 bg-gradient-to-r from-blue-500 to-green-500')}
            style={{ width: `${percent}%` }}
          />
        ) : variant === 'segmented' ? (
          <div className="h-full flex gap-0.5">
            {[...Array(10)].map((_, i) => (
              <div
                key={i}
                className={cn(
                  'flex-1 rounded-sm transition-colors',
                  i < Math.floor(percent / 10) ? getProgressColor() : 'bg-gray-200'
                )}
              />
            ))}
          </div>
        ) : (
          <div
            className={cn('h-full rounded-full transition-all duration-500', getProgressColor())}
            style={{ width: `${percent}%` }}
          />
        )}
      </div>

      <div className="flex justify-between text-xs text-gray-500">
        <span>{percent}% used</span>
        <span>{formatValue(remaining)} remaining</span>
      </div>
    </div>
  );
}