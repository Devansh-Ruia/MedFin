"""
MedFin Financial Navigation System - Complete Runnable Application
Save this as: medfin_app.py
Run with: uvicorn medfin_app:app --reload
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
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
# ENUMERATIONS
# ============================================================================

class BillStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    DISPUTED = "disputed"
    PAYMENT_PLAN = "payment_plan"
    PAID = "paid"
    COLLECTIONS = "collections"

class BillErrorType(str, Enum):
    DUPLICATE_CHARGE = "duplicate_charge"
    UNBUNDLING = "unbundling"
    UPCODING = "upcoding"
    BALANCE_BILLING = "balance_billing"

class InsuranceType(str, Enum):
    EMPLOYER = "employer"
    MARKETPLACE = "marketplace"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
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

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RiskLevel(str, Enum):
    SEVERE = "severe"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"

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
# DATA MODELS
# ============================================================================

class LineItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    cpt_code: Optional[str] = None
    description: str = "Service"
    service_date: date
    billed_amount: Decimal
    allowed_amount: Optional[Decimal] = None
    insurance_paid: Decimal = Decimal("0")
    patient_responsibility: Decimal = Decimal("0")

class MedicalBill(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    provider_name: str
    provider_type: str = "hospital"
    facility_type: Optional[str] = None
    statement_date: date
    service_date_start: date
    service_date_end: date
    line_items: list[LineItem] = Field(default_factory=list)
    total_billed: Decimal
    insurance_paid: Decimal = Decimal("0")
    patient_balance: Decimal
    status: BillStatus = BillStatus.PENDING
    due_date: Optional[date] = None
    is_in_network: Optional[bool] = None

    @property
    def days_until_due(self) -> Optional[int]:
        return (self.due_date - date.today()).days if self.due_date else None

class InsurancePlan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    plan_name: str
    insurance_type: InsuranceType
    carrier_name: str
    policy_number: str = ""
    individual_deductible: Decimal
    individual_deductible_met: Decimal = Decimal("0")
    individual_oop_max: Decimal
    individual_oop_met: Decimal = Decimal("0")
    coinsurance_rate: float = 0.2
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
        return float(self.individual_oop_met / self.individual_oop_max) if self.individual_oop_max else 1.0

class PatientFinancialProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    household_size: int = 1
    state: str
    zip_code: str
    total_monthly_gross: Decimal = Decimal("0")
    total_monthly_net: Decimal = Decimal("0")
    annual_gross_income: Decimal = Decimal("0")
    total_monthly_debt_payments: Decimal = Decimal("0")
    existing_medical_debt: Decimal = Decimal("0")
    medical_debt_in_collections: Decimal = Decimal("0")
    checking_balance: Decimal = Decimal("0")
    savings_balance: Decimal = Decimal("0")

    @property
    def debt_to_income_ratio(self) -> float:
        return float(self.total_monthly_debt_payments / self.total_monthly_gross) if self.total_monthly_gross else 0.0
    
    @property
    def federal_poverty_level_percentage(self) -> float:
        fpl = 15060 + (self.household_size - 1) * 5380
        return float(self.annual_gross_income / Decimal(str(fpl))) * 100
    
    @property
    def available_monthly_budget(self) -> Decimal:
        return self.total_monthly_net - self.total_monthly_debt_payments

class SavingsEstimate(BaseModel):
    minimum: Decimal
    expected: Decimal
    maximum: Decimal
    confidence: float

class ActionStep(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    step_number: int
    action_type: ActionType
    priority: Priority
    title: str
    description: str
    target_provider: Optional[str] = None
    estimated_effort_minutes: int
    deadline: Optional[date] = None
    savings_estimate: SavingsEstimate
    approval_likelihood: float
    detailed_steps: list[str]
    required_documents: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class RiskAssessment(BaseModel):
    overall_risk_level: RiskLevel
    risk_score: int
    collections_risk: RiskLevel
    collections_probability: float
    credit_impact_risk: RiskLevel
    bankruptcy_risk: RiskLevel
    key_risk_factors: list[str]
    mitigation_recommendations: list[str]

class BudgetImpact(BaseModel):
    current_medical_payment_burden: Decimal
    projected_after_plan: Decimal
    monthly_savings: Decimal
    recommended_monthly_payment: Decimal

class NavigationPlan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: date
    total_bills_analyzed: int
    total_amount_owed: Decimal
    potential_total_savings: SavingsEstimate
    action_steps: list[ActionStep]
    critical_actions_count: int
    risk_assessment: RiskAssessment
    budget_impact: BudgetImpact
    executive_summary: str
    confidence_score: float

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
            collections_risk=coll["level"], collections_probability=coll["prob"],
            credit_impact_risk=credit, bankruptcy_risk=bankrupt,
            key_risk_factors=self._factors(profile, bills, total),
            mitigation_recommendations=["Apply for charity care", "Negotiate before payment plans"]
        )
    
    def _collections_risk(self, bills: list[MedicalBill], profile: PatientFinancialProfile) -> dict:
        prob = 0.1
        for b in bills:
            if b.status == BillStatus.COLLECTIONS: prob = max(prob, 0.95)
            elif b.days_until_due and b.days_until_due < 0: prob = max(prob, 0.5)
        if profile.medical_debt_in_collections > 0: prob = min(1.0, prob + 0.2)
        level = RiskLevel.SEVERE if prob > 0.7 else RiskLevel.HIGH if prob > 0.5 else RiskLevel.MODERATE if prob > 0.3 else RiskLevel.LOW
        return {"level": level, "prob": prob}
    
    def _credit_risk(self, total: Decimal, profile: PatientFinancialProfile) -> RiskLevel:
        if profile.medical_debt_in_collections > 0: return RiskLevel.HIGH
        if profile.total_monthly_net > 0:
            months = total / profile.total_monthly_net
            if months > 6: return RiskLevel.HIGH
            if months > 3: return RiskLevel.MODERATE
        return RiskLevel.LOW
    
    def _bankruptcy_risk(self, total: Decimal, profile: PatientFinancialProfile) -> RiskLevel:
        if profile.annual_gross_income > 0:
            ratio = (total + profile.existing_medical_debt) / profile.annual_gross_income
            if ratio > 1.5: return RiskLevel.SEVERE
            if ratio > 1.0: return RiskLevel.HIGH
            if ratio > 0.5: return RiskLevel.MODERATE
        return RiskLevel.LOW
    
    def _calc_score(self, coll: dict, credit: RiskLevel, bankrupt: RiskLevel, profile: PatientFinancialProfile) -> int:
        score = 20 + int(coll["prob"] * 30)
        score += {RiskLevel.SEVERE: 20, RiskLevel.HIGH: 15, RiskLevel.MODERATE: 10, RiskLevel.LOW: 5}.get(credit, 0)
        score += {RiskLevel.SEVERE: 30, RiskLevel.HIGH: 22, RiskLevel.MODERATE: 15, RiskLevel.LOW: 7}.get(bankrupt, 0)
        if profile.debt_to_income_ratio > 0.4: score += 15
        return min(100, score)
    
    def _to_level(self, score: int) -> RiskLevel:
        if score >= 80: return RiskLevel.SEVERE
        if score >= 60: return RiskLevel.HIGH
        if score >= 40: return RiskLevel.MODERATE
        if score >= 20: return RiskLevel.LOW
        return RiskLevel.MINIMAL
    
    def _factors(self, profile: PatientFinancialProfile, bills: list[MedicalBill], total: Decimal) -> list[str]:
        factors = []
        if profile.debt_to_income_ratio > 0.4: factors.append("High debt-to-income ratio")
        if profile.medical_debt_in_collections > 0: factors.append("Existing debt in collections")
        past_due = [b for b in bills if b.days_until_due and b.days_until_due < 0]
        if past_due: factors.append(f"{len(past_due)} bills past due")
        return factors

# ============================================================================
# PLAN GENERATOR
# ============================================================================

class PlanGenerator:
    def generate(self, bills: list[MedicalBill], insurance: Optional[InsurancePlan],
                 profile: PatientFinancialProfile, bill_analyses: list[BillAnalysisResult],
                 risk: RiskAssessment) -> NavigationPlan:
        
        actions = []
        step_num = 1
        
        for bill, analysis in zip(bills, bill_analyses):
            # Duplicate disputes
            if analysis.duplicate_charges:
                dup_amt = sum(Decimal(str(d["amount"])) for d in analysis.duplicate_charges)
                actions.append(self._create_step(
                    step_num, ActionType.DISPUTE_BILL, Priority.CRITICAL,
                    "Dispute Duplicate Charges", "Challenge duplicate charges on bill",
                    bill.provider_name, 30, bill.due_date,
                    SavingsEstimate(minimum=dup_amt*Decimal("0.8"), expected=dup_amt*Decimal("0.95"), maximum=dup_amt, confidence=0.9),
                    ["Call billing department", "Reference specific duplicate line items", "Request written confirmation"],
                    ["itemized_bill", "eob"], ["Dispute before paying"]
                ))
                step_num += 1
            
            # Unbundling errors
            if analysis.errors_found:
                err_amt = sum(Decimal(str(e["amount"])) for e in analysis.errors_found)
                actions.append(self._create_step(
                    step_num, ActionType.DISPUTE_BILL, Priority.HIGH,
                    "Dispute Billing Errors", "Challenge unbundling/coding errors",
                    bill.provider_name, 45, bill.due_date,
                    SavingsEstimate(minimum=err_amt*Decimal("0.6"), expected=err_amt*Decimal("0.85"), maximum=err_amt, confidence=0.75),
                    ["Write formal dispute letter", "Cite CPT bundling rules", "Send certified mail"],
                    ["itemized_bill", "eob", "medical_records"], []
                ))
                step_num += 1
            
            # Verify insurance claim
            if insurance and bill.insurance_paid == 0 and bill.total_billed > Decimal("200"):
                actions.append(self._create_step(
                    step_num, ActionType.VERIFY_INSURANCE_CLAIM, Priority.HIGH,
                    "Verify Insurance Claim", "Ensure claim was submitted to insurance",
                    bill.provider_name, 20, bill.due_date,
                    SavingsEstimate(minimum=Decimal("0"), expected=bill.patient_balance*Decimal("0.6"), maximum=bill.patient_balance*Decimal("0.9"), confidence=0.5),
                    ["Call insurance to check claim status", "Contact provider if not submitted", "Get confirmation"],
                    ["insurance_card"], []
                ))
                step_num += 1
            
            # Charity care
            if profile.federal_poverty_level_percentage < 400 and bill.provider_type == "hospital" and bill.patient_balance > Decimal("1000"):
                fpl = profile.federal_poverty_level_percentage
                discount = Decimal("1.0") if fpl < 200 else Decimal("0.75") if fpl < 300 else Decimal("0.50")
                actions.append(self._create_step(
                    step_num, ActionType.REQUEST_CHARITY_CARE, Priority.HIGH,
                    "Apply for Hospital Charity Care", f"You qualify at {fpl:.0f}% FPL",
                    bill.provider_name, 60, None,
                    SavingsEstimate(minimum=bill.patient_balance*discount*Decimal("0.5"), expected=bill.patient_balance*discount, maximum=bill.patient_balance, confidence=0.7 if fpl < 300 else 0.5),
                    ["Request financial assistance application", "Gather income docs", "Submit before paying"],
                    ["proof_of_income", "tax_return", "bank_statements"], ["Apply before making payments"]
                ))
                step_num += 1
            
            # Negotiate
            if bill.patient_balance > Decimal("300"):
                actions.append(self._create_step(
                    step_num, ActionType.NEGOTIATE_BILL, Priority.MEDIUM,
                    "Negotiate Bill Reduction", "Request prompt-pay or hardship discount",
                    bill.provider_name, 20, None,
                    SavingsEstimate(minimum=bill.patient_balance*Decimal("0.10"), expected=bill.patient_balance*Decimal("0.25"), maximum=bill.patient_balance*Decimal("0.40"), confidence=0.6),
                    ["Research fair prices", "Ask for hardship discount", "Offer lump sum for bigger discount"],
                    [], []
                ))
                step_num += 1
            
            # Payment plan
            if bill.patient_balance > profile.available_monthly_budget * 2:
                actions.append(self._create_step(
                    step_num, ActionType.SETUP_PAYMENT_PLAN, Priority.MEDIUM,
                    "Setup Payment Plan", "Establish manageable monthly payments",
                    bill.provider_name, 20, None,
                    SavingsEstimate(minimum=Decimal("0"), expected=Decimal("0"), maximum=Decimal("0"), confidence=0.95),
                    ["Calculate affordable payment", "Request 0% interest plan", "Get terms in writing"],
                    [], ["Complete negotiations first"]
                ))
                step_num += 1
        
        # Sort by priority
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        actions.sort(key=lambda x: priority_order.get(x.priority, 99))
        for i, a in enumerate(actions, 1):
            a.step_number = i
        
        total_owed = sum(b.patient_balance for b in bills)
        total_savings = SavingsEstimate(
            minimum=sum(a.savings_estimate.minimum for a in actions),
            expected=sum(a.savings_estimate.expected for a in actions),
            maximum=sum(a.savings_estimate.maximum for a in actions),
            confidence=sum(a.savings_estimate.confidence for a in actions) / len(actions) if actions else 0.5
        )
        
        monthly_current = total_owed / 12
        monthly_projected = (total_owed - total_savings.expected) / 12
        
        return NavigationPlan(
            patient_id=profile.patient_id,
            valid_until=date.today() + timedelta(days=30),
            total_bills_analyzed=len(bills),
            total_amount_owed=total_owed,
            potential_total_savings=total_savings,
            action_steps=actions,
            critical_actions_count=sum(1 for a in actions if a.priority == Priority.CRITICAL),
            risk_assessment=risk,
            budget_impact=BudgetImpact(
                current_medical_payment_burden=monthly_current,
                projected_after_plan=monthly_projected,
                monthly_savings=monthly_current - monthly_projected,
                recommended_monthly_payment=min(monthly_projected, profile.available_monthly_budget * Decimal("0.1"))
            ),
            executive_summary=f"Analyzed {len(bills)} bill(s) totaling ${total_owed:,.2f}. Found {len(actions)} actions with ${total_savings.expected:,.2f} expected savings.",
            confidence_score=total_savings.confidence
        )
    
    def _create_step(self, num, action_type, priority, title, desc, provider, effort, deadline, savings, steps, docs, warnings) -> ActionStep:
        return ActionStep(
            step_number=num, action_type=action_type, priority=priority,
            title=title, description=desc, target_provider=provider,
            estimated_effort_minutes=effort, deadline=deadline,
            savings_estimate=savings, approval_likelihood=savings.confidence,
            detailed_steps=steps, required_documents=docs, warnings=warnings
        )

# ============================================================================
# API MODELS
# ============================================================================

class BillInput(BaseModel):
    provider_name: str
    provider_type: str = "hospital"
    statement_date: date
    service_date_start: date
    service_date_end: date
    total_billed: Decimal
    insurance_paid: Decimal = Decimal("0")
    patient_balance: Decimal
    status: str = "pending"
    due_date: Optional[date] = None
    is_in_network: Optional[bool] = None
    line_items: list[dict] = Field(default_factory=list)

class InsuranceInput(BaseModel):
    plan_name: str
    insurance_type: str
    carrier_name: str
    individual_deductible: Decimal
    individual_deductible_met: Decimal = Decimal("0")
    individual_oop_max: Decimal
    individual_oop_met: Decimal = Decimal("0")
    coinsurance_rate: float = 0.2
    plan_year_start: date
    plan_year_end: date

class ProfileInput(BaseModel):
    household_size: int = 1
    state: str
    zip_code: str
    annual_gross_income: Decimal
    monthly_net_income: Decimal
    monthly_debt_payments: Decimal = Decimal("0")
    existing_medical_debt: Decimal = Decimal("0")

class PlanRequest(BaseModel):
    patient_id: str
    bills: list[BillInput]
    insurance: Optional[InsuranceInput] = None
    financial_profile: ProfileInput

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="MedFin Navigation API", version="1.0.0")

bill_analyzer = BillAnalyzer()
risk_analyzer = RiskAnalyzer()
plan_generator = PlanGenerator()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "medfin"}

@app.post("/api/v1/navigation-plans")
async def create_plan(request: PlanRequest):
    # Convert inputs
    bills = []
    for b in request.bills:
        items = [LineItem(cpt_code=li.get("cpt_code"), description=li.get("description", "Service"),
                         service_date=li.get("service_date", b.service_date_start),
                         billed_amount=Decimal(str(li.get("billed_amount", 0))),
                         patient_responsibility=Decimal(str(li.get("patient_responsibility", 0))))
                for li in b.line_items]
        bills.append(MedicalBill(
            provider_name=b.provider_name, provider_type=b.provider_type,
            statement_date=b.statement_date, service_date_start=b.service_date_start,
            service_date_end=b.service_date_end, line_items=items,
            total_billed=b.total_billed, insurance_paid=b.insurance_paid,
            patient_balance=b.patient_balance, status=BillStatus(b.status),
            due_date=b.due_date or date.today() + timedelta(days=30), is_in_network=b.is_in_network
        ))
    
    insurance = None
    if request.insurance:
        i = request.insurance
        insurance = InsurancePlan(
            plan_name=i.plan_name, insurance_type=InsuranceType(i.insurance_type),
            carrier_name=i.carrier_name, individual_deductible=i.individual_deductible,
            individual_deductible_met=i.individual_deductible_met,
            individual_oop_max=i.individual_oop_max, individual_oop_met=i.individual_oop_met,
            coinsurance_rate=i.coinsurance_rate, plan_year_start=i.plan_year_start,
            plan_year_end=i.plan_year_end
        )
    
    p = request.financial_profile
    profile = PatientFinancialProfile(
        patient_id=request.patient_id, household_size=p.household_size,
        state=p.state, zip_code=p.zip_code,
        annual_gross_income=p.annual_gross_income,
        total_monthly_net=p.monthly_net_income,
        total_monthly_gross=p.annual_gross_income / 12,
        total_monthly_debt_payments=p.monthly_debt_payments,
        existing_medical_debt=p.existing_medical_debt
    )
    
    # Run analysis
    analyses = [bill_analyzer.analyze(bill, insurance) for bill in bills]
    risk = risk_analyzer.analyze(profile, bills)
    plan = plan_generator.generate(bills, insurance, profile, analyses, risk)
    
    return plan.model_dump(mode="json")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)