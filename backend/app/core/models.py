from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class InsuranceType(str, Enum):
    PRIVATE = "private"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    TRICARE = "tricare"
    NONE = "none"


class ServiceType(str, Enum):
    PRIMARY_CARE = "primary_care"
    SPECIALIST = "specialist"
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    IMAGING = "imaging"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    HOSPITALIZATION = "hospitalization"
    MENTAL_HEALTH = "mental_health"
    PREVENTIVE = "preventive"


class CostEstimationRequest(BaseModel):
    service_type: ServiceType
    procedure_code: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    insurance_type: Optional[InsuranceType] = None
    has_insurance: bool = True
    deductible_remaining: Optional[float] = 0.0
    copay: Optional[float] = None


class CostEstimationResponse(BaseModel):
    estimated_cost: float
    insurance_coverage: Optional[float] = None
    patient_responsibility: float
    breakdown: Dict[str, Any]
    confidence_score: float
    alternatives: Optional[List[Dict[str, Any]]] = None


class InsuranceInfo(BaseModel):
    insurance_type: InsuranceType
    plan_name: Optional[str] = None
    deductible: float = 0.0
    deductible_remaining: float = 0.0
    out_of_pocket_max: float = 0.0
    out_of_pocket_used: float = 0.0
    coverage_percentage: float = 0.80
    copay_primary: Optional[float] = None
    copay_specialist: Optional[float] = None
    copay_emergency: Optional[float] = None
    in_network: bool = True


class MedicalBill(BaseModel):
    bill_id: str
    provider_name: str
    service_date: str
    services: List[Dict[str, Any]]
    total_amount: float
    insurance_paid: Optional[float] = None
    patient_responsibility: float
    due_date: Optional[str] = None
    status: str = "pending"


class BillAnalysisRequest(BaseModel):
    bills: List[MedicalBill]
    insurance_info: Optional[InsuranceInfo] = None
    annual_income: Optional[float] = None
    household_size: Optional[int] = None


class NavigationAction(BaseModel):
    action_type: str
    priority: int
    description: str
    estimated_savings: Optional[float] = None
    deadline: Optional[str] = None
    resources: List[str] = []


class NavigationPlan(BaseModel):
    user_id: Optional[str] = None
    current_financial_situation: Dict[str, Any]
    recommended_actions: List[NavigationAction]
    timeline: Dict[str, Any]
    projected_savings: float
    risk_assessment: Dict[str, Any]
    created_at: str


class AssistanceProgram(BaseModel):
    program_name: str
    organization: str
    eligibility_criteria: Dict[str, Any]
    assistance_type: str  # financial, pharmaceutical, utility, etc.
    application_deadline: Optional[str] = None
    estimated_benefit: Optional[float] = None
    match_score: float
    application_url: Optional[str] = None


class PaymentPlanOption(BaseModel):
    plan_type: str
    monthly_payment: float
    total_payments: int
    total_cost: float
    interest_rate: float = 0.0
    eligibility: bool = True
    pros: List[str] = []
    cons: List[str] = []


class PaymentPlanRequest(BaseModel):
    total_debt: float
    monthly_income: float
    monthly_expenses: float
    preferences: Optional[Dict[str, Any]] = None



