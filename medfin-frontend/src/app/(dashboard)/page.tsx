// src/app/(dashboard)/page.tsx - Navigation Plan Dashboard

'use client';

import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { cn } from '@/lib/utils';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { PlanSummary } from '@/components/dashboard/PlanSummary';
import { ActionTimeline } from '@/components/dashboard/ActionTimeline';
import { QuickStats } from '@/components/dashboard/QuickStats';
import type { NavigationPlanResponse } from '@/types';

export default function DashboardPage() {
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());
  const { data: plan, isLoading, error, execute: fetchPlan } = useApi<NavigationPlanResponse, [string]>(
    (userId) => api.getNavigationPlan(userId)
  );

  useEffect(() => {
    // In production, get userId from auth context
    fetchPlan('current-user');
  }, []);

  const handleRefresh = async () => {
    await fetchPlan('current-user');
  };

  const handleActionComplete = async (id: string) => {
    try {
      await api.markActionComplete('current-user', id);
      setCompletedIds((prev) => new Set([...prev, id]));
    } catch (err) {
      console.error('Failed to mark action complete:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading your financial health plan..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={handleRefresh} className="btn btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!plan) {
    return null;
  }

  // Calculate savings breakdown by category
  const savingsBreakdown = plan.recommendations.reduce((acc, rec) => {
    const category = rec.recommendation.category;
    const existing = acc.find((item) => item.category === category);
    if (existing) {
      existing.amount += rec.recommendation.savingsEstimate.expected;
    } else {
      acc.push({ category, amount: rec.recommendation.savingsEstimate.expected });
    }
    return acc;
  }, [] as { category: string; amount: number }[]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Navigation Plan</h1>
          <p className="text-gray-600 mt-1">
            Your personalized healthcare financial action plan
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="btn btn-outline flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Plan
        </button>
      </div>

      {/* Plan Summary */}
      <PlanSummary plan={plan} />

      {/* Stats Charts */}
      <QuickStats
        dimensionalScores={plan.riskAssessment.dimensionalScores}
        savingsBreakdown={savingsBreakdown}
      />

      {/* Action Timeline */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Action Plan</h2>
        <ActionTimeline
          actionPlan={plan.actionPlan}
          onActionComplete={handleActionComplete}
          completedIds={completedIds}
        />
      </div>

      {/* Footer Meta */}
      <div className="text-center text-sm text-gray-500 pt-4 border-t">
        <p>
          Plan generated at {new Date(plan.generatedAt).toLocaleString()} • 
          Confidence: {Math.round(plan.confidence * 100)}% • 
          Processing time: {plan.processingTimeMs}ms
        </p>
      </div>
    </div>
  );
}