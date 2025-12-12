// src/components/shared/RecommendationCard.tsx

'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Clock,
  DollarSign,
  CheckCircle2,
  AlertCircle,
  FileText,
  Shield,
  Heart,
  MessageSquare,
  CreditCard,
  TrendingUp,
} from 'lucide-react';
import { cn, formatCurrency, getDifficultyColor, getPriorityColor } from '@/lib/utils';
import { DIFFICULTY_LABELS } from '@/lib/constants';
import type { RankedRecommendation, ActionCategory } from '@/types';

interface RecommendationCardProps {
  recommendation: RankedRecommendation;
  onComplete?: (id: string) => void;
  isCompleted?: boolean;
  showDetails?: boolean;
  className?: string;
}

const categoryIcons: Record<ActionCategory, React.ReactNode> = {
  billing: <FileText className="w-4 h-4" />,
  insurance: <Shield className="w-4 h-4" />,
  assistance: <Heart className="w-4 h-4" />,
  negotiation: <MessageSquare className="w-4 h-4" />,
  payment: <CreditCard className="w-4 h-4" />,
  optimization: <TrendingUp className="w-4 h-4" />,
};

export function RecommendationCard({
  recommendation,
  onComplete,
  isCompleted = false,
  showDetails = false,
  className,
}: RecommendationCardProps) {
  const [expanded, setExpanded] = useState(showDetails);
  const { recommendation: rec, rankingFactors, compositeScore, finalRank, rationale } = recommendation;

  return (
    <div
      className={cn(
        'bg-white border rounded-xl overflow-hidden transition-all duration-200',
        isCompleted ? 'border-green-200 bg-green-50/30' : 'border-gray-200 hover:border-gray-300',
        className
      )}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Rank Badge */}
          <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full text-sm font-bold text-gray-700">
            {finalRank}
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={cn('px-2 py-0.5 rounded text-xs font-medium', getPriorityColor(rec.priority))}>
                {rec.priority.toUpperCase()}
              </span>
              <span className="flex items-center gap-1 text-xs text-gray-500">
                {categoryIcons[rec.category]}
                {rec.category}
              </span>
            </div>

            <h3 className={cn('font-semibold text-gray-900', isCompleted && 'line-through text-gray-500')}>
              {rec.title}
            </h3>
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">{rec.description}</p>

            {/* Quick Stats */}
            <div className="flex flex-wrap items-center gap-4 mt-3">
              <div className="flex items-center gap-1 text-sm">
                <DollarSign className="w-4 h-4 text-green-600" />
                <span className="font-medium text-green-600">
                  {formatCurrency(rec.savingsEstimate.expected)}
                </span>
              </div>
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>{DIFFICULTY_LABELS[rec.difficulty]}</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <CheckCircle2 className="w-4 h-4" />
                <span>{Math.round(rec.successProbability * 100)}% success</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex-shrink-0 flex items-center gap-2">
            {!isCompleted && onComplete && (
              <button
                onClick={() => onComplete(rec.id)}
                className="px-3 py-1.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
              >
                Complete
              </button>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-100 bg-gray-50/50">
          {/* Reasoning */}
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-1">Why this matters</h4>
            <p className="text-sm text-gray-600">{rec.reasoning}</p>
          </div>

          {/* Steps */}
          {rec.steps.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Steps to complete</h4>
              <ol className="space-y-2">
                {rec.steps.map((step) => (
                  <li key={step.stepNumber} className="flex gap-2 text-sm">
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                      {step.stepNumber}
                    </span>
                    <div>
                      <span className="font-medium text-gray-800">{step.title}</span>
                      <p className="text-gray-600">{step.description}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Required Documents */}
          {rec.requiredDocuments.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Documents needed</h4>
              <ul className="space-y-1">
                {rec.requiredDocuments.map((doc, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                    <FileText className="w-4 h-4 text-gray-400" />
                    <span>{doc.documentType}</span>
                    {doc.required && <span className="text-red-500 text-xs">*Required</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {rec.warnings && rec.warnings.length > 0 && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">Important notes</p>
                  <ul className="mt-1 space-y-1">
                    {rec.warnings.map((warning, idx) => (
                      <li key={idx} className="text-sm text-yellow-700">{warning}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Score Breakdown */}
          <div className="mt-4 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-2">Ranking rationale: {rationale}</p>
            <div className="flex gap-4 text-xs text-gray-500">
              <span>Urgency: {rankingFactors.urgencyScore.toFixed(0)}</span>
              <span>Savings: {rankingFactors.savingsImpactScore.toFixed(0)}</span>
              <span>Success: {rankingFactors.successScore.toFixed(0)}</span>
              <span>Score: {compositeScore.toFixed(1)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}