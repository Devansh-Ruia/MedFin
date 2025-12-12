"""
MedFin Financial Navigation System - Analysis Engines
Multi-layered analysis for bills, insurance, eligibility, and risk
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
import logging

from fn_data_models import *
from analysis_utilities import BillAnalysisUtilities, RiskAnalysisUtilities, InsuranceAnalysisUtilities

logger = logging.getLogger(__name__)


# ============================================================================
# BASE ANALYZER INTERFACE
# ============================================================================

class BaseAnalyzer(ABC):
    """Abstract base for all analyzers"""
    
    @abstractmethod
    def analyze(self, *args, **kwargs) -> dict:
        pass
    
    def _safe_decimal(self, val, default=Decimal("0")) -> Decimal:
        """Safely convert to Decimal with fallback"""
        if val is None:
            return default
        try:
            return Decimal(str(val))
        except:
            return default


# ============================================================================
# BILL ANALYZER
# ============================================================================

@dataclass
class BillAnalysisResult:
    bill_id: str
    errors_found: list[dict]
    duplicate_charges: list[dict]
    overcharge_amount: Decimal
    negotiation_potential: Decimal
    recommended_actions: list[str]
    urgency_score: int  # 0-100

class BillAnalyzer(BaseAnalyzer):
    """Analyzes medical bills for errors, duplicates, and opportunities"""
    
    # Common CPT code bundling rules (simplified)
    BUNDLED_CODES = {
        "99213": ["99211", "99212"],  # E&M visits
        "43239": ["43235"],           # EGD procedures
        "29881": ["29880"],           # Knee arthroscopy
    }
    
    # Known overpriced procedures by facility type
    FAIR_PRICE_MULTIPLIERS = {
        "hospital_outpatient": 2.5,
        "hospital_inpatient": 3.0,
        "physician_office": 1.2,
        "ambulatory_center": 1.8,
    }
    
    def analyze(self, bill: 'MedicalBill', 
                insurance: Optional['InsurancePlan'] = None) -> BillAnalysisResult:
        errors = []
        duplicates = []
        overcharge = Decimal("0")
        negotiation_potential = Decimal("0")
        actions = []
        
        # 1. Check for duplicate charges
        dup_result = self._detect_duplicates(bill)
        duplicates.extend(dup_result["duplicates"])
        overcharge += dup_result["amount"]
        
        # 2. Check for unbundling
        unbundle_result = self._detect_unbundling(bill)
        errors.extend(unbundle_result["errors"])
        overcharge += unbundle_result["amount"]
        
        # 3. Validate against allowed amounts
        if insurance:
            allowed_result = self._check_allowed_amounts(bill, insurance)
            errors.extend(allowed_result["errors"])
            overcharge += allowed_result["amount"]
        
        # 4. Check balance billing (out-of-network)
        if bill.is_in_network is False and insurance:
            balance_result = self._check_balance_billing(bill, insurance)
            if balance_result["is_violation"]:
                errors.append(balance_result["error"])
                overcharge += balance_result["amount"]
        
        # 5. Calculate negotiation potential
        negotiation_potential = self._estimate_negotiation_potential(
            bill, insurance
        )
        
        # 6. Generate recommended actions
        actions = self._generate_actions(
            bill, errors, duplicates, overcharge, negotiation_potential
        )
        
        # 7. Calculate urgency
        urgency = self._calculate_urgency(bill)
        
        return BillAnalysisResult(
            bill_id=str(bill.id),
            errors_found=errors,
            duplicate_charges=duplicates,
            overcharge_amount=overcharge,
            negotiation_potential=negotiation_potential,
            recommended_actions=actions,
            urgency_score=urgency
        )
    
    def _detect_duplicates(self, bill: 'MedicalBill') -> dict:
        """Find duplicate line items within a bill"""
        duplicates, amount = BillAnalysisUtilities.detect_duplicates(bill)
        return {"duplicates": duplicates, "amount": amount}
    
    def _detect_unbundling(self, bill: 'MedicalBill') -> dict:
        """Detect potential unbundling fraud"""
        errors, amount = BillAnalysisUtilities.detect_unbundling(bill)
        return {"errors": errors, "amount": amount}
    
    def _check_allowed_amounts(self, bill: 'MedicalBill', 
                                insurance: 'InsurancePlan') -> dict:
        """Compare billed vs allowed amounts"""
        errors = []
        amount = Decimal("0")
        
        for item in bill.line_items:
            if item.allowed_amount and item.billed_amount > 0:
                ratio = item.billed_amount / item.allowed_amount
                if ratio > 3.0:  # More than 3x allowed is suspicious
                    excess = item.billed_amount - item.allowed_amount
                    errors.append({
                        "type": BillErrorType.UPCODING,
                        "item_id": str(item.id),
                        "billed": item.billed_amount,
                        "allowed": item.allowed_amount,
                        "excess": excess,
                        "confidence": 0.7
                    })
                    # Patient shouldn't pay more than allowed
                    if item.patient_responsibility > item.allowed_amount:
                        amount += item.patient_responsibility - item.allowed_amount
        
        return {"errors": errors, "amount": amount}
    
    def _check_balance_billing(self, bill: 'MedicalBill',
                                insurance: 'InsurancePlan') -> dict:
        """Check for illegal balance billing"""
        # Many states prohibit balance billing for emergency services
        if bill.facility_type == "ER":
            excess = Decimal("0")
            for item in bill.line_items:
                if item.allowed_amount:
                    if item.patient_responsibility > (
                        item.allowed_amount * Decimal(str(insurance.coinsurance_rate))
                    ):
                        excess += item.patient_responsibility - (
                            item.allowed_amount * Decimal(str(insurance.coinsurance_rate))
                        )
            
            if excess > 0:
                return {
                    "is_violation": True,
                    "error": {
                        "type": BillErrorType.BALANCE_BILLING,
                        "amount": excess,
                        "description": "Potential illegal ER balance billing",
                        "confidence": 0.8
                    },
                    "amount": excess
                }
        
        return {"is_violation": False, "error": None, "amount": Decimal("0")}
    
    def _estimate_negotiation_potential(self, bill: 'MedicalBill',
                                         insurance: Optional['InsurancePlan']) -> Decimal:
        """Estimate how much the bill could be reduced through negotiation"""
        return BillAnalysisUtilities.estimate_negotiation_potential(bill, insurance)
    
    def _calculate_urgency(self, bill: 'MedicalBill') -> int:
        """Calculate urgency score 0-100"""
        return BillAnalysisUtilities.calculate_urgency_score(bill)
    
    def _generate_actions(self, bill, errors, duplicates, 
                          overcharge, negotiation_pot) -> list[str]:
        """Generate list of recommended actions"""
        actions = []
        
        if duplicates:
            actions.append("dispute_duplicates")
        if errors:
            actions.append("dispute_errors")
        if overcharge > Decimal("100"):
            actions.append("request_itemized_bill")
        if negotiation_pot > Decimal("200"):
            actions.append("negotiate_reduction")
        
        return actions


# ============================================================================
# INSURANCE ANALYZER
# ============================================================================

@dataclass
class InsuranceAnalysisResult:
    deductible_status: dict
    oop_status: dict
    coverage_gaps: list[dict]
    coordination_opportunities: list[str]
    appeal_opportunities: list[dict]
    year_end_strategy: Optional[dict]

class InsuranceAnalyzer(BaseAnalyzer):
    """Analyzes insurance coverage and identifies opportunities"""
    
    def analyze(self, insurance: 'InsurancePlan',
                bills: list['MedicalBill'],
                secondary_insurance: Optional['InsurancePlan'] = None
               ) -> InsuranceAnalysisResult:
        
        deductible_status = self._analyze_deductible(insurance, bills)
        oop_status = self._analyze_oop_max(insurance, bills)
        coverage_gaps = self._find_coverage_gaps(insurance, bills)
        coordination = self._check_coordination(insurance, secondary_insurance)
        appeals = self._identify_appeal_opportunities(insurance, bills)
        year_end = self._generate_year_end_strategy(insurance, bills)
        
        return InsuranceAnalysisResult(
            deductible_status=deductible_status,
            oop_status=oop_status,
            coverage_gaps=coverage_gaps,
            coordination_opportunities=coordination,
            appeal_opportunities=appeals,
            year_end_strategy=year_end
        )
    
    def _analyze_deductible(self, ins: 'InsurancePlan', 
                            bills: list['MedicalBill']) -> dict:
        """Analyze deductible status and impact"""
        remaining = ins.deductible_remaining
        pending_bills_total = sum(b.patient_balance for b in bills)
        
        will_meet = remaining <= pending_bills_total
        amount_after_deductible = max(
            Decimal("0"), 
            pending_bills_total - remaining
        )
        
        return {
            "total": ins.individual_deductible,
            "met": ins.individual_deductible_met,
            "remaining": remaining,
            "will_meet_with_current_bills": will_meet,
            "amount_subject_to_coinsurance": amount_after_deductible,
            "days_until_reset": (ins.plan_year_end - date.today()).days
        }
    
    def _analyze_oop_max(self, ins: 'InsurancePlan',
                         bills: list['MedicalBill']) -> dict:
        """Analyze out-of-pocket maximum status"""
        remaining = ins.oop_remaining
        pending = sum(b.patient_balance for b in bills)
        
        proximity = "far" 
        if ins.oop_percentage_met > 0.8:
            proximity = "very_close"
        elif ins.oop_percentage_met > 0.6:
            proximity = "close"
        elif ins.oop_percentage_met > 0.4:
            proximity = "moderate"
        
        will_hit = remaining <= pending
        potential_savings_after_max = max(Decimal("0"), pending - remaining)
        
        return {
            "total": ins.individual_oop_max,
            "met": ins.individual_oop_met,
            "remaining": remaining,
            "percentage_met": ins.oop_percentage_met,
            "proximity": proximity,
            "will_hit_max": will_hit,
            "potential_savings_if_hit": potential_savings_after_max,
            "recommendation": self._oop_recommendation(ins, bills)
        }
    
    def _oop_recommendation(self, ins: 'InsurancePlan', 
                            bills: list['MedicalBill']) -> Optional[str]:
        """Generate OOP-based recommendation"""
        days_left = (ins.plan_year_end - date.today()).days
        
        if ins.oop_percentage_met > 0.85 and days_left < 60:
            return "Schedule any elective procedures before plan year ends"
        elif ins.oop_remaining < Decimal("500") and days_left < 90:
            return "You're close to your OOP max - additional care will be fully covered"
        return None
    
    def _find_coverage_gaps(self, ins: 'InsurancePlan',
                            bills: list['MedicalBill']) -> list[dict]:
        """Identify bills that may have coverage issues"""
        gaps = []
        
        for bill in bills:
            if bill.is_in_network is False:
                gaps.append({
                    "bill_id": str(bill.id),
                    "issue": "out_of_network",
                    "impact": "higher_cost_sharing",
                    "recommendation": "Check if network exception applies"
                })
            
            # Check for denied claims
            if bill.insurance_paid == 0 and bill.total_billed > Decimal("500"):
                gaps.append({
                    "bill_id": str(bill.id),
                    "issue": "possible_denial",
                    "impact": "no_insurance_payment",
                    "recommendation": "Verify claim status and appeal if denied"
                })
        
        return gaps
    
    def _check_coordination(self, primary: 'InsurancePlan',
                            secondary: Optional['InsurancePlan']) -> list[str]:
        """Check for coordination of benefits opportunities"""
        opportunities = []
        
        if secondary:
            opportunities.append(
                "Verify coordination of benefits is properly applied"
            )
            if secondary.insurance_type == InsuranceType.MEDICAID:
                opportunities.append(
                    "Medicaid may cover remaining costs after primary"
                )
        
        return opportunities
    
    def _identify_appeal_opportunities(self, ins: 'InsurancePlan',
                                        bills: list['MedicalBill']) -> list[dict]:
        """Identify claims that should be appealed"""
        appeals = []
        
        for bill in bills:
            # High patient responsibility relative to total might indicate denial
            if bill.total_billed > 0:
                patient_pct = bill.patient_balance / bill.total_billed
                if patient_pct > Decimal("0.5") and bill.total_billed > Decimal("1000"):
                    appeals.append({
                        "bill_id": str(bill.id),
                        "reason": "high_patient_share",
                        "estimated_recovery": bill.patient_balance * Decimal("0.3"),
                        "success_likelihood": 0.4
                    })
        
        return appeals
    
    def _generate_year_end_strategy(self, ins: 'InsurancePlan',
                                     bills: list['MedicalBill']) -> Optional[dict]:
        """Generate year-end insurance strategy"""
        days_left = (ins.plan_year_end - date.today()).days
        
        if days_left > 90:
            return None
        
        strategy = {
            "days_until_reset": days_left,
            "deductible_will_reset": ins.deductible_remaining > 0,
            "oop_will_reset": ins.oop_remaining > 0,
            "recommendations": []
        }
        
        if ins.oop_percentage_met > 0.7:
            strategy["recommendations"].append(
                "Consider scheduling elective care before year end"
            )
        
        if ins.deductible_remaining < Decimal("200"):
            strategy["recommendations"].append(
                "Deductible nearly met - good time for planned procedures"
            )
        
        return strategy


# ============================================================================
# ELIGIBILITY ANALYZER
# ============================================================================

@dataclass 
class EligibilityMatch:
    program_id: str
    program_name: str
    program_type: str
    match_score: float  # 0-1
    estimated_discount: float
    estimated_savings: Decimal
    missing_criteria: list[str]
    required_documents: list[str]
    application_effort: str  # low, medium, high
    approval_likelihood: float

class EligibilityAnalyzer(BaseAnalyzer):
    """Matches patients with assistance programs"""
    
    def analyze(self, profile: 'PatientFinancialProfile',
                bills: list['MedicalBill'],
                programs: list['AssistanceProgram']) -> list[EligibilityMatch]:
        
        matches = []
        total_owed = sum(b.patient_balance for b in bills)
        
        for program in programs:
            match = self._evaluate_program(profile, bills, program, total_owed)
            if match and match.match_score > 0.3:  # Min threshold
                matches.append(match)
        
        # Sort by estimated savings (descending)
        matches.sort(key=lambda m: m.estimated_savings, reverse=True)
        return matches
    
    def _evaluate_program(self, profile: 'PatientFinancialProfile',
                          bills: list['MedicalBill'],
                          program: 'AssistanceProgram',
                          total_owed: Decimal) -> Optional[EligibilityMatch]:
        """Evaluate eligibility for a single program"""
        criteria = program.eligibility
        score: float = 1.0
        missing: list[str] = []
        
        # Check FPL percentage
        if criteria.max_fpl_percentage:
            if profile.federal_poverty_level_percentage > criteria.max_fpl_percentage:
                score *= 0.0  # Disqualified
                missing.append(f"Income exceeds {criteria.max_fpl_percentage}% FPL")
            else:
                # Closer to limit = lower score
                ratio = profile.federal_poverty_level_percentage / criteria.max_fpl_percentage
                score *= (1.0 - ratio * 0.3)  # Slight penalty for being close
        
        # Check state requirements
        if criteria.required_states:
            if profile.state not in criteria.required_states:
                score *= 0.0
                missing.append(f"State {profile.state} not eligible")
        
        # Check insurance requirements
        # (Would check against actual insurance in full implementation)
        
        # Check minimum bill amount
        if criteria.min_bill_amount:
            if total_owed < criteria.min_bill_amount:
                score *= 0.5
                missing.append(f"Bill amount below ${criteria.min_bill_amount} minimum")
        
        if score <= 0:
            return None
        
        # Calculate estimated savings
        estimated_savings = total_owed * Decimal(str(program.typical_discount_percentage))
        if program.max_coverage:
            estimated_savings = min(estimated_savings, program.max_coverage)
        
        # Determine effort level
        effort = "low"
        if len(program.required_documents) > 3:
            effort = "medium"
        if len(program.required_documents) > 5:
            effort = "high"
        
        return EligibilityMatch(
            program_id=str(program.id),
            program_name=program.name,
            program_type=program.program_type,
            match_score=score,
            estimated_discount=program.typical_discount_percentage,
            estimated_savings=estimated_savings,
            missing_criteria=missing,
            required_documents=program.required_documents,
            application_effort=effort,
            approval_likelihood=score * 0.8  # Conservative estimate
        )


# ============================================================================
# RISK ANALYZER
# ============================================================================

class RiskAnalyzer(BaseAnalyzer):
    """Calculates financial risk scores and assessments"""
    
    def analyze(self, profile: 'PatientFinancialProfile',
                bills: list['MedicalBill']) -> 'RiskAssessment':
        
        total_owed = sum(b.patient_balance for b in bills)
        
        # Calculate component risks
        collections_risk = self._assess_collections_risk(bills, profile)
        credit_risk = self._assess_credit_risk(total_owed, profile)
        bankruptcy_risk = self._assess_bankruptcy_risk(total_owed, profile)
        
        # Calculate overall score (0-100)
        risk_score = self._calculate_overall_score(
            collections_risk, credit_risk, bankruptcy_risk, profile
        )
        
        # Generate factors and recommendations
        factors = self._identify_risk_factors(profile, bills, total_owed)
        mitigations = self._generate_mitigations(factors, profile)
        
        return RiskAssessment(
            overall_risk_level=self._score_to_level(risk_score),
            risk_score=risk_score,
            collections_risk=collections_risk["level"],
            collections_probability=collections_risk["probability"],
            credit_impact_risk=credit_risk,
            bankruptcy_risk=bankruptcy_risk,
            key_risk_factors=factors,
            mitigation_recommendations=mitigations
        )
    
    def _assess_collections_risk(self, bills: list['MedicalBill'],
                                  profile: 'PatientFinancialProfile') -> dict:
        """Assess risk of bills going to collections"""
        probability = 0.1  # Base probability
        
        for bill in bills:
            if bill.status == BillStatus.COLLECTIONS:
                probability = max(probability, 0.95)
            elif bill.days_until_due and bill.days_until_due < 0:
                probability = max(probability, 0.5)
            elif bill.days_until_due and bill.days_until_due < 30:
                probability = max(probability, 0.3)
        
        # Existing collections history increases risk
        if profile.medical_debt_in_collections > 0:
            probability = min(1.0, probability + 0.2)
        
        level = RiskLevel.MINIMAL
        if probability > 0.7:
            level = RiskLevel.SEVERE
        elif probability > 0.5:
            level = RiskLevel.HIGH
        elif probability > 0.3:
            level = RiskLevel.MODERATE
        elif probability > 0.15:
            level = RiskLevel.LOW
        
        return {"level": level, "probability": probability}
    
    def _assess_credit_risk(self, total_owed: Decimal,
                            profile: 'PatientFinancialProfile') -> RiskLevel:
        """Assess risk to credit score"""
        if profile.medical_debt_in_collections > 0:
            return RiskLevel.HIGH
        
        # Large balances relative to income
        monthly_income = profile.total_monthly_net
        if monthly_income > 0:
            months_of_income = total_owed / monthly_income
            if months_of_income > 6:
                return RiskLevel.HIGH
            elif months_of_income > 3:
                return RiskLevel.MODERATE
        
        return RiskLevel.LOW
    
    def _assess_bankruptcy_risk(self, total_owed: Decimal,
                                 profile: 'PatientFinancialProfile') -> RiskLevel:
        """Assess bankruptcy risk"""
        total_debt = (
            total_owed + 
            profile.existing_medical_debt + 
            sum(d.balance for d in profile.debts)
        )
        
        annual_income = profile.annual_gross_income
        if annual_income > 0:
            debt_ratio = total_debt / annual_income
            if debt_ratio > 1.5:
                return RiskLevel.SEVERE
            elif debt_ratio > 1.0:
                return RiskLevel.HIGH
            elif debt_ratio > 0.5:
                return RiskLevel.MODERATE
        
        return RiskLevel.LOW
    
    def _calculate_overall_score(self, collections: dict, credit: RiskLevel,
                                  bankruptcy: RiskLevel, 
                                  profile: 'PatientFinancialProfile') -> int:
        """Calculate overall risk score 0-100"""
        score = 20  # Base
        
        # Collections component (0-30)
        score += int(collections["probability"] * 30)
        
        # Credit component (0-20)
        credit_scores = {
            RiskLevel.SEVERE: 20, RiskLevel.HIGH: 15,
            RiskLevel.MODERATE: 10, RiskLevel.LOW: 5, RiskLevel.MINIMAL: 0
        }
        score += credit_scores.get(credit, 0)
        
        # Bankruptcy component (0-30)
        bankruptcy_scores = {
            RiskLevel.SEVERE: 30, RiskLevel.HIGH: 22,
            RiskLevel.MODERATE: 15, RiskLevel.LOW: 7, RiskLevel.MINIMAL: 0
        }
        score += bankruptcy_scores.get(bankruptcy, 0)
        
        # DTI adjustment (0-20)
        if profile.debt_to_income_ratio > 0.5:
            score += 20
        elif profile.debt_to_income_ratio > 0.4:
            score += 15
        elif profile.debt_to_income_ratio > 0.3:
            score += 10
        
        return min(100, score)
    
    def _score_to_level(self, score: int) -> RiskLevel:
        """Convert numeric score to risk level"""
        if score >= 80:
            return RiskLevel.SEVERE
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MODERATE
        elif score >= 20:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL
    
    def _identify_risk_factors(self, profile: 'PatientFinancialProfile',
                                bills: list['MedicalBill'],
                                total_owed: Decimal) -> list[str]:
        """Identify key risk factors"""
        factors = []
        
        if profile.debt_to_income_ratio > 0.4:
            factors.append("High debt-to-income ratio")
        
        if profile.medical_debt_in_collections > 0:
            factors.append("Existing medical debt in collections")
        
        past_due = [b for b in bills if b.days_until_due and b.days_until_due < 0]
        if past_due:
            factors.append(f"{len(past_due)} bills are past due")
        
        if profile.available_monthly_budget < total_owed * Decimal("0.05"):
            factors.append("Limited monthly budget for debt repayment")
        
        if total_owed > profile.annual_gross_income * Decimal("0.25"):
            factors.append("Medical debt exceeds 25% of annual income")
        
        return factors
    
    def _generate_mitigations(self, factors: list[str],
                               profile: 'PatientFinancialProfile') -> list[str]:
        """Generate mitigation recommendations"""
        mitigations = []
        
        if profile.federal_poverty_level_percentage < 400:
            mitigations.append("Apply for hospital charity care programs")
        
        if profile.debt_to_income_ratio > 0.3:
            mitigations.append("Request extended payment plans to reduce monthly burden")
        
        mitigations.append("Negotiate bill reductions before agreeing to payment plans")
        mitigations.append("Keep detailed records of all communications")
        
        return mitigations