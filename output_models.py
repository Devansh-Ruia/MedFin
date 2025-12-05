"""
MedFin Analysis Engine - Analysis Output Models
Structured output types for all analysis modules
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

# Import enums from data models
# from .data_models import RiskTier, IncomeTier, BillErrorType, ...


# ============================================================================
# INCOME ANALYSIS OUTPUT
# ============================================================================

class FPLCalculation(BaseModel):
    """Federal Poverty Level calculation details"""
    household_size: int
    annual_income: Decimal
    fpl_threshold: Decimal  # 100% FPL for household size
    fpl_percentage: float
    income_tier: 'IncomeTier'
    
    # Key thresholds
    is_below_100_fpl: bool
    is_below_138_fpl: bool  # Medicaid expansion threshold
    is_below_200_fpl: bool  # Many assistance programs
    is_below_250_fpl: bool  # Enhanced CSR threshold
    is_below_400_fpl: bool  # ACA subsidy cliff

class BudgetProjection(BaseModel):
    """Monthly budget analysis"""
    total_monthly_income: Decimal
    total_monthly_expenses: Decimal
    debt_payments: Decimal
    estimated_living_expenses: Decimal  # Based on location/household
    disposable_income: Decimal
    medical_payment_capacity: Decimal  # What can go toward medical bills
    stress_ratio: float  # Medical debt / disposable income

class AffordabilityAssessment(BaseModel):
    """Assessment of affordability for upcoming expenses"""
    procedure_name: Optional[str] = None
    estimated_cost: Decimal
    patient_responsibility_estimate: Decimal
    can_afford_lump_sum: bool
    months_to_pay_off: int
    recommended_monthly_payment: Decimal
    will_cause_hardship: bool

class IncomeAnalysisOutput(BaseModel):
    """Complete income analysis results"""
    analysis_id: UUID = Field(default_factory=uuid4)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # FPL Analysis
    fpl_calculation: FPLCalculation
    
    # Income Classification
    income_tier: 'IncomeTier'
    income_stability_score: float  # 0-1, based on source types
    has_irregular_income: bool
    primary_income_type: 'IncomeType'
    
    # Budget Analysis
    budget_projection: BudgetProjection
    
    # Risk Assessment
    financial_risk_tier: 'RiskTier'
    risk_factors: list[str]
    
    # Hardship Indicators
    hardship_flags: list[str]
    qualifies_for_hardship: bool
    hardship_score: int  # 0-100
    
    # Affordability
    affordability_assessments: list[AffordabilityAssessment] = Field(default_factory=list)
    
    # Recommendations
    income_recommendations: list[str]
    
    # Eligibility Indicators
    likely_medicaid_eligible: bool
    likely_marketplace_subsidy_eligible: bool
    likely_charity_care_eligible: bool
    estimated_charity_care_discount: float  # 0-1


# ============================================================================
# DEBT ANALYSIS OUTPUT
# ============================================================================

class DebtBreakdown(BaseModel):
    """Categorized debt breakdown"""
    total_debt: Decimal
    medical_debt: Decimal
    medical_debt_percentage: float
    consumer_debt: Decimal
    secured_debt: Decimal
    unsecured_debt: Decimal
    debt_in_collections: Decimal
    high_interest_debt: Decimal  # >20% APR

class DTIAnalysis(BaseModel):
    """Debt-to-income ratio analysis"""
    gross_dti_ratio: float
    net_dti_ratio: float
    medical_dti_ratio: float  # Medical debt payments / income
    
    # Thresholds
    is_below_28_housing: bool  # Mortgage guideline
    is_below_36_total: bool    # Traditional lending threshold
    is_below_43_qualified: bool  # QM threshold
    
    # Risk tier
    dti_risk_tier: 'RiskTier'

class DebtTrendAnalysis(BaseModel):
    """Trend analysis from payment history"""
    avg_payment_on_time_rate: float  # 0-1
    recent_delinquencies: int  # Last 12 months
    trend_direction: str  # improving, stable, declining
    estimated_months_to_payoff: Optional[int] = None
    snowball_vs_avalanche_savings: Decimal  # If switching strategies

class QualificationAssessment(BaseModel):
    """Assessment of qualification for assistance/programs"""
    program_type: str
    program_name: str
    qualification_likelihood: float  # 0-1
    qualifying_factors: list[str]
    disqualifying_factors: list[str]
    estimated_benefit: Optional[Decimal] = None
    required_actions: list[str]

class DebtAnalysisOutput(BaseModel):
    """Complete debt analysis results"""
    analysis_id: UUID = Field(default_factory=uuid4)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Debt Breakdown
    debt_breakdown: DebtBreakdown
    
    # DTI Analysis
    dti_analysis: DTIAnalysis
    
    # Risk Assessment
    debt_risk_tier: 'RiskTier'
    debt_risk_score: int  # 0-100
    risk_factors: list[str]
    
    # Collections Risk
    collections_risk_score: float  # 0-1
    bills_at_collections_risk: list[str]  # Bill IDs
    
    # Trend Analysis
    trend_analysis: Optional[DebtTrendAnalysis] = None
    
    # Qualification Assessments
    qualifications: list[QualificationAssessment]
    
    # Strategy Recommendations
    recommended_strategies: list[str]
    priority_debts: list[str]  # Account IDs in priority order
    
    # Flags
    bankruptcy_may_be_appropriate: bool
    debt_consolidation_recommended: bool
    credit_counseling_recommended: bool


# ============================================================================
# INSURANCE ANALYSIS OUTPUT
# ============================================================================

class DeductibleStatus(BaseModel):
    """Deductible tracking status"""
    total_deductible: Decimal
    amount_met: Decimal
    amount_remaining: Decimal
    percentage_met: float
    
    # Projections
    will_meet_with_pending_bills: bool
    estimated_date_to_meet: Optional[date] = None
    amount_pending_toward_deductible: Decimal

class OOPStatus(BaseModel):
    """Out-of-pocket maximum tracking"""
    total_oop_max: Decimal
    amount_met: Decimal
    amount_remaining: Decimal
    percentage_met: float
    
    # Proximity alerts
    proximity_tier: str  # far, moderate, close, very_close, met
    
    # Projections
    will_meet_with_pending_bills: bool
    potential_savings_after_max: Decimal
    
    # Strategic insight
    elective_care_recommendation: Optional[str] = None

class CoverageGap(BaseModel):
    """Identified coverage gap"""
    gap_type: str
    description: str
    affected_service: Optional[str] = None
    financial_exposure: Decimal
    mitigation_options: list[str]
    severity: 'RiskTier'

class CodingMismatch(BaseModel):
    """Potential coding issue identified"""
    bill_id: str
    line_item_id: str
    issue_type: str
    expected_code: Optional[str] = None
    actual_code: str
    expected_coverage: str
    actual_coverage: str
    potential_savings: Decimal
    confidence: float

class CoverageMatch(BaseModel):
    """Coverage match for upcoming procedure"""
    procedure_name: str
    cpt_codes: list[str]
    is_covered: bool
    requires_preauth: bool
    preauth_status: Optional[str] = None
    estimated_allowed_amount: Decimal
    estimated_patient_cost: Decimal
    network_requirement: str
    coverage_notes: list[str]

class InsuranceAnalysisOutput(BaseModel):
    """Complete insurance analysis results"""
    analysis_id: UUID = Field(default_factory=uuid4)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status Tracking
    deductible_status: DeductibleStatus
    oop_status: OOPStatus
    
    # Family deductible (if applicable)
    family_deductible_status: Optional[DeductibleStatus] = None
    family_oop_status: Optional[OOPStatus] = None
    
    # Plan Year Insights
    days_remaining_in_plan_year: int
    deductible_reset_date: date
    year_end_strategy: Optional[str] = None
    
    # Coverage Analysis
    coverage_gaps: list[CoverageGap]
    coding_mismatches: list[CodingMismatch]
    
    # Procedure Coverage
    coverage_matches: list[CoverageMatch]
    
    # Warnings
    coverage_warnings: list[str]
    network_warnings: list[str]
    
    # Coordination (if secondary insurance)
    coordination_status: Optional[str] = None
    coordination_savings_estimate: Decimal = Decimal("0")
    
    # Overall Assessment
    plan_adequacy_score: float  # 0-1
    uncovered_exposure_estimate: Decimal


# ============================================================================
# BILL ANALYSIS OUTPUT
# ============================================================================

class BillError(BaseModel):
    """Identified billing error"""
    error_id: UUID = Field(default_factory=uuid4)
    bill_id: str
    line_item_id: Optional[str] = None
    error_type: 'BillErrorType'
    severity: 'RiskTier'
    
    # Details
    description: str
    evidence: list[str]
    
    # Financial impact
    overcharge_amount: Decimal
    potential_recovery: Decimal
    recovery_confidence: float  # 0-1
    
    # Resolution
    dispute_recommended: bool
    dispute_template_id: Optional[str] = None
    estimated_resolution_days: int
    required_documents: list[str]

class DuplicateCharge(BaseModel):
    """Identified duplicate charge"""
    original_line_id: str
    duplicate_line_id: str
    charge_amount: Decimal
    service_date: date
    cpt_code: Optional[str] = None
    match_confidence: float  # 0-1
    match_type: str  # exact, similar, potential

class BundlingIssue(BaseModel):
    """Identified bundling/unbundling issue"""
    parent_code: str
    child_codes: list[str]
    issue_type: str  # unbundled, incorrect_bundle
    overbilled_amount: Decimal
    correct_billing_amount: Decimal
    cci_edit_reference: Optional[str] = None  # CMS CCI edit rule

class NegotiationOpportunity(BaseModel):
    """Bill negotiation opportunity"""
    bill_id: str
    negotiation_type: str  # prompt_pay, financial_hardship, price_match, cash_pay
    
    # Estimates
    current_balance: Decimal
    target_amount: Decimal
    expected_savings: Decimal
    savings_confidence: float
    
    # Strategy
    negotiation_script_points: list[str]
    leverage_factors: list[str]
    best_time_to_call: Optional[str] = None
    decision_maker_title: Optional[str] = None

class PreventiveCareFlag(BaseModel):
    """Service that should be preventive (no cost share)"""
    bill_id: str
    line_item_id: str
    service_description: str
    cpt_code: str
    reason_should_be_preventive: str
    patient_charged: Decimal
    uspstf_reference: Optional[str] = None

class SingleBillAnalysis(BaseModel):
    """Analysis results for a single bill"""
    bill_id: str
    provider_name: str
    patient_balance: Decimal
    
    # Errors found
    errors: list[BillError]
    duplicates: list[DuplicateCharge]
    bundling_issues: list[BundlingIssue]
    preventive_care_flags: list[PreventiveCareFlag]
    
    # Totals
    total_overcharge_identified: Decimal
    total_potential_recovery: Decimal
    
    # Negotiation
    negotiation_opportunities: list[NegotiationOpportunity]
    
    # Urgency
    urgency_score: int  # 0-100
    days_until_due: Optional[int] = None
    collections_risk: float  # 0-1

class BillAnalysisOutput(BaseModel):
    """Complete bill analysis results"""
    analysis_id: UUID = Field(default_factory=uuid4)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Individual bill analyses
    bill_analyses: list[SingleBillAnalysis]
    
    # Aggregate findings
    total_bills_analyzed: int
    total_patient_balance: Decimal
    total_errors_found: int
    total_potential_savings: Decimal
    
    # Error summary by type
    errors_by_type: dict[str, int]
    
    # Priority actions
    high_priority_disputes: list[str]  # Error IDs
    
    # Overall assessment
    billing_accuracy_score: float  # 0-1, 1 = no errors found
    
    # Recommendations
    immediate_actions: list[str]
    dispute_sequence: list[str]  # Ordered list of error IDs to dispute


# ============================================================================
# UNIFIED ANALYSIS OUTPUT
# ============================================================================

class RiskSummary(BaseModel):
    """Consolidated risk assessment"""
    overall_risk_tier: 'RiskTier'
    overall_risk_score: int  # 0-100
    
    # Component scores
    income_risk_score: int
    debt_risk_score: int
    insurance_risk_score: int
    billing_risk_score: int
    
    # Top risk factors
    critical_risk_factors: list[str]
    
    # Collections/credit risk
    collections_probability: float
    credit_impact_risk: 'RiskTier'

class OpportunitySummary(BaseModel):
    """Consolidated savings opportunities"""
    total_potential_savings: Decimal
    high_confidence_savings: Decimal  # >70% confidence
    
    # By category
    billing_error_savings: Decimal
    negotiation_savings: Decimal
    assistance_program_savings: Decimal
    insurance_optimization_savings: Decimal
    
    # Top opportunities
    top_opportunities: list[dict]  # Sorted by expected value

class StrategySummary(BaseModel):
    """Recommended strategy summary"""
    primary_strategy: str
    strategy_rationale: str
    
    # Immediate actions (next 7 days)
    immediate_actions: list[str]
    
    # Short-term actions (next 30 days)
    short_term_actions: list[str]
    
    # Long-term actions (30+ days)
    long_term_actions: list[str]
    
    # Key deadlines
    critical_deadlines: list[tuple[date, str]]

class UnifiedAnalysisOutput(BaseModel):
    """Complete unified analysis output for downstream consumption"""
    analysis_id: UUID = Field(default_factory=uuid4)
    user_id: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_version: str = "1.0.0"
    
    # Component analyses
    income_analysis: IncomeAnalysisOutput
    debt_analysis: DebtAnalysisOutput
    insurance_analysis: Optional[InsuranceAnalysisOutput] = None
    bill_analysis: BillAnalysisOutput
    
    # Synthesized outputs
    risk_summary: RiskSummary
    opportunity_summary: OpportunitySummary
    strategy_summary: StrategySummary
    
    # Key metrics for downstream
    fpl_percentage: float
    total_medical_debt: Decimal
    total_pending_bills: Decimal
    deductible_remaining: Optional[Decimal] = None
    oop_remaining: Optional[Decimal] = None
    monthly_payment_capacity: Decimal
    
    # Flags for downstream features
    needs_assistance_matching: bool
    needs_payment_plan: bool
    has_disputable_errors: bool
    has_negotiation_opportunities: bool
    urgent_action_required: bool
    
    # Data quality
    data_completeness_score: float  # 0-1
    confidence_score: float  # 0-1
    
    # Metadata
    processing_time_ms: int
    warnings: list[str] = Field(default_factory=list)