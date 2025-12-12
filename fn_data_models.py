"""
MedFin Financial Navigation System - Data Models
Comprehensive Pydantic models for healthcare financial data
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, Field, validator, computed_field
from uuid import UUID, uuid4


# ============================================================================
# ENUMERATIONS
# ============================================================================

class BillStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    DISPUTED = "disputed"
    PAYMENT_PLAN = "payment_plan"
    PAID = "paid"
    COLLECTIONS = "collections"
    WRITTEN_OFF = "written_off"

class BillErrorType(str, Enum):
    DUPLICATE_CHARGE = "duplicate_charge"
    INCORRECT_CODE = "incorrect_code"
    UNBUNDLING = "unbundling"
    UPCODING = "upcoding"
    BALANCE_BILLING = "balance_billing"
    WRONG_PATIENT = "wrong_patient"
    SERVICE_NOT_RENDERED = "service_not_rendered"
    TIMING_ERROR = "timing_error"
    MODIFIER_ERROR = "modifier_error"

class InsuranceType(str, Enum):
    EMPLOYER = "employer"
    MARKETPLACE = "marketplace"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    TRICARE = "tricare"
    PRIVATE = "private"
    NONE = "none"

class ActionType(str, Enum):
    DISPUTE_BILL = "dispute_bill"
    REQUEST_ITEMIZATION = "request_itemization"
    APPLY_ASSISTANCE = "apply_assistance"
    NEGOTIATE_BILL = "negotiate_bill"
    SETUP_PAYMENT_PLAN = "setup_payment_plan"
    FILE_INSURANCE_APPEAL = "file_insurance_appeal"
    REQUEST_CHARITY_CARE = "request_charity_care"
    VERIFY_INSURANCE_CLAIM = "verify_insurance_claim"
    CHECK_COORDINATION = "check_coordination"
    REQUEST_PRICE_MATCH = "request_price_match"

class Priority(str, Enum):
    CRITICAL = "critical"      # Immediate action, collections threat
    HIGH = "high"              # Time-sensitive, high savings
    MEDIUM = "medium"          # Moderate urgency
    LOW = "low"                # Nice to have
    INFORMATIONAL = "info"     # FYI only

class RiskLevel(str, Enum):
    SEVERE = "severe"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"


# ============================================================================
# CORE DATA MODELS
# ============================================================================

class LineItem(BaseModel):
    """Individual charge on a medical bill"""
    id: UUID = Field(default_factory=uuid4)
    cpt_code: Optional[str] = None
    hcpcs_code: Optional[str] = None
    icd10_codes: list[str] = Field(default_factory=list)
    description: str
    service_date: date
    quantity: int = 1
    billed_amount: Decimal
    allowed_amount: Optional[Decimal] = None
    insurance_paid: Decimal = Decimal("0")
    patient_responsibility: Decimal
    is_flagged: bool = False
    error_type: Optional[BillErrorType] = None
    error_confidence: float = 0.0  # 0-1 confidence in error detection

class MedicalBill(BaseModel):
    """Complete medical bill with all line items"""
    id: UUID = Field(default_factory=uuid4)
    provider_name: str
    provider_npi: Optional[str] = None
    provider_type: str  # hospital, physician, lab, etc.
    facility_type: Optional[str] = None  # inpatient, outpatient, ER
    statement_date: date
    service_date_start: date
    service_date_end: date
    line_items: list[LineItem]
    total_billed: Decimal
    total_allowed: Optional[Decimal] = None
    insurance_paid: Decimal = Decimal("0")
    patient_balance: Decimal
    status: BillStatus = BillStatus.PENDING
    due_date: Optional[date] = None
    is_in_network: Optional[bool] = None
    claim_number: Optional[str] = None
    account_number: Optional[str] = None
    
    @property
    def days_until_due(self) -> Optional[int]:
        if self.due_date:
            return (self.due_date - date.today()).days
        return None
    
    @property
    def total_errors_detected(self) -> int:
        return sum(1 for li in self.line_items if li.is_flagged)

class InsurancePlan(BaseModel):
    """Patient's insurance coverage details"""
    id: UUID = Field(default_factory=uuid4)
    plan_name: str
    insurance_type: InsuranceType
    carrier_name: str
    policy_number: str
    group_number: Optional[str] = None
    is_primary: bool = True
    
    # Deductible tracking
    individual_deductible: Decimal
    individual_deductible_met: Decimal = Decimal("0")
    family_deductible: Optional[Decimal] = None
    family_deductible_met: Decimal = Decimal("0")
    
    # Out-of-pocket tracking
    individual_oop_max: Decimal
    individual_oop_met: Decimal = Decimal("0")
    family_oop_max: Optional[Decimal] = None
    family_oop_met: Decimal = Decimal("0")
    
    # Cost sharing
    copay_primary: Decimal = Decimal("0")
    copay_specialist: Decimal = Decimal("0")
    copay_er: Decimal = Decimal("0")
    coinsurance_rate: float = 0.2  # Patient pays this %
    
    plan_year_start: date
    plan_year_end: date
    
    @property
    def deductible_remaining(self) -> Decimal:
        return max(Decimal("0"), self.individual_deductible - self.individual_deductible_met)
    
    @property
    def oop_remaining(self) -> Decimal:
        return max(Decimal("0"), self.individual_oop_max - self.individual_oop_met)
    
    @property
    def oop_percentage_met(self) -> float:
        if self.individual_oop_max == 0:
            return 1.0
        return float(self.individual_oop_met / self.individual_oop_max)

