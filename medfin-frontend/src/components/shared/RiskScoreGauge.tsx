// src/components/shared/RiskScoreGauge.tsx

'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { cn, getRiskGaugeColor } from '@/lib/utils';
import type { RiskCategory } from '@/types';

interface RiskScoreGaugeProps {
  score: number;
  category: RiskCategory;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export function RiskScoreGauge({
  score,
  category,
  size = 'md',
  showLabel = true,
  className,
}: RiskScoreGaugeProps) {
  const dimensions = {
    sm: { width: 120, height: 80, innerRadius: 35, outerRadius: 50 },
    md: { width: 180, height: 110, innerRadius: 50, outerRadius: 70 },
    lg: { width: 240, height: 140, innerRadius: 65, outerRadius: 90 },
  };

  const { width, height, innerRadius, outerRadius } = dimensions[size];
  const color = getRiskGaugeColor(score);

  const data = [
    { value: score, fill: color },
    { value: 100 - score, fill: '#e5e7eb' },
  ];

  const categoryLabels: Record<RiskCategory, string> = {
    critical: 'Critical Risk',
    high: 'High Risk',
    moderate: 'Moderate Risk',
    low: 'Low Risk',
    minimal: 'Minimal Risk',
  };

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <div style={{ width, height }} className="relative">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={innerRadius}
              outerRadius={outerRadius}
              paddingAngle={0}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div 
          className="absolute inset-0 flex items-end justify-center pb-2"
          style={{ top: size === 'sm' ? '20%' : '30%' }}
        >
          <span 
            className="font-bold"
            style={{ 
              fontSize: size === 'sm' ? '1.5rem' : size === 'md' ? '2rem' : '2.5rem',
              color 
            }}
          >
            {score}
          </span>
        </div>
      </div>
      {showLabel && (
        <p 
          className="mt-1 font-medium"
          style={{ color, fontSize: size === 'sm' ? '0.75rem' : '0.875rem' }}
        >
          {categoryLabels[category]}
        </p>
      )}
    </div>
  );
}