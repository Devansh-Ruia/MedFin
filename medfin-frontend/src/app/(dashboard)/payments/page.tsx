// src/app/(dashboard)/payments/page.tsx - Payment Plan Generator

'use client';

import React, { useState } from 'react';
import { 
  CreditCard, 
  Calculator, 
  CheckCircle2, 
  Star,
  Clock,
  DollarSign,
  Percent,
  AlertCircle
} from 'lucide-react';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { cn, formatCurrency } from '@/lib/utils';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import type { PaymentPlanRequest, PaymentPlanResponse, PaymentPlanOption } from '@/types';

export default function PaymentPlansPage() {
  const [formData, setFormData] = useState<PaymentPlanRequest>({
    totalAmount: 0,
    monthlyBudget: 0,
    preferredTermMonths: undefined,
    includeFees: true,
  });
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);

  const { data: plans, isLoading, error, execute: generatePlans } = useApi<PaymentPlanResponse, [PaymentPlanRequest]>(
    (req) => api.generatePaymentPlans(req)
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.totalAmount <= 0 || formData.monthlyBudget <= 0) return;
    setSelectedPlanId(null);
    await generatePlans(formData);
  };

  const handleSelectPlan = async (planId: string) => {
    setSelectedPlanId(planId);
    // In production, would call api.selectPaymentPlan(planId, 'current-user')
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Payment Plan Generator</h1>
        <p className="text-gray-600 mt-1">
          Find the best payment plan option for your medical bills
        </p>
      </div>

      {/* Input Form */}
      <div className="card">
        <div className="card-header">
          <h2 className="font-semibold text-gray-900">Enter Your Details</h2>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total Amount */}
              <div>
                <label className="label mb-1.5">Total Amount Owed</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.totalAmount || ''}
                    onChange={(e) => setFormData((prev) => ({ 
                      ...prev, 
                      totalAmount: parseFloat(e.target.value) || 0 
                    }))}
                    className="input pl-7"
                    placeholder="0.00"
                  />
                </div>
              </div>

              {/* Monthly Budget */}
              <div>
                <label className="label mb-1.5">Monthly Budget</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.monthlyBudget || ''}
                    onChange={(e) => setFormData((prev) => ({ 
                      ...prev, 
                      monthlyBudget: parseFloat(e.target.value) || 0 
                    }))}
                    className="input pl-7"
                    placeholder="0.00"
                  />
                </div>
                <p className="help-text mt-1">What you can afford monthly</p>
              </div>

              {/* Preferred Term */}
              <div>
                <label className="label mb-1.5">Preferred Term (Optional)</label>
                <select
                  value={formData.preferredTermMonths || ''}
                  onChange={(e) => setFormData((prev) => ({ 
                    ...prev, 
                    preferredTermMonths: e.target.value ? parseInt(e.target.value) : undefined 
                  }))}
                  className="input"
                >
                  <option value="">No preference</option>
                  <option value="3">3 months</option>
                  <option value="6">6 months</option>
                  <option value="12">12 months</option>
                  <option value="18">18 months</option>
                  <option value="24">24 months</option>
                  <option value="36">36 months</option>
                </select>
              </div>

              {/* Include Fees */}
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.includeFees}
                    onChange={(e) => setFormData((prev) => ({ 
                      ...prev, 
                      includeFees: e.target.checked 
                    }))}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Include fees in calculations</span>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={formData.totalAmount <= 0 || formData.monthlyBudget <= 0 || isLoading}
              className="btn btn-primary"
            >
              {isLoading ? 'Generating Plans...' : 'Generate Payment Plans'}
            </button>
          </form>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="py-12">
          <LoadingSpinner text="Calculating payment options..." />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {plans && (
        <div className="space-y-6 animate-fade-in">
          {/* Summary */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              Generating plans for <strong>{formatCurrency(plans.originalAmount)}</strong> with a 
              monthly budget of <strong>{formatCurrency(formData.monthlyBudget)}</strong>
            </p>
          </div>

          {/* Plan Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {plans.options.map((option) => (
              <PlanCard
                key={option.planId}
                plan={option}
                isRecommended={option.planId === plans.recommendedPlanId}
                isSelected={option.planId === selectedPlanId}
                onSelect={() => handleSelectPlan(option.planId)}
                monthlyBudget={formData.monthlyBudget}
              />
            ))}
          </div>

          {/* Comparison Notes */}
          {plans.comparisonNotes.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-gray-900">Important Notes</h3>
              </div>
              <div className="card-body">
                <ul className="space-y-2">
                  {plans.comparisonNotes.map((note, idx) => (
                    <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                      {note}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Comparison Table */}
          <div className="card overflow-hidden">
            <div className="card-header">
              <h3 className="font-semibold text-gray-900">Plan Comparison</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan Type</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monthly</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Term</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Interest</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Cost</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Extra Paid</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {plans.options.map((option) => (
                    <tr 
                      key={option.planId}
                      className={cn(
                        'hover:bg-gray-50',
                        option.planId === plans.recommendedPlanId && 'bg-green-50'
                      )}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {formatPlanType(option.planType)}
                          </span>
                          {option.planId === plans.recommendedPlanId && (
                            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">
                        {formatCurrency(option.monthlyPayment)}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        {option.termMonths} mo
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        {option.interestRate > 0 ? `${option.interestRate}%` : 'None'}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">
                        {formatCurrency(option.totalCost)}
                      </td>
                      <td className={cn(
                        'px-4 py-3 text-right font-medium',
                        option.totalInterest > 0 ? 'text-red-600' : 'text-green-600'
                      )}>
                        {option.totalInterest > 0 
                          ? `+${formatCurrency(option.totalInterest + option.setupFee)}`
                          : formatCurrency(0)
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PlanCard({ 
  plan, 
  isRecommended, 
  isSelected, 
  onSelect,
  monthlyBudget 
}: { 
  plan: PaymentPlanOption; 
  isRecommended: boolean;
  isSelected: boolean;
  onSelect: () => void;
  monthlyBudget: number;
}) {
  const withinBudget = plan.monthlyPayment <= monthlyBudget;

  return (
    <div className={cn(
      'card relative overflow-hidden transition-all',
      isRecommended && 'ring-2 ring-green-500',
      isSelected && 'ring-2 ring-blue-500',
      !withinBudget && 'opacity-70'
    )}>
      {/* Recommended Badge */}
      {isRecommended && (
        <div className="absolute top-0 right-0 bg-green-500 text-white px-3 py-1 text-xs font-medium rounded-bl-lg flex items-center gap-1">
          <Star className="w-3 h-3 fill-white" />
          Recommended
        </div>
      )}

      <div className="card-body">
        {/* Plan Type */}
        <div className="flex items-center gap-2 mb-4">
          <div className={cn(
            'p-2 rounded-lg',
            plan.planType === 'interest_free' ? 'bg-green-100' :
            plan.planType === 'low_interest' ? 'bg-blue-100' :
            plan.planType === 'hardship' ? 'bg-purple-100' :
            'bg-gray-100'
          )}>
            <CreditCard className={cn(
              'w-5 h-5',
              plan.planType === 'interest_free' ? 'text-green-600' :
              plan.planType === 'low_interest' ? 'text-blue-600' :
              plan.planType === 'hardship' ? 'text-purple-600' :
              'text-gray-600'
            )} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{formatPlanType(plan.planType)}</h3>
            {plan.recommendationReason && (
              <p className="text-xs text-gray-500">{plan.recommendationReason}</p>
            )}
          </div>
        </div>

        {/* Key Stats */}
        <div className="space-y-3 mb-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 flex items-center gap-1">
              <DollarSign className="w-4 h-4" />
              Monthly Payment
            </span>
            <span className={cn(
              'text-lg font-bold',
              withinBudget ? 'text-green-600' : 'text-red-600'
            )}>
              {formatCurrency(plan.monthlyPayment)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Term Length
            </span>
            <span className="text-gray-900 font-medium">{plan.termMonths} months</span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 flex items-center gap-1">
              <Percent className="w-4 h-4" />
              Interest Rate
            </span>
            <span className={cn(
              'font-medium',
              plan.interestRate === 0 ? 'text-green-600' : 'text-gray-900'
            )}>
              {plan.interestRate === 0 ? 'No Interest' : `${plan.interestRate}% APR`}
            </span>
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-gray-100">
            <span className="text-sm text-gray-600">Total Cost</span>
            <span className="text-lg font-bold text-gray-900">{formatCurrency(plan.totalCost)}</span>
          </div>

          {plan.totalInterest > 0 && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">Interest Paid</span>
              <span className="text-sm text-red-600">+{formatCurrency(plan.totalInterest)}</span>
            </div>
          )}
        </div>

        {/* Features */}
        {plan.features.length > 0 && (
          <div className="mb-4">
            <ul className="space-y-1">
              {plan.features.slice(0, 3).map((feature, idx) => (
                <li key={idx} className="text-xs text-gray-600 flex items-start gap-1">
                  <CheckCircle2 className="w-3 h-3 text-green-500 flex-shrink-0 mt-0.5" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Budget Warning */}
        {!withinBudget && (
          <div className="p-2 bg-orange-50 border border-orange-200 rounded-lg mb-4">
            <p className="text-xs text-orange-700 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              Exceeds your monthly budget by {formatCurrency(plan.monthlyPayment - monthlyBudget)}
            </p>
          </div>
        )}

        {/* Select Button */}
        <button
          onClick={onSelect}
          className={cn(
            'w-full btn',
            isSelected ? 'btn-primary' : 'btn-outline'
          )}
        >
          {isSelected ? (
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Selected
            </span>
          ) : (
            'Select This Plan'
          )}
        </button>
      </div>
    </div>
  );
}

function formatPlanType(type: PaymentPlanOption['planType']): string {
  const labels: Record<PaymentPlanOption['planType'], string> = {
    interest_free: 'Interest-Free Plan',
    low_interest: 'Low Interest Plan',
    extended: 'Extended Payment Plan',
    hardship: 'Hardship Plan',
  };
  return labels[type];
}