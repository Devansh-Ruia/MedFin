// src/components/dashboard/QuickStats.tsx

'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { cn, formatCurrency } from '@/lib/utils';
import type { RiskDimensionScore } from '@/types';

interface QuickStatsProps {
  dimensionalScores: RiskDimensionScore[];
  savingsBreakdown?: { category: string; amount: number }[];
  className?: string;
}

const DIMENSION_LABELS: Record<string, string> = {
  income_stability: 'Income',
  debt_burden: 'Debt',
  medical_debt_ratio: 'Med. Debt',
  collections_exposure: 'Collections',
  payment_history: 'Payments',
  upcoming_costs: 'Upcoming',
  insurance_gaps: 'Ins. Gaps',
  coverage_adequacy: 'Coverage',
  bill_errors: 'Bill Errors',
  affordability: 'Afford.',
};

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function QuickStats({ dimensionalScores, savingsBreakdown, className }: QuickStatsProps) {
  const riskChartData = dimensionalScores
    .sort((a, b) => b.weightedScore - a.weightedScore)
    .slice(0, 6)
    .map((d) => ({
      name: DIMENSION_LABELS[d.dimension] || d.dimension,
      score: Math.round(d.score),
      weighted: Math.round(d.weightedScore),
    }));

  return (
    <div className={cn('grid grid-cols-1 lg:grid-cols-2 gap-6', className)}>
      {/* Risk Dimensions Chart */}
      <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm">
        <h3 className="font-semibold text-gray-900 mb-4">Risk by Dimension</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={riskChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}`} />
              <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number) => [`${value}`, 'Score']}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
              />
              <Bar dataKey="score" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Savings Breakdown */}
      {savingsBreakdown && savingsBreakdown.length > 0 && (
        <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-4">Savings by Category</h3>
          <div className="h-64 flex items-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={savingsBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="amount"
                  nameKey="category"
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {savingsBreakdown.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), 'Savings']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}