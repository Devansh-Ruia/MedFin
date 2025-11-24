'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { Activity, ArrowRight, Shield, TrendingUp, Calculator, FileText, Heart } from 'lucide-react'

export default function Home() {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null // Will redirect to dashboard
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Activity className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">MedFin</h1>
                <p className="text-sm text-gray-600">Healthcare Financial Navigator</p>
              </div>
            </div>
            <div className="flex space-x-4">
              <Link 
                href="/login" 
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Sign In
              </Link>
              <Link 
                href="/register" 
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
            Navigate Your <span className="text-blue-600">Healthcare Costs</span> with Confidence
          </h1>
          <p className="mt-6 max-w-3xl mx-auto text-xl text-gray-500">
            MedFin is your autonomous healthcare financial navigator. Analyze bills, estimate costs, 
            find assistance programs, and create personalized payment plans—all in one place.
          </p>
          <div className="mt-10 flex justify-center space-x-4">
            <Link 
              href="/register" 
              className="bg-blue-600 text-white px-8 py-3 rounded-md text-lg font-medium hover:bg-blue-700 flex items-center"
            >
              Start Free Today
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link 
              href="/login" 
              className="bg-white text-blue-600 px-8 py-3 rounded-md text-lg font-medium border border-blue-600 hover:bg-blue-50"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-extrabold text-gray-900">
              Everything You Need to Manage Healthcare Costs
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
              Our AI-powered tools help you understand, manage, and reduce your healthcare expenses.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <FileText className="h-8 w-8 text-blue-600" />
                </div>
              </div>
              <h3 className="mt-6 text-lg font-medium text-gray-900">Bill Analysis</h3>
              <p className="mt-2 text-base text-gray-500">
                Upload and analyze your medical bills to identify errors, negotiate charges, 
                and understand what you owe.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-green-100 p-3 rounded-lg">
                  <Calculator className="h-8 w-8 text-green-600" />
                </div>
              </div>
              <h3 className="mt-6 text-lg font-medium text-gray-900">Cost Estimation</h3>
              <p className="mt-2 text-base text-gray-500">
                Get accurate cost estimates for medical procedures before you receive care, 
                including your out-of-pocket responsibility.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-purple-100 p-3 rounded-lg">
                  <Shield className="h-8 w-8 text-purple-600" />
                </div>
              </div>
              <h3 className="mt-6 text-lg font-medium text-gray-900">Insurance Analysis</h3>
              <p className="mt-2 text-base text-gray-500">
                Understand your insurance coverage, deductibles, and out-of-pocket maximums 
                to maximize your benefits.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-yellow-100 p-3 rounded-lg">
                  <TrendingUp className="h-8 w-8 text-yellow-600" />
                </div>
              </div>
              <h3 className="mt-6 text-lg font-medium text-gray-900">Navigation Plans</h3>
              <p className="mt-2 text-base text-gray-500">
                Get personalized step-by-step plans to navigate complex healthcare 
                financial situations.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-red-100 p-3 rounded-lg">
                  <Heart className="h-8 w-8 text-red-600" />
                </div>
              </div>
              <h3 className="mt-6 text-lg font-medium text-gray-900">Assistance Programs</h3>
              <p className="mt-2 text-base text-gray-500">
                Discover financial assistance programs, charity care, and other resources 
                you may qualify for.
              </p>
            </div>

            <div className="text-center">
              <div className="flex justify-center">
                <div className="bg-indigo-100 p-3 rounded-lg">
                  <Activity className="h-8 w-8 text-indigo-600" />
                </div>
              </div>
              <h3 className="mt-6 text-lg font-medium text-gray-900">Payment Plans</h3>
              <p className="mt-2 text-base text-gray-500">
                Create manageable payment plans that work with your budget and help you 
                pay off medical debt over time.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-blue-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-extrabold text-white">
            Ready to Take Control of Your Healthcare Costs?
          </h2>
          <p className="mt-4 text-xl text-blue-100">
            Join thousands of users who have saved money and reduced stress with MedFin.
          </p>
          <div className="mt-10">
            <Link 
              href="/register" 
              className="bg-white text-blue-600 px-8 py-3 rounded-md text-lg font-medium hover:bg-gray-50 inline-flex items-center"
            >
              Get Started Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2024 MedFin. Autonomous Healthcare Financial Navigation System.
          </p>
        </div>
      </footer>
    </div>
  )
}



