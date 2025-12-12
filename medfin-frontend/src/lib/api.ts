// src/lib/api.ts

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  ApiResponse,
  NavigationPlanResponse,
  CostEstimateRequest,
  CostEstimateResponse,
  BillAnalysisResponse,
  InsuranceAnalysisResponse,
  AssistanceIntakeRequest,
  AssistanceMatchResponse,
  PaymentPlanRequest,
  PaymentPlanResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class MedFinApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = typeof window !== 'undefined' 
          ? localStorage.getItem('medfin_token') 
          : null;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const message = this.getErrorMessage(error);
        console.error('[MedFin API Error]:', message);
        return Promise.reject(new Error(message));
      }
    );
  }

  private getErrorMessage(error: AxiosError): string {
    if (error.response) {
      const data = error.response.data as { message?: string; error?: string };
      return data.message || data.error || `Server error: ${error.response.status}`;
    }
    if (error.request) {
      return 'Network error: Unable to reach server';
    }
    return error.message || 'An unexpected error occurred';
  }

  // ============================================
  // NAVIGATION PLAN
  // ============================================

  async getNavigationPlan(userId: string): Promise<ApiResponse<NavigationPlanResponse>> {
    const response = await this.client.get<ApiResponse<NavigationPlanResponse>>(
      `/navigation/plan`,
      { params: { userId } }
    );
    return response.data;
  }

  async refreshNavigationPlan(userId: string): Promise<ApiResponse<NavigationPlanResponse>> {
    const response = await this.client.post<ApiResponse<NavigationPlanResponse>>(
      `/navigation/plan/refresh`,
      { userId }
    );
    return response.data;
  }

  async markActionComplete(
    userId: string, 
    recommendationId: string
  ): Promise<ApiResponse<{ success: boolean }>> {
    const response = await this.client.post<ApiResponse<{ success: boolean }>>(
      `/navigation/plan/actions/${recommendationId}/complete`,
      { userId }
    );
    return response.data;
  }

  // ============================================
  // COST ESTIMATION
  // ============================================

  async estimateCost(request: CostEstimateRequest): Promise<ApiResponse<CostEstimateResponse>> {
    const response = await this.client.post<ApiResponse<CostEstimateResponse>>(
      `/cost/estimate`,
      request
    );
    return response.data;
  }

  async searchServices(query: string): Promise<ApiResponse<{ services: { code: string; name: string }[] }>> {
    const response = await this.client.get<ApiResponse<{ services: { code: string; name: string }[] }>>(
      `/cost/services/search`,
      { params: { q: query } }
    );
    return response.data;
  }

  // ============================================
  // BILL ANALYSIS
  // ============================================

  async analyzeBill(file: File): Promise<ApiResponse<BillAnalysisResponse>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<ApiResponse<BillAnalysisResponse>>(
      `/bills/analyze`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000, // Longer timeout for file upload
      }
    );
    return response.data;
  }

  async getBillAnalysis(billId: string): Promise<ApiResponse<BillAnalysisResponse>> {
    const response = await this.client.get<ApiResponse<BillAnalysisResponse>>(
      `/bills/analyze/${billId}`
    );
    return response.data;
  }

  async generateItemizedRequest(billId: string): Promise<ApiResponse<{ template: string }>> {
    const response = await this.client.post<ApiResponse<{ template: string }>>(
      `/bills/${billId}/itemized-request`
    );
    return response.data;
  }

  // ============================================
  // INSURANCE ANALYSIS
  // ============================================

  async analyzeInsurance(userId: string): Promise<ApiResponse<InsuranceAnalysisResponse>> {
    const response = await this.client.get<ApiResponse<InsuranceAnalysisResponse>>(
      `/insurance/analyze`,
      { params: { userId } }
    );
    return response.data;
  }

  async updateInsuranceInfo(
    userId: string, 
    data: Partial<InsuranceAnalysisResponse>
  ): Promise<ApiResponse<InsuranceAnalysisResponse>> {
    const response = await this.client.put<ApiResponse<InsuranceAnalysisResponse>>(
      `/insurance/analyze`,
      { userId, ...data }
    );
    return response.data;
  }

  // ============================================
  // ASSISTANCE PROGRAMS
  // ============================================

  async matchAssistancePrograms(
    request: AssistanceIntakeRequest
  ): Promise<ApiResponse<AssistanceMatchResponse>> {
    const response = await this.client.post<ApiResponse<AssistanceMatchResponse>>(
      `/assistance/match`,
      request
    );
    return response.data;
  }

  async getProgramDetails(programId: string): Promise<ApiResponse<AssistanceProgram>> {
    const response = await this.client.get<ApiResponse<AssistanceProgram>>(
      `/assistance/programs/${programId}`
    );
    return response.data;
  }

  // ============================================
  // PAYMENT PLANS
  // ============================================

  async generatePaymentPlans(
    request: PaymentPlanRequest
  ): Promise<ApiResponse<PaymentPlanResponse>> {
    const response = await this.client.post<ApiResponse<PaymentPlanResponse>>(
      `/payment-plans/generate`,
      request
    );
    return response.data;
  }

  async selectPaymentPlan(
    planId: string, 
    userId: string
  ): Promise<ApiResponse<{ confirmationId: string }>> {
    const response = await this.client.post<ApiResponse<{ confirmationId: string }>>(
      `/payment-plans/${planId}/select`,
      { userId }
    );
    return response.data;
  }
}

// Export singleton instance
export const api = new MedFinApiClient();

// Export class for testing
export { MedFinApiClient };