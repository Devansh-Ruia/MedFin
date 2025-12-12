// src/components/dashboard/ActionTimeline.tsx

'use client';

import React from 'react';
import { Clock, AlertTriangle, Calendar, Repeat } from 'lucide-react';
import { cn } from '@/lib/utils';
import { RecommendationCard } from '@/components/shared/RecommendationCard';
import type { ActionPlan } from '@/types';

interface ActionTimelineProps {
  actionPlan: ActionPlan;
  onActionComplete?: (id: string) => void;
  completedIds?: Set<string>;
  className?: string;
}

const timeframeSections = [
  {
    key: 'immediate' as const,
    title: 'Immediate Actions',
    subtitle: 'Critical items requiring urgent attention',
    icon: AlertTriangle,
    iconColor: 'text-red-500',
    bgColor: 'bg-red-50',
  },
  {
    key: 'thisWeek' as const,
    title: 'This Week',
    subtitle: 'High priority items for the next 7 days',
    icon: Clock,
    iconColor: 'text-orange-500',
    bgColor: 'bg-orange-50',
  },
  {
    key: 'thisMonth' as const,
    title: 'This Month',
    subtitle: 'Medium priority items to complete within 30 days',
    icon: Calendar,
    iconColor: 'text-blue-500',
    bgColor: 'bg-blue-50',
  },
  {
    key: 'ongoing' as const,
    title: 'Ongoing',
    subtitle: 'Lower priority and recurring tasks',
    icon: Repeat,
    iconColor: 'text-gray-500',
    bgColor: 'bg-gray-50',
  },
];

export function ActionTimeline({
  actionPlan,
  onActionComplete,
  completedIds = new Set(),
  className,
}: ActionTimelineProps) {
  return (
    <div className={cn('space-y-8', className)}>
      {timeframeSections.map((section) => {
        const items = actionPlan[section.key];
        if (items.length === 0) return null;

        const Icon = section.icon;
        const completedCount = items.filter(
          (item) => completedIds.has(item.recommendation.id)
        ).length;

        return (
          <div key={section.key}>
            {/* Section Header */}
            <div className={cn('flex items-center gap-3 p-4 rounded-t-xl', section.bgColor)}>
              <div className={cn('p-2 rounded-lg bg-white shadow-sm', section.iconColor)}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{section.title}</h3>
                <p className="text-sm text-gray-600">{section.subtitle}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700">
                  {completedCount} / {items.length}
                </p>
                <p className="text-xs text-gray-500">completed</p>
              </div>
            </div>

            {/* Action Cards */}
            <div className="space-y-3 pt-3">
              {items.map((item) => (
                <RecommendationCard
                  key={item.recommendation.id}
                  recommendation={item}
                  onComplete={onActionComplete}
                  isCompleted={completedIds.has(item.recommendation.id)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}