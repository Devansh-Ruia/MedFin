"""
MedFin Financial Navigation System - Complete Runnable Application
Save this as: medfin_app.py
Run with: uvicorn medfin_app:app --reload
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Callable
from uuid import UUID, uuid4
from dataclasses import dataclass, field
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fn_data_models import *  # Import all centralized data models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# ANALYSIS RESULTS
# ============================================================================

@dataclass
class BillAnalysisResult:
    bill_id: str
    errors_found: list[dict]
    duplicate_charges: list[dict]
    overcharge_amount: Decimal
    negotiation_potential: Decimal
    urgency_score: int

# ============================================================================
# BILL ANALYZER
# ============================================================================

class BillAnalyzer:
    BUNDLED_CODES = {"43239": ["43235"], "29881": ["29880"], "99213": ["99211", "99212"]}
    
    def analyze(self, bill: MedicalBill, insurance: Optional[InsurancePlan] = None) -> BillAnalysisResult:
        duplicates, dup_amount = self._detect_duplicates(bill)
        errors, err_amount = self._detect_unbundling(bill)
        negotiation = self._estimate_negotiation(bill, insurance)
        urgency = self._calc_urgency(bill)
        
        return BillAnalysisResult(
            bill_id=str(bill.id), errors_found=errors, duplicate_charges=duplicates,
            overcharge_amount=dup_amount + err_amount, negotiation_potential=negotiation,
            urgency_score=urgency
        )
    
    def _detect_duplicates(self, bill: MedicalBill) -> tuple[list, Decimal]:
        seen, dups, amt = {}, [], Decimal("0")
        for item in bill.line_items:
            key = (item.cpt_code, item.service_date, item.billed_amount)
            if key in seen:
                dups.append({"type": "duplicate", "amount": item.billed_amount, "cpt": item.cpt_code})
                amt += item.billed_amount
            else:
                seen[key] = item.id
        return dups, amt
    
    def _detect_unbundling(self, bill: MedicalBill) -> tuple[list, Decimal]:
        codes = {li.cpt_code for li in bill.line_items if li.cpt_code}
        errors, amt = [], Decimal("0")
        for parent, children in self.BUNDLED_CODES.items():
            if parent in codes:
                for child in children:
                    if child in codes:
                        item = next((li for li in bill.line_items if li.cpt_code == child), None)
                        if item:
                            errors.append({"type": "unbundling", "parent": parent, "child": child, "amount": item.billed_amount})
                            amt += item.billed_amount
        return errors, amt
    
    def _estimate_negotiation(self, bill: MedicalBill, ins: Optional[InsurancePlan]) -> Decimal:
        if not ins: return bill.patient_balance * Decimal("0.50")
        return bill.patient_balance * Decimal("0.15" if bill.is_in_network else "0.30")
    
    def _calc_urgency(self, bill: MedicalBill) -> int:
        score = 50
        if bill.days_until_due:
            if bill.days_until_due < 0: score += 30
            elif bill.days_until_due < 14: score += 20
        if bill.status == BillStatus.COLLECTIONS: score += 25
        return min(100, score)

# ============================================================================
# RISK ANALYZER
# ============================================================================

class RiskAnalyzer:
    def analyze(self, profile: PatientFinancialProfile, bills: list[MedicalBill]) -> RiskAssessment:
        total = sum(b.patient_balance for b in bills)
        coll = self._collections_risk(bills, profile)
        credit = self._credit_risk(total, profile)
        bankrupt = self._bankruptcy_risk(total, profile)
        score = self._calc_score(coll, credit, bankrupt, profile)
        
        return RiskAssessment(
            overall_risk_level=self._to_level(score), risk_score=score,
            collections_risk=coll, collections_probability=self._to_prob(coll),
            credit_impact_risk=credit, bankruptcy_risk=bankrupt,
            key_risk_factors=self._risk_factors(profile, total),
            mitigation_recommendations=self._mitigations(profile, total)
        )
    
    def _collections_risk(self, bills: list[MedicalBill], profile: PatientFinancialProfile) -> RiskLevel:
        overdue = sum(b.patient_balance for b in bills if b.status == BillStatus.COLLECTIONS)
        if overdue > profile.annual_gross_income * Decimal("0.1"): return RiskLevel.SEVERE
        if overdue > Decimal("5000"): return RiskLevel.HIGH
        if overdue > Decimal("1000"): return RiskLevel.MODERATE
        return RiskLevel.LOW
    
    def _credit_risk(self, total_owed: Decimal, profile: PatientFinancialProfile) -> RiskLevel:
        dti = profile.debt_to_income_ratio
        if dti > 0.5: return RiskLevel.SEVERE
        if dti > 0.4: return RiskLevel.HIGH
        if dti > 0.3: return RiskLevel.MODERATE
        return RiskLevel.LOW
    
    def _bankruptcy_risk(self, total_owed: Decimal, profile: PatientFinancialProfile) -> RiskLevel:
        if total_owed > profile.annual_gross_income: return RiskLevel.SEVERE
        if total_owed > profile.annual_gross_income * Decimal("0.5"): return RiskLevel.HIGH
        return RiskLevel.MODERATE
    
    def _calc_score(self, coll: RiskLevel, credit: RiskLevel, bankrupt: RiskLevel, profile: PatientFinancialProfile) -> int:
        score = 50
        if coll == RiskLevel.SEVERE: score += 25
        elif coll == RiskLevel.HIGH: score += 15
        elif coll == RiskLevel.MODERATE: score += 8
        
        if credit == RiskLevel.SEVERE: score += 20
        elif credit == RiskLevel.HIGH: score += 12
        elif credit == RiskLevel.MODERATE: score += 6
        
        if bankrupt == RiskLevel.SEVERE: score += 15
        elif bankrupt == RiskLevel.HIGH: score += 8
        
        return min(100, score)
    
    def _to_level(self, score: int) -> RiskLevel:
        if score >= 80: return RiskLevel.SEVERE
        if score >= 60: return RiskLevel.HIGH
        if score >= 40: return RiskLevel.MODERATE
        return RiskLevel.LOW
    
    def _to_prob(self, level: RiskLevel) -> float:
        mapping = {RiskLevel.SEVERE: 0.8, RiskLevel.HIGH: 0.6, RiskLevel.MODERATE: 0.3, RiskLevel.LOW: 0.1}
        return mapping.get(level, 0.1)
    
    def _risk_factors(self, profile: PatientFinancialProfile, total: Decimal) -> list[str]:
        factors = []
        if profile.debt_to_income_ratio > 0.4: factors.append("High debt-to-income ratio")
        if profile.federal_poverty_level_percentage < 200: factors.append("Low income relative to FPL")
        if total > profile.annual_gross_income * Decimal("0.3"): factors.append("High medical debt burden")
        if profile.medical_debt_in_collections > 0: factors.append("Medical debt in collections")
        return factors
    
    def _mitigations(self, profile: PatientFinancialProfile, total: Decimal) -> list[str]:
        mitigations = []
        if profile.federal_poverty_level_percentage < 200:
            mitigations.append("Apply for financial assistance programs")
        if total > Decimal("5000"):
            mitigations.append("Consider medical debt consolidation")
        if profile.debt_to_income_ratio > 0.4:
            mitigations.append("Review budget and reduce non-essential expenses")
        return mitigations

# ============================================================================
# PLAN GENERATOR
# ============================================================================

class PlanGenerator:
    def __init__(self):
        self.bill_analyzer = BillAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
    
    def generate_plan(self, profile: PatientFinancialProfile, bills: list[MedicalBill], 
                   insurance: Optional[InsurancePlan] = None) -> NavigationPlan:
        # Analyze each bill
        bill_results = [self.bill_analyzer.analyze(bill, insurance) for bill in bills]
        
        # Risk assessment
        risk = self.risk_analyzer.analyze(profile, bills)
        
        # Generate action steps
        actions = self._generate_actions(bill_results, profile, risk)
        
        # Calculate budget impact
        budget_impact = self._calc_budget_impact(profile, bills, actions)
        
        # Calculate savings
        total_savings = sum(br.negotiation_potential for br in bill_results)
        savings = SavingsEstimate(
            minimum=total_savings * Decimal("0.3"),
            expected=total_savings * Decimal("0.5"),
            maximum=total_savings * Decimal("0.8"),
            confidence=0.7
        )
        
        # Create navigation plan
        plan = NavigationPlan(
            patient_id=profile.patient_id,
            generated_at=datetime.utcnow(),
            valid_until=date.today() + timedelta(days=90),
            total_bills_analyzed=len(bills),
            total_amount_owed=sum(b.patient_balance for b in bills),
            potential_total_savings=savings,
            action_steps=actions,
            critical_actions_count=sum(1 for a in actions if a.priority == Priority.CRITICAL),
            risk_assessment=risk,
            budget_impact=budget_impact,
            executive_summary=self._generate_summary(profile, bills, risk, savings),
            confidence_score=0.8
        )
        
        return plan
    
    def _generate_actions(self, bill_results: list[BillAnalysisResult], 
                       profile: PatientFinancialProfile, risk: RiskAssessment) -> list[ActionStep]:
        actions = []
        step_num = 1
        
        # Bill dispute actions
        for br in bill_results:
            if br.overcharge_amount > Decimal("100"):
                actions.append(ActionStep(
                    step_number=step_num,
                    action_type=ActionType.DISPUTE_BILL,
                    priority=Priority.HIGH,
                    title=f"Dispute Bill {br.bill_id}",
                    description=f"Potential overcharges of ${br.overcharge_amount} detected",
                    estimated_effort_minutes=120,
                    deadline=date.today() + timedelta(days=30),
                    recommended_start=date.today(),
                    savings_estimate=SavingsEstimate(
                        minimum=br.overcharge_amount * Decimal("0.3"),
                        expected=br.overcharge_amount * Decimal("0.6"),
                        maximum=br.overcharge_amount,
                        confidence=0.8
                    ),
                    approval_likelihood=0.7,
                    detailed_steps=[
                        "Gather all documentation for the bill",
                        "Review each line item for accuracy",
                        "Contact provider billing department",
                        "File formal dispute if necessary"
                    ]
                ))
                step_num += 1
        
        # Assistance application actions
        if profile.federal_poverty_level_percentage < 250:
            actions.append(ActionStep(
                step_number=step_num,
                action_type=ActionType.APPLY_ASSISTANCE,
                priority=Priority.HIGH,
                title="Apply for Financial Assistance",
                description="Eligible for financial assistance programs",
                estimated_effort_minutes=180,
                deadline=date.today() + timedelta(days=60),
                recommended_start=date.today(),
                savings_estimate=SavingsEstimate(
                    minimum=Decimal("1000"),
                    expected=Decimal("2500"),
                    maximum=Decimal("5000"),
                    confidence=0.6
                ),
                approval_likelihood=0.8,
                detailed_steps=[
                    "Research hospital charity care programs",
                    "Complete application forms",
                    "Gather income documentation",
                    "Submit applications to multiple programs"
                ]
            ))
        
        return actions
    
    def _calc_budget_impact(self, profile: PatientFinancialProfile, 
                          bills: list[MedicalBill], actions: list[ActionStep]) -> BudgetImpact:
        current_monthly = sum(b.patient_balance / 12 for b in bills if b.patient_balance > 0)
        projected_monthly = current_monthly * Decimal("0.7")  # Assume 30% reduction
        
        return BudgetImpact(
            current_medical_payment_burden=current_monthly,
            projected_after_plan=projected_monthly,
            monthly_savings=current_monthly - projected_monthly,
            recommended_monthly_payment=projected_monthly
        )
    
    def _generate_summary(self, profile: PatientFinancialProfile, bills: list[MedicalBill],
                       risk: RiskAssessment, savings: SavingsEstimate) -> str:
        total_owed = sum(b.patient_balance for b in bills)
        return f"""
        Patient {profile.patient_id} has ${total_owed:,.2f} in medical debt across {len(bills)} bills.
        Risk assessment shows {risk.overall_risk_level.value} risk level with a score of {risk.risk_score}/100.
        Estimated potential savings of ${savings.expected:,.2f} through bill disputes and assistance programs.
        Key risk factors: {', '.join(risk.key_risk_factors[:3])}.
        Recommended actions focus on reducing debt burden and preventing collections.
        """

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(title="MedFin Financial Navigation System", version="1.0.0")

# Global instances
plan_generator = PlanGenerator()

@app.get("/")
async def root():
    return {"message": "MedFin Financial Navigation System API"}

@app.post("/generate-plan")
async def generate_navigation_plan(
    profile: PatientFinancialProfile,
    bills: list[MedicalBill],
    insurance: Optional[InsurancePlan] = None
):
    try:
        plan = plan_generator.generate_plan(profile, bills, insurance)
        return {"success": True, "plan": plan}
    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