class IncomeSource(BaseModel):
    """Individual income source"""
    source_type: str  # employment, disability, social_security, etc.
    gross_monthly: Decimal
    net_monthly: Decimal
    is_verified: bool = False

class DebtItem(BaseModel):
    """Non-medical debt for budget analysis"""
    debt_type: str  # mortgage, auto, credit_card, student_loan
    creditor: str
    balance: Decimal
    monthly_payment: Decimal
    interest_rate: float
    is_secured: bool = False

class PatientFinancialProfile(BaseModel):
    """Complete patient financial picture"""
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    
    # Household info
    household_size: int = 1
    dependents: int = 0
    state: str
    county: Optional[str] = None
    zip_code: str
    
    # Income
    income_sources: list[IncomeSource] = Field(default_factory=list)
    total_monthly_gross: Decimal = Decimal("0")
    total_monthly_net: Decimal = Decimal("0")
    annual_gross_income: Decimal = Decimal("0")
    
    # Assets
    checking_balance: Decimal = Decimal("0")
    savings_balance: Decimal = Decimal("0")
    retirement_accounts: Decimal = Decimal("0")
    other_assets: Decimal = Decimal("0")
    
    # Debts
    debts: list[DebtItem] = Field(default_factory=list)
    total_monthly_debt_payments: Decimal = Decimal("0")
    
    # Medical specific
    existing_medical_debt: Decimal = Decimal("0")
    medical_debt_in_collections: Decimal = Decimal("0")
    
    # Computed metrics
    @property
    def debt_to_income_ratio(self) -> float:
        if self.total_monthly_gross == 0:
            return 0.0
        return float(self.total_monthly_debt_payments / self.total_monthly_gross)
    
    @property
    def federal_poverty_level_percentage(self) -> float:
        # 2024 FPL thresholds (continental US)
        fpl_base = 15060
        fpl_per_person = 5380
        fpl_threshold = fpl_base + (self.household_size - 1) * fpl_per_person
        return float(self.annual_gross_income / Decimal(str(fpl_threshold))) * 100
    
    @property
    def available_monthly_budget(self) -> Decimal:
        return self.total_monthly_net - self.total_monthly_debt_payments


# ============================================================================
# ASSISTANCE PROGRAMS
# ============================================================================

class EligibilityCriteria(BaseModel):
    """Criteria for assistance program eligibility"""
    max_fpl_percentage: Optional[float] = None
    max_annual_income: Optional[Decimal] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    required_insurance_types: list[InsuranceType] = Field(default_factory=list)
    excluded_insurance_types: list[InsuranceType] = Field(default_factory=list)
    required_states: list[str] = Field(default_factory=list)
    min_bill_amount: Optional[Decimal] = None
    diagnosis_codes: list[str] = Field(default_factory=list)

class AssistanceProgram(BaseModel):
    """Financial assistance program details"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    program_type: str  # charity_care, state_assistance, pharma, nonprofit
    provider_name: Optional[str] = None  # If hospital-specific
    eligibility: EligibilityCriteria
    typical_discount_percentage: float
    max_coverage: Optional[Decimal] = None
    application_url: Optional[str] = None
    required_documents: list[str] = Field(default_factory=list)
    processing_days: int = 30
    is_retroactive: bool = False


# ============================================================================
# ACTION PLAN OUTPUT MODELS
# ============================================================================

class SavingsEstimate(BaseModel):
    """Projected savings from an action"""
    minimum: Decimal
    expected: Decimal
    maximum: Decimal
    confidence: float  # 0-1

class ActionStep(BaseModel):
    """Single action in the navigation plan"""
    id: UUID = Field(default_factory=uuid4)
    step_number: int
    action_type: ActionType
    priority: Priority
    title: str
    description: str
    
    # Targets
    target_bill_id: Optional[UUID] = None
    target_provider: Optional[str] = None
    target_program_id: Optional[UUID] = None
    
    # Effort and timing
    estimated_effort_minutes: int
    deadline: Optional[date] = None
    recommended_start: date
    
    # Financial impact
    savings_estimate: SavingsEstimate
    approval_likelihood: float  # 0-1
    
    # Instructions
    detailed_steps: list[str]
    required_documents: list[str] = Field(default_factory=list)
    contact_info: Optional[str] = None
    template_id: Optional[str] = None
    
    # Dependencies
    depends_on_steps: list[int] = Field(default_factory=list)
    
    # Warnings
    warnings: list[str] = Field(default_factory=list)

class RiskAssessment(BaseModel):
    """Overall financial risk assessment"""
    overall_risk_level: RiskLevel
    risk_score: int  # 0-100
    
    collections_risk: RiskLevel
    collections_probability: float
    
    credit_impact_risk: RiskLevel
    
    bankruptcy_risk: RiskLevel
    
    key_risk_factors: list[str]
    mitigation_recommendations: list[str]

class BudgetImpact(BaseModel):
    """Impact on patient's monthly budget"""
    current_medical_payment_burden: Decimal
    projected_after_plan: Decimal
    monthly_savings: Decimal
    
    percent_of_income_current: float
    percent_of_income_projected: float
    
    recommended_monthly_payment: Decimal
    maximum_sustainable_payment: Decimal

