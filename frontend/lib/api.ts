import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

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

// Auth API
export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface LoginData {
  username: string
  password: string
}

export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  is_active: boolean
  created_at: string
  has_insurance_info?: boolean
}

export const register = (data: RegisterData) =>
  api.post('/api/v1/auth/register', data)

export const login = async (data: LoginData) => {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('password', data.password)
  
  const response = await api.post('/api/v1/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  
  // Store token
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token)
  }
  
  return response
}

export const getCurrentUser = () => api.get<User>('/api/v1/auth/me')

export const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

// User Dashboard API
export const getUserDashboard = () =>
  api.get('/api/v1/user/dashboard')

// Export API
export const exportDashboardPDF = () =>
  api.get('/api/v1/user/export/dashboard-pdf', {
    responseType: 'blob'
  })

export const exportNavigationPlanPDF = (planId: number) =>
  api.get(`/api/v1/user/export/navigation-plan/${planId}/pdf`, {
    responseType: 'blob'
  })

// User Data API
export const saveInsuranceInfo = (data: InsuranceInfo) =>
  api.post('/api/v1/user/insurance', data)

export const getInsuranceInfo = () =>
  api.get<InsuranceInfo>('/api/v1/user/insurance')

export const saveBill = (data: MedicalBill) =>
  api.post('/api/v1/user/bills', data)

export const getSavedBills = () =>
  api.get<MedicalBill[]>('/api/v1/user/bills')

export const saveCostEstimate = (data: any) =>
  api.post('/api/v1/user/cost-estimates', data)

export const getSavedCostEstimates = () =>
  api.get('/api/v1/user/cost-estimates')

export const saveNavigationPlan = (data: any) =>
  api.post('/api/v1/user/navigation-plans', data)

export const getSavedNavigationPlans = () =>
  api.get('/api/v1/user/navigation-plans')

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
