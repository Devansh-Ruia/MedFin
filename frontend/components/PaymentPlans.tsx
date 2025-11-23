'use client'

import { useState } from 'react'
import { generatePaymentPlans } from '@/lib/api'
import { CreditCard, CheckCircle, AlertCircle } from 'lucide-react'

export default function PaymentPlans() {
  const [loading, setLoading] = useState(false)
  const [plans, setPlans] = useState<any[]>([])
  const [formData, setFormData] = useState({
    total_debt: '',
    monthly_income: '',
    monthly_expenses: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await generatePaymentPlans({
        total_debt: parseFloat(formData.total_debt),
        monthly_income: parseFloat(formData.monthly_income),
        monthly_expenses: parseFloat(formData.monthly_expenses),
      })
      setPlans(response.data)
    } catch (error: any) {
      console.error('Error generating payment plans:', error)
      alert('Error generating payment plans: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <CreditCard className="h-6 w-6 text-primary-600" />
          <span>Payment Plan Options</span>
        </h2>
        <p className="text-gray-600 mb-6">
          Generate personalized payment plan options for your medical debt.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Total Medical Debt
            </label>
            <input
              type="number"
              value={formData.total_debt}
              onChange={(e) => setFormData({ ...formData, total_debt: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="$0.00"
              min="0"
              step="0.01"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Monthly Income
              </label>
              <input
                type="number"
                value={formData.monthly_income}
                onChange={(e) => setFormData({ ...formData, monthly_income: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="$0.00"
                min="0"
                step="0.01"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Monthly Expenses
              </label>
              <input
                type="number"
                value={formData.monthly_expenses}
                onChange={(e) => setFormData({ ...formData, monthly_expenses: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="$0.00"
                min="0"
                step="0.01"
                required
              />
            </div>
          </div>

          {formData.monthly_income && formData.monthly_expenses && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Disposable Income</p>
              <p className="text-xl font-bold text-blue-700">
                ${(parseFloat(formData.monthly_income) - parseFloat(formData.monthly_expenses)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Generating Plans...' : 'Generate Payment Plans'}
          </button>
        </form>
      </div>

      {/* Payment Plan Results */}
      {plans.length > 0 && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              {plans.length} Payment Plan Option{plans.length !== 1 ? 's' : ''}
            </h3>
            <div className="space-y-4">
              {plans.map((plan, idx) => (
                <div
                  key={idx}
                  className={`border-2 rounded-lg p-6 ${
                    plan.eligibility
                      ? plan.interest_rate === 0
                        ? 'border-green-200 bg-green-50'
                        : 'border-blue-200 bg-blue-50'
                      : 'border-gray-200 bg-gray-50 opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h4 className="text-xl font-bold text-gray-900">{plan.plan_type}</h4>
                      {!plan.eligibility && (
                        <span className="inline-block mt-1 text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                          May not be affordable
                        </span>
                      )}
                    </div>
                    {plan.interest_rate === 0 && plan.eligibility && (
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Monthly Payment</p>
                      <p className="text-2xl font-bold text-gray-900">
                        ${plan.monthly_payment.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Payments</p>
                      <p className="text-2xl font-bold text-gray-900">{plan.total_payments}</p>
                      <p className="text-xs text-gray-500">
                        {Math.round(plan.total_payments / 12)} year{Math.round(plan.total_payments / 12) !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Cost</p>
                      <p className="text-2xl font-bold text-gray-900">
                        ${plan.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                      {plan.interest_rate > 0 && (
                        <p className="text-xs text-red-600">
                          {plan.interest_rate}% interest
                        </p>
                      )}
                    </div>
                  </div>

                  {plan.pros && plan.pros.length > 0 && (
                    <div className="mb-3">
                      <p className="text-sm font-semibold text-gray-700 mb-2">Pros:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {plan.pros.map((pro: string, pIdx: number) => (
                          <li key={pIdx}>{pro}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {plan.cons && plan.cons.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-2">Cons:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {plan.cons.map((con: string, cIdx: number) => (
                          <li key={cIdx}>{con}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {plans.length === 0 && !loading && (
        <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
          Enter your financial information above to generate payment plan options.
        </div>
      )}
    </div>
  )
}



