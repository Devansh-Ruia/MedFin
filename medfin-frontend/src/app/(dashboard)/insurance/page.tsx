// src/app/(dashboard)/insurance/page.tsx - Insurance Analysis

'use client';

import React, { useEffect } from 'react';
import { 
  Shield, 
  AlertTriangle, 
  Calendar, 
  TrendingUp,
  CheckCircle2,
  Clock
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { cn, formatCurrency, formatDate, calculateProgressPercent } from '@/lib/utils';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ProgressTracker } from '@/components/shared/ProgressTracker';
import { RecommendationCard } from '@/components/shared/RecommendationCard';
import type { InsuranceAnalysisResponse, CoverageWarning, BenefitUtilization } from '@/types';

export default function InsuranceAnalysisPage() {
  const { data: insurance, isLoading, error, execute: fetchInsurance } = useApi<InsuranceAnalysisResponse, [string]>(
    (userId) => api.analyzeInsurance(userId)
  );

  useEffect(() => {
    fetchInsurance('current-user');
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingSpinner size="lg" text="Analyzing your insurance coverage..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={() => fetchInsurance('current-user')} className="btn btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!insurance) return null;

  const benefitChartData = insurance.benefitUtilization.map((benefit) => ({
    name: benefit.benefitType,
    used: benefit.used,
    remaining: benefit.remaining,
    percent: benefit.percentUsed,
  }));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Insurance Analysis</h1>
          <p className="text-gray-600 mt-1">
            {insurance.planName} • {insurance.planType}
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Calendar className="w-4 h-4 text-gray-500" />
          <span className="text-gray-600">
            Plan year ends {formatDate(insurance.planYearEnd)} ({insurance.daysUntilReset} days)
          </span>
        </div>
      </div>

      {/* Deductible & OOP Trackers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Deductible Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-gray-900">Deductible Progress</h2>
          </div>
          <div className="card-body space-y-4">
            <ProgressTracker
              label="Individual"
              used={insurance.deductible.individual.used}
              total={insurance.deductible.individual.limit}
              variant="gradient"
              size="lg"
            />
            <ProgressTracker
              label="Family"
              used={insurance.deductible.family.used}
              total={insurance.deductible.family.limit}
              variant="gradient"
              size="lg"
            />
            <div className="pt-2 border-t border-gray-100">
              <p className={cn(
                'text-sm font-medium',
                insurance.deductible.percentMet >= 70 ? 'text-green-600' : 'text-gray-600'
              )}>
                {insurance.deductible.percentMet >= 100 ? (
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    Deductible fully met!
                  </span>
                ) : (
                  `${insurance.deductible.percentMet}% of deductible met`
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Out-of-Pocket Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-gray-900">Out-of-Pocket Maximum</h2>
          </div>
          <div className="card-body space-y-4">
            <ProgressTracker
              label="Individual"
              used={insurance.outOfPocket.individual.used}
              total={insurance.outOfPocket.individual.limit}
              variant="gradient"
              size="lg"
            />
            <ProgressTracker
              label="Family"
              used={insurance.outOfPocket.family.used}
              total={insurance.outOfPocket.family.limit}
              variant="gradient"
              size="lg"
            />
            <div className="pt-2 border-t border-gray-100">
              <p className={cn(
                'text-sm font-medium',
                insurance.outOfPocket.percentMet >= 90 ? 'text-green-600' : 'text-gray-600'
              )}>
                {insurance.outOfPocket.percentMet >= 100 ? (
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    OOP max reached - no more cost sharing!
                  </span>
                ) : (
                  `${formatCurrency(insurance.outOfPocket.individual.remaining)} remaining to OOP max`
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Coverage Warnings */}
      {insurance.coverageWarnings.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">Coverage Alerts</h2>
          {insurance.coverageWarnings.map((warning, idx) => (
            <WarningCard key={idx} warning={warning} />
          ))}
        </div>
      )}

      {/* Benefit Utilization Chart */}
      {insurance.benefitUtilization.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-gray-900">Benefit Utilization</h2>
          </div>
          <div className="card-body">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={benefitChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                  <XAxis type="number" tickFormatter={(v) => formatCurrency(v)} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      formatCurrency(value),
                      name === 'used' ? 'Used' : 'Remaining',
                    ]}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="used" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="remaining" stackId="a" fill="#e5e7eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Benefit Details */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {insurance.benefitUtilization.map((benefit) => (
                <BenefitCard key={benefit.benefitType} benefit={benefit} />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* HSA/FSA Balance */}
      {insurance.hsaFsaBalance !== undefined && (
        <div className="card bg-purple-50 border-purple-200">
          <div className="card-body">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Shield className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-purple-700">HSA/FSA Balance Available</p>
                <p className="text-2xl font-bold text-purple-900">
                  {formatCurrency(insurance.hsaFsaBalance)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Year-End Projection */}
      <div className="card">
        <div className="card-header">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Year-End Projection
          </h2>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Projected Spending</p>
              <p className="text-xl font-bold text-gray-900">
                {formatCurrency(insurance.estimatedYearEndPosition.projectedSpending)}
              </p>
            </div>
            <div className={cn(
              'p-4 rounded-lg',
              insurance.estimatedYearEndPosition.projectedDeductibleMet 
                ? 'bg-green-50' 
                : 'bg-yellow-50'
            )}>
              <p className="text-sm text-gray-600">Deductible Status</p>
              <p className={cn(
                'text-xl font-bold',
                insurance.estimatedYearEndPosition.projectedDeductibleMet 
                  ? 'text-green-600' 
                  : 'text-yellow-600'
              )}>
                {insurance.estimatedYearEndPosition.projectedDeductibleMet 
                  ? 'Will be met' 
                  : 'May not be met'}
              </p>
            </div>
            <div className={cn(
              'p-4 rounded-lg',
              insurance.estimatedYearEndPosition.projectedOopMet 
                ? 'bg-green-50' 
                : 'bg-blue-50'
            )}>
              <p className="text-sm text-gray-600">OOP Max Status</p>
              <p className={cn(
                'text-xl font-bold',
                insurance.estimatedYearEndPosition.projectedOopMet 
                  ? 'text-green-600' 
                  : 'text-blue-600'
              )}>
                {insurance.estimatedYearEndPosition.projectedOopMet 
                  ? 'Will be reached' 
                  : 'Not expected'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Optimization Suggestions */}
      {insurance.optimizationSuggestions.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Optimization Opportunities</h2>
          <div className="space-y-3">
            {insurance.optimizationSuggestions.map((rec, idx) => (
              <RecommendationCard
                key={rec.id}
                recommendation={{
                  recommendation: rec,
                  rankingFactors: {
                    urgencyScore: 70,
                    savingsImpactScore: 80,
                    successScore: 75,
                    riskReductionScore: 60,
                    easeScore: 70,
                  },
                  compositeScore: 75,
                  finalRank: idx + 1,
                  rationale: 'Based on insurance analysis',
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function WarningCard({ warning }: { warning: CoverageWarning }) {
  const severityStyles = {
    critical: 'bg-red-50 border-red-200',
    warning: 'bg-orange-50 border-orange-200',
    caution: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  };

  const iconColors = {
    critical: 'text-red-600',
    warning: 'text-orange-600',
    caution: 'text-yellow-600',
    info: 'text-blue-600',
  };

  return (
    <div className={cn('p-4 rounded-lg border', severityStyles[warning.severity])}>
      <div className="flex items-start gap-3">
        <AlertTriangle className={cn('w-5 h-5 flex-shrink-0', iconColors[warning.severity])} />
        <div className="flex-1">
          <p className="font-medium text-gray-900">{warning.title}</p>
          <p className="text-sm text-gray-600 mt-1">{warning.description}</p>
          {warning.recommendation && (
            <p className="text-sm text-blue-600 mt-2">💡 {warning.recommendation}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function BenefitCard({ benefit }: { benefit: BenefitUtilization }) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">{benefit.benefitType}</span>
        <span className="text-sm text-gray-500">{benefit.percentUsed}%</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full',
            benefit.percentUsed >= 80 ? 'bg-green-500' : 'bg-blue-500'
          )}
          style={{ width: `${Math.min(100, benefit.percentUsed)}%` }}
        />
      </div>
      <div className="flex justify-between mt-1 text-xs text-gray-500">
        <span>Used: {formatCurrency(benefit.used)}</span>
        <span>Left: {formatCurrency(benefit.remaining)}</span>
      </div>
      {benefit.expiresAt && (
        <p className="text-xs text-orange-600 mt-1 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Expires {formatDate(benefit.expiresAt)}
        </p>
      )}
    </div>
  );
}