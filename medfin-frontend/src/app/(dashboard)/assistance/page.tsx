// src/app/(dashboard)/assistance/page.tsx - Assistance Program Matcher

'use client';

import React, { useState } from 'react';
import { 
  Heart, 
  CheckCircle2, 
  HelpCircle, 
  XCircle,
  ExternalLink,
  Phone,
  Mail,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { cn, formatCurrency } from '@/lib/utils';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { US_STATES } from '@/lib/constants';
import type { AssistanceIntakeRequest, AssistanceMatchResponse, AssistanceProgram } from '@/types';

export default function AssistancePage() {
  const [formData, setFormData] = useState<AssistanceIntakeRequest>({
    householdSize: 1,
    annualIncome: 0,
    state: '',
    insuranceStatus: 'insured',
    medicalConditions: [],
    currentMedicalDebt: 0,
    employmentStatus: '',
  });

  const { data: results, isLoading, error, execute: matchPrograms } = useApi<AssistanceMatchResponse, [AssistanceIntakeRequest]>(
    (req) => api.matchAssistancePrograms(req)
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await matchPrograms(formData);
  };

  const handleInputChange = (field: keyof AssistanceIntakeRequest, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Financial Assistance Finder</h1>
        <p className="text-gray-600 mt-1">
          Find programs that can help reduce your healthcare costs
        </p>
      </div>

      {/* Intake Form */}
      <div className="card">
        <div className="card-header">
          <h2 className="font-semibold text-gray-900">Tell Us About Your Situation</h2>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Household Size */}
              <div>
                <label className="label mb-1.5">Household Size</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={formData.householdSize}
                  onChange={(e) => handleInputChange('householdSize', parseInt(e.target.value) || 1)}
                  className="input"
                />
                <p className="help-text mt-1">Include yourself and dependents</p>
              </div>

              {/* Annual Income */}
              <div>
                <label className="label mb-1.5">Annual Household Income</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="number"
                    min="0"
                    value={formData.annualIncome || ''}
                    onChange={(e) => handleInputChange('annualIncome', parseInt(e.target.value) || 0)}
                    className="input pl-7"
                    placeholder="0"
                  />
                </div>
                <p className="help-text mt-1">Gross annual income before taxes</p>
              </div>

              {/* State */}
              <div>
                <label className="label mb-1.5">State</label>
                <select
                  value={formData.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  className="input"
                >
                  <option value="">Select state...</option>
                  {US_STATES.map((state) => (
                    <option key={state.value} value={state.value}>
                      {state.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Insurance Status */}
              <div>
                <label className="label mb-1.5">Insurance Status</label>
                <select
                  value={formData.insuranceStatus}
                  onChange={(e) => handleInputChange('insuranceStatus', e.target.value as AssistanceIntakeRequest['insuranceStatus'])}
                  className="input"
                >
                  <option value="insured">Insured</option>
                  <option value="uninsured">Uninsured</option>
                  <option value="underinsured">Underinsured</option>
                </select>
              </div>

              {/* Current Medical Debt */}
              <div>
                <label className="label mb-1.5">Current Medical Debt (Optional)</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="number"
                    min="0"
                    value={formData.currentMedicalDebt || ''}
                    onChange={(e) => handleInputChange('currentMedicalDebt', parseInt(e.target.value) || 0)}
                    className="input pl-7"
                    placeholder="0"
                  />
                </div>
              </div>

              {/* Employment Status */}
              <div>
                <label className="label mb-1.5">Employment Status (Optional)</label>
                <select
                  value={formData.employmentStatus || ''}
                  onChange={(e) => handleInputChange('employmentStatus', e.target.value)}
                  className="input"
                >
                  <option value="">Select...</option>
                  <option value="employed_full">Employed Full-Time</option>
                  <option value="employed_part">Employed Part-Time</option>
                  <option value="self_employed">Self-Employed</option>
                  <option value="unemployed">Unemployed</option>
                  <option value="retired">Retired</option>
                  <option value="disabled">Disabled</option>
                  <option value="student">Student</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={!formData.state || formData.annualIncome <= 0 || isLoading}
              className="btn btn-primary"
            >
              {isLoading ? 'Finding Programs...' : 'Find Assistance Programs'}
            </button>
          </form>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="py-12">
          <LoadingSpinner text="Searching for assistance programs..." />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-6 animate-fade-in">
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card bg-blue-50 border-blue-200">
              <div className="card-body">
                <p className="text-sm text-blue-700">Your FPL Percentage</p>
                <p className="text-2xl font-bold text-blue-900">{results.fplPercentage}%</p>
                <p className="text-xs text-blue-600 mt-1">
                  {results.fplPercentage < 138 ? 'May qualify for Medicaid' :
                   results.fplPercentage < 250 ? 'May qualify for enhanced subsidies' :
                   results.fplPercentage < 400 ? 'May qualify for marketplace subsidies' :
                   'Above subsidy threshold'}
                </p>
              </div>
            </div>

            <div className="card bg-green-50 border-green-200">
              <div className="card-body">
                <p className="text-sm text-green-700">Programs Found</p>
                <p className="text-2xl font-bold text-green-900">{results.matchedPrograms.length}</p>
              </div>
            </div>

            <div className="card bg-purple-50 border-purple-200">
              <div className="card-body">
                <p className="text-sm text-purple-700">Potential Relief</p>
                <p className="text-2xl font-bold text-purple-900">
                  {formatCurrency(results.totalPotentialRelief.min)} - {formatCurrency(results.totalPotentialRelief.max)}
                </p>
              </div>
            </div>
          </div>

          {/* Program Cards */}
          {results.matchedPrograms.length > 0 ? (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Matched Programs</h2>
              {results.matchedPrograms.map((program) => (
                <ProgramCard key={program.programId} program={program} />
              ))}
            </div>
          ) : (
            <div className="card">
              <div className="card-body text-center py-12">
                <Heart className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">No programs matched your criteria.</p>
                <p className="text-sm text-gray-500 mt-2">
                  Try adjusting your income or household size, or contact a financial counselor for assistance.
                </p>
              </div>
            </div>
          )}

          {/* Next Steps */}
          {results.nextSteps.length > 0 && (
            <div className="card bg-blue-50 border-blue-200">
              <div className="card-header border-blue-100">
                <h2 className="font-semibold text-blue-900">Recommended Next Steps</h2>
              </div>
              <div className="card-body">
                <ol className="space-y
// src/app/(dashboard)/assistance/page.tsx (continued)

          {/* Next Steps */}
          {results.nextSteps.length > 0 && (
            <div className="card bg-blue-50 border-blue-200">
              <div className="card-header border-blue-100">
                <h2 className="font-semibold text-blue-900">Recommended Next Steps</h2>
              </div>
              <div className="card-body">
                <ol className="space-y-3">
                  {results.nextSteps.map((step) => (
                    <li key={step.stepNumber} className="flex gap-3">
                      <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-200 text-blue-800 rounded-full text-sm font-medium">
                        {step.stepNumber}
                      </span>
                      <div>
                        <p className="font-medium text-blue-900">{step.title}</p>
                        <p className="text-sm text-blue-700">{step.description}</p>
                        {step.tips && step.tips.length > 0 && (
                          <ul className="mt-2 space-y-1">
                            {step.tips.map((tip, idx) => (
                              <li key={idx} className="text-sm text-blue-600 flex items-start gap-1">
                                <span>💡</span> {tip}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ProgramCard({ program }: { program: AssistanceProgram }) {
  const [expanded, setExpanded] = useState(false);

  const eligibilityColors = {
    eligible: 'bg-green-100 text-green-800 border-green-200',
    likely_eligible: 'bg-blue-100 text-blue-800 border-blue-200',
    may_qualify: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    ineligible: 'bg-gray-100 text-gray-600 border-gray-200',
  };

  const eligibilityIcons = {
    eligible: <CheckCircle2 className="w-4 h-4" />,
    likely_eligible: <CheckCircle2 className="w-4 h-4" />,
    may_qualify: <HelpCircle className="w-4 h-4" />,
    ineligible: <XCircle className="w-4 h-4" />,
  };

  const eligibilityLabels = {
    eligible: 'Eligible',
    likely_eligible: 'Likely Eligible',
    may_qualify: 'May Qualify',
    ineligible: 'Not Eligible',
  };

  const programTypeLabels: Record<AssistanceProgram['programType'], string> = {
    charity_care: 'Charity Care',
    medicaid: 'Medicaid',
    state_program: 'State Program',
    hospital_financial_assistance: 'Hospital Financial Assistance',
    nonprofit: 'Nonprofit Organization',
    pharmaceutical: 'Pharmaceutical Assistance',
  };

  return (
    <div className={cn(
      'card overflow-hidden transition-all',
      program.eligibilityStatus === 'ineligible' && 'opacity-60'
    )}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 p-2 bg-purple-100 rounded-lg">
            <Heart className="w-5 h-5 text-purple-600" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-gray-900">{program.programName}</h3>
              <span className={cn(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border',
                eligibilityColors[program.eligibilityStatus]
              )}>
                {eligibilityIcons[program.eligibilityStatus]}
                {eligibilityLabels[program.eligibilityStatus]}
              </span>
            </div>

            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
              <span>{program.provider}</span>
              <span>•</span>
              <span>{programTypeLabels[program.programType]}</span>
            </div>

            <p className="text-sm text-gray-600 mt-2">{program.coverageType}</p>

            {/* Estimated Relief */}
            <div className="mt-3 p-3 bg-green-50 rounded-lg inline-block">
              <p className="text-sm text-green-700">Potential Relief</p>
              <p className="text-lg font-bold text-green-600">
                {formatCurrency(program.estimatedRelief.min)} - {formatCurrency(program.estimatedRelief.max)}
              </p>
            </div>
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-100 bg-gray-50/50">
          {/* Requirements */}
          {program.requirements.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Requirements</h4>
              <ul className="space-y-1">
                {program.requirements.map((req, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                    {req}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Application Process */}
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">How to Apply</h4>
            <p className="text-sm text-gray-600">{program.applicationProcess}</p>
            <p className="text-sm text-gray-500 mt-1">
              Processing time: {program.processingTime}
            </p>
          </div>

          {/* Contact Info */}
          {program.contactInfo && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Contact Information</h4>
              <div className="space-y-1">
                <p className="text-sm text-gray-600">{program.contactInfo.department}</p>
                {program.contactInfo.phone && (
                  <p className="text-sm text-gray-600 flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-400" />
                    {program.contactInfo.phone}
                  </p>
                )}
                {program.contactInfo.email && (
                  <p className="text-sm text-gray-600 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-gray-400" />
                    {program.contactInfo.email}
                  </p>
                )}
                {program.contactInfo.hours && (
                  <p className="text-sm text-gray-500">{program.contactInfo.hours}</p>
                )}
              </div>
            </div>
          )}

          {/* Notes */}
          {program.notes && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">{program.notes}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-4">
            {program.applicationUrl && (
              
                href={program.applicationUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary flex items-center gap-2"
              >
                Apply Now
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
            <button className="btn btn-outline">
              Save for Later
            </button>
          </div>
        </div>
      )}
    </div>
  );
}