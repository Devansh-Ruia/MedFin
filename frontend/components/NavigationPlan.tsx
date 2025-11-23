'use client'

import { useState } from 'react'
import { generateNavigationPlan } from '@/lib/api'
import { Activity, AlertCircle, TrendingUp, Calendar, DollarSign } from 'lucide-react'
import type { MedicalBill, InsuranceInfo } from '@/lib/api'

export default function NavigationPlan() {
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState<any>(null)
  const [formData, setFormData] = useState({
    bills: [] as MedicalBill[],
    insurance_info: null as InsuranceInfo | null,
    annual_income: '',
    household_size: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await generateNavigationPlan({
        bills: formData.bills,
        insurance_info: formData.insurance_info || undefined,
        annual_income: formData.annual_income ? parseFloat(formData.annual_income) : undefined,
        household_size: formData.household_size ? parseInt(formData.household_size) : undefined,
      })
      setPlan(response.data)
    } catch (error: any) {
      console.error('Error generating plan:', error)
      alert('Error generating navigation plan: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const addBill = () => {
    setFormData({
      ...formData,
      bills: [
        ...formData.bills,
        {
          bill_id: `BILL-${Date.now()}`,
          provider_name: '',
          service_date: new Date().toISOString().split('T')[0],
          services: [],
          total_amount: 0,
          patient_responsibility: 0,
          status: 'pending',
        },
      ],
    })
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <Activity className="h-6 w-6 text-primary-600" />
          <span>Autonomous Navigation Plan</span>
        </h2>
        <p className="text-gray-600 mb-6">
          Get an autonomous financial navigation plan based on your medical bills and financial situation.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Bills */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Medical Bills
            </label>
            {formData.bills.map((bill, idx) => (
              <div key={idx} className="border rounded-lg p-4 mb-4 space-y-3">
                <input
                  type="text"
                  placeholder="Provider Name"
                  value={bill.provider_name}
                  onChange={(e) => {
                    const newBills = [...formData.bills]
                    newBills[idx].provider_name = e.target.value
                    setFormData({ ...formData, bills: newBills })
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="number"
                    placeholder="Total Amount"
                    value={bill.total_amount || ''}
                    onChange={(e) => {
                      const newBills = [...formData.bills]
                      newBills[idx].total_amount = parseFloat(e.target.value) || 0
                      newBills[idx].patient_responsibility = parseFloat(e.target.value) || 0
                      setFormData({ ...formData, bills: newBills })
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-md"
                  />
                  <input
                    type="number"
                    placeholder="Patient Responsibility"
                    value={bill.patient_responsibility || ''}
                    onChange={(e) => {
                      const newBills = [...formData.bills]
                      newBills[idx].patient_responsibility = parseFloat(e.target.value) || 0
                      setFormData({ ...formData, bills: newBills })
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
            ))}
            <button
              type="button"
              onClick={addBill}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              + Add Bill
            </button>
          </div>

          {/* Financial Information */}
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

          <button
            type="submit"
            disabled={loading || formData.bills.length === 0}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Generating Plan...' : 'Generate Navigation Plan'}
          </button>
        </form>
      </div>

      {/* Results */}
      {plan && (
        <div className="space-y-4">
          {/* Current Situation */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Current Financial Situation</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total Medical Debt</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${plan.current_financial_situation?.total_medical_debt?.toLocaleString() || '0.00'}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Projected Savings</p>
                <p className="text-2xl font-bold text-green-700">
                  ${plan.projected_savings?.toLocaleString() || '0.00'}
                </p>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Hardship Level</p>
                <p className="text-xl font-bold text-yellow-700 capitalize">
                  {plan.current_financial_situation?.hardship_level || 'N/A'}
                </p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Risk Level</p>
                <p className="text-xl font-bold text-red-700 capitalize">
                  {plan.risk_assessment?.risk_level || 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Recommended Actions */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-primary-600" />
              <span>Recommended Actions</span>
            </h3>
            <div className="space-y-4">
              {plan.recommended_actions?.map((action: any, idx: number) => (
                <div key={idx} className="border-l-4 border-primary-500 pl-4 py-2">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{action.description}</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Priority: {action.priority} • {action.action_type.replace('_', ' ').toUpperCase()}
                      </p>
                      {action.estimated_savings > 0 && (
                        <p className="text-sm font-medium text-green-600 mt-1">
                          Potential Savings: ${action.estimated_savings.toLocaleString()}
                        </p>
                      )}
                      {action.deadline && (
                        <p className="text-sm text-gray-500 mt-1">
                          Deadline: {new Date(action.deadline).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                  {action.resources && action.resources.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500">Resources:</p>
                      <ul className="list-disc list-inside text-xs text-primary-600">
                        {action.resources.map((resource: string, rIdx: number) => (
                          <li key={rIdx}>
                            <a href={resource} target="_blank" rel="noopener noreferrer" className="hover:underline">
                              {resource}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Risk Assessment */}
          {plan.risk_assessment && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <span>Risk Assessment</span>
              </h3>
              <div className="space-y-2">
                <p className="text-gray-700">
                  <span className="font-semibold">Risk Level:</span>{' '}
                  <span className="capitalize">{plan.risk_assessment.risk_level}</span>
                  {' '}(Score: {plan.risk_assessment.risk_score})
                </p>
                <p className="text-gray-700">{plan.risk_assessment.recommendation}</p>
                {plan.risk_assessment.risk_factors && plan.risk_assessment.risk_factors.length > 0 && (
                  <ul className="list-disc list-inside text-gray-600 mt-2">
                    {plan.risk_assessment.risk_factors.map((factor: string, idx: number) => (
                      <li key={idx}>{factor}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {/* Timeline */}
          {plan.timeline && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <Calendar className="h-5 w-5 text-primary-600" />
                <span>Action Timeline</span>
              </h3>
              <div className="space-y-4">
                {Object.entries(plan.timeline).map(([period, actions]: [string, any]) => (
                  <div key={period}>
                    <h4 className="font-semibold text-gray-900 capitalize mb-2">{period.replace('_', ' ')}</h4>
                    {actions && Array.isArray(actions) && actions.length > 0 ? (
                      <ul className="list-disc list-inside text-gray-600 ml-4">
                        {actions.map((action: any, idx: number) => (
                          <li key={idx}>
                            {action.action?.replace('_', ' ') || action.action_type?.replace('_', ' ')}
                            {action.deadline && (
                              <span className="text-sm text-gray-500">
                                {' '}— Due: {new Date(action.deadline).toLocaleDateString()}
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-gray-500 text-sm ml-4">No actions scheduled</p>
                    )}
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



