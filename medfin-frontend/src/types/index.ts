// src/types/index.ts

// ============================================
// RISK & SCORING TYPES
// ============================================

export type RiskCategory = 'critical' | 'high' | 'moderate' | 'low' | 'minimal';
export type RiskDimension = 
  | 'income_stability' 
  | 'debt_burden' 
  | 'medical_debt_ratio'
  | 'collections_exposure'
  | 'payment_history'
  | 'upcoming_costs'
  | 'insurance_gaps'
  | 'coverage_adequacy'
  | 'bill_errors'
  | 'affordability';

export type AlertSeverity = 'critical' | 'warning' | 'caution' | 'info';
export type ActionPriority = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type DifficultyLevel = 'trivial' | 'easy' | 'moderate' | 'challenging' | 'complex';
export type ActionCategory = 'billing' | 'insurance' | 'assistance' | 'negotiation' | 'payment' | 'optimization';

export interface RiskFactor {
  dimension: RiskDimension;
  factor: string;
  impact: number;
  description: string;
}

export interface RiskDimensionScore {
  dimension: RiskDimension;
  score: number;
  weight: number;
  weightedScore: number;
  factors: RiskFactor[];
}

export interface Alert {
  severity: AlertSeverity;
  title: string;
  message: string;
  actionRequired?: boolean;
  relatedRecommendationId?: string;
}

export interface RiskAssessment {
  overallScore: number;
  category: RiskCategory;
  dimensionalScores: RiskDimensionScore[];
  topRiskDrivers: RiskFactor[];
  criticalFactors: RiskFactor[];
  alerts: Alert[];
  confidence: number;
  dataCompleteness: number;
  summary: string;
}

// ============================================
// RECOMMENDATION TYPES
// ============================================

export interface SavingsEstimate {
  min: number;
  expected: number;
  max: number;
  confidence: number;
}

export interface ActionStep {
  stepNumber: number;
  title: string;
  description: string;
  estimatedMinutes: number;
  tips?: string[];
  script?: string;
}

export interface DocumentRequirement {
  documentType: string;
  description: string;
  required: boolean;
  whereToFind?: string;
}

export interface ContactInfo {
  department: string;
  phone?: string;
  email?: string;
  hours?: string;
  notes?: string;
}

export interface Recommendation {
  id: string;
  category: ActionCategory;
  priority: ActionPriority;
  title: string;
  description: string;
  reasoning: string;
  savingsEstimate: SavingsEstimate;
  timeEstimateMinutes: number;
  difficulty: DifficultyLevel;
  successProbability: number;
  steps: ActionStep[];
  requiredDocuments: DocumentRequirement[];
  contactInfo?: ContactInfo;
  deadline?: string;
  prerequisites: string[];
  warnings?: string[];
  tips: string[];
}

export interface RankingFactors {
  urgencyScore: number;
  savingsImpactScore: number;
  successScore: number;
  riskReductionScore: number;
  easeScore: number;
}

export interface RankedRecommendation {
  recommendation: Recommendation;
  rankingFactors: RankingFactors;
  compositeScore: number;
  finalRank: number;
  rationale: string;
}

// ============================================
// NAVIGATION PLAN TYPES
// ============================================

export interface ActionPlan {
  immediate: RankedRecommendation[];
  thisWeek: RankedRecommendation[];
  thisMonth: RankedRecommendation[];
  ongoing: RankedRecommendation[];
}

export interface TotalSavings {
  min: number;
  expected: number;
  max: number;
}

export interface NavigationPlanResponse {
  userId: string;
  riskAssessment: RiskAssessment;
  recommendations: RankedRecommendation[];
  actionPlan: ActionPlan;
  totalPotentialSavings: TotalSavings;
  totalRiskReduction: number;
  criticalActionCount: number;
  executiveSummary: string;
  keyTakeaways: string[];
  alerts: Alert[];
  confidence: number;
  processingTimeMs: number;
  generatedAt: string;
}

// ============================================
// COST ESTIMATION TYPES
// ============================================

export interface CostEstimateRequest {
  serviceCode: string;
  serviceName?: string;
  zipCode: string;
  insuranceId?: string;
  networkStatus?: 'in_network' | 'out_of_network' | 'unknown';
}

export interface ProviderCost {
  providerId: string;
  providerName: string;
  facilityType: string;
  address: string;
  distance: number;
  estimatedCost: number;
  patientResponsibility: number;
  insurancePays: number;
  networkStatus: 'in_network' | 'out_of_network';
  qualityRating?: number;
}

export interface CostEstimateResponse {
  serviceCode: string;
  serviceName: string;
  averageCost: number;
  costRange: { min: number; max: number };
  patientResponsibility: number;
  insuranceCoverage: number;
  deductibleApplied: number;
  coinsurance: number;
  copay: number;
  providers: ProviderCost[];
  savingsTips: string[];
  generatedAt: string;
}