class NavigationPlan(BaseModel):
    """Complete financial navigation plan"""
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: date
    
    # Summary
    total_bills_analyzed: int
    total_amount_owed: Decimal
    potential_total_savings: SavingsEstimate
    
    # Actions
    action_steps: list[ActionStep]
    critical_actions_count: int
    
    # Assessments
    risk_assessment: RiskAssessment
    budget_impact: BudgetImpact
    
    # Timeline
    plan_duration_days: int
    key_deadlines: list[tuple[date, str]]
    
    # Explanations
    executive_summary: str
    methodology_notes: list[str]
    assumptions: list[str]
    
    # Metadata
    confidence_score: float
    data_completeness_score: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# RISK ASSESSMENT AND RECOMMENDATION MODELS
# ============================================================================

class RiskCategory(str, Enum):
    """Overall risk classification"""
    CRITICAL = "critical"      # Score 80-100: Immediate intervention required
    HIGH = "high"              # Score 60-79: Urgent attention needed
    MODERATE = "moderate"      # Score 40-59: Active management required
    LOW = "low"                # Score 20-39: Monitor and maintain
    MINIMAL = "minimal"        # Score 0-19: Healthy financial state

class RiskDimension(str, Enum):
    """Individual risk assessment dimensions"""
    INCOME_STABILITY = "income_stability"
    DEBT_BURDEN = "debt_burden"
    MEDICAL_DEBT_RATIO = "medical_debt_ratio"
    UPCOMING_COSTS = "upcoming_costs"
    INSURANCE_GAPS = "insurance_gaps"
    BILL_ERRORS = "bill_errors"
    PAYMENT_HISTORY = "payment_history"
    COLLECTIONS_EXPOSURE = "collections_exposure"
    COVERAGE_ADEQUACY = "coverage_adequacy"
    AFFORDABILITY = "affordability"

class ActionCategory(str, Enum):
    """Categories of recommended actions"""
    BILL_DISPUTE = "bill_dispute"
    INSURANCE_APPEAL = "insurance_appeal"
    ASSISTANCE_APPLICATION = "assistance_application"
    NEGOTIATION = "negotiation"
    PAYMENT_OPTIMIZATION = "payment_optimization"
    INSURANCE_OPTIMIZATION = "insurance_optimization"
    DEBT_MANAGEMENT = "debt_management"
    COST_AVOIDANCE = "cost_avoidance"
    DOCUMENT_REQUEST = "document_request"
    VERIFICATION = "verification"

class ActionPriority(str, Enum):
    """Priority levels for recommended actions"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DifficultyLevel(str, Enum):
    """Difficulty of completing an action"""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    COMPLEX = "complex"

class SuccessLikelihood(str, Enum):
    """Likelihood of successful outcome"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"

