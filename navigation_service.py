"""
MedFin Financial Navigation System - Main Service & FastAPI
Orchestration layer and REST API endpoints
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Import internal modules (from previous artifacts)
# from .data_models import *
# from .analysis_engines import *
# from .decision_engine import *

logger = logging.getLogger(__name__)


# ============================================================================
# SERVICE LAYER
# ============================================================================

class NavigationService:
    """Main orchestration service for financial navigation"""
    
    def __init__(self, 
                 assistance_db: 'AssistanceProgramDB',
                 cache: Optional['CacheService'] = None):
        self.assistance_db = assistance_db
        self.cache = cache
        
        # Initialize analyzers
        self.bill_analyzer = BillAnalyzer()
        self.insurance_analyzer = InsuranceAnalyzer()
        self.eligibility_analyzer = EligibilityAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        
        # Initialize plan generator
        self.plan_generator = PlanGenerator()
    
    async def generate_navigation_plan(
        self,
        patient_id: str,
        bills: list['MedicalBill'],
        insurance: Optional['InsurancePlan'],
        profile: 'PatientFinancialProfile'
    ) -> 'NavigationPlan':
        """Generate complete financial navigation plan"""
        
        logger.info(f"Generating navigation plan for patient {patient_id}")
        
        # Step 1: Validate and enrich input data
        bills = self._validate_bills(bills)
        profile = self._enrich_profile(profile)
        
        # Step 2: Analyze each bill
        bill_analyses = []
        for bill in bills:
            analysis = self.bill_analyzer.analyze(bill, insurance)
            bill_analyses.append(analysis)
        
        # Step 3: Analyze insurance coverage
        insurance_analysis = None
        if insurance:
            insurance_analysis = self.insurance_analyzer.analyze(
                insurance, bills
            )
        
        # Step 4: Match assistance programs
        programs = await self.assistance_db.get_programs_for_state(profile.state)
        eligibility_matches = self.eligibility_analyzer.analyze(
            profile, bills, programs
        )
        
        # Step 5: Assess financial risk
        risk_assessment = self.risk_analyzer.analyze(profile, bills)
        
        # Step 6: Generate navigation plan
        plan = self.plan_generator.generate(
            bills=bills,
            insurance=insurance,
            profile=profile,
            bill_analyses=bill_analyses,
            insurance_analysis=insurance_analysis,
            eligibility_matches=eligibility_matches,
            risk_assessment=risk_assessment
        )
        
        # Step 7: Cache plan (if cache available)
        if self.cache:
            await self.cache.set(
                f"plan:{patient_id}:{plan.id}",
                plan.model_dump_json(),
                ttl=86400  # 24 hours
            )
        
        logger.info(f"Generated plan {plan.id} with {len(plan.action_steps)} actions")
        return plan
    
    def _validate_bills(self, bills: list['MedicalBill']) -> list['MedicalBill']:
        """Validate and clean bill data"""
        validated = []
        for bill in bills:
            # Ensure minimum required fields
            if bill.patient_balance <= 0:
                continue  # Skip paid bills
            
            # Set defaults for missing dates
            if not bill.due_date:
                bill.due_date = date.today() + timedelta(days=30)
            
            validated.append(bill)
        
        return validated
    
    def _enrich_profile(self, profile: 'PatientFinancialProfile') -> 'PatientFinancialProfile':
        """Enrich profile with computed fields"""
        # Calculate totals if not provided
        if not profile.total_monthly_gross and profile.income_sources:
            profile.total_monthly_gross = sum(
                src.gross_monthly for src in profile.income_sources
            )
            profile.total_monthly_net = sum(
                src.net_monthly for src in profile.income_sources
            )
            profile.annual_gross_income = profile.total_monthly_gross * 12
        
        if not profile.total_monthly_debt_payments and profile.debts:
            profile.total_monthly_debt_payments = sum(
                d.monthly_payment for d in profile.debts
            )
        
        return profile
    
    async def update_plan_status(
        self,
        plan_id: UUID,
        step_id: UUID,
        status: str,
        outcome: Optional[dict] = None
    ) -> dict:
        """Update status of an action step"""
        # In production, this would update the database
        return {
            "plan_id": str(plan_id),
            "step_id": str(step_id),
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# MOCK DATABASE SERVICES
# ============================================================================

class AssistanceProgramDB:
    """Mock database for assistance programs"""
    
    def __init__(self):
        # Pre-populate with common programs
        self.programs = self._load_default_programs()
    
    def _load_default_programs(self) -> list['AssistanceProgram']:
        """Load default assistance programs"""
        return [
            AssistanceProgram(
                name="Hospital Charity Care",
                program_type="charity_care",
                eligibility=EligibilityCriteria(
                    max_fpl_percentage=400,
                    min_bill_amount=Decimal("500")
                ),
                typical_discount_percentage=0.75,
                required_documents=[
                    "proof_of_income", "tax_return", "bank_statements"
                ],
                processing_days=30,
                is_retroactive=True
            ),
            AssistanceProgram(
                name="State Medical Debt Relief",
                program_type="state_assistance",
                eligibility=EligibilityCriteria(
                    max_fpl_percentage=300,
                    required_states=["CA", "NY", "MA", "WA"]
                ),
                typical_discount_percentage=0.50,
                required_documents=["proof_of_income", "medical_bills"],
                processing_days=45
            ),
            AssistanceProgram(
                name="Nonprofit Medical Bill Assistance",
                program_type="nonprofit",
                eligibility=EligibilityCriteria(
                    max_fpl_percentage=500,
                    min_bill_amount=Decimal("1000")
                ),
                typical_discount_percentage=0.40,
                max_coverage=Decimal("10000"),
                required_documents=["proof_of_income", "bills", "id_document"],
                processing_days=21
            )
        ]
    
    async def get_programs_for_state(self, state: str) -> list['AssistanceProgram']:
        """Get applicable programs for a state"""
        applicable = []
        for program in self.programs:
            criteria = program.eligibility
            if not criteria.required_states or state in criteria.required_states:
                applicable.append(program)
        return applicable


class CacheService:
    """Simple in-memory cache (replace with Redis in production)"""
    
    def __init__(self):
        self._cache = {}
    
    async def get(self, key: str) -> Optional[str]:
        item = self._cache.get(key)
        if item and item["expires"] > datetime.utcnow().timestamp():
            return item["value"]
        return None
    
    async def set(self, key: str, value: str, ttl: int = 3600):
        self._cache[key] = {
            "value": value,
            "expires": datetime.utcnow().timestamp() + ttl
        }


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class BillInput(BaseModel):
    """API input for a medical bill"""
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
    """API input for insurance info"""
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

class FinancialProfileInput(BaseModel):
    """API input for patient financial profile"""
    household_size: int = 1
    state: str
    zip_code: str
    annual_gross_income: Decimal
    monthly_net_income: Decimal
    monthly_debt_payments: Decimal = Decimal("0")
    existing_medical_debt: Decimal = Decimal("0")
    checking_balance: Decimal = Decimal("0")
    savings_balance: Decimal = Decimal("0")

class NavigationPlanRequest(BaseModel):
    """Complete request for navigation plan"""
    patient_id: str
    bills: list[BillInput]
    insurance: Optional[InsuranceInput] = None
    financial_profile: FinancialProfileInput

class ActionStepResponse(BaseModel):
    """API response for an action step"""
    step_number: int
    action_type: str
    priority: str
    title: str
    description: str
    target_provider: Optional[str]
    estimated_effort_minutes: int
    deadline: Optional[date]
    savings_minimum: str
    savings_expected: str
    savings_maximum: str
    approval_likelihood: float
    detailed_steps: list[str]
    required_documents: list[str]
    warnings: list[str]

class NavigationPlanResponse(BaseModel):
    """Complete API response for navigation plan"""
    plan_id: str
    patient_id: str
    generated_at: str
    valid_until: date
    
    # Summary
    total_bills_analyzed: int
    total_amount_owed: str
    potential_savings_expected: str
    potential_savings_range: str
    
    # Actions
    action_steps: list[ActionStepResponse]
    critical_actions_count: int
    
    # Risk
    risk_level: str
    risk_score: int
    risk_factors: list[str]
    
    # Budget
    current_monthly_burden: str
    projected_monthly_burden: str
    recommended_monthly_payment: str
    
    # Timeline
    plan_duration_days: int
    key_deadlines: list[dict]
    
    # Narrative
    executive_summary: str
    confidence_score: float


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Initialize services
assistance_db = AssistanceProgramDB()
cache_service = CacheService()
navigation_service = NavigationService(assistance_db, cache_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MedFin Navigation Service")
    yield
    # Shutdown
    logger.info("Shutting down MedFin Navigation Service")

app = FastAPI(
    title="MedFin Financial Navigation API",
    description="AI-powered healthcare financial navigation and planning",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/api/v1/navigation-plans", response_model=NavigationPlanResponse)
async def create_navigation_plan(request: NavigationPlanRequest):
    """Generate a personalized financial navigation plan"""
    
    try:
        # Convert API models to internal models
        bills = [_convert_bill_input(b) for b in request.bills]
        insurance = _convert_insurance_input(request.insurance) if request.insurance else None
        profile = _convert_profile_input(request.patient_id, request.financial_profile)
        
        # Generate plan
        plan = await navigation_service.generate_navigation_plan(
            patient_id=request.patient_id,
            bills=bills,
            insurance=insurance,
            profile=profile
        )
        
        # Convert to response model
        return _convert_plan_to_response(plan)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error generating navigation plan")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/navigation-plans/{plan_id}")
async def get_navigation_plan(plan_id: str):
    """Retrieve an existing navigation plan"""
    # In production, fetch from database
    raise HTTPException(status_code=404, detail="Plan not found")


@app.patch("/api/v1/navigation-plans/{plan_id}/steps/{step_id}")
async def update_step_status(plan_id: str, step_id: str, status: str):
    """Update the status of an action step"""
    result = await navigation_service.update_plan_status(
        UUID(plan_id), UUID(step_id), status
    )
    return result


@app.get("/api/v1/assistance-programs")
async def list_assistance_programs(state: str):
    """List available assistance programs for a state"""
    programs = await assistance_db.get_programs_for_state(state)
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "type": p.program_type,
            "max_fpl": p.eligibility.max_fpl_percentage,
            "typical_discount": p.typical_discount_percentage
        }
        for p in programs
    ]


# ============================================================================
# CONVERSION HELPERS
# ============================================================================

def _convert_bill_input(inp: BillInput) -> 'MedicalBill':
    """Convert API bill input to internal model"""
    line_items = []
    for li in inp.line_items:
        line_items.append(LineItem(
            cpt_code=li.get("cpt_code"),
            description=li.get("description", "Service"),
            service_date=li.get("service_date", inp.service_date_start),
            billed_amount=Decimal(str(li.get("billed_amount", 0))),
            patient_responsibility=Decimal(str(li.get("patient_responsibility", 0)))
        ))
    
    return MedicalBill(
        provider_name=inp.provider_name,
        provider_type=inp.provider_type,
        statement_date=inp.statement_date,
        service_date_start=inp.service_date_start,
        service_date_end=inp.service_date_end,
        line_items=line_items,
        total_billed=inp.total_billed,
        insurance_paid=inp.insurance_paid,
        patient_balance=inp.patient_balance,
        status=BillStatus(inp.status),
        due_date=inp.due_date,
        is_in_network=inp.is_in_network
    )

def _convert_insurance_input(inp: InsuranceInput) -> 'InsurancePlan':
    """Convert API insurance input to internal model"""
    return InsurancePlan(
        plan_name=inp.plan_name,
        insurance_type=InsuranceType(inp.insurance_type),
        carrier_name=inp.carrier_name,
        policy_number="",  # Not needed for analysis
        individual_deductible=inp.individual_deductible,
        individual_deductible_met=inp.individual_deductible_met,
        individual_oop_max=inp.individual_oop_max,
        individual_oop_met=inp.individual_oop_met,
        coinsurance_rate=inp.coinsurance_rate,
        plan_year_start=inp.plan_year_start,
        plan_year_end=inp.plan_year_end
    )

def _convert_profile_input(patient_id: str, inp: FinancialProfileInput) -> 'PatientFinancialProfile':
    """Convert API profile input to internal model"""
    return PatientFinancialProfile(
        patient_id=patient_id,
        household_size=inp.household_size,
        state=inp.state,
        zip_code=inp.zip_code,
        annual_gross_income=inp.annual_gross_income,
        total_monthly_net=inp.monthly_net_income,
        total_monthly_gross=inp.annual_gross_income / 12,
        total_monthly_debt_payments=inp.monthly_debt_payments,
        existing_medical_debt=inp.existing_medical_debt,
        checking_balance=inp.checking_balance,
        savings_balance=inp.savings_balance
    )

def _convert_plan_to_response(plan: 'NavigationPlan') -> NavigationPlanResponse:
    """Convert internal plan to API response"""
    action_steps = [
        ActionStepResponse(
            step_number=s.step_number,
            action_type=s.action_type.value,
            priority=s.priority.value,
            title=s.title,
            description=s.description,
            target_provider=s.target_provider,
            estimated_effort_minutes=s.estimated_effort_minutes,
            deadline=s.deadline,
            savings_minimum=f"${s.savings_estimate.minimum:,.2f}",
            savings_expected=f"${s.savings_estimate.expected:,.2f}",
            savings_maximum=f"${s.savings_estimate.maximum:,.2f}",
            approval_likelihood=s.approval_likelihood,
            detailed_steps=s.detailed_steps,
            required_documents=s.required_documents,
            warnings=s.warnings
        )
        for s in plan.action_steps
    ]
    
    return NavigationPlanResponse(
        plan_id=str(plan.id),
        patient_id=plan.patient_id,
        generated_at=plan.generated_at.isoformat(),
        valid_until=plan.valid_until,
        total_bills_analyzed=plan.total_bills_analyzed,
        total_amount_owed=f"${plan.total_amount_owed:,.2f}",
        potential_savings_expected=f"${plan.potential_total_savings.expected:,.2f}",
        potential_savings_range=f"${plan.potential_total_savings.minimum:,.2f} - ${plan.potential_total_savings.maximum:,.2f}",
        action_steps=action_steps,
        critical_actions_count=plan.critical_actions_count,
        risk_level=plan.risk_assessment.overall_risk_level.value,
        risk_score=plan.risk_assessment.risk_score,
        risk_factors=plan.risk_assessment.key_risk_factors,
        current_monthly_burden=f"${plan.budget_impact.current_medical_payment_burden:,.2f}",
        projected_monthly_burden=f"${plan.budget_impact.projected_after_plan:,.2f}",
        recommended_monthly_payment=f"${plan.budget_impact.recommended_monthly_payment:,.2f}",
        plan_duration_days=plan.plan_duration_days,
        key_deadlines=[
            {"date": d.isoformat(), "action": a} 
            for d, a in plan.key_deadlines
        ],
        executive_summary=plan.executive_summary,
        confidence_score=plan.confidence_score
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "medfin-navigation",
        "version": "1.0.0"
    }