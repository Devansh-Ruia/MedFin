'use client'

import { useState } from 'react'
import { analyzeInsurance } from '@/lib/api'
import { Shield, AlertCircle, CheckCircle } from 'lucide-react'
import type { InsuranceInfo } from '@/lib/api'

export default function InsuranceAnalysis() {
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<any>(null)
  const [formData, setFormData] = useState<InsuranceInfo>({
    insurance_type: 'private',
    deductible: 2000,
    deductible_remaining: 1500,
    out_of_pocket_max: 8000,
    out_of_pocket_used: 2000,
    coverage_percentage: 0.8,
    in_network: true,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await analyzeInsurance(formData)
      setAnalysis(response.data)
    } catch (error: any) {
      console.error('Error analyzing insurance:', error)
      alert('Error analyzing insurance: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <Shield className="h-6 w-6 text-primary-600" />
          <span>Insurance Coverage Analysis</span>
        </h2>
        <p className="text-gray-600 mb-6">
          Analyze your insurance coverage and get recommendations for optimizing your benefits.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Insurance Type
            </label>
            <select
              value={formData.insurance_type}
              onChange={(e) => setFormData({ ...formData, insurance_type: e.target.value as any })}
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
                Annual Deductible
              </label>
              <input
                type="number"
                value={formData.deductible}
                onChange={(e) => setFormData({ ...formData, deductible: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Deductible Remaining
              </label>
              <input
                type="number"
                value={formData.deductible_remaining}
                onChange={(e) => setFormData({ ...formData, deductible_remaining: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                min="0"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Out-of-Pocket Maximum
              </label>
              <input
                type="number"
                value={formData.out_of_pocket_max}
                onChange={(e) => setFormData({ ...formData, out_of_pocket_max: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Out-of-Pocket Used
              </label>
              <input
                type="number"
                value={formData.out_of_pocket_used}
                onChange={(e) => setFormData({ ...formData, out_of_pocket_used: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                min="0"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Coverage Percentage (0-1)
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.coverage_percentage}
              onChange={(e) => setFormData({ ...formData, coverage_percentage: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              min="0"
              max="1"
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="in_network"
              checked={formData.in_network}
              onChange={(e) => setFormData({ ...formData, in_network: e.target.checked })}
              className="h-4 w-4 text-primary-600 border-gray-300 rounded"
            />
            <label htmlFor="in_network" className="text-sm font-medium text-gray-700">
              Provider is in-network
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze Coverage'}
          </button>
        </form>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-4">
          {/* Coverage Status */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Coverage Status</h3>
            <div className={`p-4 rounded-lg ${
              analysis.coverage_status === 'good' ? 'bg-green-50 border border-green-200' :
              analysis.coverage_status === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
              'bg-blue-50 border border-blue-200'
            }`}>
              <div className="flex items-center space-x-2">
                {analysis.coverage_status === 'good' ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                )}
                <span className="font-semibold capitalize text-gray-900">
                  {analysis.coverage_status.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>

          {/* Deductible Progress */}
          {analysis.deductible_progress && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Deductible Progress</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Progress</span>
                  <span className="font-semibold">
                    {analysis.deductible_progress.percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full ${
                      analysis.deductible_progress.met ? 'bg-green-600' : 'bg-blue-600'
                    }`}
                    style={{ width: `${Math.min(analysis.deductible_progress.percentage, 100)}%` }}
                  ></div>
                </div>
                {analysis.deductible_progress.met ? (
                  <p className="text-sm text-green-600 font-medium">✓ Deductible met!</p>
                ) : (
                  <p className="text-sm text-gray-600">
                    ${analysis.deductible_progress.remaining.toLocaleString()} remaining
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Out-of-Pocket Progress */}
          {analysis.out_of_pocket_progress && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Out-of-Pocket Maximum Progress</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Progress</span>
                  <span className="font-semibold">
                    {analysis.out_of_pocket_progress.percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full ${
                      analysis.out_of_pocket_progress.max_reached ? 'bg-green-600' : 'bg-purple-600'
                    }`}
                    style={{ width: `${Math.min(analysis.out_of_pocket_progress.percentage, 100)}%` }}
                  ></div>
                </div>
                {analysis.out_of_pocket_progress.max_reached ? (
                  <p className="text-sm text-green-600 font-medium">
                    ✓ Maximum reached! Additional covered services should be at 100%
                  </p>
                ) : (
                  <p className="text-sm text-gray-600">
                    ${analysis.out_of_pocket_progress.remaining.toLocaleString()} remaining
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Warnings */}
          {analysis.warnings && analysis.warnings.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                <span>Warnings</span>
              </h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {analysis.warnings.map((warning: string, idx: number) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Recommendations</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {analysis.recommendations.map((rec: string, idx: number) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}