class AlertSeverity(str, Enum):
    """Severity level for alerts"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class RiskFactor(BaseModel):
    """Individual risk factor with scoring"""
    factor: str
    description: str
    impact_score: float = Field(ge=0, le=1)  # 0-1 impact on overall risk
    category: RiskDimension
    is_reversible: bool = False
    timeframe_to_resolution: Optional[str] = None

class RiskDimensionScore(BaseModel):
    """Score for a specific risk dimension"""
    dimension: RiskDimension
    score: int = Field(ge=0, le=100)
    level: RiskCategory
    primary_factors: list[RiskFactor]
    trend: str = "stable"  # improving, worsening, stable
    confidence: float = Field(ge=0, le=1)

class Alert(BaseModel):
    """Alert for immediate attention"""
    alert_id: UUID = Field(default_factory=uuid4)
    severity: AlertSeverity
    title: str
    description: str
    recommendation: str
    deadline: Optional[date] = None
    financial_impact: Optional[Decimal] = None
    action_required: bool = True

class EnhancedRiskAssessment(BaseModel):
    """Complete risk assessment output"""
    assessment_id: UUID = Field(default_factory=uuid4)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    overall_score: int = Field(ge=0, le=100)
    category: RiskCategory
    category_description: str
    dimension_scores: dict[RiskDimension, RiskDimensionScore] = Field(default_factory=dict)
    top_risk_factors: list[RiskFactor] = Field(default_factory=list)
    critical_factors: list[RiskFactor] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    critical_alert_count: int = 0
    data_completeness: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    data_quality_warnings: list[str] = Field(default_factory=list)
    summary: str = ""
    key_insights: list[str] = Field(default_factory=list)

class EnhancedSavingsEstimate(BaseModel):
    """Estimated financial impact"""
    minimum: Decimal = Decimal("0")
    expected: Decimal = Decimal("0")
    maximum: Decimal = Decimal("0")
    confidence: float = Field(ge=0, le=1, default=0.5)
    calculation_method: str = "estimated"
    assumptions: list[str] = Field(default_factory=list)

class TimeEstimate(BaseModel):
    """Time required to complete action"""
    minimum_minutes: int = 0
    expected_minutes: int = 0
    maximum_minutes: int = 0
    
    @property
    def formatted_time(self) -> str:
        mins = self.expected_minutes
        if mins < 60: return f"{mins} minutes"
        hours = mins // 60
        remaining = mins % 60
        if remaining == 0: return f"{hours} hour{'s' if hours > 1 else ''}"
        return f"{hours}h {remaining}m"

class DocumentRequirement(BaseModel):
    """Document needed for an action"""
    document_type: str
    description: str
    required_by: Optional[date] = None
    where_to_obtain: Optional[str] = None
    alternative_options: list[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    """Specific recommendation for patient action"""
    recommendation_id: UUID = Field(default_factory=uuid4)
    category: ActionCategory
    priority: ActionPriority
    difficulty: DifficultyLevel
    success_likelihood: SuccessLikelihood
    
    title: str
    description: str
    rationale: str
    
    # Financial impact
    savings_estimate: EnhancedSavingsEstimate
    time_estimate: TimeEstimate
    
    # Requirements
    required_documents: list[DocumentRequirement] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    
    # Execution details
    steps: list[str]
    contacts: list[str] = Field(default_factory=list)
    templates: list[str] = Field(default_factory=list)
    
    # Context
    applicable_bills: list[UUID] = Field(default_factory=list)
    target_providers: list[str] = Field(default_factory=list)
    relevant_programs: list[UUID] = Field(default_factory=list)
    
    # Warnings and considerations
    warnings: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    success_factors: list[str] = Field(default_factory=list)

class RankingFactors(BaseModel):
    """Factors used to rank recommendations"""
    financial_impact_score: float = Field(ge=0, le=1)
    urgency_score: float = Field(ge=0, le=1)
    success_probability_score: float = Field(ge=0, le=1)
    effort_score: float = Field(ge=0, le=1)  # Lower is better
    risk_reduction_score: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)

class RankedRecommendation(BaseModel):
    """Recommendation with ranking information"""
    recommendation: Recommendation
    rank: int
    ranking_factors: RankingFactors
    rationale: str

class RecommendationContext(BaseModel):
    """Context for generating recommendations"""
    patient_profile: PatientFinancialProfile
    bills: list[MedicalBill] = Field(default_factory=list)
    insurance_plans: list[InsurancePlan] = Field(default_factory=list)
    risk_assessment: Optional[EnhancedRiskAssessment] = None
    existing_recommendations: list[Recommendation] = Field(default_factory=list)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    time_constraints: Optional[TimeEstimate] = None
    financial_constraints: Optional[EnhancedSavingsEstimate] = None

class ActionPlan(BaseModel):
    """Organized action plan from ranked recommendations"""
    plan_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    patient_id: str
    
    # Recommendations
    ranked_recommendations: list[RankedRecommendation]
    total_recommendations: int
    critical_recommendations: int
    
    # Timeline
    estimated_completion_time: TimeEstimate
    key_deadlines: list[tuple[date, str]]
    
    # Expected outcomes
    total_potential_savings: EnhancedSavingsEstimate
    risk_reduction_projection: str
    
    # Organization
    phases: dict[str, list[RankedRecommendation]] = Field(default_factory=dict)
    dependencies: dict[str, list[str]] = Field(default_factory=dict)

class EngineOutput(BaseModel):
    """Output from analysis engine"""
    context: RecommendationContext
    risk_assessment: Optional[EnhancedRiskAssessment]
    recommendations: list[Recommendation]
    ranked_recommendations: list[RankedRecommendation]
    action_plan: ActionPlan
    processing_time_ms: int
    confidence_score: float
    warnings: list[str] = Field(default_factory=list)