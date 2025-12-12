// src/components/dashboard/PlanSummary.tsx

'use client';

import React from 'react';
import { Target, TrendingUp, AlertCircle, Clock, CheckCircle2 } from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { RiskScoreGauge } from '@/components/shared/RiskScoreGauge';
import { SavingsCard } from '@/components/shared/SavingsCard';
import type { NavigationPlanResponse } from '@/types';

interface PlanSummaryProps {
  plan: NavigationPlanResponse;
  className?: string;
}

export function PlanSummary({ plan, className }: PlanSummaryProps) {
  const { riskAssessment, totalPotentialSavings, recommendations, criticalActionCount, keyTakeaways } = plan;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Executive Summary */}
      <div className="p-6 bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl text-white">
        <h2 className="text-xl font-semibold mb-2">Your Financial Health Summary</h2>
        <p className="text-slate-300">{plan.executiveSummary}</p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Risk Score */}
        <div className="p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
          <RiskScoreGauge
            score={riskAssessment.overallScore}
            category={riskAssessment.category}
            size="sm"
          />
        </div>

        {/* Total Savings */}
        <SavingsCard savings={totalPotentialSavings} variant="compact" />

        {/* Action Count */}
        <div className="p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Target className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Actions Available</p>
              <p className="text-2xl font-bold text-gray-900">{recommendations.length}</p>
            </div>
          </div>
        </div>

        {/* Critical Actions */}
        <div className="p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-lg',
              criticalActionCount > 0 ? 'bg-red-100' : 'bg-green-100'
            )}>
              {criticalActionCount > 0 ? (
                <AlertCircle className="w-5 h-5 text-red-600" />
              ) : (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              )}
            </div>
            <div>
              <p className="text-sm text-gray-600">Critical Actions</p>
              <p className={cn(
                'text-2xl font-bold',
                criticalActionCount > 0 ? 'text-red-600' : 'text-green-600'
              )}>
                {criticalActionCount}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Takeaways */}
      {keyTakeaways.length > 0 && (
        <div className="p-5 bg-blue-50 border border-blue-200 rounded-xl">
          <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Key Insights
          </h3>
          <ul className="space-y-2">
            {keyTakeaways.map((takeaway, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-blue-800">
                <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center bg-blue-200 rounded-full text-xs font-medium">
                  {idx + 1}
                </span>
                {takeaway}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Alerts */}
      {plan.alerts.length > 0 && (
        <div className="space-y-2">
          {plan.alerts.map((alert, idx) => (
            <div
              key={idx}
              className={cn(
                'p-4 rounded-lg border flex items-start gap-3',
                alert.severity === 'critical' && 'bg-red-50 border-red-200',
                alert.severity === 'warning' && 'bg-orange-50 border-orange-200',
                alert.severity === 'caution' && 'bg-yellow-50 border-yellow-200',
                alert.severity === 'info' && 'bg-blue-50 border-blue-200'
              )}
            >
              <AlertCircle className={cn(
                'w-5 h-5 flex-shrink-0',
                alert.severity === 'critical' && 'text-red-600',
                alert.severity === 'warning' && 'text-orange-600',
                alert.severity === 'caution' && 'text-yellow-600',
                alert.severity === 'info' && 'text-blue-600'
              )} />
              <div>
                <p className="font-medium text-gray-900">{alert.title}</p>
                <p className="text-sm text-gray-600">{alert.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}