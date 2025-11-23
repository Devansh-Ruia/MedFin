'use client'

import { useState } from 'react'
import { analyzeBills } from '@/lib/api'
import { FileText, AlertTriangle, TrendingUp } from 'lucide-react'
import type { MedicalBill, InsuranceInfo } from '@/lib/api'

export default function BillAnalysis() {
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<any>(null)
  const [bills, setBills] = useState<MedicalBill[]>([
    {
      bill_id: 'BILL-001',
      provider_name: '',
      service_date: new Date().toISOString().split('T')[0],
      services: [],
      total_amount: 0,
      patient_responsibility: 0,
      status: 'pending',
    },
  ])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await analyzeBills({ bills })
      setAnalysis(response.data)
    } catch (error: any) {
      console.error('Error analyzing bills:', error)
      alert('Error analyzing bills: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const addBill = () => {
    setBills([
      ...bills,
      {
        bill_id: `BILL-${Date.now()}`,
        provider_name: '',
        service_date: new Date().toISOString().split('T')[0],
        services: [],
        total_amount: 0,
        patient_responsibility: 0,
        status: 'pending',
      },
    ])
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <FileText className="h-6 w-6 text-primary-600" />
          <span>Medical Bill Analysis</span>
        </h2>
        <p className="text-gray-600 mb-6">
          Analyze your medical bills for errors, savings opportunities, and negotiation strategies.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {bills.map((bill, idx) => (
            <div key={idx} className="border rounded-lg p-4 space-y-3">
              <h3 className="font-semibold text-gray-900">Bill #{idx + 1}</h3>
              <input
                type="text"
                placeholder="Provider Name"
                value={bill.provider_name}
                onChange={(e) => {
                  const newBills = [...bills]
                  newBills[idx].provider_name = e.target.value
                  setBills(newBills)
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="date"
                  value={bill.service_date}
                  onChange={(e) => {
                    const newBills = [...bills]
                    newBills[idx].service_date = e.target.value
                    setBills(newBills)
                  }}
                  className="px-3 py-2 border border-gray-300 rounded-md"
                />
                <input
                  type="number"
                  placeholder="Total Amount"
                  value={bill.total_amount || ''}
                  onChange={(e) => {
                    const newBills = [...bills]
                    newBills[idx].total_amount = parseFloat(e.target.value) || 0
                    newBills[idx].patient_responsibility = parseFloat(e.target.value) || 0
                    setBills(newBills)
                  }}
                  className="px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <input
                type="number"
                placeholder="Patient Responsibility"
                value={bill.patient_responsibility || ''}
                onChange={(e) => {
                  const newBills = [...bills]
                  newBills[idx].patient_responsibility = parseFloat(e.target.value) || 0
                  setBills(newBills)
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
              {bill.insurance_paid !== undefined && (
                <input
                  type="number"
                  placeholder="Insurance Paid"
                  value={bill.insurance_paid || ''}
                  onChange={(e) => {
                    const newBills = [...bills]
                    newBills[idx].insurance_paid = parseFloat(e.target.value) || undefined
                    setBills(newBills)
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={addBill}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            + Add Another Bill
          </button>

          <button
            type="submit"
            disabled={loading || bills.length === 0}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze Bills'}
          </button>
        </form>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Bill Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total Bills</p>
                <p className="text-2xl font-bold text-gray-900">{analysis.total_bills}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total Amount</p>
                <p className="text-2xl font-bold text-purple-700">
                  ${analysis.total_amount?.toLocaleString()}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Insurance Paid</p>
                <p className="text-2xl font-bold text-green-700">
                  ${analysis.total_insurance_paid?.toLocaleString()}
                </p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Your Responsibility</p>
                <p className="text-2xl font-bold text-red-700">
                  ${analysis.total_patient_responsibility?.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Issues */}
          {analysis.issues && analysis.issues.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <span>Potential Issues</span>
              </h3>
              <div className="space-y-3">
                {analysis.issues.map((issue: any, idx: number) => (
                  <div key={idx} className="border-l-4 border-yellow-500 pl-4 py-2">
                    <h4 className="font-semibold text-gray-900">{issue.issue}</h4>
                    <p className="text-sm text-gray-600 mt-1">{issue.description}</p>
                    {issue.bill_id && (
                      <p className="text-xs text-gray-500 mt-1">Bill ID: {issue.bill_id}</p>
                    )}
                  </div>
                ))}
              </div>
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

          {/* Savings Opportunities */}
          {analysis.savings_opportunities && analysis.savings_opportunities.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span>Savings Opportunities</span>
              </h3>
              <div className="space-y-3">
                {analysis.savings_opportunities.map((opp: any, idx: number) => (
                  <div key={idx} className="border border-green-200 bg-green-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900">{opp.opportunity}</h4>
                    <p className="text-sm text-gray-600 mt-1">{opp.description}</p>
                    <p className="text-lg font-bold text-green-700 mt-2">
                      Potential Savings: ${opp.estimated_savings?.toLocaleString()}
                    </p>
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



