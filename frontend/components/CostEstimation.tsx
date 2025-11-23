'use client'

import { useState } from 'react'
import { estimateCost } from '@/lib/api'
import { DollarSign, TrendingDown, Info } from 'lucide-react'

export default function CostEstimation() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [formData, setFormData] = useState({
    service_type: 'primary_care',
    description: '',
    location: '',
    has_insurance: true,
    insurance_type: 'private',
    deductible_remaining: '0',
    copay: '',
  })

  const serviceTypes = [
    { value: 'primary_care', label: 'Primary Care' },
    { value: 'specialist', label: 'Specialist' },
    { value: 'emergency', label: 'Emergency' },
    { value: 'surgery', label: 'Surgery' },
    { value: 'imaging', label: 'Imaging' },
    { value: 'laboratory', label: 'Laboratory' },
    { value: 'pharmacy', label: 'Pharmacy' },
    { value: 'hospitalization', label: 'Hospitalization' },
    { value: 'mental_health', label: 'Mental Health' },
    { value: 'preventive', label: 'Preventive Care' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await estimateCost({
        ...formData,
        deductible_remaining: parseFloat(formData.deductible_remaining) || 0,
        copay: formData.copay ? parseFloat(formData.copay) : undefined,
      })
      setResult(response.data)
    } catch (error: any) {
      console.error('Error estimating cost:', error)
      alert('Error estimating cost: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <DollarSign className="h-6 w-6 text-primary-600" />
          <span>Healthcare Cost Estimation</span>
        </h2>
        <p className="text-gray-600 mb-6">
          Get cost estimates for healthcare services based on your insurance coverage.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Service Type
            </label>
            <select
              value={formData.service_type}
              onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            >
              {serviceTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optional)
            </label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Brief description of service"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location (optional)
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="State or City"
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="has_insurance"
              checked={formData.has_insurance}
              onChange={(e) => setFormData({ ...formData, has_insurance: e.target.checked })}
              className="h-4 w-4 text-primary-600 border-gray-300 rounded"
            />
            <label htmlFor="has_insurance" className="text-sm font-medium text-gray-700">
              I have insurance
            </label>
          </div>

          {formData.has_insurance && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Insurance Type
                </label>
                <select
                  value={formData.insurance_type}
                  onChange={(e) => setFormData({ ...formData, insurance_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="private">Private Insurance</option>
                  <option value="medicare">Medicare</option>
                  <option value="medicaid">Medicaid</option>
                  <option value="tricare">TRICARE</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Deductible Remaining
                  </label>
                  <input
                    type="number"
                    value={formData.deductible_remaining}
                    onChange={(e) => setFormData({ ...formData, deductible_remaining: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="$0.00"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Copay (optional)
                  </label>
                  <input
                    type="number"
                    value={formData.copay}
                    onChange={(e) => setFormData({ ...formData, copay: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="$0.00"
                    min="0"
                  />
                </div>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Estimating...' : 'Estimate Cost'}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Cost Estimate</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Estimated Cost</p>
                <p className="text-3xl font-bold text-gray-900">
                  ${result.estimated_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              {result.insurance_coverage !== null && result.insurance_coverage !== undefined && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Insurance Coverage</p>
                  <p className="text-3xl font-bold text-green-700">
                    ${result.insurance_coverage?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              )}
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Your Responsibility</p>
                <p className="text-3xl font-bold text-red-700">
                  ${result.patient_responsibility?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>

            {result.confidence_score && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  Confidence Score: {(result.confidence_score * 100).toFixed(0)}%
                </p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full"
                    style={{ width: `${result.confidence_score * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* Breakdown */}
          {result.breakdown && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <Info className="h-5 w-5 text-primary-600" />
                <span>Cost Breakdown</span>
              </h3>
              <dl className="grid grid-cols-2 gap-4">
                {Object.entries(result.breakdown).map(([key, value]: [string, any]) => (
                  <div key={key}>
                    <dt className="text-sm text-gray-600 capitalize">
                      {key.replace(/_/g, ' ')}
                    </dt>
                    <dd className="text-lg font-semibold text-gray-900">
                      {typeof value === 'number'
                        ? value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                        : String(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Alternatives */}
          {result.alternatives && result.alternatives.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <TrendingDown className="h-5 w-5 text-green-600" />
                <span>Lower-Cost Alternatives</span>
              </h3>
              <div className="space-y-3">
                {result.alternatives.map((alt: any, idx: number) => (
                  <div key={idx} className="border border-green-200 bg-green-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900">{alt.option}</h4>
                    <p className="text-sm text-gray-600 mt-1">{alt.description}</p>
                    <div className="mt-2 flex items-center space-x-4">
                      <div>
                        <p className="text-xs text-gray-600">Estimated Cost</p>
                        <p className="text-lg font-bold text-green-700">
                          ${alt.estimated_cost?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Potential Savings</p>
                        <p className="text-lg font-bold text-green-700">
                          ${alt.savings?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}



