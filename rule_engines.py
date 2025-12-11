"""
MedFin Smart Recommendations + Risk Scoring Engine
Core Engine Implementation
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, Callable
from collections import defaultdict
import logging

# Assume models from above are imported

logger = logging.getLogger(__name__)


# ============================================================================
# RISK SCORING ENGINE
# ============================================================================

class RiskScoringEngine:
    """
    Comprehensive multi-dimensional risk scoring engine.
    
    Evaluates 10 risk dimensions and produces a composite risk score
    with detailed factor breakdown and alerts.
    """
    
    # Risk dimension weights (must sum to 1.0)
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
    
    # Thresholds for various metrics
    FPL_CRITICAL = 100      # Below 100% FPL
    FPL_HIGH = 200          # Below 200% FPL
    FPL_MODERATE = 400      # Below 400% FPL
    
    DTI_CRITICAL = 0.50     # 50%+ DTI
    DTI_HIGH = 0.43         # QM threshold
    DTI_MODERATE = 0.36     # Traditional lending threshold
    
    COLLECTIONS_CRITICAL = Decimal("5000")
    COLLECTIONS_HIGH = Decimal("1000")
    
    def __init__(self):
        self.dimension_scorers = {
            RiskDimension.INCOME_STABILITY: self._score_income_stability,
            RiskDimension.DEBT_BURDEN: self._score_debt_burden,
            RiskDimension.MEDICAL_DEBT_RATIO: self._score_medical_debt_ratio,
            RiskDimension.UPCOMING_COSTS: self._score_upcoming_costs,
            RiskDimension.INSURANCE_GAPS: self._score_insurance_gaps,
            RiskDimension.BILL_ERRORS: self._score_bill_errors,
            RiskDimension.PAYMENT_HISTORY: self._score_payment_history,
            RiskDimension.COLLECTIONS_EXPOSURE: self._score_collections_exposure,
            RiskDimension.COVERAGE_ADEQUACY: self._score_coverage_adequacy,
            RiskDimension.AFFORDABILITY: self._score_affordability,
        }
    
    def calculate_risk(self, context: 'RecommendationContext') -> RiskAssessment:
        """Calculate comprehensive risk assessment from context."""
        
        dimension_scores = {}
        all_factors = []
        critical_factors = []
        alerts = []
        data_quality_warnings = []
        
        # Score each dimension
        for dimension, scorer in self.dimension_scorers.items():
            try:
                dim_score, factors = scorer(context)
                dimension_scores[dimension] = dim_score
                all_factors.extend(factors)
                
                # Collect critical factors
                for f in factors:
                    if f.is_critical:
                        critical_factors.append(f)
                        
            except Exception as e:
                logger.warning(f"Failed to score dimension {dimension}: {e}")
                # Use default moderate score on failure
                dimension_scores[dimension] = RiskDimensionScore(
                    dimension=dimension,
                    score=50,
                    category=RiskCategory.MODERATE,
                    factors=[],
                    primary_driver="Unable to assess"
                )
                data_quality_warnings.append(f"Could not fully assess {dimension.value}")
        
        # Calculate weighted overall score
        overall_score = self._calculate_overall_score(dimension_scores)
        
        # Apply critical factor overrides
        if critical_factors:
            # Critical factors can push score up
            critical_boost = len(critical_factors) * 10
            overall_score = min(100, overall_score + critical_boost)
        
        # Determine category
        category = RiskDimensionScore.score_to_category(overall_score)
        
        # Generate alerts
        alerts = self._generate_alerts(dimension_scores, critical_factors, context)
        
        # Get top risk factors (sorted by weighted contribution)
        all_factors.sort(key=lambda f: f.weighted_contribution, reverse=True)
        top_factors = all_factors[:5]
        
        # Calculate data completeness
        completeness = self._assess_data_completeness(context)
        
        # Generate summary
        summary = self._generate_risk_summary(
            overall_score, category, top_factors, critical_factors
        )
        
        return RiskAssessment(
            overall_score=overall_score,
            category=category,
            category_description=self._get_category_description(category),
            dimension_scores=dimension_scores,
            top_risk_factors=top_factors,
            critical_factors=critical_factors,
            alerts=alerts,
            critical_alert_count=sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
            data_completeness=completeness,
            confidence_score=completeness * 0.9,  # Slightly lower than completeness
            data_quality_warnings=data_quality_warnings,
            summary=summary,
            key_insights=self._generate_insights(dimension_scores, top_factors)
        )
    
    def _calculate_overall_score(self, dimension_scores: dict) -> int:
        """Calculate weighted overall risk score."""
        total = 0.0
        for dim, score in dimension_scores.items():
            weight = self.DIMENSION_WEIGHTS.get(dim, 0.1)
            total += score.score * weight
        return int(round(total))
    
    # =========================================================================
    # DIMENSION SCORERS
    # =========================================================================
    
    def _score_income_stability(self, ctx: 'RecommendationContext') -> tuple:
        """
        Score income stability risk (0-100, higher = more risk).
        
        Factors:
        - FPL percentage (lower = higher risk)
        - Income source stability (gig work, irregular = higher risk)
        - Verified vs unverified income
        - Single vs multiple income sources
        """
        factors = []
        score = 0
        
        income = ctx.income_analysis or ctx.income_data
        if not income:
            return self._default_dimension_score(RiskDimension.INCOME_STABILITY), factors
        
        # FPL-based scoring (40% of dimension)
        fpl = ctx.fpl_percentage or getattr(income, 'fpl_percentage', 500)
        
        if fpl < self.FPL_CRITICAL:
            fpl_score = 100
            factors.append(RiskFactor(
                factor_id="INC_FPL_CRITICAL",
                dimension=RiskDimension.INCOME_STABILITY,
                name="Critical Poverty Level",
                description=f"Income at {fpl:.0f}% of federal poverty level",
                raw_value=fpl,
                normalized_score=100,
                weight=0.4,
                evidence=[f"FPL: {fpl:.1f}%", "Below 100% FPL threshold"],
                is_critical=True
            ))
        elif fpl < self.FPL_HIGH:
            fpl_score = 75
            factors.append(RiskFactor(
                factor_id="INC_FPL_HIGH",
                dimension=RiskDimension.INCOME_STABILITY,
                name="Low Income Level",
                description=f"Income at {fpl:.0f}% of federal poverty level",
                raw_value=fpl,
                normalized_score=75,
                weight=0.4,
                evidence=[f"FPL: {fpl:.1f}%"]
            ))
        elif fpl < self.FPL_MODERATE:
            fpl_score = 50
        else:
            fpl_score = max(0, 100 - (fpl / 10))  # Decrease score as FPL increases
        
        score += fpl_score * 0.4
        
        # Income stability scoring (30% of dimension)
        stability_score = 0
        if hasattr(income, 'income_stability_score'):
            stability = income.income_stability_score
            stability_score = (1 - stability) * 100  # Invert: high stability = low risk
            if stability < 0.5:
                factors.append(RiskFactor(
                    factor_id="INC_UNSTABLE",
                    dimension=RiskDimension.INCOME_STABILITY,
                    name="Unstable Income",
                    description="Income sources are irregular or unstable",
                    raw_value=stability,
                    normalized_score=int((1-stability) * 100),
                    weight=0.3,
                    evidence=["High proportion of gig/irregular income"]
                ))
        score += stability_score * 0.3
        
        # Income source diversity (15% of dimension)
        sources = getattr(income, 'income_sources', [])
        if len(sources) <= 1:
            diversity_score = 60
            factors.append(RiskFactor(
                factor_id="INC_SINGLE_SOURCE",
                dimension=RiskDimension.INCOME_STABILITY,
                name="Single Income Source",
                description="Reliance on single income source increases vulnerability",
                raw_value=len(sources),
                normalized_score=60,
                weight=0.15,
                evidence=[f"Only {len(sources)} income source(s)"]
            ))
        else:
            diversity_score = max(0, 60 - (len(sources) * 15))
        score += diversity_score * 0.15
        
        # Verification status (15% of dimension)
        verified = sum(1 for s in sources if getattr(s, 'is_verified', False))
        unverified_ratio = 1 - (verified / max(1, len(sources)))
        verification_score = unverified_ratio * 60
        score += verification_score * 0.15
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.INCOME_STABILITY,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Low income relative to poverty level" if fpl < 200 else "Income stability concerns"
        )
        
        return dim_score, factors
    
    def _score_debt_burden(self, ctx: 'RecommendationContext') -> tuple:
        """
        Score debt burden risk.
        
        Factors:
        - DTI ratio (higher = more risk)
        - Total debt relative to income
        - High-interest debt proportion
        - Secured vs unsecured debt mix
        """
        factors = []
        score = 0
        
        debt = ctx.debt_analysis or ctx.debt_data
        income = ctx.income_analysis or ctx.income_data
        
        if not debt:
            return self._default_dimension_score(RiskDimension.DEBT_BURDEN), factors
        
        # DTI Scoring (50% of dimension)
        dti = getattr(debt, 'gross_dti_ratio', None) or getattr(
            getattr(debt, 'dti_analysis', None), 'gross_dti_ratio', 0.3
        )
        
        if dti >= self.DTI_CRITICAL:
            dti_score = 100
            factors.append(RiskFactor(
                factor_id="DEBT_DTI_CRITICAL",
                dimension=RiskDimension.DEBT_BURDEN,
                name="Critical Debt-to-Income",
                description=f"DTI ratio of {dti:.1%} exceeds critical threshold",
                raw_value=dti,
                normalized_score=100,
                weight=0.5,
                evidence=[f"DTI: {dti:.1%}", "Exceeds 50% critical threshold"],
                is_critical=True
            ))
        elif dti >= self.DTI_HIGH:
            dti_score = 80
            factors.append(RiskFactor(
                factor_id="DEBT_DTI_HIGH",
                dimension=RiskDimension.DEBT_BURDEN,
                name="High Debt-to-Income",
                description=f"DTI ratio of {dti:.1%} is elevated",
                raw_value=dti,
                normalized_score=80,
                weight=0.5,
                evidence=[f"DTI: {dti:.1%}", "Exceeds QM threshold of 43%"]
            ))
        elif dti >= self.DTI_MODERATE:
            dti_score = 60
        else:
            dti_score = max(0, dti * 150)  # Linear scale below moderate
        
        score += dti_score * 0.5
        
        # Total debt relative to annual income (30% of dimension)
        total_debt = getattr(debt, 'total_debt', Decimal("0"))
        annual_income = Decimal("0")
        if income:
            annual_income = getattr(income, 'total_annual_gross', Decimal("0"))
        
        if annual_income > 0:
            debt_ratio = float(total_debt / annual_income)
            if debt_ratio > 2.0:
                ratio_score = 100
                factors.append(RiskFactor(
                    factor_id="DEBT_RATIO_CRITICAL",
                    dimension=RiskDimension.DEBT_BURDEN,
                    name="Debt Exceeds 2x Annual Income",
                    description="Total debt exceeds twice annual income",
                    raw_value=debt_ratio,
                    normalized_score=100,
                    weight=0.3,
                    is_critical=True
                ))
            elif debt_ratio > 1.0:
                ratio_score = 70
            else:
                ratio_score = debt_ratio * 70
        else:
            ratio_score = 50  # Unknown
        
        score += ratio_score * 0.3
        
        # High-interest debt proportion (20% of dimension)
        high_int = getattr(getattr(debt, 'debt_breakdown', None), 'high_interest_debt', Decimal("0"))
        if total_debt > 0:
            high_int_ratio = float(high_int / total_debt)
            high_int_score = high_int_ratio * 100
            if high_int_ratio > 0.5:
                factors.append(RiskFactor(
                    factor_id="DEBT_HIGH_INTEREST",
                    dimension=RiskDimension.DEBT_BURDEN,
                    name="High-Interest Debt",
                    description="Over 50% of debt is high-interest (>20% APR)",
                    raw_value=high_int_ratio,
                    normalized_score=int(high_int_score),
                    weight=0.2
                ))
        else:
            high_int_score = 0
        
        score += high_int_score * 0.2
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.DEBT_BURDEN,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="High debt-to-income ratio" if dti >= 0.36 else "Debt levels"
        )
        
        return dim_score, factors
    
    def _score_medical_debt_ratio(self, ctx: 'RecommendationContext') -> tuple:
        """Score medical debt as proportion of total debt and income."""
        factors = []
        score = 0
        
        debt = ctx.debt_analysis or ctx.debt_data
        income = ctx.income_analysis or ctx.income_data
        
        if not debt:
            return self._default_dimension_score(RiskDimension.MEDICAL_DEBT_RATIO), factors
        
        # Medical debt as percentage of income (60% of dimension)
        medical_debt = getattr(debt, 'total_medical_debt', Decimal("0"))
        pending_bills = sum(
            getattr(b, 'patient_balance', Decimal("0")) 
            for b in ctx.bills
        )
        total_medical = medical_debt + pending_bills
        
        annual_income = Decimal("0")
        if income:
            annual_income = getattr(income, 'total_annual_gross', Decimal("1"))
        
        if annual_income > 0:
            medical_ratio = float(total_medical / annual_income)
            if medical_ratio > 0.5:
                ratio_score = 100
                factors.append(RiskFactor(
                    factor_id="MED_RATIO_CRITICAL",
                    dimension=RiskDimension.MEDICAL_DEBT_RATIO,
                    name="Catastrophic Medical Debt",
                    description="Medical debt exceeds 50% of annual income",
                    raw_value=medical_ratio,
                    normalized_score=100,
                    weight=0.6,
                    is_critical=True
                ))
            elif medical_ratio > 0.25:
                ratio_score = 75
                factors.append(RiskFactor(
                    factor_id="MED_RATIO_HIGH",
                    dimension=RiskDimension.MEDICAL_DEBT_RATIO,
                    name="High Medical Debt Burden",
                    description="Medical debt exceeds 25% of annual income",
                    raw_value=medical_ratio,
                    normalized_score=75,
                    weight=0.6
                ))
            elif medical_ratio > 0.10:
                ratio_score = 50
            else:
                ratio_score = medical_ratio * 500  # Scale up small ratios
        else:
            ratio_score = 50
        
        score += ratio_score * 0.6
        
        # Medical debt as proportion of total debt (40% of dimension)
        total_debt = getattr(debt, 'total_debt', Decimal("1"))
        if total_debt > 0:
            med_proportion = float(total_medical / total_debt)
            prop_score = med_proportion * 80  # Max 80 for this factor
            if med_proportion > 0.5:
                factors.append(RiskFactor(
                    factor_id="MED_PROPORTION",
                    dimension=RiskDimension.MEDICAL_DEBT_RATIO,
                    name="Medical-Heavy Debt Profile",
                    description="Medical debt is majority of total debt",
                    raw_value=med_proportion,
                    normalized_score=int(prop_score),
                    weight=0.4
                ))
        else:
            prop_score = 0
        
        score += prop_score * 0.4
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.MEDICAL_DEBT_RATIO,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Medical debt relative to income"
        )
        
        return dim_score, factors
    
    def _score_upcoming_costs(self, ctx: 'RecommendationContext') -> tuple:
        """Score risk from upcoming/expected medical costs."""
        factors = []
        score = 0
        
        procedures = ctx.upcoming_procedures or []
        income = ctx.income_analysis or ctx.income_data
        insurance = ctx.insurance_analysis or ctx.insurance_data
        
        if not procedures:
            # No upcoming procedures = low risk for this dimension
            return RiskDimensionScore(
                dimension=RiskDimension.UPCOMING_COSTS,
                score=10,
                category=RiskCategory.MINIMAL,
                factors=[],
                primary_driver="No known upcoming costs"
            ), []
        
        # Calculate total expected costs
        total_expected = Decimal("0")
        for proc in procedures:
            cost = Decimal(str(proc.get('estimated_cost', 0)))
            patient_resp = Decimal(str(proc.get('patient_responsibility', cost * Decimal("0.3"))))
            total_expected += patient_resp
        
        # Compare to monthly income and payment capacity
        monthly_income = Decimal("0")
        payment_capacity = Decimal("0")
        if income:
            monthly_income = getattr(income, 'total_monthly_net', Decimal("0"))
            budget = getattr(income, 'budget_projection', None)
            if budget:
                payment_capacity = getattr(budget, 'medical_payment_capacity', monthly_income * Decimal("0.1"))
        
        # Months to pay off upcoming costs
        if payment_capacity > 0:
            months_to_pay = int(total_expected / payment_capacity)
            if months_to_pay > 24:
                cost_score = 100
                factors.append(RiskFactor(
                    factor_id="UPCOMING_UNAFFORDABLE",
                    dimension=RiskDimension.UPCOMING_COSTS,
                    name="Unaffordable Upcoming Costs",
                    description=f"Would take {months_to_pay}+ months to pay off",
                    raw_value=months_to_pay,
                    normalized_score=100,
                    weight=0.7,
                    is_critical=True
                ))
            elif months_to_pay > 12:
                cost_score = 70
            elif months_to_pay > 6:
                cost_score = 50
            else:
                cost_score = months_to_pay * 8
        else:
            cost_score = 80  # Can't pay anything
        
        score += cost_score * 0.7
        
        # Deductible impact
        if insurance:
            ded_remaining = getattr(insurance, 'deductible_remaining', Decimal("0"))
            if ded_remaining > total_expected * Decimal("0.5"):
                factors.append(RiskFactor(
                    factor_id="UPCOMING_DEDUCTIBLE",
                    dimension=RiskDimension.UPCOMING_COSTS,
                    name="Deductible Not Met",
                    description="Significant deductible remaining",
                    raw_value=float(ded_remaining),
                    normalized_score=60,
                    weight=0.3
                ))
                score += 60 * 0.3
            else:
                score += 20 * 0.3
        else:
            score += 40 * 0.3
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.UPCOMING_COSTS,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver=f"${total_expected:,.0f} in expected costs"
        )
        
        return dim_score, factors
    
    def _score_insurance_gaps(self, ctx: 'RecommendationContext') -> tuple:
        """Score risk from insurance coverage gaps."""
        factors = []
        score = 0
        
        insurance = ctx.insurance_analysis or ctx.insurance_data
        
        if not insurance:
            # No insurance = maximum risk
            factors.append(RiskFactor(
                factor_id="INS_NONE",
                dimension=RiskDimension.INSURANCE_GAPS,
                name="No Insurance Coverage",
                description="Patient has no health insurance",
                raw_value=None,
                normalized_score=100,
                weight=1.0,
                is_critical=True
            ))
            return RiskDimensionScore(
                dimension=RiskDimension.INSURANCE_GAPS,
                score=100,
                category=RiskCategory.CRITICAL,
                factors=factors,
                primary_driver="No insurance coverage"
            ), factors
        
        # Coverage gaps from analysis (60% of dimension)
        gaps = getattr(insurance, 'coverage_gaps', [])
        if gaps:
            gap_exposure = sum(getattr(g, 'financial_exposure', Decimal("0")) for g in gaps)
            if gap_exposure > Decimal("5000"):
                gap_score = 80
                factors.append(RiskFactor(
                    factor_id="INS_GAPS_HIGH",
                    dimension=RiskDimension.INSURANCE_GAPS,
                    name="Significant Coverage Gaps",
                    description=f"${gap_exposure:,.0f} in potential uncovered expenses",
                    raw_value=float(gap_exposure),
                    normalized_score=80,
                    weight=0.6
                ))
            elif gap_exposure > Decimal("1000"):
                gap_score = 50
            else:
                gap_score = 30
        else:
            gap_score = 0
        
        score += gap_score * 0.6
        
        # Plan adequacy (40% of dimension)
        adequacy = getattr(insurance, 'plan_adequacy_score', 0.7)
        adequacy_score = (1 - adequacy) * 100
        if adequacy < 0.5:
            factors.append(RiskFactor(
                factor_id="INS_INADEQUATE",
                dimension=RiskDimension.INSURANCE_GAPS,
                name="Inadequate Plan Coverage",
                description="Insurance plan has significant limitations",
                raw_value=adequacy,
                normalized_score=int(adequacy_score),
                weight=0.4
            ))
        
        score += adequacy_score * 0.4
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.INSURANCE_GAPS,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Coverage gaps" if gaps else "Plan limitations"
        )
        
        return dim_score, factors
    
    def _score_bill_errors(self, ctx: 'RecommendationContext') -> tuple:
        """Score risk from billing errors and disputes."""
        factors = []
        score = 0
        
        bill_analysis = ctx.bill_analysis
        bills = ctx.bills
        
        if not bill_analysis and not bills:
            return self._default_dimension_score(RiskDimension.BILL_ERRORS), factors
        
        # Error count and value (70% of dimension)
        total_errors = 0
        error_value = Decimal("0")
        
        if bill_analysis:
            total_errors = getattr(bill_analysis, 'total_errors_found', 0)
            error_value = getattr(bill_analysis, 'total_potential_savings', Decimal("0"))
        
        if total_errors > 5:
            error_score = 80
            factors.append(RiskFactor(
                factor_id="BILL_MANY_ERRORS",
                dimension=RiskDimension.BILL_ERRORS,
                name="Multiple Billing Errors",
                description=f"{total_errors} billing errors detected",
                raw_value=total_errors,
                normalized_score=80,
                weight=0.5
            ))
        elif total_errors > 0:
            error_score = 40 + (total_errors * 8)
        else:
            error_score = 10
        
        score += error_score * 0.5
        
        # Error value relative to total balance
        total_balance = sum(
            getattr(b, 'patient_balance', Decimal("0")) 
            for b in bills
        )
        
        if total_balance > 0 and error_value > 0:
            error_ratio = float(error_value / total_balance)
            value_score = min(100, error_ratio * 200)  # Cap at 100
            if error_ratio > 0.25:
                factors.append(RiskFactor(
                    factor_id="BILL_HIGH_ERROR_VALUE",
                    dimension=RiskDimension.BILL_ERRORS,
                    name="High Error Value",
                    description=f"${error_value:,.0f} in potential overcharges",
                    raw_value=float(error_value),
                    normalized_score=int(value_score),
                    weight=0.2
                ))
        else:
            value_score = 0
        
        score += value_score * 0.2
        
        # Billing accuracy score (30% of dimension)
        accuracy = getattr(bill_analysis, 'billing_accuracy_score', 1.0) if bill_analysis else 1.0
        accuracy_risk = (1 - accuracy) * 100
        score += accuracy_risk * 0.3
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.BILL_ERRORS,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver=f"{total_errors} errors worth ${error_value:,.0f}"
        )
        
        return dim_score, factors
    
    def _score_payment_history(self, ctx: 'RecommendationContext') -> tuple:
        """Score risk from payment history patterns."""
        factors = []
        score = 0
        
        debt = ctx.debt_analysis or ctx.debt_data
        
        if not debt:
            return self._default_dimension_score(RiskDimension.PAYMENT_HISTORY), factors
        
        # Delinquent accounts (50% of dimension)
        delinquent = getattr(debt, 'delinquent_account_count', 0)
        if delinquent > 3:
            delinq_score = 90
            factors.append(RiskFactor(
                factor_id="PAYMENT_MANY_DELINQUENT",
                dimension=RiskDimension.PAYMENT_HISTORY,
                name="Multiple Delinquent Accounts",
                description=f"{delinquent} accounts are past due",
                raw_value=delinquent,
                normalized_score=90,
                weight=0.5,
                is_critical=True
            ))
        elif delinquent > 0:
            delinq_score = 30 + (delinquent * 20)
            factors.append(RiskFactor(
                factor_id="PAYMENT_DELINQUENT",
                dimension=RiskDimension.PAYMENT_HISTORY,
                name="Delinquent Accounts",
                description=f"{delinquent} account(s) past due",
                raw_value=delinquent,
                normalized_score=delinq_score,
                weight=0.5
            ))
        else:
            delinq_score = 0
        
        score += delinq_score * 0.5
        
        # Payment trend (30% of dimension)
        trend = getattr(debt, 'trend_analysis', None)
        if trend:
            trend_dir = getattr(trend, 'trend_direction', 'stable')
            if trend_dir == 'declining':
                trend_score = 70
                factors.append(RiskFactor(
                    factor_id="PAYMENT_DECLINING",
                    dimension=RiskDimension.PAYMENT_HISTORY,
                    name="Declining Payment Trend",
                    description="Payment consistency is worsening",
                    raw_value=trend_dir,
                    normalized_score=70,
                    weight=0.3
                ))
            elif trend_dir == 'improving':
                trend_score = 20
            else:
                trend_score = 40
        else:
            trend_score = 40
        
        score += trend_score * 0.3
        
        # On-time rate (20% of dimension)
        if trend:
            on_time_rate = getattr(trend, 'avg_payment_on_time_rate', 0.8)
            ontime_score = (1 - on_time_rate) * 100
        else:
            ontime_score = 30
        
        score += ontime_score * 0.2
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.PAYMENT_HISTORY,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Delinquent accounts" if delinquent > 0 else "Payment patterns"
        )
        
        return dim_score, factors
    
    def _score_collections_exposure(self, ctx: 'RecommendationContext') -> tuple:
        """Score risk from collections exposure."""
        factors = []
        score = 0
        
        debt = ctx.debt_analysis or ctx.debt_data
        bills = ctx.bills
        
        # Current collections (50% of dimension)
        in_collections = Decimal("0")
        if debt:
            in_collections = getattr(debt, 'medical_debt_in_collections', Decimal("0"))
        
        if in_collections >= self.COLLECTIONS_CRITICAL:
            coll_score = 100
            factors.append(RiskFactor(
                factor_id="COLL_CRITICAL",
                dimension=RiskDimension.COLLECTIONS_EXPOSURE,
                name="Significant Collections",
                description=f"${in_collections:,.0f} in collections",
                raw_value=float(in_collections),
                normalized_score=100,
                weight=0.5,
                is_critical=True
            ))
        elif in_collections >= self.COLLECTIONS_HIGH:
            coll_score = 70
            factors.append(RiskFactor(
                factor_id="COLL_HIGH",
                dimension=RiskDimension.COLLECTIONS_EXPOSURE,
                name="Active Collections",
                description=f"${in_collections:,.0f} in collections",
                raw_value=float(in_collections),
                normalized_score=70,
                weight=0.5
            ))
        elif in_collections > 0:
            coll_score = 40
        else:
            coll_score = 0
        
        score += coll_score * 0.5
        
        # Collections risk from current bills (50% of dimension)
        at_risk_bills = []
        risk_amount = Decimal("0")
        
        for bill in bills:
            days_until_due = getattr(bill, 'days_until_due', None)
            if days_until_due is not None and days_until_due < 0:
                at_risk_bills.append(bill)
                risk_amount += getattr(bill, 'patient_balance', Decimal("0"))
        
        if risk_amount > Decimal("2000"):
            risk_score = 80
            factors.append(RiskFactor(
                factor_id="COLL_RISK_HIGH",
                dimension=RiskDimension.COLLECTIONS_EXPOSURE,
                name="High Collections Risk",
                description=f"${risk_amount:,.0f} past due, at risk of collections",
                raw_value=float(risk_amount),
                normalized_score=80,
                weight=0.5
            ))
        elif risk_amount > 0:
            risk_score = 50
        else:
            risk_score = 0
        
        score += risk_score * 0.5
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.COLLECTIONS_EXPOSURE,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver=f"${in_collections + risk_amount:,.0f} in/at-risk collections"
        )
        
        return dim_score, factors
    
    def _score_coverage_adequacy(self, ctx: 'RecommendationContext') -> tuple:
        """Score adequacy of insurance coverage relative to needs."""
        factors = []
        score = 0
        
        insurance = ctx.insurance_analysis or ctx.insurance_data
        
        if not insurance:
            return RiskDimensionScore(
                dimension=RiskDimension.COVERAGE_ADEQUACY,
                score=80,
                category=RiskCategory.HIGH,
                factors=[RiskFactor(
                    factor_id="COV_NONE",
                    dimension=RiskDimension.COVERAGE_ADEQUACY,
                    name="No Insurance",
                    description="No insurance coverage",
                    raw_value=None,
                    normalized_score=80,
                    weight=1.0
                )],
                primary_driver="No insurance coverage"
            ), factors
        
        # Deductible burden (40% of dimension)
        deductible = getattr(insurance, 'individual_deductible', Decimal("0"))
        if isinstance(deductible, dict):
            deductible = Decimal(str(deductible.get('total_deductible', 0)))
        
        if deductible > Decimal("5000"):
            ded_score = 70
            factors.append(RiskFactor(
                factor_id="COV_HIGH_DED",
                dimension=RiskDimension.COVERAGE_ADEQUACY,
                name="High Deductible",
                description=f"${deductible:,.0f} deductible",
                raw_value=float(deductible),
                normalized_score=70,
                weight=0.4
            ))
        elif deductible > Decimal("2500"):
            ded_score = 50
        else:
            ded_score = 20
        
        score += ded_score * 0.4
        
        # OOP max burden (30% of dimension)
        oop_max = getattr(insurance, 'individual_oop_max', Decimal("0"))
        if isinstance(oop_max, dict):
            oop_max = Decimal(str(oop_max.get('total_oop_max', 0)))
        
        if oop_max > Decimal("10000"):
            oop_score = 60
        elif oop_max > Decimal("6000"):
            oop_score = 40
        else:
            oop_score = 20
        
        score += oop_score * 0.3
        
        # Year-end proximity (30% of dimension)
        days_left = getattr(insurance, 'days_until_plan_year_end', 365)
        if days_left < 30:
            year_score = 40
            factors.append(RiskFactor(
                factor_id="COV_YEAR_END",
                dimension=RiskDimension.COVERAGE_ADEQUACY,
                name="Plan Year Ending",
                description=f"Plan year ends in {days_left} days",
                raw_value=days_left,
                normalized_score=40,
                weight=0.3
            ))
        else:
            year_score = 10
        
        score += year_score * 0.3
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.COVERAGE_ADEQUACY,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Plan cost-sharing structure"
        )
        
        return dim_score, factors
    
    def _score_affordability(self, ctx: 'RecommendationContext') -> tuple:
        """Score overall affordability of medical expenses."""
        factors = []
        score = 0
        
        income = ctx.income_analysis or ctx.income_data
        bills = ctx.bills
        
        if not income:
            return self._default_dimension_score(RiskDimension.AFFORDABILITY), factors
        
        # Payment capacity vs current bills (60% of dimension)
        budget = getattr(income, 'budget_projection', None)
        payment_capacity = Decimal("0")
        
        if budget:
            payment_capacity = getattr(budget, 'medical_payment_capacity', Decimal("0"))
        
        total_owed = sum(
            getattr(b, 'patient_balance', Decimal("0")) 
            for b in bills
        )
        
        if payment_capacity > 0:
            months_to_pay = int(total_owed / payment_capacity) if total_owed > 0 else 0
            
            if months_to_pay > 36:
                afford_score = 100
                factors.append(RiskFactor(
                    factor_id="AFFORD_CRITICAL",
                    dimension=RiskDimension.AFFORDABILITY,
                    name="Unaffordable Medical Debt",
                    description=f"Would take {months_to_pay}+ months to pay off",
                    raw_value=months_to_pay,
                    normalized_score=100,
                    weight=0.6,
                    is_critical=True
                ))
            elif months_to_pay > 24:
                afford_score = 75
            elif months_to_pay > 12:
                afford_score = 50
            else:
                afford_score = min(50, months_to_pay * 4)
        else:
            afford_score = 90
            factors.append(RiskFactor(
                factor_id="AFFORD_NO_CAPACITY",
                dimension=RiskDimension.AFFORDABILITY,
                name="No Payment Capacity",
                description="No disposable income for medical payments",
                raw_value=0,
                normalized_score=90,
                weight=0.6,
                is_critical=True
            ))
        
        score += afford_score * 0.6
        
        # Stress ratio (40% of dimension)
        if budget:
            stress = getattr(budget, 'stress_ratio', 0)
            if stress > 2.0:
                stress_score = 80
            elif stress > 1.0:
                stress_score = 60
            elif stress > 0.5:
                stress_score = 40
            else:
                stress_score = stress * 80
        else:
            stress_score = 40
        
        score += stress_score * 0.4
        
        dim_score = RiskDimensionScore(
            dimension=RiskDimension.AFFORDABILITY,
            score=int(round(score)),
            category=RiskDimensionScore.score_to_category(int(score)),
            factors=factors,
            primary_driver="Payment capacity relative to debt"
        )
        
        return dim_score, factors
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _default_dimension_score(self, dimension: RiskDimension) -> RiskDimensionScore:
        """Return default moderate score when data is unavailable."""
        return RiskDimensionScore(
            dimension=dimension,
            score=40,
            category=RiskCategory.MODERATE,
            factors=[],
            primary_driver="Insufficient data for assessment"
        )
    
    def _generate_alerts(self, 
                         dimension_scores: dict,
                         critical_factors: list,
                         ctx: 'RecommendationContext') -> list[Alert]:
        """Generate alerts based on risk assessment."""
        alerts = []
        
        # Critical factor alerts
        for factor in critical_factors:
            alerts.append(Alert(
                severity=AlertSeverity.CRITICAL,
                title=factor.name,
                message=factor.description,
                related_dimension=factor.dimension,
                action_required=True
            ))
        
        # Past-due bill alerts
        for bill in ctx.bills:
            days = getattr(bill, 'days_until_due', None)
            if days is not None and days < 0:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    title=f"Past Due: {getattr(bill, 'provider_name', 'Unknown')}",
                    message=f"Bill is {abs(days)} days past due",
                    related_dimension=RiskDimension.COLLECTIONS_EXPOSURE,
                    action_required=True,
                    deadline=date.today()
                ))
        
        # Year-end alerts
        insurance = ctx.insurance_analysis or ctx.insurance_data
        if insurance:
            days_left = getattr(insurance, 'days_until_plan_year_end', 365)
            if days_left < 30:
                alerts.append(Alert(
                    severity=AlertSeverity.CAUTION,
                    title="Plan Year Ending Soon",
                    message=f"Deductible resets in {days_left} days",
                    related_dimension=RiskDimension.COVERAGE_ADEQUACY,
                    deadline=date.today() + timedelta(days=days_left)
                ))
        
        return alerts
    
    def _assess_data_completeness(self, ctx: 'RecommendationContext') -> float:
        """Assess completeness of input data."""
        scores = []
        
        if ctx.income_analysis or ctx.income_data:
            scores.append(0.9)
        else:
            scores.append(0.3)
        
        if ctx.debt_analysis or ctx.debt_data:
            scores.append(0.9)
        else:
            scores.append(0.3)
        
        if ctx.insurance_analysis or ctx.insurance_data:
            scores.append(0.9)
        else:
            scores.append(0.5)  # Uninsured is valid state
        
        if ctx.bills:
            scores.append(0.9)
        else:
            scores.append(0.5)
        
        return sum(scores) / len(scores)
    
    def _generate_risk_summary(self, 
                               score: int, 
                               category: RiskCategory,
                               top_factors: list,
                               critical_factors: list) -> str:
        """Generate human-readable risk summary."""
        
        summaries = {
            RiskCategory.CRITICAL: "Your financial situation requires immediate attention. ",
            RiskCategory.HIGH: "You face significant financial challenges that need prompt action. ",
            RiskCategory.MODERATE: "Your finances need active management but are manageable. ",
            RiskCategory.LOW: "Your financial situation is relatively stable. ",
            RiskCategory.MINIMAL: "Your finances are in good shape. "
        }
        
        summary = summaries.get(category, "")
        
        if top_factors:
            top_names = [f.name for f in top_factors[:3]]
            summary += f"Key concerns: {', '.join(top_names)}. "
        
        if critical_factors:
            summary += f"Critical issues requiring immediate attention: {len(critical_factors)}."
        
        return summary
    
    def _generate_insights(self, 
                           dimension_scores: dict,
                           top_factors: list) -> list[str]:
        """Generate key insights from analysis."""
        insights = []
        
        # Highest risk dimension
        highest_dim = max(dimension_scores.values(), key=lambda x: x.score)
        if highest_dim.score >= 60:
            insights.append(f"Highest risk area: {highest_dim.dimension.value.replace('_', ' ').title()}")
        
        # Top factors
        for factor in top_factors[:3]:
            insights.append(factor.description)
        
        return insights
    
    def _get_category_description(self, category: RiskCategory) -> str:
        """Get description for risk category."""
        descriptions = {
            RiskCategory.CRITICAL: "Immediate intervention required - financial hardship likely without action",
            RiskCategory.HIGH: "Urgent attention needed - significant risk of financial distress",
            RiskCategory.MODERATE: "Active management required - some financial pressure present",
            RiskCategory.LOW: "Monitor and maintain - minor concerns only",
            RiskCategory.MINIMAL: "Healthy financial state - continue current practices"
        }
        return descriptions.get(category, "Unknown risk level")