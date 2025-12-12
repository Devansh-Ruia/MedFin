// src/app/(dashboard)/costs/page.tsx - Cost Estimation Interface

'use client';

import React, { useState } from 'react';
import { Search, MapPin, Building2, DollarSign, Star, Navigation } from 'lucide-react';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { cn, formatCurrency, isValidZipCode } from '@/lib/utils';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import type { CostEstimateRequest, CostEstimateResponse, ProviderCost } from '@/types';

export default function CostEstimationPage() {
  const [formData, setFormData] = useState<CostEstimateRequest>({
    serviceCode: '',
    serviceName: '',
    zipCode: '',
    insuranceId: '',
    networkStatus: 'unknown',
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [serviceResults, setServiceResults] = useState<{ code: string; name: string }[]>([]);

  const { data: estimate, isLoading, error, execute: getEstimate } = useApi<CostEstimateResponse, [CostEstimateRequest]>(
    (req) => api.estimateCost(req)
  );

  const handleServiceSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setServiceResults([]);
      return;
    }

    try {
      const response = await api.searchServices(query);
      if (response.success && response.data) {
        setServiceResults(response.data.services);
      }
    } catch (err) {
      console.error('Service search failed:', err);
    }
  };

  const handleServiceSelect = (service: { code: string; name: string }) => {
    setFormData((prev) => ({ ...prev, serviceCode: service.code, serviceName: service.name }));
    setSearchQuery(service.name);
    setServiceResults([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.serviceCode || !isValidZipCode(formData.zipCode)) return;
    await getEstimate(formData);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cost Estimator</h1>
        <p className="text-gray-600 mt-1">
          Get accurate cost estimates for medical services in your area
        </p>
      </div>

      {/* Search Form */}
      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Service Search */}
              <div className="relative">
                <label className="label mb-1.5">Medical Service</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleServiceSearch(e.target.value)}
                    placeholder="Search for a procedure or service..."
                    className="input pl-10"
                  />
                </div>
                {/* Autocomplete Dropdown */}
                {serviceResults.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
                    {serviceResults.map((service) => (
                      <button
                        key={service.code}
                        type="button"
                        onClick={() => handleServiceSelect(service)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 text-sm"
                      >
                        <span className="font-medium">{service.name}</span>
                        <span className="text-gray-500 ml-2">({service.code})</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* ZIP Code */}
              <div>
                <label className="label mb-1.5">ZIP Code</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={formData.zipCode}
                    onChange={(e) => setFormData((prev) => ({ ...prev, zipCode: e.target.value }))}
                    placeholder="Enter ZIP code"
                    maxLength={10}
                    className="input pl-10"
                  />
                </div>
              </div>

              {/* Insurance (Optional) */}
              <div>
                <label className="label mb-1.5">Insurance Plan (Optional)</label>
                <input
                  type="text"
                  value={formData.insuranceId || ''}
                  onChange={(e) => setFormData((prev) => ({ ...prev, insuranceId: e.target.value }))}
                  placeholder="Enter insurance plan ID"
                  className="input"
                />
              </div>

              {/* Network Status */}
              <div>
                <label className="label mb-1.5">Network Status</label>
                <select
                  value={formData.networkStatus}
                  onChange={(e) => setFormData((prev) => ({ 
                    ...prev, 
                    networkStatus: e.target.value as CostEstimateRequest['networkStatus'] 
                  }))}
                  className="input"
                >
                  <option value="unknown">Not sure</option>
                  <option value="in_network">In-Network</option>
                  <option value="out_of_network">Out-of-Network</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={!formData.serviceCode || !isValidZipCode(formData.zipCode) || isLoading}
              className="btn btn-primary w-full md:w-auto"
            >
              {isLoading ? 'Estimating...' : 'Get Estimate'}
            </button>
          </form>
        </div>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="py-12">
          <LoadingSpinner text="Calculating estimates..." />
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {estimate && (
        <div className="space-y-6 animate-fade-in">
          {/* Summary Card */}
          <div className="card">
            <div className="card-body">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                {estimate.serviceName}
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Average Cost</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(estimate.averageCost)}
                  </p>
                  <p className="text-xs text-gray-500">
                    Range: {formatCurrency(estimate.costRange.min)} - {formatCurrency(estimate.costRange.max)}
                  </p>
                </div>

                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-700">Your Estimated Cost</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(estimate.patientResponsibility)}
                  </p>
                  <p className="text-xs text-green-600">After insurance</p>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">Insurance Pays</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatCurrency(estimate.insuranceCoverage)}
                  </p>
                </div>

                <div className="p-4 bg-orange-50 rounded-lg">
                  <p className="text-sm text-orange-700">Deductible Applied</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {formatCurrency(estimate.deductibleApplied)}
                  </p>
                </div>
              </div>

              {/* Cost Breakdown */}
              {(estimate.copay > 0 || estimate.coinsurance > 0) && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <p className="text-sm text-gray-600">
                    <strong>Copay:</strong> {formatCurrency(estimate.copay)} • 
                    <strong> Coinsurance:</strong> {formatCurrency(estimate.coinsurance)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Provider Comparison */}
          {estimate.providers.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-gray-900">Nearby Providers</h3>
              </div>
              <div className="divide-y divide-gray-100">
                {estimate.providers.map((provider, idx) => (
                  <ProviderRow key={provider.providerId} provider={provider} rank={idx + 1} />
                ))}
              </div>
            </div>
          )}

          {/* Savings Tips */}
          {estimate.savingsTips.length > 0 && (
            <div className="card bg-blue-50 border-blue-200">
              <div className="card-body">
                <h3 className="font-semibold text-blue-900 mb-2">💡 Cost Saving Tips</h3>
                <ul className="space-y-2">
                  {estimate.savingsTips.map((tip, idx) => (
                    <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                      <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center bg-blue-200 rounded-full text-xs font-medium">
                        {idx + 1}
                      </span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ProviderRow({ provider, rank }: { provider: ProviderCost; rank: number }) {
  return (
    <div className="p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start gap-4">
        <div className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
          rank === 1 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
        )}>
          {rank}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-gray-900">{provider.providerName}</h4>
            <span className={cn(
              'px-2 py-0.5 rounded text-xs font-medium',
              provider.networkStatus === 'in_network'
                ? 'bg-green-100 text-green-700'
                : 'bg-orange-100 text-orange-700'
            )}>
              {provider.networkStatus === 'in_network' ? 'In-Network' : 'Out-of-Network'}
            </span>
          </div>

          <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Building2 className="w-4 h-4" />
              {provider.facilityType}
            </span>
            <span className="flex items-center gap-1">
              <Navigation className="w-4 h-4" />
              {provider.distance.toFixed(1)} mi
            </span>
            {provider.qualityRating && (
              <span className="flex items-center gap-1">
                <Star className="w-4 h-4 text-yellow-500" />
                {provider.qualityRating.toFixed(1)}
              </span>
            )}
          </div>

          <p className="text-sm text-gray-500 mt-1">{provider.address}</p>
        </div>

        <div className="text-right">
          <p className="text-lg font-bold text-gray-900">
            {formatCurrency(provider.patientResponsibility)}
          </p>
          <p className="text-xs text-gray-500">Your cost</p>
          <p className="text-sm text-gray-600 mt-1">
            Total: {formatCurrency(provider.estimatedCost)}
          </p>
        </div>
      </div>
    </div>
  );
}