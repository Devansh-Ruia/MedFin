import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface CostEstimationRequest {
  service_type: string
  procedure_code?: string
  description?: string
  location?: string
  insurance_type?: string
  has_insurance: boolean
  deductible_remaining?: number
  copay?: number
}

export interface InsuranceInfo {
  insurance_type: string
  plan_name?: string
  deductible: number
  deductible_remaining: number
  out_of_pocket_max: number
  out_of_pocket_used: number
  coverage_percentage: number
  copay_primary?: number
  copay_specialist?: number
  copay_emergency?: number
  in_network: boolean
}

export interface MedicalBill {
  bill_id: string
  provider_name: string
  service_date: string
  services: Array<{
    code?: string
    description?: string
    cost?: number
  }>
  total_amount: number
  insurance_paid?: number
  patient_responsibility: number
  due_date?: string
  status: string
}

// Cost Estimation API
export const estimateCost = (data: CostEstimationRequest) =>
  api.post('/api/v1/cost/estimate', data)

// Insurance API
export const analyzeInsurance = (data: InsuranceInfo) =>
  api.post('/api/v1/insurance/analyze', data)

// Bills API
export const analyzeBills = (data: {
  bills: MedicalBill[]
  insurance_info?: InsuranceInfo
  annual_income?: number
  household_size?: number
}) => api.post('/api/v1/bills/analyze', data)

// Navigation API
export const generateNavigationPlan = (data: {
  bills: MedicalBill[]
  insurance_info?: InsuranceInfo
  annual_income?: number
  household_size?: number
}) => api.post('/api/v1/navigation/plan', data)

// Assistance API
export const matchAssistancePrograms = (data: {
  annual_income?: number
  household_size?: number
  insurance_info?: InsuranceInfo
  medical_debt?: number
  has_prescriptions?: boolean
  has_diagnosis?: boolean
}) => api.post('/api/v1/assistance/match', data)

// Payment Plans API
export const generatePaymentPlans = (data: {
  total_debt: number
  monthly_income: number
  monthly_expenses: number
  preferences?: Record<string, any>
}) => api.post('/api/v1/payment-plans/generate', data)

export default api



