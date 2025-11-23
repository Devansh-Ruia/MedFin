'use client'

import { useState } from 'react'
import CostEstimation from '@/components/CostEstimation'
import NavigationPlan from '@/components/NavigationPlan'
import BillAnalysis from '@/components/BillAnalysis'
import InsuranceAnalysis from '@/components/InsuranceAnalysis'
import AssistancePrograms from '@/components/AssistancePrograms'
import PaymentPlans from '@/components/PaymentPlans'
import { Activity, DollarSign, FileText, Shield, Heart, CreditCard } from 'lucide-react'

export default function Home() {
  const [activeTab, setActiveTab] = useState('navigation')

  const tabs = [
    { id: 'navigation', label: 'Navigation', icon: Activity },
    { id: 'cost', label: 'Cost Estimation', icon: DollarSign },
    { id: 'bills', label: 'Bill Analysis', icon: FileText },
    { id: 'insurance', label: 'Insurance', icon: Shield },
    { id: 'assistance', label: 'Assistance', icon: Heart },
    { id: 'payments', label: 'Payment Plans', icon: CreditCard },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <Activity className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">MedFin</h1>
                <p className="text-sm text-gray-600">Healthcare Financial Navigator</p>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              Autonomous Financial Navigation
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'navigation' && <NavigationPlan />}
        {activeTab === 'cost' && <CostEstimation />}
        {activeTab === 'bills' && <BillAnalysis />}
        {activeTab === 'insurance' && <InsuranceAnalysis />}
        {activeTab === 'assistance' && <AssistancePrograms />}
        {activeTab === 'payments' && <PaymentPlans />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2024 MedFin. Autonomous Healthcare Financial Navigation System.
          </p>
        </div>
      </footer>
    </div>
  )
}



