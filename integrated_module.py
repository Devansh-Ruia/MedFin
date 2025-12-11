"""
MedFin Smart Recommendations + Risk Scoring Engine
Complete Production Module

This module provides:
1. Multi-dimensional risk scoring (0-100)
2. Personalized recommendation generation
3. Intelligent multi-factor ranking
4. Integration with existing MedFin system

Usage:
    from smart_recommendation_engine import SmartRecommendationEngine, RecommendationContext
    
    engine = SmartRecommendationEngine()
    context = RecommendationContext(
        user_id="USER-123",
        income_analysis=income_result,
        debt_analysis=debt_result,
        insurance_analysis=insurance_result,
        bill_analysis=bill_result,
        bills=parsed_bills,
        fpl_percentage=245.5
    )
    result = engine.analyze(context)
    
    print(f"Risk Score: {result.risk_assessment.overall_score}")
    for rec in result.recommendations[:5]:
        print(f"[{rec.final_rank}] {rec.recommendation.title}")

Author: MedFin Engineering Team
Version: 1.0.0
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, Field, computed_field
from uuid import UUID, uuid4
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMERATIONS
# ============================================================================

class RiskCategory(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"

class RiskDimension(str, Enum):
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
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "info"

class DifficultyLevel(str, Enum):
    TRIVIAL = "trivial"
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    COMPLEX = "complex"

class SuccessLikelihood(str, Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNCERTAIN = "uncertain"

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    CAUTION = "caution"
    INFO = "info"


# ============================================================================
# DATA MODELS
# ============================================================================

class RiskFactor(BaseModel):
    """Individual factor contributing to risk score"""
    factor_id: str
    dimension: RiskDimension
    name: str
    description: str
    raw_value: Any
    normalized_score: int = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)
    is_critical: bool = False
    
    @computed_field
    @property
    def weighted_contribution(self) -> float:
        return self.normalized_score * self.weight


class RiskDimensionScore(BaseModel):
    """Score for a single risk dimension"""
    dimension: RiskDimension
    score: int = Field(ge=0, le=100)
    category: RiskCategory
    factors: list[RiskFactor] = Field(default_factory=list)
    primary_driver: Optional[str] = None
    
    @classmethod
    def score_to_category(cls, score: int) -> RiskCategory:
        if score >= 80: return RiskCategory.CRITICAL
        elif score >= 60: return RiskCategory.HIGH
        elif score >= 40: return RiskCategory.MODERATE
        elif score >= 20: return RiskCategory.LOW
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


class RiskAssessment(BaseModel):
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


class SavingsEstimate(BaseModel):
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
    
    @computed_field
    @property
    def formatted_time(self) -> str:
        mins = self.expected_minutes
        if mins < 60: return f"{mins} minutes"
        hours = mins // 60
        remaining = mins % 60
        if remaining == 0: return f"{hours} hour{'s' if hours > 1 else ''}"
        return f"{hours}h {remaining}m"


class ActionStep(BaseModel):
    """Detailed step within a recommendation"""
    step_number: int
    instruction: str
    detail: Optional[str] = None
    tips: list[str] = Field(default_factory=list)


class DocumentRequirement(BaseModel):
    """Document needed to complete action"""
    document_type: str
    description: str
    is_required: bool = True
    how_to_obtain: Optional[str] = None


class Recommendation(BaseModel):
    """Complete recommendation"""
    recommendation_id: UUID = Field(default_factory=uuid4)
    category: ActionCategory
    priority: ActionPriority
    title: str
    short_description: str
    detailed_description: str
    reasoning: str
    savings_estimate: SavingsEstimate
    risk_reduction_score: int = Field(ge=0, le=100, default=0)
    time_estimate: TimeEstimate
    difficulty: DifficultyLevel
    success_probability: float = Field(ge=0, le=1)
    success_likelihood: SuccessLikelihood
    action_steps: list[ActionStep] = Field(default_factory=list)
    required_documents: list[DocumentRequirement] = Field(default_factory=list)
    deadline: Optional[date] = None
    optimal_timing: Optional[str] = None
    target_entity: Optional[str] = None
    target_bill_id: Optional[UUID] = None
    target_amount: Optional[Decimal] = None
    prerequisites: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    script_template: Optional[str] = None
    priority_score: float = 0.0
    rank: int = 0

    @computed_field
    @property
    def urgency_label(self) -> str:
        if self.deadline:
            days = (self.deadline - date.today()).days
            if days < 0: return "OVERDUE"
            elif days == 0: return "DUE TODAY"
            elif days <= 3: return f"DUE IN {days} DAYS"
            elif days <= 7: return "THIS WEEK"
            elif days <= 14: return "NEXT 2 WEEKS"
            elif days <= 30: return "THIS MONTH"
        return "FLEXIBLE"


class RankingFactors(BaseModel):
    """Factors used for priority calculation"""
    urgency_score: float = Field(ge=0, le=100)
    savings_impact_score: float = Field(ge=0, le=100)
    success_score: float = Field(ge=0, le=100)
    risk_reduction_score: float = Field(ge=0, le=100)
    ease_score: float = Field(ge=0, le=100)
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
    rationale: str


class RecommendationContext(BaseModel):
    """Input context for generating recommendations"""
    context_id: UUID = Field(default_factory=uuid4)
    user_id: str
    income_analysis: Optional[Any] = None
    debt_analysis: Optional[Any] = None
    insurance_analysis: Optional[Any] = None
    bill_analysis: Optional[Any] = None
    income_data: Optional[Any] = None
    debt_data: Optional[Any] = None
    insurance_data: Optional[Any] = None
    bills: list[Any] = Field(default_factory=list)
    fpl_percentage: Optional[float] = None
    state: Optional[str] = None
    upcoming_procedures: list[dict] = Field(default_factory=list)
    has_hsa: bool = False
    hsa_balance: Decimal = Decimal("0")
    has_fsa: bool = False
    fsa_balance: Decimal = Decimal("0")


class ActionPlan(BaseModel):
    """Organized action plan by timeframe"""
    immediate_actions: list[Recommendation] = Field(default_factory=list)
    this_week_actions: list[Recommendation] = Field(default_factory=list)
    this_month_actions: list[Recommendation] = Field(default_factory=list)
    ongoing_actions: list[Recommendation] = Field(default_factory=list)


class EngineOutput(BaseModel):
    """Complete engine output"""
    output_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    risk_assessment: RiskAssessment
    recommendations: list[RankedRecommendation] = Field(default_factory=list)
    total_recommendations: int = 0
    action_plan: ActionPlan
    total_potential_savings: SavingsEstimate
    total_risk_reduction_possible: int = 0
    critical_actions_count: int = 0
    executive_summary: str
    key_takeaways: list[str] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    data_completeness_score: float = Field(ge=0, le=1)
    limitations: list[str] = Field(default_factory=list)
    processing_time_ms: int = 0
    engine_version: str = "1.0.0"


# ============================================================================
# RISK SCORING ENGINE
# ============================================================================

class RiskScoringEngine:
    """Multi-dimensional risk scoring engine"""
    
    DIMENSION_WEIGHTS = {
        RiskDimension.INCOME_STABILITY: 0.12,
        RiskDimension.DEBT_BURDEN: 0.12,
        RiskDimension.MEDICAL_DEBT_RATIO: 0.12,
        RiskDimension.UPCOMING_COSTS: 0.10,
        RiskDimension.INSURANCE_GAPS: 0.10,
        RiskDimension.BILL_ERRORS: 0.08,
        RiskDimension.PAYMENT_HISTORY: 0.10,
        RiskDimension.COLLECTIONS_EXPOSURE: 0.12,
        RiskDimension.COVERAGE_ADEQUACY: 0.08,
        RiskDimension.AFFORDABILITY: 0.06,
    }
    
    def calculate_risk(self, context: RecommendationContext) -> RiskAssessment:
        """Calculate comprehensive risk assessment"""
        dimension_scores = {}
        all_factors = []
        critical_factors = []
        
        # Score each dimension
        for dimension in RiskDimension:
            dim_score, factors = self._score_dimension(dimension, context)
            dimension_scores[dimension] = dim_score
            all_factors.extend(factors)
            critical_factors.extend([f for f in factors if f.is_critical])
        
        # Calculate weighted overall score
        overall_score = sum(
            dim_score.score * self.DIMENSION_WEIGHTS.get(dim, 0.1)
            for dim, dim_score in dimension_scores.items()
        )
        
        # Apply critical factor boost
        if critical_factors:
            overall_score = min(100, overall_score + len(critical_factors) * 10)
        
        overall_score = int(round(overall_score))
        category = RiskDimensionScore.score_to_category(overall_score)
        
        # Generate alerts
        alerts = self._generate_alerts(dimension_scores, critical_factors, context)
        
        # Sort factors by contribution
        all_factors.sort(key=lambda f: f.weighted_contribution, reverse=True)
        
        return RiskAssessment(
            overall_score=overall_score,
            category=category,
            category_description=self._get_category_description(category),
            dimension_scores=dimension_scores,
            top_risk_factors=all_factors[:5],
            critical_factors=critical_factors,
            alerts=alerts,
            critical_alert_count=sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
            data_completeness=self._assess_completeness(context),
            confidence_score=self._assess_completeness(context) * 0.9,
            summary=self._generate_summary(overall_score, category, all_factors[:3], critical_factors),
            key_insights=[f.description for f in all_factors[:4]]
        )
    
    def _score_dimension(self, dimension: RiskDimension, ctx: RecommendationContext) -> tuple:
        """Score a single dimension"""
        scorers = {
            RiskDimension.INCOME_STABILITY: self._score_income,
            RiskDimension.DEBT_BURDEN: self._score_debt,
            RiskDimension.MEDICAL_DEBT_RATIO: self._score_medical_debt,
            RiskDimension.COLLECTIONS_EXPOSURE: self._score_collections,
            RiskDimension.BILL_ERRORS: self._score_bill_errors,
            RiskDimension.INSURANCE_GAPS: self._score_insurance_gaps,
            RiskDimension.AFFORDABILITY: self._score_affordability,
        }
        
        scorer = scorers.get(dimension)
        if scorer:
            return scorer(ctx)
        
        # Default moderate score for unimplemented dimensions
        return RiskDimensionScore(
            dimension=dimension,
            score=40,
            category=RiskCategory.MODERATE,
            factors=[],
            primary_driver="Assessment pending"
        ), []
    
    def _score_income(self, ctx: RecommendationContext) -> tuple:
        """Score income stability risk"""
        factors = []
        score = 0
        
        fpl = ctx.fpl_percentage or 500
        
        if fpl < 100:
            score = 90
            factors.append(RiskFactor(
                factor_id="INC_FPL_CRITICAL",
                dimension=RiskDimension.INCOME_STABILITY,
                name="Critical Poverty Level",
                description=f"Income at {fpl:.0f}% of federal poverty level",
                raw_value=fpl,
                normalized_score=90,
                weight=1.0,
                is_critical=True
            ))
        elif fpl < 200:
            score = 70
            factors.append(RiskFactor(
                factor_id="INC_FPL_HIGH",
                dimension=RiskDimension.INCOME_STABILITY,
                name="Low Income",
                description=f"Income at {fpl:.0f}% FPL",
                raw_value=fpl,
                normalized_score=70,
                weight=0.8
            ))
        elif fpl < 400:
            score = 40
        else:
            score = max(0, 100 - (fpl / 10))
        
        return RiskDimensionScore(
            dimension=RiskDimension.INCOME_STABILITY,
            score=int(score),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Income relative to poverty level"
        ), factors
    
    def _score_debt(self, ctx: RecommendationContext) -> tuple:
        """Score debt burden risk"""
        factors = []
        debt = ctx.debt_analysis or ctx.debt_data
        
        if not debt:
            return RiskDimensionScore(
                dimension=RiskDimension.DEBT_BURDEN,
                score=40,
                category=RiskCategory.MODERATE,
                factors=[],
                primary_driver="Insufficient data"
            ), []
        
        dti = getattr(getattr(debt, 'dti_analysis', None), 'gross_dti_ratio', 0.3)
        
        if dti >= 0.50:
            score = 95
            factors.append(RiskFactor(
                factor_id="DEBT_DTI_CRITICAL",
                dimension=RiskDimension.DEBT_BURDEN,
                name="Critical DTI",
                description=f"Debt-to-income ratio of {dti:.1%}",
                raw_value=dti,
                normalized_score=95,
                weight=1.0,
                is_critical=True
            ))
        elif dti >= 0.43:
            score = 75
        elif dti >= 0.36:
            score = 55
        else:
            score = dti * 150
        
        return RiskDimensionScore(
            dimension=RiskDimension.DEBT_BURDEN,
            score=int(score),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Debt-to-income ratio"
        ), factors
    
    def _score_medical_debt(self, ctx: RecommendationContext) -> tuple:
        """Score medical debt ratio risk"""
        factors = []
        debt = ctx.debt_analysis or ctx.debt_data
        
        medical = getattr(debt, 'total_medical_debt', Decimal("0")) if debt else Decimal("0")
        pending = sum(getattr(b, 'patient_balance', Decimal("0")) for b in ctx.bills)
        total_medical = medical + pending
        
        income = ctx.income_analysis or ctx.income_data
        annual = getattr(income, 'total_annual_gross', Decimal("50000")) if income else Decimal("50000")
        
        if annual > 0:
            ratio = float(total_medical / annual)
            if ratio > 0.5:
                score = 90
                factors.append(RiskFactor(
                    factor_id="MED_RATIO_CRITICAL",
                    dimension=RiskDimension.MEDICAL_DEBT_RATIO,
                    name="Catastrophic Medical Debt",
                    description=f"Medical debt exceeds 50% of annual income",
                    raw_value=ratio,
                    normalized_score=90,
                    weight=1.0,
                    is_critical=True
                ))
            elif ratio > 0.25:
                score = 65
            elif ratio > 0.10:
                score = 45
            else:
                score = ratio * 400
        else:
            score = 50
        
        return RiskDimensionScore(
            dimension=RiskDimension.MEDICAL_DEBT_RATIO,
            score=int(score),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Medical debt relative to income"
        ), factors
    
    def _score_collections(self, ctx: RecommendationContext) -> tuple:
        """Score collections exposure risk"""
        factors = []
        debt = ctx.debt_analysis or ctx.debt_data
        
        in_collections = getattr(debt, 'medical_debt_in_collections', Decimal("0")) if debt else Decimal("0")
        
        # Check past due bills
        past_due_amount = Decimal("0")
        for bill in ctx.bills:
            days = getattr(bill, 'days_until_due', None)
            if days is not None and days < 0:
                past_due_amount += getattr(bill, 'patient_balance', Decimal("0"))
        
        total_risk = in_collections + past_due_amount
        
        if in_collections >= Decimal("5000"):
            score = 95
            factors.append(RiskFactor(
                factor_id="COLL_CRITICAL",
                dimension=RiskDimension.COLLECTIONS_EXPOSURE,
                name="Significant Collections",
                description=f"${in_collections:,.0f} in collections",
                raw_value=float(in_collections),
                normalized_score=95,
                weight=1.0,
                is_critical=True
            ))
        elif in_collections > 0:
            score = 70
            factors.append(RiskFactor(
                factor_id="COLL_ACTIVE",
                dimension=RiskDimension.COLLECTIONS_EXPOSURE,
                name="Active Collections",
                description=f"${in_collections:,.0f} in collections",
                raw_value=float(in_collections),
                normalized_score=70,
                weight=0.8
            ))
        elif past_due_amount > 0:
            score = 55
            factors.append(RiskFactor(
                factor_id="COLL_RISK",
                dimension=RiskDimension.COLLECTIONS_EXPOSURE,
                name="Collections Risk",
                description=f"${past_due_amount:,.0f} past due",
                raw_value=float(past_due_amount),
                normalized_score=55,
                weight=0.7
            ))
        else:
            score = 10
        
        return RiskDimensionScore(
            dimension=RiskDimension.COLLECTIONS_EXPOSURE,
            score=int(score),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Collections and past-due amounts"
        ), factors
    
    def _score_bill_errors(self, ctx: RecommendationContext) -> tuple:
        """Score billing error risk"""
        factors = []
        ba = ctx.bill_analysis
        
        if not ba:
            return RiskDimensionScore(
                dimension=RiskDimension.BILL_ERRORS,
                score=30,
                category=RiskCategory.LOW,
                factors=[],
                primary_driver="No bill analysis available"
            ), []
        
        total_errors = getattr(ba, 'total_errors_found', 0)
        potential_savings = getattr(ba, 'total_potential_savings', Decimal("0"))
        
        if total_errors > 5:
            score = 75
            factors.append(RiskFactor(
                factor_id="BILL_MANY_ERRORS",
                dimension=RiskDimension.BILL_ERRORS,
                name="Multiple Billing Errors",
                description=f"{total_errors} errors worth ${potential_savings:,.0f}",
                raw_value=total_errors,
                normalized_score=75,
                weight=0.8
            ))
        elif total_errors > 0:
            score = 40 + (total_errors * 7)
        else:
            score = 15
        
        return RiskDimensionScore(
            dimension=RiskDimension.BILL_ERRORS,
            score=int(min(100, score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Billing accuracy"
        ), factors
    
    def _score_insurance_gaps(self, ctx: RecommendationContext) -> tuple:
        """Score insurance gap risk"""
        factors = []
        ins = ctx.insurance_analysis or ctx.insurance_data
        
        if not ins:
            factors.append(RiskFactor(
                factor_id="INS_NONE",
                dimension=RiskDimension.INSURANCE_GAPS,
                name="No Insurance",
                description="No health insurance coverage",
                raw_value=None,
                normalized_score=85,
                weight=1.0,
                is_critical=True
            ))
            return RiskDimensionScore(
                dimension=RiskDimension.INSURANCE_GAPS,
                score=85,
                category=RiskCategory.CRITICAL,
                factors=factors,
                primary_driver="No insurance"
            ), factors
        
        gaps = getattr(ins, 'coverage_gaps', [])
        adequacy = getattr(ins, 'plan_adequacy_score', 0.7)
        
        score = (1 - adequacy) * 70
        if len(gaps) > 0:
            score += len(gaps) * 10
        
        return RiskDimensionScore(
            dimension=RiskDimension.INSURANCE_GAPS,
            score=int(min(100, score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Coverage adequacy"
        ), factors
    
    def _score_affordability(self, ctx: RecommendationContext) -> tuple:
        """Score affordability risk"""
        factors = []
        income = ctx.income_analysis or ctx.income_data
        
        total_owed = sum(getattr(b, 'patient_balance', Decimal("0")) for b in ctx.bills)
        
        if income:
            budget = getattr(income, 'budget_projection', None)
            capacity = getattr(budget, 'medical_payment_capacity', Decimal("500")) if budget else Decimal("500")
            
            if capacity > 0:
                months = int(total_owed / capacity) if total_owed > 0 else 0
                if months > 36:
                    score = 90
                    factors.append(RiskFactor(
                        factor_id="AFFORD_CRITICAL",
                        dimension=RiskDimension.AFFORDABILITY,
                        name="Unaffordable Debt",
                        description=f"Would take {months}+ months to pay",
                        raw_value=months,
                        normalized_score=90,
                        weight=1.0,
                        is_critical=True
                    ))
                elif months > 24:
                    score = 70
                elif months > 12:
                    score = 50
                else:
                    score = months * 4
            else:
                score = 85
        else:
            score = 50
        
        return RiskDimensionScore(
            dimension=RiskDimension.AFFORDABILITY,
            score=int(score),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Payment capacity"
        ), factors
    
    def _generate_alerts(self, dim_scores, critical_factors, ctx) -> list[Alert]:
        """Generate alerts from risk assessment"""
        alerts = []
        
        for f in critical_factors:
            alerts.append(Alert(
                severity=AlertSeverity.CRITICAL,
                title=f.name,
                message=f.description,
                related_dimension=f.dimension,
                action_required=True
            ))
        
        for bill in ctx.bills:
            days = getattr(bill, 'days_until_due', None)
            if days is not None and days < 0:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    title=f"Past Due: {getattr(bill, 'provider_name', 'Unknown')}",
                    message=f"Bill is {abs(days)} days past due",
                    action_required=True
                ))
        
        return alerts
    
    def _assess_completeness(self, ctx: RecommendationContext) -> float:
        """Assess data completeness"""
        scores = []
        scores.append(0.9 if (ctx.income_analysis or ctx.income_data) else 0.3)
        scores.append(0.9 if (ctx.debt_analysis or ctx.debt_data) else 0.3)
        scores.append(0.9 if (ctx.insurance_analysis or ctx.insurance_data) else 0.5)
        scores.append(0.9 if ctx.bills else 0.5)
        return sum(scores) / len(scores)
    
    def _get_category_description(self, cat: RiskCategory) -> str:
        return {
            RiskCategory.CRITICAL: "Immediate intervention required",
            RiskCategory.HIGH: "Urgent attention needed",
            RiskCategory.MODERATE: "Active management required",
            RiskCategory.LOW: "Monitor and maintain",
            RiskCategory.MINIMAL: "Healthy financial state"
        }.get(cat, "Unknown")
    
    def _generate_summary(self, score, cat, top_factors, critical) -> str:
        summary = f"Your healthcare financial risk is {cat.value.upper()} (score: {score}/100). "
        if top_factors:
            summary += f"Key concerns: {', '.join(f.name.lower() for f in top_factors[:2])}. "
        if critical:
            summary += f"Critical issues: {len(critical)}."
        return summary


# ============================================================================
# RECOMMENDATION GENERATOR
# ============================================================================

class RecommendationGenerator:
    """Generates personalized recommendations"""
    
    def generate_recommendations(self, ctx: RecommendationContext, 
                                  risk: RiskAssessment) -> list[Recommendation]:
        """Generate all applicable recommendations"""
        recommendations = []
        
        recommendations.extend(self._billing_recommendations(ctx))
        recommendations.extend(self._insurance_recommendations(ctx))
        recommendations.extend(self._assistance_recommendations(ctx))
        recommendations.extend(self._negotiation_recommendations(ctx))
        recommendations.extend(self._payment_recommendations(ctx))
        
        return recommendations
    
    def _billing_recommendations(self, ctx: RecommendationContext) -> list[Recommendation]:
        """Generate billing recommendations"""
        recs = []
        ba = ctx.bill_analysis
        
        if not ba:
            return recs
        
        for single_ba in getattr(ba, 'bill_analyses', []):
            provider = getattr(single_ba, 'provider_name', 'Provider')
            balance = getattr(single_ba, 'patient_balance', Decimal("0"))
            
            # Duplicates
            duplicates = getattr(single_ba, 'duplicates', [])
            if duplicates:
                amt = sum(getattr(d, 'charge_amount', Decimal("0")) for d in duplicates)
                recs.append(Recommendation(
                    category=ActionCategory.BILL_DISPUTE,
                    priority=ActionPriority.CRITICAL,
                    title="Dispute Duplicate Charges",
                    short_description="Challenge duplicate charges on your bill",
                    detailed_description=f"We found duplicate charges totaling ${amt:,.0f}",
                    reasoning="Duplicate charges are billing errors that should be removed",
                    savings_estimate=SavingsEstimate(
                        minimum=amt * Decimal("0.8"),
                        expected=amt * Decimal("0.95"),
                        maximum=amt,
                        confidence=0.90
                    ),
                    time_estimate=TimeEstimate(minimum_minutes=20, expected_minutes=30, maximum_minutes=45),
                    difficulty=DifficultyLevel.EASY,
                    success_probability=0.90,
                    success_likelihood=SuccessLikelihood.VERY_HIGH,
                    target_entity=provider,
                    target_amount=balance,
                    action_steps=[
                        ActionStep(step_number=1, instruction="Call billing department"),
                        ActionStep(step_number=2, instruction="Reference specific duplicate line items"),
                        ActionStep(step_number=3, instruction="Request written confirmation of removal")
                    ]
                ))
            
            # Unbundling
            bundling = getattr(single_ba, 'bundling_issues', [])
            if bundling:
                amt = sum(getattr(b, 'overbilled_amount', Decimal("0")) for b in bundling)
                recs.append(Recommendation(
                    category=ActionCategory.BILL_DISPUTE,
                    priority=ActionPriority.HIGH,
                    title="Dispute Unbundled Charges",
                    short_description="Challenge improperly separated charges",
                    detailed_description="Services that should be billed together were separated",
                    reasoning="Unbundling violates medical coding rules",
                    savings_estimate=SavingsEstimate(
                        minimum=amt * Decimal("0.6"),
                        expected=amt * Decimal("0.85"),
                        maximum=amt,
                        confidence=0.80
                    ),
                    time_estimate=TimeEstimate(minimum_minutes=30, expected_minutes=45, maximum_minutes=70),
                    difficulty=DifficultyLevel.MODERATE,
                    success_probability=0.80,
                    success_likelihood=SuccessLikelihood.HIGH,
                    target_entity=provider,
                    target_amount=balance
                ))
        
        return recs
    
    def _insurance_recommendations(self, ctx: RecommendationContext) -> list[Recommendation]:
        """Generate insurance recommendations"""
        recs = []
        
        for bill in ctx.bills:
            ins_paid = getattr(bill, 'insurance_paid', Decimal("0"))
            total = getattr(bill, 'total_billed', Decimal("0"))
            balance = getattr(bill, 'patient_balance', Decimal("0"))
            
            if ins_paid == 0 and total > Decimal("200"):
                recs.append(Recommendation(
                    category=ActionCategory.VERIFICATION,
                    priority=ActionPriority.HIGH,
                    title="Verify Insurance Claim Was Filed",
                    short_description="Ensure provider submitted claim to insurance",
                    detailed_description="No insurance payment recorded - claim may not have been submitted",
                    reasoning="You shouldn't pay until insurance processes the claim",
                    savings_estimate=SavingsEstimate(
                        minimum=Decimal("0"),
                        expected=balance * Decimal("0.6"),
                        maximum=balance * Decimal("0.9"),
                        confidence=0.50
                    ),
                    time_estimate=TimeEstimate(expected_minutes=20),
                    difficulty=DifficultyLevel.EASY,
                    success_probability=0.85,
                    success_likelihood=SuccessLikelihood.VERY_HIGH,
                    target_entity=getattr(bill, 'provider_name', 'Provider'),
                    target_amount=balance
                ))
        
        return recs
    
    def _assistance_recommendations(self, ctx: RecommendationContext) -> list[Recommendation]:
        """Generate assistance program recommendations"""
        recs = []
        fpl = ctx.fpl_percentage or 500
        total = sum(getattr(b, 'patient_balance', Decimal("0")) for b in ctx.bills)
        
        if fpl < 400 and total > Decimal("500"):
            discount = Decimal("1.0") if fpl < 100 else Decimal("0.75") if fpl < 200 else Decimal("0.50") if fpl < 300 else Decimal("0.35")
            conf = 0.85 if fpl < 200 else 0.70 if fpl < 300 else 0.50
            
            recs.append(Recommendation(
                category=ActionCategory.ASSISTANCE_APPLICATION,
                priority=ActionPriority.HIGH if fpl < 200 else ActionPriority.MEDIUM,
                title="Apply for Hospital Charity Care",
                short_description="Get bills reduced based on income",
                detailed_description=f"At {fpl:.0f}% FPL, you may qualify for significant bill reduction",
                reasoning="Hospitals are required to offer financial assistance",
                savings_estimate=SavingsEstimate(
                    minimum=total * discount * Decimal("0.5"),
                    expected=total * discount,
                    maximum=total,
                    confidence=conf
                ),
                time_estimate=TimeEstimate(expected_minutes=60),
                difficulty=DifficultyLevel.MODERATE,
                success_probability=conf,
                success_likelihood=SuccessLikelihood.HIGH if conf > 0.6 else SuccessLikelihood.MODERATE,
                tips=["Apply BEFORE making any payments", "Can apply for past bills too"]
            ))
        
        return recs
    
    def _negotiation_recommendations(self, ctx: RecommendationContext) -> list[Recommendation]:
        """Generate negotiation recommendations"""
        recs = []
        
        for bill in ctx.bills:
            balance = getattr(bill, 'patient_balance', Decimal("0"))
            if balance < Decimal("300"):
                continue
            
            recs.append(Recommendation(
                category=ActionCategory.NEGOTIATION,
                priority=ActionPriority.MEDIUM,
                title="Negotiate Prompt Pay Discount",
                short_description="Get 15-25% off for paying quickly",
                detailed_description="Most providers offer discounts for immediate payment",
                reasoning="Providers prefer guaranteed payment",
                savings_estimate=SavingsEstimate(
                    minimum=balance * Decimal("0.10"),
                    expected=balance * Decimal("0.20"),
                    maximum=balance * Decimal("0.30"),
                    confidence=0.70
                ),
                time_estimate=TimeEstimate(expected_minutes=20),
                difficulty=DifficultyLevel.EASY,
                success_probability=0.70,
                success_likelihood=SuccessLikelihood.HIGH,
                target_entity=getattr(bill, 'provider_name', 'Provider'),
                target_amount=balance,
                script_template="I'd like to pay this in full today. What prompt-pay discount can you offer?"
            ))
        
        return recs
    
    def _payment_recommendations(self, ctx: RecommendationContext) -> list[Recommendation]:
        """Generate payment recommendations"""
        recs = []
        total = sum(getattr(b, 'patient_balance', Decimal("0")) for b in ctx.bills)
        
        if ctx.has_hsa and ctx.hsa_balance > 0:
            usable = min(ctx.hsa_balance, total)
            tax_savings = usable * Decimal("0.25")
            recs.append(Recommendation(
                category=ActionCategory.PAYMENT_OPTIMIZATION,
                priority=ActionPriority.MEDIUM,
                title="Use HSA Funds",
                short_description="Pay with pre-tax dollars",
                detailed_description=f"Use ${usable:,.0f} from HSA, save ~${tax_savings:,.0f} in taxes",
                reasoning="HSA payments provide tax savings",
                savings_estimate=SavingsEstimate(
                    minimum=tax_savings * Decimal("0.8"),
                    expected=tax_savings,
                    maximum=tax_savings * Decimal("1.2"),
                    confidence=0.99
                ),
                time_estimate=TimeEstimate(expected_minutes=10),
                difficulty=DifficultyLevel.TRIVIAL,
                success_probability=0.99,
                success_likelihood=SuccessLikelihood.VERY_HIGH
            ))
        
        recs.append(Recommendation(
            category=ActionCategory.PAYMENT_OPTIMIZATION,
            priority=ActionPriority.LOW,
            title="Set Up Interest-Free Payment Plan",
            short_description="Establish manageable monthly payments",
            detailed_description="Spread payments over time at 0% interest",
            reasoning="Protects your budget while paying down debt",
            savings_estimate=SavingsEstimate(confidence=0.95),
            time_estimate=TimeEstimate(expected_minutes=20),
            difficulty=DifficultyLevel.EASY,
            success_probability=0.95,
            success_likelihood=SuccessLikelihood.VERY_HIGH,
            warnings=["Complete ALL negotiations before setting up payment plan"]
        ))
        
        return recs


# ============================================================================
# RANKING ENGINE
# ============================================================================

class RankingEngine:
    """Multi-factor recommendation ranking"""
    
    EASE_SCORES = {
        DifficultyLevel.TRIVIAL: 100,
        DifficultyLevel.EASY: 80,
        DifficultyLevel.MODERATE: 60,
        DifficultyLevel.CHALLENGING: 40,
        DifficultyLevel.COMPLEX: 20,
    }
    
    def rank_recommendations(self, recs: list[Recommendation], 
                              risk: RiskAssessment) -> list[RankedRecommendation]:
        """Rank recommendations by priority score"""
        ranked = []
        
        for rec in recs:
            factors = self._calc_factors(rec, risk)
            ranked.append(RankedRecommendation(
                recommendation=rec,
                ranking_factors=factors,
                final_rank=0,
                rationale=self._rationale(rec, factors)
            ))
        
        ranked.sort(key=lambda x: x.ranking_factors.composite_score, reverse=True)
        
        for i, r in enumerate(ranked, 1):
            r.final_rank = i
            r.recommendation.rank = i
            r.recommendation.priority_score = r.ranking_factors.composite_score
        
        return ranked
    
    def _calc_factors(self, rec: Recommendation, risk: RiskAssessment) -> RankingFactors:
        """Calculate ranking factors"""
        # Urgency
        urgency = 25
        if rec.deadline:
            days = (rec.deadline - date.today()).days
            if days < 0: urgency = 100
            elif days <= 3: urgency = 85
            elif days <= 7: urgency = 70
            elif days <= 14: urgency = 55
            elif days <= 30: urgency = 40
        
        priority_adj = {ActionPriority.CRITICAL: 20, ActionPriority.HIGH: 10}.get(rec.priority, 0)
        urgency = min(100, urgency + priority_adj)
        
        # Savings
        exp = float(rec.savings_estimate.expected)
        if exp > 5000: savings = 100
        elif exp > 2000: savings = 80
        elif exp > 500: savings = 60
        elif exp > 100: savings = 40
        else: savings = 20
        
        savings *= (0.7 + rec.savings_estimate.confidence * 0.3)
        
        # Success
        success = rec.success_probability * 100
        
        # Risk reduction
        risk_red = 30 + {
            ActionCategory.ASSISTANCE_APPLICATION: 30,
            ActionCategory.BILL_DISPUTE: 20,
            ActionCategory.INSURANCE_APPEAL: 20,
        }.get(rec.category, 10)
        
        # Ease
        ease = self.EASE_SCORES.get(rec.difficulty, 50)
        
        return RankingFactors(
            urgency_score=urgency,
            savings_impact_score=savings,
            success_score=success,
            risk_reduction_score=min(100, risk_red),
            ease_score=ease
        )
    
    def _rationale(self, rec: Recommendation, factors: RankingFactors) -> str:
        """Generate ranking rationale"""
        parts = []
        if factors.urgency_score >= 80: parts.append("time-critical")
        if factors.savings_impact_score >= 70: parts.append(f"${rec.savings_estimate.expected:,.0f} potential savings")
        if factors.success_score >= 70: parts.append("high success probability")
        if factors.ease_score >= 70: parts.append("easy to complete")
        return f"Priority factors: {', '.join(parts)}" if parts else "Balanced priority"


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class SmartRecommendationEngine:
    """Main orchestrator for the Smart Recommendation Engine"""
    
    def __init__(self):
        self.risk_scorer = RiskScoringEngine()
        self.rec_generator = RecommendationGenerator()
        self.ranking_engine = RankingEngine()
    
    def analyze(self, context: RecommendationContext) -> EngineOutput:
        """Perform complete analysis"""
        start = time.time()
        
        # Risk Assessment
        risk = self.risk_scorer.calculate_risk(context)
        
        # Generate Recommendations
        recs = self.rec_generator.generate_recommendations(context, risk)
        
        # Rank Recommendations
        ranked = self.ranking_engine.rank_recommendations(recs, risk)
        
        # Organize Action Plan
        action_plan = self._organize_plan(ranked)
        
        # Calculate Totals
        total_savings = self._calc_total_savings(ranked)
        
        # Generate Summary
        summary = self._generate_summary(context, risk, ranked, total_savings)
        
        return EngineOutput(
            user_id=context.user_id,
            risk_assessment=risk,
            recommendations=ranked,
            total_recommendations=len(ranked),
            action_plan=action_plan,
            total_potential_savings=total_savings,
            total_risk_reduction_possible=min(80, len(ranked) * 5),
            critical_actions_count=sum(1 for r in ranked if r.recommendation.priority == ActionPriority.CRITICAL),
            executive_summary=summary,
            key_takeaways=self._takeaways(risk, ranked),
            alerts=risk.alerts,
            confidence_score=risk.confidence_score,
            data_completeness_score=risk.data_completeness,
            limitations=risk.data_quality_warnings,
            processing_time_ms=int((time.time() - start) * 1000)
        )
    
    def _organize_plan(self, ranked: list[RankedRecommendation]) -> ActionPlan:
        """Organize into action plan"""
        immediate, this_week, this_month, ongoing = [], [], [], []
        
        for r in ranked:
            rec = r.recommendation
            if rec.priority == ActionPriority.CRITICAL:
                immediate.append(rec)
            elif rec.priority == ActionPriority.HIGH:
                this_week.append(rec)
            elif rec.priority == ActionPriority.MEDIUM:
                this_month.append(rec)
            else:
                ongoing.append(rec)
        
        return ActionPlan(
            immediate_actions=immediate,
            this_week_actions=this_week,
            this_month_actions=this_month,
            ongoing_actions=ongoing
        )
    
    def _calc_total_savings(self, ranked: list[RankedRecommendation]) -> SavingsEstimate:
        """Calculate total potential savings"""
        return SavingsEstimate(
            minimum=sum(r.recommendation.savings_estimate.minimum for r in ranked),
            expected=sum(r.recommendation.savings_estimate.expected for r in ranked),
            maximum=sum(r.recommendation.savings_estimate.maximum for r in ranked),
            confidence=sum(r.recommendation.savings_estimate.confidence for r in ranked) / max(1, len(ranked)),
            calculation_method="aggregated"
        )
    
    def _generate_summary(self, ctx, risk, ranked, savings) -> str:
        """Generate executive summary"""
        parts = [
            f"Risk: {risk.category.value.upper()} ({risk.overall_score}/100).",
            f"Found {len(ranked)} actions.",
            f"Potential savings: ${savings.expected:,.0f}."
        ]
        critical = sum(1 for r in ranked if r.recommendation.priority == ActionPriority.CRITICAL)
        if critical:
            parts.append(f"{critical} critical action(s) need immediate attention.")
        return " ".join(parts)
    
    def _takeaways(self, risk: RiskAssessment, ranked: list[RankedRecommendation]) -> list[str]:
        """Generate key takeaways"""
        takeaways = []
        
        if risk.category in [RiskCategory.CRITICAL, RiskCategory.HIGH]:
            takeaways.append("Your situation requires immediate action")
        else:
            takeaways.append("Proactive steps can prevent future stress")
        
        if ranked:
            top = ranked[0].recommendation
            takeaways.append(f"Top priority: {top.title} (${top.savings_estimate.expected:,.0f})")
        
        easy = [r for r in ranked if r.recommendation.difficulty in [DifficultyLevel.TRIVIAL, DifficultyLevel.EASY]]
        if easy:
            total = sum(r.recommendation.savings_estimate.expected for r in easy)
            takeaways.append(f"{len(easy)} easy actions could save ${total:,.0f}")
        
        return takeaways[:5]


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    context = RecommendationContext(
        user_id="TEST-USER-001",
        fpl_percentage=245.5,
        state="CA",
        bills=[],  # Would include actual ParsedBill objects
        has_hsa=True,
        hsa_balance=Decimal("1200")
    )
    
    engine = SmartRecommendationEngine()
    result = engine.analyze(context)
    
    print(f"Risk Score: {result.risk_assessment.overall_score}")
    print(f"Risk Category: {result.risk_assessment.category.value}")
    print(f"Total Recommendations: {result.total_recommendations}")
    print(f"Potential Savings: ${result.total_potential_savings.expected:,.0f}")
    print(f"\nTop Recommendations:")
    for r in result.recommendations[:5]:
        print(f"  [{r.final_rank}] {r.recommendation.title} - ${r.recommendation.savings_estimate.expected:,.0f}")