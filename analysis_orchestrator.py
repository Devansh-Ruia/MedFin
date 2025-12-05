"""
MedFin Analysis Engine - Unified Analysis Orchestrator
Combines all analysis modules into a single comprehensive output
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)


class UnifiedAnalysisEngine:
    """
    Main orchestrator for the MedFin Analysis Engine.
    Combines income, debt, insurance, and bill analysis into unified output.
    """
    
    def __init__(self):
        self.income_analyzer = IncomeAnalyzer()
        self.debt_analyzer = DebtAnalyzer()
        self.insurance_analyzer = InsuranceAnalyzer()
        self.bill_analyzer = BillAnalyzer()
    
    def analyze(self, profile: 'UserFinancialProfile') -> 'UnifiedAnalysisOutput':
        """
        Perform comprehensive analysis on user's complete financial profile.
        
        Args:
            profile: Complete user financial profile with all data
            
        Returns:
            UnifiedAnalysisOutput with all analyses and synthesized recommendations
        """
        start_time = time.time()
        warnings = []
        
        try:
            # ================================================================
            # PHASE 1: INCOME ANALYSIS
            # ================================================================
            logger.info(f"Starting analysis for user {profile.user_id}")
            
            pending_bills_total = sum(b.patient_balance for b in profile.bills)
            
            income_analysis = self.income_analyzer.analyze(
                income_data=profile.income,
                debt_data=profile.debt,
                pending_bills_total=pending_bills_total,
                expected_procedures=profile.expected_procedures
            )
            
            fpl_percentage = income_analysis.fpl_calculation.fpl_percentage
            
            # ================================================================
            # PHASE 2: DEBT ANALYSIS
            # ================================================================
            debt_analysis = self.debt_analyzer.analyze(
                debt_data=profile.debt,
                income_data=profile.income,
                fpl_percentage=fpl_percentage
            )
            
            # ================================================================
            # PHASE 3: INSURANCE ANALYSIS (if applicable)
            # ================================================================
            insurance_analysis = None
            if profile.insurance:
                insurance_analysis = self.insurance_analyzer.analyze(
                    insurance=profile.insurance,
                    bills=profile.bills,
                    expected_procedures=profile.expected_procedures,
                    secondary_insurance=profile.secondary_insurance
                )
            else:
                warnings.append("No insurance information provided - analysis limited")
            
            # ================================================================
            # PHASE 4: BILL ANALYSIS
            # ================================================================
            bill_analysis = self.bill_analyzer.analyze(
                bills=profile.bills,
                insurance=profile.insurance,
                fpl_percentage=fpl_percentage
            )
            
            # ================================================================
            # PHASE 5: SYNTHESIS
            # ================================================================
            
            # Risk Summary
            risk_summary = self._synthesize_risk(
                income_analysis, debt_analysis, insurance_analysis, bill_analysis
            )
            
            # Opportunity Summary
            opportunity_summary = self._synthesize_opportunities(
                income_analysis, debt_analysis, insurance_analysis, bill_analysis,
                profile
            )
            
            # Strategy Summary
            strategy_summary = self._synthesize_strategy(
                income_analysis, debt_analysis, insurance_analysis, bill_analysis,
                risk_summary, profile
            )
            
            # ================================================================
            # PHASE 6: BUILD OUTPUT
            # ================================================================
            
            # Calculate key metrics
            total_medical_debt = profile.debt.total_medical_debt + pending_bills_total
            
            # Determine downstream flags
            needs_assistance = (
                fpl_percentage < 400 or 
                income_analysis.qualifies_for_hardship
            )
            needs_payment_plan = (
                pending_bills_total > income_analysis.budget_projection.medical_payment_capacity * 3
            )
            has_errors = bill_analysis.total_errors_found > 0
            has_negotiation = any(
                len(ba.negotiation_opportunities) > 0 
                for ba in bill_analysis.bill_analyses
            )
            urgent = (
                risk_summary.overall_risk_tier in [RiskTier.SEVERE, RiskTier.CRITICAL] or
                any(ba.urgency_score > 70 for ba in bill_analysis.bill_analyses)
            )
            
            # Data quality scores
            completeness = self._assess_completeness(profile)
            confidence = self._calculate_confidence(
                income_analysis, debt_analysis, insurance_analysis, bill_analysis
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return UnifiedAnalysisOutput(
                user_id=profile.user_id,
                income_analysis=income_analysis,
                debt_analysis=debt_analysis,
                insurance_analysis=insurance_analysis,
                bill_analysis=bill_analysis,
                risk_summary=risk_summary,
                opportunity_summary=opportunity_summary,
                strategy_summary=strategy_summary,
                fpl_percentage=fpl_percentage,
                total_medical_debt=total_medical_debt,
                total_pending_bills=pending_bills_total,
                deductible_remaining=profile.insurance.deductible_remaining if profile.insurance else None,
                oop_remaining=profile.insurance.oop_remaining if profile.insurance else None,
                monthly_payment_capacity=income_analysis.budget_projection.medical_payment_capacity,
                needs_assistance_matching=needs_assistance,
                needs_payment_plan=needs_payment_plan,
                has_disputable_errors=has_errors,
                has_negotiation_opportunities=has_negotiation,
                urgent_action_required=urgent,
                data_completeness_score=completeness,
                confidence_score=confidence,
                processing_time_ms=processing_time,
                warnings=warnings
            )
            
        except Exception as e:
            logger.exception(f"Analysis failed for user {profile.user_id}")
            raise
    
    def _synthesize_risk(self, income: 'IncomeAnalysisOutput',
                         debt: 'DebtAnalysisOutput',
                         insurance: Optional['InsuranceAnalysisOutput'],
                         bills: 'BillAnalysisOutput') -> 'RiskSummary':
        """Synthesize overall risk assessment from all components"""
        
        # Component scores (0-100)
        income_score = income.hardship_score
        debt_score = debt.debt_risk_score
        
        insurance_score = 30  # Default for uninsured
        if insurance:
            # Higher score = higher risk
            insurance_score = int((1 - insurance.plan_adequacy_score) * 100)
            if insurance.deductible_status.percentage_met < 0.5:
                insurance_score += 20
        
        bill_score = int((1 - bills.billing_accuracy_score) * 50)
        bill_score += sum(10 for ba in bills.bill_analyses if ba.collections_risk > 0.5)
        bill_score = min(100, bill_score)
        
        # Weighted overall score
        weights = {"income": 0.30, "debt": 0.30, "insurance": 0.20, "bills": 0.20}
        overall_score = int(
            income_score * weights["income"] +
            debt_score * weights["debt"] +
            insurance_score * weights["insurance"] +
            bill_score * weights["bills"]
        )
        
        # Determine tier
        if overall_score >= 70:
            tier = RiskTier.CRITICAL
        elif overall_score >= 55:
            tier = RiskTier.SEVERE
        elif overall_score >= 40:
            tier = RiskTier.HIGH
        elif overall_score >= 25:
            tier = RiskTier.MODERATE
        elif overall_score >= 10:
            tier = RiskTier.LOW
        else:
            tier = RiskTier.MINIMAL
        
        # Collect critical factors
        critical_factors = []
        
        if income.qualifies_for_hardship:
            critical_factors.append("Financial hardship indicators present")
        
        if debt.collections_risk_score > 0.5:
            critical_factors.append("High risk of bills going to collections")
        
        if debt.bankruptcy_may_be_appropriate:
            critical_factors.append("Debt levels may warrant bankruptcy consultation")
        
        if insurance and insurance.uncovered_exposure_estimate > Decimal("5000"):
            critical_factors.append(f"${insurance.uncovered_exposure_estimate:,.0f} uncovered exposure")
        
        # Collections probability
        max_collections_risk = max(
            (ba.collections_risk for ba in bills.bill_analyses),
            default=0.0
        )
        
        # Credit impact tier
        if debt.debt_breakdown.debt_in_collections > 0:
            credit_tier = RiskTier.HIGH
        elif debt.dti_analysis.gross_dti_ratio > 0.5:
            credit_tier = RiskTier.MODERATE
        else:
            credit_tier = RiskTier.LOW
        
        return RiskSummary(
            overall_risk_tier=tier,
            overall_risk_score=overall_score,
            income_risk_score=income_score,
            debt_risk_score=debt_score,
            insurance_risk_score=insurance_score,
            billing_risk_score=bill_score,
            critical_risk_factors=critical_factors,
            collections_probability=max_collections_risk,
            credit_impact_risk=credit_tier
        )
    
    def _synthesize_opportunities(self, income: 'IncomeAnalysisOutput',
                                    debt: 'DebtAnalysisOutput',
                                    insurance: Optional['InsuranceAnalysisOutput'],
                                    bills: 'BillAnalysisOutput',
                                    profile: 'UserFinancialProfile') -> 'OpportunitySummary':
        """Synthesize savings opportunities from all components"""
        
        # Bill error savings
        billing_savings = bills.total_potential_savings
        high_conf_billing = sum(
            e.potential_recovery for ba in bills.bill_analyses
            for e in ba.errors if e.recovery_confidence > 0.7
        )
        
        # Negotiation savings
        negotiation_savings = sum(
            opp.expected_savings
            for ba in bills.bill_analyses
            for opp in ba.negotiation_opportunities
        )
        
        # Assistance program savings
        assistance_savings = Decimal("0")
        if income.likely_charity_care_eligible:
            pending = sum(b.patient_balance for b in profile.bills)
            assistance_savings = pending * Decimal(str(income.estimated_charity_care_discount))
        
        for qual in debt.qualifications:
            if qual.estimated_benefit:
                assistance_savings += qual.estimated_benefit
        
        # Insurance optimization
        insurance_savings = Decimal("0")
        if insurance:
            insurance_savings += insurance.coordination_savings_estimate
            for mismatch in insurance.coding_mismatches:
                insurance_savings += mismatch.potential_savings
        
        # Total
        total_savings = billing_savings + negotiation_savings + assistance_savings + insurance_savings
        high_confidence = high_conf_billing + (negotiation_savings * Decimal("0.5"))
        
        # Top opportunities
        top_ops = []
        
        if billing_savings > 0:
            top_ops.append({
                "type": "billing_errors",
                "description": "Dispute identified billing errors",
                "savings": float(billing_savings),
                "confidence": 0.75
            })
        
        if assistance_savings > 0:
            top_ops.append({
                "type": "assistance_programs",
                "description": "Apply for financial assistance",
                "savings": float(assistance_savings),
                "confidence": income.estimated_charity_care_discount
            })
        
        if negotiation_savings > 0:
            top_ops.append({
                "type": "negotiation",
                "description": "Negotiate bill reductions",
                "savings": float(negotiation_savings),
                "confidence": 0.55
            })
        
        top_ops.sort(key=lambda x: x["savings"], reverse=True)
        
        return OpportunitySummary(
            total_potential_savings=total_savings,
            high_confidence_savings=high_confidence,
            billing_error_savings=billing_savings,
            negotiation_savings=negotiation_savings,
            assistance_program_savings=assistance_savings,
            insurance_optimization_savings=insurance_savings,
            top_opportunities=top_ops[:5]
        )
    
    def _synthesize_strategy(self, income: 'IncomeAnalysisOutput',
                              debt: 'DebtAnalysisOutput',
                              insurance: Optional['InsuranceAnalysisOutput'],
                              bills: 'BillAnalysisOutput',
                              risk: 'RiskSummary',
                              profile: 'UserFinancialProfile') -> 'StrategySummary':
        """Synthesize strategic recommendations"""
        
        # Determine primary strategy
        if income.fpl_calculation.is_below_200_fpl:
            primary = "MAXIMIZE_ASSISTANCE"
            rationale = "Income below 200% FPL qualifies for significant assistance"
        elif risk.overall_risk_tier in [RiskTier.SEVERE, RiskTier.CRITICAL]:
            primary = "STABILIZE_IMMEDIATELY"
            rationale = "Critical financial risk requires immediate intervention"
        elif bills.total_errors_found > 0:
            primary = "DISPUTE_FIRST"
            rationale = "Resolve billing errors before making any payments"
        elif income.qualifies_for_hardship:
            primary = "HARDSHIP_PATH"
            rationale = "Financial hardship qualifies for additional options"
        else:
            primary = "NEGOTIATE_AND_PAY"
            rationale = "Negotiate reductions then set up manageable payments"
        
        # Immediate actions (next 7 days)
        immediate = []
        
        # Past due bills
        past_due = [ba for ba in bills.bill_analyses if ba.days_until_due and ba.days_until_due < 0]
        if past_due:
            immediate.append(f"Contact {len(past_due)} provider(s) with past-due bills immediately")
        
        # High-priority errors
        if bills.high_priority_disputes:
            immediate.append("File disputes for identified billing errors")
        
        # Request itemized bills
        immediate.append("Request itemized bills from all providers")
        
        # Don't pay yet
        if bills.total_errors_found > 0:
            immediate.append("Do not make payments until errors are resolved")
        
        # Short-term actions (next 30 days)
        short_term = []
        
        if income.likely_charity_care_eligible:
            short_term.append("Apply for hospital charity care programs")
        
        for qual in debt.qualifications:
            if qual.qualification_likelihood > 0.5:
                short_term.append(f"Apply for {qual.program_name}")
        
        if insurance and insurance.coverage_gaps:
            short_term.append("Address coverage gaps with insurer")
        
        short_term.extend(debt.recommended_strategies[:2])
        
        # Long-term actions (30+ days)
        long_term = []
        
        if debt.debt_consolidation_recommended:
            long_term.append("Consider debt consolidation options")
        
        if debt.credit_counseling_recommended:
            long_term.append("Consult nonprofit credit counselor")
        
        long_term.append("Set up interest-free payment plans for remaining balances")
        long_term.append("Build emergency fund to prevent future medical debt")
        
        # Key deadlines
        deadlines = []
        
        for ba in bills.bill_analyses:
            if ba.days_until_due and ba.days_until_due < 30:
                due_date = date.today() + timedelta(days=ba.days_until_due)
                deadlines.append((due_date, f"{ba.provider_name} bill due"))
        
        if insurance:
            if insurance.days_remaining_in_plan_year < 60:
                deadlines.append(
                    (insurance.deductible_reset_date, "Insurance plan year ends")
                )
        
        deadlines.sort(key=lambda x: x[0])
        
        return StrategySummary(
            primary_strategy=primary,
            strategy_rationale=rationale,
            immediate_actions=immediate[:5],
            short_term_actions=short_term[:5],
            long_term_actions=long_term[:5],
            critical_deadlines=deadlines[:5]
        )
    
    def _assess_completeness(self, profile: 'UserFinancialProfile') -> float:
        """Assess data completeness score"""
        score = 0.0
        checks = 0
        
        # Income data
        checks += 1
        if profile.income.income_sources:
            score += 1
        
        checks += 1
        if profile.income.total_annual_gross > 0:
            score += 1
        
        # Debt data
        checks += 1
        if profile.debt.accounts or profile.debt.total_debt == 0:
            score += 1
        
        # Insurance data
        checks += 1
        if profile.insurance:
            score += 1
        
        # Bills
        checks += 1
        if profile.bills:
            score += 1
            # Check bill completeness
            checks += 1
            if any(b.line_items for b in profile.bills):
                score += 1
        
        return score / checks if checks > 0 else 0.5
    
    def _calculate_confidence(self, income, debt, insurance, bills) -> float:
        """Calculate overall analysis confidence"""
        confidences = [
            1.0 - (income.hardship_score / 200),  # Lower hardship = higher confidence
            0.8 if debt.trend_analysis else 0.6,  # Have payment history
            0.9 if insurance else 0.5,  # Have insurance data
            bills.billing_accuracy_score  # Bill analysis accuracy
        ]
        return sum(confidences) / len(confidences)