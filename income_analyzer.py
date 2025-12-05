"""
MedFin Analysis Engine - Income Analyzer Module
Comprehensive income analysis with FPL calculation and hardship detection
"""

from decimal import Decimal
from datetime import date
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class IncomeAnalyzer:
    """Analyzes household income, calculates FPL, and assesses financial stability"""
    
    # 2024 Federal Poverty Level Guidelines (Continental US)
    # Source: HHS Poverty Guidelines
    FPL_2024_BASE = Decimal("15060")
    FPL_2024_PER_PERSON = Decimal("5380")
    
    # Alaska and Hawaii have different thresholds
    FPL_ALASKA_MULTIPLIER = Decimal("1.25")
    FPL_HAWAII_MULTIPLIER = Decimal("1.15")
    
    # Living expense estimates by region (monthly, per household member)
    REGIONAL_EXPENSE_ESTIMATES = {
        "high_cost": Decimal("2500"),    # NYC, SF, LA
        "medium_cost": Decimal("1800"),  # Most metros
        "low_cost": Decimal("1400"),     # Rural areas
    }
    
    # Zip code prefixes for high-cost areas (simplified)
    HIGH_COST_ZIPS = {"100", "101", "102", "103", "104", "941", "900", "902"}
    
    def __init__(self):
        self.analysis_result = None
    
    def analyze(self, income_data: 'IncomeData', 
                debt_data: 'DebtData',
                pending_bills_total: Decimal = Decimal("0"),
                expected_procedures: list[dict] = None) -> 'IncomeAnalysisOutput':
        """Perform comprehensive income analysis"""
        
        expected_procedures = expected_procedures or []
        
        # Step 1: Calculate FPL
        fpl_calc = self._calculate_fpl(income_data)
        
        # Step 2: Determine income tier
        income_tier = self._determine_income_tier(fpl_calc.fpl_percentage)
        
        # Step 3: Assess income stability
        stability_score, has_irregular = self._assess_stability(income_data)
        
        # Step 4: Calculate budget projection
        budget = self._calculate_budget_projection(
            income_data, debt_data, pending_bills_total
        )
        
        # Step 5: Assess financial risk
        risk_tier, risk_factors = self._assess_financial_risk(
            fpl_calc, budget, debt_data, income_data
        )
        
        # Step 6: Detect hardship indicators
        hardship_flags, qualifies_hardship, hardship_score = self._detect_hardship(
            fpl_calc, budget, debt_data, income_data
        )
        
        # Step 7: Assess affordability for expected procedures
        affordability = self._assess_affordability(
            expected_procedures, budget, income_data
        )
        
        # Step 8: Generate recommendations
        recommendations = self._generate_recommendations(
            fpl_calc, income_tier, risk_tier, hardship_flags, income_data
        )
        
        # Step 9: Determine eligibility indicators
        medicaid_eligible = self._check_medicaid_eligibility(fpl_calc, income_data.state)
        subsidy_eligible = fpl_calc.is_below_400_fpl and not medicaid_eligible
        charity_eligible = fpl_calc.fpl_percentage < 400
        charity_discount = self._estimate_charity_discount(fpl_calc.fpl_percentage)
        
        return IncomeAnalysisOutput(
            fpl_calculation=fpl_calc,
            income_tier=income_tier,
            income_stability_score=stability_score,
            has_irregular_income=has_irregular,
            primary_income_type=self._get_primary_income_type(income_data),
            budget_projection=budget,
            financial_risk_tier=risk_tier,
            risk_factors=risk_factors,
            hardship_flags=hardship_flags,
            qualifies_for_hardship=qualifies_hardship,
            hardship_score=hardship_score,
            affordability_assessments=affordability,
            income_recommendations=recommendations,
            likely_medicaid_eligible=medicaid_eligible,
            likely_marketplace_subsidy_eligible=subsidy_eligible,
            likely_charity_care_eligible=charity_eligible,
            estimated_charity_care_discount=charity_discount
        )
    
    def _calculate_fpl(self, income_data: 'IncomeData') -> 'FPLCalculation':
        """Calculate Federal Poverty Level percentage"""
        household_size = income_data.household_size
        annual_income = income_data.total_annual_gross
        state = income_data.state.upper()
        
        # Calculate FPL threshold
        fpl_threshold = self.FPL_2024_BASE + (
            self.FPL_2024_PER_PERSON * (household_size - 1)
        )
        
        # Adjust for Alaska/Hawaii
        if state == "AK":
            fpl_threshold *= self.FPL_ALASKA_MULTIPLIER
        elif state == "HI":
            fpl_threshold *= self.FPL_HAWAII_MULTIPLIER
        
        # Calculate percentage
        fpl_percentage = float(annual_income / fpl_threshold * 100) if fpl_threshold > 0 else 0
        
        return FPLCalculation(
            household_size=household_size,
            annual_income=annual_income,
            fpl_threshold=fpl_threshold,
            fpl_percentage=fpl_percentage,
            income_tier=self._determine_income_tier(fpl_percentage),
            is_below_100_fpl=fpl_percentage < 100,
            is_below_138_fpl=fpl_percentage < 138,
            is_below_200_fpl=fpl_percentage < 200,
            is_below_250_fpl=fpl_percentage < 250,
            is_below_400_fpl=fpl_percentage < 400
        )
    
    def _determine_income_tier(self, fpl_percentage: float) -> 'IncomeTier':
        """Determine income tier based on FPL percentage"""
        if fpl_percentage < 100:
            return IncomeTier.VERY_LOW
        elif fpl_percentage < 200:
            return IncomeTier.LOW
        elif fpl_percentage < 400:
            return IncomeTier.MODERATE
        elif fpl_percentage < 600:
            return IncomeTier.MIDDLE
        elif fpl_percentage < 800:
            return IncomeTier.UPPER_MIDDLE
        else:
            return IncomeTier.HIGH
    
    def _assess_stability(self, income_data: 'IncomeData') -> tuple[float, bool]:
        """Assess income stability score (0-1) and irregular income flag"""
        if not income_data.income_sources:
            return 0.5, True
        
        score = 1.0
        has_irregular = False
        
        # Unstable income types
        unstable_types = {
            IncomeType.GIG_WORK, IncomeType.SELF_EMPLOYMENT,
            IncomeType.IRREGULAR, IncomeType.OTHER
        }
        
        # Stable income types
        very_stable_types = {
            IncomeType.SOCIAL_SECURITY, IncomeType.PENSION,
            IncomeType.DISABILITY
        }
        
        total_income = income_data.total_monthly_gross
        if total_income == 0:
            return 0.3, True
        
        # Weight by income amount
        unstable_income = sum(
            s.monthly_gross for s in income_data.income_sources
            if s.income_type in unstable_types or not s.is_stable
        )
        
        very_stable_income = sum(
            s.monthly_gross for s in income_data.income_sources
            if s.income_type in very_stable_types
        )
        
        unstable_ratio = float(unstable_income / total_income)
        stable_ratio = float(very_stable_income / total_income)
        
        has_irregular = unstable_ratio > 0.3
        
        # Calculate score
        score = 1.0 - (unstable_ratio * 0.5) + (stable_ratio * 0.2)
        score = max(0.1, min(1.0, score))
        
        # Penalize for unverified income
        unverified = sum(1 for s in income_data.income_sources if not s.is_verified)
        if unverified > 0:
            score *= 0.9
        
        return score, has_irregular
    
    def _calculate_budget_projection(self, income_data: 'IncomeData',
                                      debt_data: 'DebtData',
                                      pending_medical: Decimal) -> 'BudgetProjection':
        """Calculate monthly budget breakdown"""
        monthly_income = income_data.total_monthly_net
        debt_payments = debt_data.total_minimum_payments
        
        # Estimate living expenses based on location
        cost_tier = self._get_cost_tier(income_data.state, 
                                        getattr(income_data, 'zip_code', None))
        base_expense = self.REGIONAL_EXPENSE_ESTIMATES[cost_tier]
        living_expenses = base_expense * income_data.household_size * Decimal("0.7")
        
        # Cap living expenses at reasonable percentage of income
        living_expenses = min(living_expenses, monthly_income * Decimal("0.65"))
        
        total_expenses = debt_payments + living_expenses
        disposable = monthly_income - total_expenses
        
        # Medical payment capacity (max 10% of disposable, min $50 if disposable)
        medical_capacity = max(
            Decimal("0"),
            min(disposable * Decimal("0.10"), disposable - Decimal("200"))
        )
        if medical_capacity < 0:
            medical_capacity = Decimal("0")
        
        # Calculate stress ratio
        stress_ratio = 0.0
        if disposable > 0:
            stress_ratio = float(pending_medical / (disposable * 12))
        elif pending_medical > 0:
            stress_ratio = 10.0  # Very high stress
        
        return BudgetProjection(
            total_monthly_income=monthly_income,
            total_monthly_expenses=total_expenses,
            debt_payments=debt_payments,
            estimated_living_expenses=living_expenses,
            disposable_income=disposable,
            medical_payment_capacity=medical_capacity,
            stress_ratio=min(10.0, stress_ratio)
        )
    
    def _get_cost_tier(self, state: str, zip_code: Optional[str]) -> str:
        """Determine cost of living tier"""
        high_cost_states = {"CA", "NY", "MA", "CT", "NJ", "HI", "DC"}
        low_cost_states = {"MS", "AR", "WV", "AL", "KY", "OK", "MO"}
        
        if zip_code and zip_code[:3] in self.HIGH_COST_ZIPS:
            return "high_cost"
        elif state.upper() in high_cost_states:
            return "high_cost"
        elif state.upper() in low_cost_states:
            return "low_cost"
        return "medium_cost"
    
    def _assess_financial_risk(self, fpl: 'FPLCalculation',
                                budget: 'BudgetProjection',
                                debt_data: 'DebtData',
                                income_data: 'IncomeData') -> tuple['RiskTier', list[str]]:
        """Assess overall financial risk"""
        risk_factors = []
        score = 0
        
        # FPL-based risk
        if fpl.fpl_percentage < 100:
            score += 30
            risk_factors.append("Income below federal poverty level")
        elif fpl.fpl_percentage < 200:
            score += 20
            risk_factors.append("Income below 200% FPL")
        elif fpl.fpl_percentage < 400:
            score += 10
        
        # Budget stress
        if budget.disposable_income < Decimal("200"):
            score += 25
            risk_factors.append("Very limited disposable income")
        elif budget.disposable_income < Decimal("500"):
            score += 15
            risk_factors.append("Limited disposable income")
        
        if budget.stress_ratio > 2.0:
            score += 20
            risk_factors.append("Medical debt exceeds 2 years of disposable income")
        elif budget.stress_ratio > 1.0:
            score += 10
            risk_factors.append("Significant medical debt burden")
        
        # Debt-based risk
        if debt_data.medical_debt_in_collections > 0:
            score += 15
            risk_factors.append("Medical debt currently in collections")
        
        if debt_data.delinquent_account_count > 0:
            score += 10
            risk_factors.append(f"{debt_data.delinquent_account_count} delinquent accounts")
        
        # Income stability
        stability, _ = self._assess_stability(income_data)
        if stability < 0.5:
            score += 10
            risk_factors.append("Unstable income sources")
        
        # Determine tier
        if score >= 60:
            tier = RiskTier.CRITICAL
        elif score >= 45:
            tier = RiskTier.SEVERE
        elif score >= 30:
            tier = RiskTier.HIGH
        elif score >= 15:
            tier = RiskTier.MODERATE
        elif score >= 5:
            tier = RiskTier.LOW
        else:
            tier = RiskTier.MINIMAL
        
        return tier, risk_factors
    
    def _detect_hardship(self, fpl: 'FPLCalculation',
                         budget: 'BudgetProjection',
                         debt_data: 'DebtData',
                         income_data: 'IncomeData') -> tuple[list[str], bool, int]:
        """Detect financial hardship indicators"""
        flags = []
        score = 0
        
        # Income-based hardship
        if fpl.is_below_100_fpl:
            flags.append("SEVERE_POVERTY")
            score += 40
        elif fpl.is_below_200_fpl:
            flags.append("LOW_INCOME")
            score += 25
        
        # Medical debt burden
        annual_income = income_data.total_annual_gross
        if annual_income > 0:
            medical_debt_ratio = debt_data.total_medical_debt / annual_income
            if medical_debt_ratio > Decimal("0.5"):
                flags.append("CATASTROPHIC_MEDICAL_DEBT")
                score += 30
            elif medical_debt_ratio > Decimal("0.25"):
                flags.append("HIGH_MEDICAL_DEBT_BURDEN")
                score += 20
            elif medical_debt_ratio > Decimal("0.10"):
                flags.append("SIGNIFICANT_MEDICAL_DEBT")
                score += 10
        
        # Budget stress
        if budget.disposable_income <= 0:
            flags.append("NEGATIVE_CASH_FLOW")
            score += 25
        elif budget.medical_payment_capacity < Decimal("50"):
            flags.append("NO_MEDICAL_PAYMENT_CAPACITY")
            score += 15
        
        # Collections
        if debt_data.medical_debt_in_collections > Decimal("1000"):
            flags.append("MEDICAL_COLLECTIONS")
            score += 15
        
        # Recent job loss or income reduction
        # Would check income history if available
        
        qualifies = len(flags) >= 2 or score >= 40
        return flags, qualifies, min(100, score)
    
    def _assess_affordability(self, procedures: list[dict],
                               budget: 'BudgetProjection',
                               income_data: 'IncomeData') -> list['AffordabilityAssessment']:
        """Assess affordability for expected procedures"""
        assessments = []
        
        for proc in procedures:
            name = proc.get("name", "Procedure")
            est_cost = Decimal(str(proc.get("estimated_cost", 0)))
            patient_resp = Decimal(str(proc.get("patient_responsibility", est_cost)))
            
            # Can afford lump sum?
            can_lump = patient_resp <= budget.medical_payment_capacity * 3
            
            # Months to pay off
            if budget.medical_payment_capacity > 0:
                months = int(patient_resp / budget.medical_payment_capacity) + 1
            else:
                months = 999
            
            # Recommended payment
            if months <= 12:
                recommended = patient_resp / 12
            elif months <= 24:
                recommended = patient_resp / 24
            else:
                recommended = budget.medical_payment_capacity
            
            # Will cause hardship?
            hardship = (
                patient_resp > income_data.total_monthly_net * 2 or
                months > 24
            )
            
            assessments.append(AffordabilityAssessment(
                procedure_name=name,
                estimated_cost=est_cost,
                patient_responsibility_estimate=patient_resp,
                can_afford_lump_sum=can_lump,
                months_to_pay_off=min(months, 999),
                recommended_monthly_payment=recommended,
                will_cause_hardship=hardship
            ))
        
        return assessments
    
    def _generate_recommendations(self, fpl: 'FPLCalculation',
                                   income_tier: 'IncomeTier',
                                   risk_tier: 'RiskTier',
                                   hardship_flags: list[str],
                                   income_data: 'IncomeData') -> list[str]:
        """Generate income-related recommendations"""
        recs = []
        
        if fpl.is_below_138_fpl:
            if income_data.state in self._get_medicaid_expansion_states():
                recs.append("You may qualify for Medicaid - apply immediately")
            else:
                recs.append("Check your state's Medicaid eligibility requirements")
        
        if fpl.is_below_250_fpl:
            recs.append("Apply for hospital financial assistance programs")
            recs.append("Request charity care applications from all providers")
        
        if fpl.is_below_400_fpl:
            recs.append("You may qualify for ACA marketplace subsidies")
        
        if "CATASTROPHIC_MEDICAL_DEBT" in hardship_flags:
            recs.append("Consider consulting with a medical billing advocate")
            recs.append("Document all hardship for assistance applications")
        
        if risk_tier in [RiskTier.SEVERE, RiskTier.CRITICAL]:
            recs.append("Contact a nonprofit credit counselor")
            recs.append("Do not pay bills until you've explored all options")
        
        return recs
    
    def _get_primary_income_type(self, income_data: 'IncomeData') -> 'IncomeType':
        """Get the primary (highest) income type"""
        if not income_data.income_sources:
            return IncomeType.OTHER
        return max(income_data.income_sources, 
                   key=lambda s: s.monthly_gross).income_type
    
    def _check_medicaid_eligibility(self, fpl: 'FPLCalculation', state: str) -> bool:
        """Check likely Medicaid eligibility"""
        expansion_states = self._get_medicaid_expansion_states()
        if state.upper() in expansion_states:
            return fpl.fpl_percentage < 138
        else:
            # Non-expansion states have stricter limits
            return fpl.fpl_percentage < 50  # Very rough estimate
    
    def _get_medicaid_expansion_states(self) -> set:
        """Return set of Medicaid expansion states"""
        return {
            "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "HI", "ID",
            "IL", "IN", "IA", "KY", "LA", "ME", "MD", "MA", "MI", "MN",
            "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND",
            "OH", "OK", "OR", "PA", "RI", "SD", "UT", "VT", "VA", "WA", "WV"
        }
    
    def _estimate_charity_discount(self, fpl_percentage: float) -> float:
        """Estimate likely charity care discount based on FPL"""
        if fpl_percentage < 100:
            return 1.0  # 100% discount
        elif fpl_percentage < 150:
            return 0.90
        elif fpl_percentage < 200:
            return 0.75
        elif fpl_percentage < 250:
            return 0.60
        elif fpl_percentage < 300:
            return 0.50
        elif fpl_percentage < 400:
            return 0.35
        else:
            return 0.0