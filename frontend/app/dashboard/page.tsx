'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { getUserDashboard, exportDashboardPDF, exportNavigationPlanPDF } from '@/lib/api'
import { 
  User, 
  FileText, 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  Shield,
  Calendar,
  Clock,
  Plus,
  Eye,
  Download
} from 'lucide-react'

interface DashboardData {
  user_info: {
    id: number
    email: string
    username: string
    full_name?: string
    is_active: boolean
    created_at: string
  }
  insurance_info?: {
    id: number
    insurance_type: string
    plan_name?: string
    deductible: number
    deductible_remaining: number
    out_of_pocket_max: number
    coverage_percentage: number
  }
  summary: {
    total_bills: number
    total_bill_amount: number
    total_plans: number
    total_projected_savings: number
    total_estimates: number
    has_insurance: boolean
  }
  recent_bills: Array<{
    id: number
    provider_name: string
    service_date: string
    patient_responsibility: number
    status: string
    created_at: string
  }>
  recent_plans: Array<{
    id: number
    projected_savings: number
    status: string
    created_at: string
  }>
  recent_estimates: Array<{
    id: number
    service_type: string
    estimated_cost: number
    patient_responsibility: number
    created_at: string
  }>
}

export default function DashboardPage() {
  const { user, isAuthenticated, loading: authLoading } = useAuth()
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      fetchDashboardData()
    }
  }, [isAuthenticated, authLoading, router])

  const fetchDashboardData = async () => {
    try {
      const response = await getUserDashboard()
      setDashboardData(response.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated || !dashboardData) {
    return null
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const handleExportDashboard = async () => {
    try {
      const response = await exportDashboardPDF()
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `medfin_dashboard_${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export dashboard:', error)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="px-4 py-6 sm:px-0">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Welcome back, {dashboardData.user_info.full_name || dashboardData.user_info.username}!
              </h1>
              <p className="mt-2 text-gray-600">
                Here's an overview of your healthcare financial navigation.
              </p>
            </div>
            <div className="flex space-x-3">
              <button 
                onClick={handleExportDashboard}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <Download className="h-4 w-4 mr-2" />
                Export Dashboard
              </button>
              <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                New Navigation Plan
              </button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <FileText className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Bills
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {dashboardData.summary.total_bills}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-600">Total Amount: </span>
                  <span className="font-medium text-gray-900">
                    {formatCurrency(dashboardData.summary.total_bill_amount)}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Navigation Plans
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {dashboardData.summary.total_plans}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-600">Projected Savings: </span>
                  <span className="font-medium text-green-600">
                    {formatCurrency(dashboardData.summary.total_projected_savings)}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Calculator className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Cost Estimates
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {dashboardData.summary.total_estimates}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-600">Insurance Status: </span>
                  <span className={`font-medium ${dashboardData.summary.has_insurance ? 'text-green-600' : 'text-orange-600'}`}>
                    {dashboardData.summary.has_insurance ? 'On File' : 'Not Set'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Shield className="h-6 w-6 text-indigo-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Insurance Coverage
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {dashboardData.insurance_info ? `${dashboardData.insurance_info.coverage_percentage * 100}%` : 'N/A'}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <span className="text-gray-600">Plan: </span>
                  <span className="font-medium text-gray-900">
                    {dashboardData.insurance_info?.plan_name || 'Not Set'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Recent Bills */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Recent Bills
                  </h3>
                  <button className="text-sm text-blue-600 hover:text-blue-500">
                    View All
                  </button>
                </div>
                <div className="space-y-3">
                  {dashboardData.recent_bills.length > 0 ? (
                    dashboardData.recent_bills.map((bill) => (
                      <div key={bill.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{bill.provider_name}</p>
                          <p className="text-sm text-gray-500">{formatDate(bill.service_date)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-900">
                            {formatCurrency(bill.patient_responsibility)}
                          </p>
                          <p className="text-xs text-gray-500 capitalize">{bill.status}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No bills saved yet</p>
                  )}
                </div>
              </div>
            </div>

            {/* Recent Navigation Plans */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Navigation Plans
                  </h3>
                  <button className="text-sm text-blue-600 hover:text-blue-500">
                    View All
                  </button>
                </div>
                <div className="space-y-3">
                  {dashboardData.recent_plans.length > 0 ? (
                    dashboardData.recent_plans.map((plan) => (
                      <div key={plan.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-gray-900">Navigation Plan</p>
                          <p className="text-sm text-gray-500">{formatDate(plan.created_at)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-green-600">
                            {formatCurrency(plan.projected_savings)}
                          </p>
                          <p className="text-xs text-gray-500 capitalize">{plan.status}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No navigation plans created yet</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Cost Estimates */}
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Recent Cost Estimates
                </h3>
                <button className="text-sm text-blue-600 hover:text-blue-500">
                  View All
                </button>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {dashboardData.recent_estimates.length > 0 ? (
                  dashboardData.recent_estimates.map((estimate) => (
                    <div key={estimate.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-900">{estimate.service_type}</h4>
                        <span className="text-xs text-gray-500">{formatDate(estimate.created_at)}</span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Est. Cost:</span>
                          <span className="font-medium">{formatCurrency(estimate.estimated_cost)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Your Cost:</span>
                          <span className="font-medium text-blue-600">{formatCurrency(estimate.patient_responsibility)}</span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500 col-span-full">No cost estimates saved yet</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
