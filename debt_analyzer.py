"""
MedFin Analysis Engine - Debt Analyzer Module
Comprehensive debt analysis with DTI calculation and strategy recommendations
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DebtAnalyzer:
    """Analyzes debt load, calculates DTI, and recommends strategies"""
    
    # DTI thresholds
    DTI_EXCELLENT = 0.20
    DTI_GOOD = 0.28
    DTI_ACCEPTABLE = 0.36
    DTI_CONCERNING = 0.43
    DTI_CRITICAL = 0.50
    
    # High interest rate threshold
    HIGH_INTEREST_THRESHOLD = 0.20
    
    def __init__(self):
        self.analysis_result = None
    
    def analyze(self, debt_data: 'DebtData',
                income_data: 'IncomeData',
                fpl_percentage: float) -> 'DebtAnalysisOutput':
        """Perform comprehensive debt analysis"""
        
        # Step 1: Calculate debt breakdown
        breakdown = self._calculate_breakdown(debt_data)
        
        # Step 2: Calculate DTI ratios
        dti = self._calculate_dti(debt_data, income_data)
        
        # Step 3: Assess debt risk
        risk_tier, risk_score, risk_factors = self._assess_risk(
            debt_data, dti, income_data
        )
        
        # Step 4: Calculate collections risk
        collections_risk, at_risk_bills = self._assess_collections_risk(debt_data)
        
        # Step 5: Analyze payment trends
        trend_analysis = self._analyze_trends(debt_data)
        
        # Step 6: Assess qualification for programs
        qualifications = self._assess_qualifications(
            debt_data, income_data, fpl_percentage
        )
        
        # Step 7: Generate strategy recommendations
        strategies, priority_debts = self._generate_strategies(
            debt_data, dti, income_data, fpl_percentage
        )
        
        # Step 8: Check for extreme measures
        bankruptcy_appropriate = self._check_bankruptcy_indicators(
            debt_data, income_data
        )
        consolidation_rec = self._check_consolidation(debt_data, dti)
        counseling_rec = risk_tier in [RiskTier.HIGH, RiskTier.SEVERE, RiskTier.CRITICAL]
        
        return DebtAnalysisOutput(
            debt_breakdown=breakdown,
            dti_analysis=dti,
            debt_risk_tier=risk_tier,
            debt_risk_score=risk_score,
            risk_factors=risk_factors,
            collections_risk_score=collections_risk,
            bills_at_collections_risk=at_risk_bills,
            trend_analysis=trend_analysis,
            qualifications=qualifications,
            recommended_strategies=strategies,
            priority_debts=priority_debts,
            bankruptcy_may_be_appropriate=bankruptcy_appropriate,
            debt_consolidation_recommended=consolidation_rec,
            credit_counseling_recommended=counseling_rec
        )
    
    def _calculate_breakdown(self, debt_data: 'DebtData') -> 'DebtBreakdown':
        """Calculate detailed debt breakdown"""
        total = debt_data.total_debt
        medical = debt_data.total_medical_debt
        consumer = debt_data.total_consumer_debt
        
        # Calculate secured vs unsecured
        secured = sum(a.current_balance for a in debt_data.accounts if a.is_secured)
        unsecured = total - secured
        
        # Collections
        in_collections = sum(
            a.current_balance for a in debt_data.accounts if a.in_collections
        )
        
        # High interest
        high_interest = sum(
            a.current_balance for a in debt_data.accounts
            if a.interest_rate and a.interest_rate > self.HIGH_INTEREST_THRESHOLD * 100
        )
        
        medical_pct = float(medical / total) if total > 0 else 0
        
        return DebtBreakdown(
            total_debt=total,
            medical_debt=medical,
            medical_debt_percentage=medical_pct,
            consumer_debt=consumer,
            secured_debt=secured,
            unsecured_debt=unsecured,
            debt_in_collections=in_collections,
            high_interest_debt=high_interest
        )
    
    def _calculate_dti(self, debt_data: 'DebtData',
                       income_data: 'IncomeData') -> 'DTIAnalysis':
        """Calculate debt-to-income ratios"""
        monthly_gross = income_data.total_monthly_gross
        monthly_net = income_data.total_monthly_net
        monthly_debt = debt_data.total_minimum_payments
        
        # Calculate medical-specific DTI
        medical_payments = sum(
            a.minimum_payment for a in debt_data.accounts if a.is_medical
        )
        
        # Handle zero income
        if monthly_gross <= 0:
            return DTIAnalysis(
                gross_dti_ratio=99.0,
                net_dti_ratio=99.0,
                medical_dti_ratio=99.0,
                is_below_28_housing=False,
                is_below_36_total=False,
                is_below_43_qualified=False,
                dti_risk_tier=RiskTier.CRITICAL
            )
        
        gross_dti = float(monthly_debt / monthly_gross)
        net_dti = float(monthly_debt / monthly_net) if monthly_net > 0 else 99.0
        medical_dti = float(medical_payments / monthly_gross)
        
        # Determine risk tier
        if gross_dti >= self.DTI_CRITICAL:
            risk = RiskTier.CRITICAL
        elif gross_dti >= self.DTI_CONCERNING:
            risk = RiskTier.SEVERE
        elif gross_dti >= self.DTI_ACCEPTABLE:
            risk = RiskTier.HIGH
        elif gross_dti >= self.DTI_GOOD:
            risk = RiskTier.MODERATE
        elif gross_dti >= self.DTI_EXCELLENT:
            risk = RiskTier.LOW
        else:
            risk = RiskTier.MINIMAL
        
        return DTIAnalysis(
            gross_dti_ratio=gross_dti,
            net_dti_ratio=net_dti,
            medical_dti_ratio=medical_dti,
            is_below_28_housing=gross_dti < 0.28,
            is_below_36_total=gross_dti < 0.36,
            is_below_43_qualified=gross_dti < 0.43,
            dti_risk_tier=risk
        )
    
    def _assess_risk(self, debt_data: 'DebtData',
                     dti: 'DTIAnalysis',
                     income_data: 'IncomeData') -> tuple['RiskTier', int, list[str]]:
        """Assess overall debt risk"""
        score = 0
        factors = []
        
        # DTI-based scoring
        if dti.gross_dti_ratio >= 0.50:
            score += 30
            factors.append(f"Critical DTI ratio: {dti.gross_dti_ratio:.1%}")
        elif dti.gross_dti_ratio >= 0.43:
            score += 25
            factors.append(f"High DTI ratio: {dti.gross_dti_ratio:.1%}")
        elif dti.gross_dti_ratio >= 0.36:
            score += 15
            factors.append(f"Elevated DTI ratio: {dti.gross_dti_ratio:.1%}")
        
        # Collections
        if debt_data.medical_debt_in_collections > 0:
            score += 20
            factors.append(f"${debt_data.medical_debt_in_collections:,.0f} in collections")
        
        # Delinquencies
        delinquent = debt_data.delinquent_account_count
        if delinquent > 3:
            score += 20
            factors.append(f"{delinquent} delinquent accounts")
        elif delinquent > 0:
            score += 10
            factors.append(f"{delinquent} delinquent account(s)")
        
        # Debt to income (total debt, not monthly)
        annual_income = income_data.total_annual_gross
        if annual_income > 0:
            debt_ratio = debt_data.total_debt / annual_income
            if debt_ratio > Decimal("2.0"):
                score += 20
                factors.append("Total debt exceeds 2x annual income")
            elif debt_ratio > Decimal("1.0"):
                score += 10
                factors.append("Total debt exceeds annual income")
        
        # High interest burden
        high_interest_pct = 0
        if debt_data.total_debt > 0:
            high_int = sum(
                a.current_balance for a in debt_data.accounts
                if a.interest_rate and a.interest_rate > 20
            )
            high_interest_pct = float(high_int / debt_data.total_debt)
        
        if high_interest_pct > 0.5:
            score += 10
            factors.append("Over 50% of debt is high-interest")
        
        # Determine tier
        if score >= 60:
            tier = RiskTier.CRITICAL
        elif score >= 45:
            tier = RiskTier.SEVERE
        elif score >= 30:
            tier = RiskTier.HIGH
        elif score >= 15:
            tier = RiskTier.MODERATE
        elif score > 0:
            tier = RiskTier.LOW
        else:
            tier = RiskTier.MINIMAL
        
        return tier, min(100, score), factors
    
    def _assess_collections_risk(self, debt_data: 'DebtData') -> tuple[float, list[str]]:
        """Assess risk of bills going to collections"""
        at_risk = []
        max_risk = 0.0
        
        for account in debt_data.accounts:
            risk = 0.0
            
            if account.status == DebtStatus.COLLECTIONS:
                risk = 0.99
            elif account.status == DebtStatus.DELINQUENT_90:
                risk = 0.85
            elif account.status == DebtStatus.DELINQUENT_60:
                risk = 0.60
            elif account.status == DebtStatus.DELINQUENT_30:
                risk = 0.35
            elif account.next_due_date:
                days_until = (account.next_due_date - date.today()).days
                if days_until < 0:
                    risk = 0.50
                elif days_until < 14:
                    risk = 0.20
            
            if risk > 0.3:
                at_risk.append(str(account.id))
            
            max_risk = max(max_risk, risk)
        
        return max_risk, at_risk
    
    def _analyze_trends(self, debt_data: 'DebtData') -> Optional['DebtTrendAnalysis']:
        """Analyze payment history trends"""
        history = debt_data.payment_history
        if not history or len(history) < 3:
            return None
        
        # Calculate on-time rate
        on_time = sum(1 for p in history if p.was_on_time)
        on_time_rate = on_time / len(history)
        
        # Recent delinquencies (last 12 entries)
        recent = sorted(history, key=lambda p: p.month, reverse=True)[:12]
        recent_delinq = sum(1 for p in recent if not p.was_on_time)
        
        # Trend direction
        if len(recent) >= 6:
            first_half = recent[len(recent)//2:]
            second_half = recent[:len(recent)//2]
            first_rate = sum(1 for p in first_half if p.was_on_time) / len(first_half)
            second_rate = sum(1 for p in second_half if p.was_on_time) / len(second_half)
            
            if second_rate > first_rate + 0.1:
                trend = "improving"
            elif second_rate < first_rate - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Estimate payoff time
        total_debt = debt_data.total_debt
        avg_payment = sum(p.amount_paid for p in recent) / len(recent)
        if avg_payment > 0:
            months_to_payoff = int(total_debt / avg_payment)
        else:
            months_to_payoff = None
        
        return DebtTrendAnalysis(
            avg_payment_on_time_rate=on_time_rate,
            recent_delinquencies=recent_delinq,
            trend_direction=trend,
            estimated_months_to_payoff=months_to_payoff,
            snowball_vs_avalanche_savings=Decimal("0")  # Would require detailed calc
        )
    
    def _assess_qualifications(self, debt_data: 'DebtData',
                                income_data: 'IncomeData',
                                fpl_percentage: float) -> list['QualificationAssessment']:
        """Assess qualification for various assistance programs"""
        qualifications = []
        
        # Hospital charity care
        if fpl_percentage < 400 and debt_data.total_medical_debt > 0:
            likelihood = 0.9 if fpl_percentage < 200 else 0.7 if fpl_percentage < 300 else 0.5
            qualifications.append(QualificationAssessment(
                program_type="charity_care",
                program_name="Hospital Financial Assistance",
                qualification_likelihood=likelihood,
                qualifying_factors=[
                    f"Income at {fpl_percentage:.0f}% FPL",
                    f"Medical debt of ${debt_data.total_medical_debt:,.0f}"
                ],
                disqualifying_factors=[],
                estimated_benefit=debt_data.total_medical_debt * Decimal(str(likelihood)),
                required_actions=[
                    "Request financial assistance application",
                    "Gather income documentation",
                    "Submit before making payments"
                ]
            ))
        
        # Interest-free payment plans
        if debt_data.total_medical_debt > Decimal("500"):
            qualifications.append(QualificationAssessment(
                program_type="payment_plan",
                program_name="0% Interest Payment Plan",
                qualification_likelihood=0.85,
                qualifying_factors=["Most hospitals offer interest-free plans"],
                disqualifying_factors=[],
                estimated_benefit=Decimal("0"),  # Doesn't reduce total
                required_actions=[
                    "Contact billing department",
                    "Request 0% payment plan options",
                    "Get terms in writing"
                ]
            ))
        
        # Debt relief programs
        if (debt_data.total_medical_debt > income_data.total_annual_gross * Decimal("0.25")):
            qualifications.append(QualificationAssessment(
                program_type="debt_relief",
                program_name="Medical Debt Relief Programs",
                qualification_likelihood=0.6,
                qualifying_factors=[
                    "Medical debt exceeds 25% of annual income",
                    "Demonstrates financial hardship"
                ],
                disqualifying_factors=[],
                estimated_benefit=debt_data.total_medical_debt * Decimal("0.5"),
                required_actions=[
                    "Contact nonprofit debt relief organizations",
                    "Document hardship circumstances"
                ]
            ))
        
        return qualifications
    
    def _generate_strategies(self, debt_data: 'DebtData',
                              dti: 'DTIAnalysis',
                              income_data: 'IncomeData',
                              fpl_percentage: float) -> tuple[list[str], list[str]]:
        """Generate debt management strategies"""
        strategies = []
        priority_debts = []
        
        # Primary strategy based on situation
        if fpl_percentage < 250:
            strategies.append("APPLY_CHARITY_CARE_FIRST")
            strategies.append("Apply for all available financial assistance before paying")
        
        if debt_data.medical_debt_in_collections > 0:
            strategies.append("ADDRESS_COLLECTIONS_IMMEDIATELY")
            strategies.append("Validate collection debts before paying")
        
        if dti.gross_dti_ratio > 0.43:
            strategies.append("NEGOTIATE_ALL_BILLS")
            strategies.append("Request hardship discounts on all balances")
        
        # Prioritize debts
        accounts = sorted(
            debt_data.accounts,
            key=lambda a: (
                a.status == DebtStatus.COLLECTIONS,  # Collections first
                a.interest_rate or 0,  # Then high interest
                -a.current_balance  # Then largest balance
            ),
            reverse=True
        )
        
        priority_debts = [str(a.id) for a in accounts[:5]]
        
        # Additional strategies
        if any(a.interest_rate and a.interest_rate > 20 for a in debt_data.accounts):
            strategies.append("Target high-interest debt first (avalanche method)")
        
        strategies.append("Always negotiate before agreeing to payment plans")
        strategies.append("Request itemized bills for all medical debt")
        
        return strategies, priority_debts
    
    def _check_bankruptcy_indicators(self, debt_data: 'DebtData',
                                      income_data: 'IncomeData') -> bool:
        """Check if bankruptcy might be appropriate"""
        total_debt = debt_data.total_debt
        annual_income = income_data.total_annual_gross
        
        if annual_income <= 0:
            return total_debt > Decimal("10000")
        
        debt_ratio = total_debt / annual_income
        
        return (
            debt_ratio > Decimal("2.0") or
            (debt_data.medical_debt_in_collections > annual_income * Decimal("0.5"))
        )
    
    def _check_consolidation(self, debt_data: 'DebtData',
                              dti: 'DTIAnalysis') -> bool:
        """Check if debt consolidation is recommended"""
        # Multiple high-interest accounts
        high_int_count = sum(
            1 for a in debt_data.accounts
            if a.interest_rate and a.interest_rate > 15
        )
        
        return (
            high_int_count >= 3 and
            dti.gross_dti_ratio < 0.43 and  # Can still qualify
            debt_data.total_debt > Decimal("5000")
        )