"""
MedFin Smart Recommendations + Risk Scoring Engine
Complete Data Models and Schemas
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, Field, computed_field
from uuid import UUID, uuid4


# ============================================================================
# ENUMERATIONS
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
    """Priority levels for recommendations"""
    CRITICAL = "critical"      # Must act within 24-48 hours
    HIGH = "high"              # Act within 7 days
    MEDIUM = "medium"          # Act within 30 days
    LOW = "low"                # Act when convenient
    INFORMATIONAL = "info"     # For awareness only

class DifficultyLevel(str, Enum):
    """Effort required to complete action"""
    TRIVIAL = "trivial"        # < 15 minutes, no expertise needed
    EASY = "easy"              # 15-30 minutes, basic knowledge
    MODERATE = "moderate"      # 30-60 minutes, some research needed
    CHALLENGING = "challenging" # 1-2 hours, may need help
    COMPLEX = "complex"        # 2+ hours, professional assistance recommended

class SuccessLikelihood(str, Enum):
    """Probability of action success"""
    VERY_HIGH = "very_high"    # 80-100%
    HIGH = "high"              # 60-79%
    MODERATE = "moderate"      # 40-59%
    LOW = "low"                # 20-39%
    UNCERTAIN = "uncertain"    # <20% or unknown

class AlertSeverity(str, Enum):
    """Severity of alerts and warnings"""
    CRITICAL = "critical"      # Requires immediate attention
    WARNING = "warning"        # Requires attention soon
    CAUTION = "caution"        # Be aware
    INFO = "info"              # For information


# ============================================================================
# RISK SCORING MODELS
# ============================================================================

class RiskFactor(BaseModel):
    """Individual factor contributing to risk score"""
    factor_id: str
    dimension: RiskDimension
    name: str
    description: str
    raw_value: Any                          # The underlying data point
    normalized_score: int = Field(ge=0, le=100)  # Contribution to risk (0-100)
    weight: float = Field(ge=0, le=1)       # Weight in overall calculation
    evidence: list[str] = Field(default_factory=list)  # Supporting data points
    is_critical: bool = False               # If True, can override overall score
    
    @computed_field
    @property
    def weighted_contribution(self) -> float:
        """Weighted contribution to overall risk score"""
        return self.normalized_score * self.weight

class RiskDimensionScore(BaseModel):
    """Score for a single risk dimension"""
    dimension: RiskDimension
    score: int = Field(ge=0, le=100)
    category: RiskCategory
    factors: list[RiskFactor] = Field(default_factory=list)
    primary_driver: Optional[str] = None
    trend: Optional[str] = None  # improving, stable, worsening
    
    @classmethod
    def score_to_category(cls, score: int) -> RiskCategory:
        if score >= 80:
            return RiskCategory.CRITICAL
        elif score >= 60:
            return RiskCategory.HIGH
        elif score >= 40:
            return RiskCategory.MODERATE
        elif score >= 20:
            return RiskCategory.LOW
        return RiskCategory.MINIMAL

class Alert(BaseModel):
    """System alert or warning"""
    alert_id: UUID = Field(default_factory=uuid4)
    severity: AlertSeverity
    title: str
    message: str
    related_dimension: Optional[RiskDimension] = None
    action_required: bool = False
    deadline: Optional[date] = None
    dismiss_after_action: Optional[str] = None  # Action ID that dismisses this

class RiskAssessment(BaseModel):
    """Complete risk assessment output"""
    assessment_id: UUID = Field(default_factory=uuid4)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Overall Risk
    overall_score: int = Field(ge=0, le=100)
    category: RiskCategory
    category_description: str
    
    # Dimensional Breakdown
    dimension_scores: dict[RiskDimension, RiskDimensionScore] = Field(default_factory=dict)
    
    # Risk Drivers
    top_risk_factors: list[RiskFactor] = Field(default_factory=list)  # Top 5 drivers
    critical_factors: list[RiskFactor] = Field(default_factory=list)  # Any critical flags
    
    # Alerts
    alerts: list[Alert] = Field(default_factory=list)
    critical_alert_count: int = 0
    
    # Trend Analysis
    trend_direction: Optional[str] = None  # improving, stable, worsening
    projected_30_day_score: Optional[int] = None
    
    # Confidence
    data_completeness: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    data_quality_warnings: list[str] = Field(default_factory=list)
    
    # Executive Summary
    summary: str = ""
    key_insights: list[str] = Field(default_factory=list)


# ============================================================================
# RECOMMENDATION MODELS
# ============================================================================

class SavingsEstimate(BaseModel):
    """Estimated financial impact of an action"""
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
    
    @computed_field
    @property
    def formatted_time(self) -> str:
        mins = self.expected_minutes
        if mins < 60:
            return f"{mins} minutes"
        hours = mins // 60
        remaining = mins % 60
        if remaining == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        return f"{hours}h {remaining}m"

class ActionStep(BaseModel):
    """Detailed step within a recommendation"""
    step_number: int
    instruction: str
    detail: Optional[str] = None
    tips: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class ContactInfo(BaseModel):
    """Contact information for executing action"""
    entity_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    department: Optional[str] = None
    best_contact_times: Optional[str] = None
    reference_numbers: dict[str, str] = Field(default_factory=dict)

class DocumentRequirement(BaseModel):
    """Document needed to complete action"""
    document_type: str
    description: str
    is_required: bool = True
    how_to_obtain: Optional[str] = None
    typical_wait_time: Optional[str] = None

class Recommendation(BaseModel):
    """Complete recommendation with all details"""
    recommendation_id: UUID = Field(default_factory=uuid4)
    
    # Classification
    category: ActionCategory
    priority: ActionPriority
    
    # Core Information
    title: str
    short_description: str
    detailed_description: str
    reasoning: str  # Why this is recommended
    
    # Impact Assessment
    savings_estimate: SavingsEstimate
    risk_reduction_score: int = Field(ge=0, le=100, default=0)  # How much this reduces risk
    
    # Execution Details
    time_estimate: TimeEstimate
    difficulty: DifficultyLevel
    success_probability: float = Field(ge=0, le=1)
    success_likelihood: SuccessLikelihood
    
    # Steps & Requirements
    action_steps: list[ActionStep] = Field(default_factory=list)
    required_documents: list[DocumentRequirement] = Field(default_factory=list)
    contact_info: Optional[ContactInfo] = None
    
    # Timing
    deadline: Optional[date] = None
    optimal_timing: Optional[str] = None  # e.g., "Before month end", "Tuesday-Thursday 10am-2pm"
    time_sensitivity: str = "flexible"  # critical, time_sensitive, flexible
    
    # Context
    target_entity: Optional[str] = None  # Provider name, insurer, etc.
    target_bill_id: Optional[UUID] = None
    target_amount: Optional[Decimal] = None
    
    # Dependencies
    prerequisites: list[str] = Field(default_factory=list)  # Other rec IDs that must be done first
    blocks: list[str] = Field(default_factory=list)  # Rec IDs that can't be done until this is done
    
    # Additional Context
    warnings: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    common_obstacles: list[str] = Field(default_factory=list)
    
    # Script/Template
    script_template: Optional[str] = None  # What to say when calling
    letter_template_id: Optional[str] = None
    
    # Ranking (computed by ranking engine)
    priority_score: float = 0.0  # 0-100 composite score
    rank: int = 0

    @computed_field
    @property
    def urgency_label(self) -> str:
        if self.deadline:
            days = (self.deadline - date.today()).days
            if days < 0:
                return "OVERDUE"
            elif days == 0:
                return "DUE TODAY"
            elif days <= 3:
                return f"DUE IN {days} DAYS"
            elif days <= 7:
                return "THIS WEEK"
            elif days <= 14:
                return "NEXT 2 WEEKS"
            elif days <= 30:
                return "THIS MONTH"
        return "FLEXIBLE"


# ============================================================================
# RANKING MODELS
# ============================================================================

class RankingFactors(BaseModel):
    """Factors used to calculate recommendation priority"""
    urgency_score: float = Field(ge=0, le=100)      # Time sensitivity
    savings_impact_score: float = Field(ge=0, le=100)  # Financial benefit
    success_score: float = Field(ge=0, le=100)      # Likelihood of success
    risk_reduction_score: float = Field(ge=0, le=100)  # Risk mitigation value
    ease_score: float = Field(ge=0, le=100)         # Inverse of difficulty
    
    # Weights for composite calculation
    urgency_weight: float = 0.25
    savings_weight: float = 0.25
    success_weight: float = 0.20
    risk_weight: float = 0.15
    ease_weight: float = 0.15
    
    @computed_field
    @property
    def composite_score(self) -> float:
        return (
            self.urgency_score * self.urgency_weight +
            self.savings_impact_score * self.savings_weight +
            self.success_score * self.success_weight +
            self.risk_reduction_score * self.risk_weight +
            self.ease_score * self.ease_weight
        )

class RankedRecommendation(BaseModel):
    """Recommendation with ranking details"""
    recommendation: Recommendation
    ranking_factors: RankingFactors
    final_rank: int
    rationale: str  # Why this ranking


# ============================================================================
# CONTEXT MODELS (INPUT)
# ============================================================================

class RecommendationContext(BaseModel):
    """Complete context for generating recommendations"""
    context_id: UUID = Field(default_factory=uuid4)
    user_id: str
    
    # Existing Analysis Results (from current MedFin system)
    income_analysis: Optional[Any] = None  # IncomeAnalysisOutput
    debt_analysis: Optional[Any] = None    # DebtAnalysisOutput
    insurance_analysis: Optional[Any] = None  # InsuranceAnalysisOutput
    bill_analysis: Optional[Any] = None    # BillAnalysisOutput
    
    # Raw Data (if analysis not available)
    income_data: Optional[Any] = None      # IncomeData
    debt_data: Optional[Any] = None        # DebtData
    insurance_data: Optional[Any] = None   # InsurancePlan
    bills: list[Any] = Field(default_factory=list)  # ParsedBill[]
    
    # Additional Context
    fpl_percentage: Optional[float] = None
    state: Optional[str] = None
    upcoming_procedures: list[dict] = Field(default_factory=list)
    user_preferences: dict = Field(default_factory=dict)
    
    # Data Quality Indicators
    data_completeness: dict[str, float] = Field(default_factory=dict)


# ============================================================================
# OUTPUT MODELS
# ============================================================================

class ActionPlan(BaseModel):
    """Organized action plan by timeframe"""
    immediate_actions: list[Recommendation] = Field(default_factory=list)  # Next 48 hours
    this_week_actions: list[Recommendation] = Field(default_factory=list)  # This week
    this_month_actions: list[Recommendation] = Field(default_factory=list)  # This month
    ongoing_actions: list[Recommendation] = Field(default_factory=list)     # Long-term

class EngineOutput(BaseModel):
    """Complete output from the recommendation engine"""
    output_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    
    # Risk Assessment
    risk_assessment: RiskAssessment
    
    # Recommendations
    recommendations: list[RankedRecommendation] = Field(default_factory=list)
    total_recommendations: int = 0
    
    # Organized Action Plan
    action_plan: ActionPlan
    
    # Summary Metrics
    total_potential_savings: SavingsEstimate
    total_risk_reduction_possible: int = 0
    critical_actions_count: int = 0
    
    # Executive Summary
    executive_summary: str
    key_takeaways: list[str] = Field(default_factory=list)
    
    # Alerts
    alerts: list[Alert] = Field(default_factory=list)
    
    # Data Quality
    confidence_score: float = Field(ge=0, le=1)
    data_completeness_score: float = Field(ge=0, le=1)
    limitations: list[str] = Field(default_factory=list)
    
    # Processing Metadata
    processing_time_ms: int = 0
    engine_version: str = "1.0.0"