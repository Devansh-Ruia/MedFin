// src/components/shared/SavingsCard.tsx

'use client';

import React from 'react';
import { TrendingUp, DollarSign } from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import type { TotalSavings } from '@/types';

interface SavingsCardProps {
  savings: TotalSavings;
  title?: string;
  variant?: 'default' | 'compact' | 'highlight';
  className?: string;
}

export function SavingsCard({
  savings,
  title = 'Potential Savings',
  variant = 'default',
  className,
}: SavingsCardProps) {
  if (variant === 'compact') {
    return (
      <div className={cn('flex items-center gap-2 p-3 bg-green-50 rounded-lg', className)}>
        <DollarSign className="w-5 h-5 text-green-600" />
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="font-semibold text-green-700">{formatCurrency(savings.expected)}</p>
        </div>
      </div>
    );
  }

  if (variant === 'highlight') {
    return (
      <div className={cn(
        'relative overflow-hidden p-6 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl text-white',
        className
      )}>
        <div className="absolute top-0 right-0 w-32 h-32 -mr-8 -mt-8 bg-white/10 rounded-full" />
        <div className="relative">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5" />
            <span className="text-sm font-medium text-green-100">{title}</span>
          </div>
          <p className="text-4xl font-bold mb-2">
            {formatCurrency(savings.expected)}
          </p>
          <p className="text-sm text-green-100">
            Range: {formatCurrency(savings.min)} – {formatCurrency(savings.max)}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      'p-4 bg-white border border-gray-200 rounded-xl shadow-sm',
      className
    )}>
      <div className="flex items-center gap-2 mb-3">
        <div className="p-2 bg-green-100 rounded-lg">
          <DollarSign className="w-5 h-5 text-green-600" />
        </div>
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <p className="text-3xl font-bold text-green-600 mb-1">
        {formatCurrency(savings.expected)}
      </p>
      <p className="text-sm text-gray-500">
        Range: {formatCurrency(savings.min)} – {formatCurrency(savings.max)}
      </p>
    </div>
  );
}