'use client'

import { useState } from 'react'
import { matchAssistancePrograms } from '@/lib/api'
import { Heart, ExternalLink, TrendingUp } from 'lucide-react'
import type { InsuranceInfo } from '@/lib/api'

export default function AssistancePrograms() {
  const [loading, setLoading] = useState(false)
  const [programs, setPrograms] = useState<any[]>([])
  const [formData, setFormData] = useState({
    annual_income: '',
    household_size: '',
    medical_debt: '',
    has_prescriptions: false,
    has_diagnosis: true,
    insurance_type: 'private',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const insurance_info: InsuranceInfo | undefined = formData.insurance_type !== 'none' ? {
        insurance_type: formData.insurance_type as any,
        deductible: 0,
        deductible_remaining: 0,
        out_of_pocket_max: 0,
        out_of_pocket_used: 0,
        coverage_percentage: 0.8,
        in_network: true,
      } : undefined

      const response = await matchAssistancePrograms({
        annual_income: formData.annual_income ? parseFloat(formData.annual_income) : undefined,
        household_size: formData.household_size ? parseInt(formData.household_size) : undefined,
        insurance_info,
        medical_debt: formData.medical_debt ? parseFloat(formData.medical_debt) : 0,
        has_prescriptions: formData.has_prescriptions,
        has_diagnosis: formData.has_diagnosis,
      })
      setPrograms(response.data)
    } catch (error: any) {
      console.error('Error matching programs:', error)
      alert('Error matching programs: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <Heart className="h-6 w-6 text-primary-600" />
          <span>Financial Assistance Programs</span>
        </h2>
        <p className="text-gray-600 mb-6">
          Find financial assistance programs that match your situation.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Annual Income (optional)
              </label>
              <input
                type="number"
                value={formData.annual_income}
                onChange={(e) => setFormData({ ...formData, annual_income: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="$0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Household Size (optional)
              </label>
              <input
                type="number"
                value={formData.household_size}
                onChange={(e) => setFormData({ ...formData, household_size: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="1"
                min="1"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Total Medical Debt
            </label>
            <input
              type="number"
              value={formData.medical_debt}
              onChange={(e) => setFormData({ ...formData, medical_debt: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="$0.00"
              min="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Insurance Type
            </label>
            <select
              value={formData.insurance_type}
              onChange={(e) => setFormData({ ...formData, insurance_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="none">No Insurance</option>
              <option value="private">Private Insurance</option>
              <option value="medicare">Medicare</option>
              <option value="medicaid">Medicaid</option>
              <option value="tricare">TRICARE</option>
            </select>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="has_prescriptions"
                checked={formData.has_prescriptions}
                onChange={(e) => setFormData({ ...formData, has_prescriptions: e.target.checked })}
                className="h-4 w-4 text-primary-600 border-gray-300 rounded"
              />
              <label htmlFor="has_prescriptions" className="text-sm font-medium text-gray-700">
                I have prescription medications
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="has_diagnosis"
                checked={formData.has_diagnosis}
                onChange={(e) => setFormData({ ...formData, has_diagnosis: e.target.checked })}
                className="h-4 w-4 text-primary-600 border-gray-300 rounded"
              />
              <label htmlFor="has_diagnosis" className="text-sm font-medium text-gray-700">
                I have a medical diagnosis
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Finding Programs...' : 'Find Matching Programs'}
          </button>
        </form>
      </div>

      {/* Program Results */}
      {programs.length > 0 && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Found {programs.length} Matching Program{programs.length !== 1 ? 's' : ''}
            </h3>
            <div className="space-y-4">
              {programs.map((program, idx) => (
                <div
                  key={idx}
                  className="border rounded-lg p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-gray-900">{program.program_name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{program.organization}</p>
                    </div>
                    <div className="ml-4">
                      <div className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm font-semibold">
                        {(program.match_score * 100).toFixed(0)}% Match
                      </div>
                    </div>
                  </div>

                  <div className="mb-3">
                    <span className="inline-block bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-medium capitalize">
                      {program.assistance_type}
                    </span>
                  </div>

                  {program.estimated_benefit && (
                    <div className="mb-3 flex items-center space-x-2 text-green-700">
                      <TrendingUp className="h-4 w-4" />
                      <span className="font-semibold">
                        Estimated Benefit: ${program.estimated_benefit.toLocaleString()}
                      </span>
                    </div>
                  )}

                  {program.application_url && (
                    <a
                      href={program.application_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 text-primary-600 hover:text-primary-700 font-medium"
                    >
                      <span>Apply Now</span>
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}

                  {program.eligibility_criteria && Object.keys(program.eligibility_criteria).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm font-semibold text-gray-700 mb-2">Eligibility Criteria:</p>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {Object.entries(program.eligibility_criteria).map(([key, value]: [string, any]) => (
                          <li key={key}>
                            <span className="capitalize">{key.replace(/_/g, ' ')}</span>:{' '}
                            {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {program.application_deadline && (
                    <p className="mt-3 text-sm text-gray-600">
                      Application Deadline: {new Date(program.application_deadline).toLocaleDateString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {programs.length === 0 && !loading && (
        <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
          Submit the form above to find matching assistance programs.
        </div>
      )}
    </div>
  )
}



