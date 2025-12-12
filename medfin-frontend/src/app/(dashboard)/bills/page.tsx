// src/app/(dashboard)/bills/page.tsx - Bill Analysis Tool

'use client';

import React, { useState } from 'react';
import { 
  FileWarning, 
  CheckCircle2, 
  AlertTriangle, 
  Copy, 
  Download,
  DollarSign,
  FileText,
  XCircle
} from 'lucide-react';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { cn, formatCurrency } from '@/lib/utils';
import { FileUpload } from '@/components/shared/FileUpload';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { RecommendationCard } from '@/components/shared/RecommendationCard';
import type { BillAnalysisResponse, BillError, FileUploadState } from '@/types';

export default function BillAnalysisPage() {
  const [uploadState, setUploadState] = useState<FileUploadState>({
    file: null,
    progress: 0,
    status: 'idle',
  });
  const [itemizedTemplate, setItemizedTemplate] = useState<string | null>(null);

  const { data: analysis, isLoading, error, execute: analyzeBill, reset } = useApi<BillAnalysisResponse, [File]>(
    async (file) => {
      setUploadState((prev) => ({ ...prev, status: 'uploading', progress: 30 }));
      const response = await api.analyzeBill(file);
      setUploadState((prev) => ({ ...prev, status: 'complete', progress: 100 }));
      return response;
    }
  );

  const handleFileSelect = async (file: File) => {
    setUploadState({ file, progress: 0, status: 'uploading' });
    setItemizedTemplate(null);
    await analyzeBill(file);
  };

  const handleGenerateTemplate = async () => {
    if (!analysis) return;
    try {
      const response = await api.generateItemizedRequest(analysis.billId);
      if (response.success && response.data) {
        setItemizedTemplate(response.data.template);
      }
    } catch (err) {
      console.error('Failed to generate template:', err);
    }
  };

  const handleCopyTemplate = () => {
    if (itemizedTemplate) {
      navigator.clipboard.writeText(itemizedTemplate);
    }
  };

  const handleReset = () => {
    reset();
    setUploadState({ file: null, progress: 0, status: 'idle' });
    setItemizedTemplate(null);
  };

  const totalErrors = analysis?.errors.length || 0;
  const totalDuplicates = analysis?.duplicates.length || 0;
  const totalMismatches = analysis?.coverageMismatches.length || 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Bill Analysis</h1>
        <p className="text-gray-600 mt-1">
          Upload your medical bills to identify errors and potential savings
        </p>
      </div>

      {/* Upload Section */}
      {!analysis && (
        <div className="card">
          <div className="card-body">
            <FileUpload
              onFileSelect={handleFileSelect}
              accept=".pdf,.png,.jpg,.jpeg"
              maxSizeMB={10}
              uploadState={uploadState}
            />
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && uploadState.status !== 'complete' && (
        <div className="py-12">
          <LoadingSpinner text="Analyzing your bill..." />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700">
            <XCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
          <button onClick={handleReset} className="mt-3 btn btn-outline text-sm">
            Try Again
          </button>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6 animate-fade-in">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card">
              <div className="card-body">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <FileText className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Total Billed</p>
                    <p className="text-xl font-bold text-gray-900">
                      {formatCurrency(analysis.totalBilled)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-body">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <DollarSign className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Insurance Paid</p>
                    <p className="text-xl font-bold text-blue-600">
                      {formatCurrency(analysis.insurancePaid)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-body">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <FileWarning className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Your Balance</p>
                    <p className="text-xl font-bold text-orange-600">
                      {formatCurrency(analysis.patientBalance)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="card bg-green-50 border-green-200">
              <div className="card-body">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <DollarSign className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-green-700">Potential Savings</p>
                    <p className="text-xl font-bold text-green-600">
                      {formatCurrency(analysis.potentialSavings.total)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Issues Found */}
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Issues Found</h2>
              <div className="flex items-center gap-4 text-sm">
                <span className={cn(
                  'flex items-center gap-1',
                  totalErrors > 0 ? 'text-red-600' : 'text-gray-500'
                )}>
                  <AlertTriangle className="w-4 h-4" />
                  {totalErrors} Errors
                </span>
                <span className={cn(
                  'flex items-center gap-1',
                  totalDuplicates > 0 ? 'text-orange-600' : 'text-gray-500'
                )}>
                  <Copy className="w-4 h-4" />
                  {totalDuplicates} Duplicates
                </span>
                <span className={cn(
                  'flex items-center gap-1',
                  totalMismatches > 0 ? 'text-yellow-600' : 'text-gray-500'
                )}>
                  <FileWarning className="w-4 h-4" />
                  {totalMismatches} Mismatches
                </span>
              </div>
            </div>

            {totalErrors + totalDuplicates + totalMismatches === 0 ? (
              <div className="card-body text-center py-8">
                <CheckCircle2 className="w-12 h-12 mx-auto text-green-500 mb-3" />
                <p className="text-gray-600">No issues found in this bill!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {/* Errors */}
                {analysis.errors.map((error, idx) => (
                  <ErrorRow key={`error-${idx}`} error={error} />
                ))}

                {/* Duplicates */}
                {analysis.duplicates.map((dup, idx) => (
                  <div key={`dup-${idx}`} className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <Copy className="w-4 h-4 text-orange-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">Duplicate Charge Detected</p>
                        <p className="text-sm text-gray-600">
                          Amount: {formatCurrency(dup.amount)}
                        </p>
                      </div>
                      <span className="text-sm font-medium text-green-600">
                        Save {formatCurrency(dup.amount)}
                      </span>
                    </div>
                  </div>
                ))}

                {/* Coverage Mismatches */}
                {analysis.coverageMismatches.map((mismatch, idx) => (
                  <div key={`mismatch-${idx}`} className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-yellow-100 rounded-lg">
                        <FileWarning className="w-4 h-4 text-yellow-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">Coverage Mismatch: {mismatch.serviceName}</p>
                        <p className="text-sm text-gray-600">
                          Expected: {formatCurrency(mismatch.expectedCoverage)} • 
                          Actual: {formatCurrency(mismatch.actualCoverage)}
                        </p>
                        <p className="text-sm text-gray-500">{mismatch.reason}</p>
                      </div>
                      <span className="text-sm font-medium text-green-600">
                        Save {formatCurrency(mismatch.discrepancy)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Itemized Bill Request */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-gray-900">Request Itemized Bill</h2>
            </div>
            <div className="card-body">
              {!itemizedTemplate ? (
                <div className="text-center py-4">
                  <p className="text-gray-600 mb-4">
                    Generate a template letter to request an itemized bill from the provider.
                  </p>
                  <button onClick={handleGenerateTemplate} className="btn btn-primary">
                    Generate Template
                  </button>
                </div>
              ) : (
                <div>
                  <div className="relative">
                    <pre className="p-4 bg-gray-50 rounded-lg text-sm text-gray-700 whitespace-pre-wrap font-mono">
                      {itemizedTemplate}
                    </pre>
                    <button
                      onClick={handleCopyTemplate}
                      className="absolute top-2 right-2 p-2 bg-white rounded-lg shadow-sm hover:bg-gray-50"
                    >
                      <Copy className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                  <div className="flex gap-2 mt-4">
                    <button onClick={handleCopyTemplate} className="btn btn-outline flex items-center gap-2">
                      <Copy className="w-4 h-4" />
                      Copy to Clipboard
                    </button>
                    <button className="btn btn-outline flex items-center gap-2">
                      <Download className="w-4 h-4" />
                      Download PDF
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Recommendations */}
          {analysis.recommendations.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Recommended Actions</h2>
              <div className="space-y-3">
                {analysis.recommendations.map((rec, idx) => (
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
                      rationale: 'Based on bill analysis',
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* New Analysis Button */}
          <div className="text-center pt-4">
            <button onClick={handleReset} className="btn btn-outline">
              Analyze Another Bill
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ErrorRow({ error }: { error: BillError }) {
  const severityColors = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-orange-100 text-orange-700',
    low: 'bg-yellow-100 text-yellow-700',
  };

  const errorTypeLabels: Record<BillError['errorType'], string> = {
    duplicate: 'Duplicate Charge',
    unbundling: 'Unbundling Error',
    upcoding: 'Upcoding',
    preventive_miscoding: 'Preventive Care Miscoding',
    balance_billing: 'Balance Billing',
    other: 'Other Issue',
  };

  return (
    <div className="p-4">
      <div className="flex items-start gap-3">
        <div className={cn('p-2 rounded-lg', severityColors[error.severity].split(' ')[0])}>
          <AlertTriangle className={cn('w-4 h-4', severityColors[error.severity].split(' ')[1])} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="font-medium text-gray-900">{errorTypeLabels[error.errorType]}</p>
            <span className={cn('px-2 py-0.5 rounded text-xs font-medium', severityColors[error.severity])}>
              {error.severity}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{error.description}</p>
          <p className="text-sm text-blue-600 mt-2">Action: {error.actionRequired}</p>
        </div>
        <span className="text-sm font-medium text-green-600">
          Save {formatCurrency(error.potentialSavings)}
        </span>
      </div>
    </div>
  );
}