// ============================================
// BILL ANALYSIS TYPES
// ============================================

export interface BillError {
  errorType: 'duplicate' | 'unbundling' | 'upcoding' | 'preventive_miscoding' | 'balance_billing' | 'other';
  severity: 'high' | 'medium' | 'low';
  description: string;
  lineItems: string[];
  potentialSavings: number;
  actionRequired: string;
}

export interface CoverageMismatch {
  serviceCode: string;
  serviceName: string;
  billedAmount: number;
  expectedCoverage: number;
  actualCoverage: number;
  discrepancy: number;
  reason: string;
}

export interface BillAnalysisResponse {
  billId: string;
  providerName: string;
  totalBilled: number;
  insurancePaid: number;
  patientBalance: number;
  errors: BillError[];
  duplicates: { originalId: string; duplicateId: string; amount: number }[];
  coverageMismatches: CoverageMismatch[];
  potentialSavings: {
    fromErrors: number;
    fromDisputes: number;
    fromNegotiation: number;
    total: number;
  };
  recommendations: Recommendation[];
  itemizedBillTemplate?: string;
  analyzedAt: string;
}

// ============================================
// INSURANCE ANALYSIS TYPES
// ============================================

export interface DeductibleStatus {
  individual: { limit: number; used: number; remaining: number };
  family: { limit: number; used: number; remaining: number };
  percentMet: number;
}

export interface OutOfPocketStatus {
  individual: { limit: number; used: number; remaining: number };
  family: { limit: number; used: number; remaining: number };
  percentMet: number;
}

export interface CoverageWarning {
  type: 'gap' | 'limitation' | 'exclusion' | 'expiring';
  severity: AlertSeverity;
  title: string;
  description: string;
  recommendation?: string;
}

export interface BenefitUtilization {
  benefitType: string;
  totalAllowed: number;
  used: number;
  remaining: number;
  percentUsed: number;
  expiresAt?: string;
}

export interface InsuranceAnalysisResponse {
  planName: string;
  planType: string;
  deductible: DeductibleStatus;
  outOfPocket: OutOfPocketStatus;
  planYearEnd: string;
  daysUntilReset: number;
  coverageWarnings: CoverageWarning[];
  benefitUtilization: BenefitUtilization[];
  optimizationSuggestions: Recommendation[];
  hsaFsaBalance?: number;
  estimatedYearEndPosition: {
    projectedSpending: number;
    projectedDeductibleMet: boolean;
    projectedOopMet: boolean;
  };
  analyzedAt: string;
}

// ============================================
// ASSISTANCE PROGRAM TYPES
// ============================================

export interface AssistanceIntakeRequest {
  householdSize: number;
  annualIncome: number;
  state: string;
  insuranceStatus: 'insured' | 'uninsured' | 'underinsured';
  medicalConditions?: string[];
  currentMedicalDebt?: number;
  employmentStatus?: string;
}

export interface AssistanceProgram {
  programId: string;
  programName: string;
  programType: 'charity_care' | 'medicaid' | 'state_program' | 'hospital_financial_assistance' | 'nonprofit' | 'pharmaceutical';
  provider: string;
  eligibilityStatus: 'eligible' | 'likely_eligible' | 'may_qualify' | 'ineligible';
  eligibilityConfidence: number;
  estimatedRelief: { min: number; max: number };
  coverageType: string;
  requirements: string[];
  applicationProcess: string;
  applicationUrl?: string;
  applicationDeadline?: string;
  processingTime: string;
  contactInfo: ContactInfo;
  notes?: string;
}

export interface AssistanceMatchResponse {
  fplPercentage: number;
  matchedPrograms: AssistanceProgram[];
  totalPotentialRelief: { min: number; max: number };
  recommendedPriority: string[];
  nextSteps: ActionStep[];
  matchedAt: string;
}

// ============================================
// PAYMENT PLAN TYPES
// ============================================

export interface PaymentPlanRequest {
  totalAmount: number;
  monthlyBudget: number;
  preferredTermMonths?: number;
  includeFees: boolean;
}

export interface PaymentPlanOption {
  planId: string;
  planType: 'interest_free' | 'low_interest' | 'extended' | 'hardship';
  termMonths: number;
  monthlyPayment: number;
  totalCost: number;
  interestRate: number;
  totalInterest: number;
  setupFee: number;
  lateFee: number;
  features: string[];
  requirements: string[];
  isRecommended: boolean;
  recommendationReason?: string;
}

export interface PaymentPlanResponse {
  originalAmount: number;
  options: PaymentPlanOption[];
  recommendedPlanId: string;
  comparisonNotes: string[];
  generatedAt: string;
}

// ============================================
// API RESPONSE WRAPPER
// ============================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta?: {
    requestId: string;
    timestamp: string;
    processingTimeMs: number;
  };
}

// ============================================
// UI STATE TYPES
// ============================================

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface FileUploadState {
  file: File | null;
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
}