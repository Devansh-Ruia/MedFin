from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from io import BytesIO

from app.core.database import get_db
from app.core.db_models import User, UserInsurance, SavedBill, SavedNavigationPlan, SavedCostEstimate
from app.core.security import get_current_active_user
from app.core.models import InsuranceType
from app.services.pdf_generator import PDFGenerator

router = APIRouter()


# Insurance endpoints
class InsuranceInfoCreate(BaseModel):
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


class InsuranceInfoResponse(BaseModel):
    id: int
    insurance_type: str
    plan_name: Optional[str]
    deductible: float
    deductible_remaining: float
    out_of_pocket_max: float
    out_of_pocket_used: float
    coverage_percentage: float
    copay_primary: Optional[float]
    copay_specialist: Optional[float]
    copay_emergency: Optional[float]
    in_network: bool

    class Config:
        from_attributes = True


@router.post("/insurance", response_model=InsuranceInfoResponse)
async def save_insurance_info(
    insurance: InsuranceInfoCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> InsuranceInfoResponse:
    """Save or update user's insurance information."""
    
    # Check if insurance info already exists
    result = await db.execute(
        select(UserInsurance).where(UserInsurance.user_id == current_user.id)
    )
    existing_insurance = result.scalar_one_or_none()
    
    if existing_insurance:
        # Update existing
        existing_insurance.insurance_type = insurance.insurance_type.value
        existing_insurance.plan_name = insurance.plan_name
        existing_insurance.deductible = insurance.deductible
        existing_insurance.deductible_remaining = insurance.deductible_remaining
        existing_insurance.out_of_pocket_max = insurance.out_of_pocket_max
        existing_insurance.out_of_pocket_used = insurance.out_of_pocket_used
        existing_insurance.coverage_percentage = insurance.coverage_percentage
        existing_insurance.copay_primary = insurance.copay_primary
        existing_insurance.copay_specialist = insurance.copay_specialist
        existing_insurance.copay_emergency = insurance.copay_emergency
        existing_insurance.in_network = insurance.in_network
        db_insurance = existing_insurance
    else:
        # Create new
        db_insurance = UserInsurance(
            user_id=current_user.id,
            insurance_type=insurance.insurance_type.value,
            plan_name=insurance.plan_name,
            deductible=insurance.deductible,
            deductible_remaining=insurance.deductible_remaining,
            out_of_pocket_max=insurance.out_of_pocket_max,
            out_of_pocket_used=insurance.out_of_pocket_used,
            coverage_percentage=insurance.coverage_percentage,
            copay_primary=insurance.copay_primary,
            copay_specialist=insurance.copay_specialist,
            copay_emergency=insurance.copay_emergency,
            in_network=insurance.in_network
        )
        db.add(db_insurance)
    
    await db.commit()
    await db.refresh(db_insurance)
    return db_insurance


@router.get("/insurance", response_model=Optional[InsuranceInfoResponse])
async def get_insurance_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[InsuranceInfoResponse]:
    """Get user's insurance information."""
    
    result = await db.execute(
        select(UserInsurance).where(UserInsurance.user_id == current_user.id)
    )
    insurance = result.scalar_one_or_none()
    return insurance


# Bill endpoints
class BillCreate(BaseModel):
    bill_id: str
    provider_name: str
    service_date: str
    services: List[Dict[str, Any]]
    total_amount: float
    insurance_paid: Optional[float] = None
    patient_responsibility: float
    due_date: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None


class BillResponse(BaseModel):
    id: int
    bill_id: str
    provider_name: str
    service_date: str
    services: List[Dict[str, Any]]
    total_amount: float
    insurance_paid: Optional[float]
    patient_responsibility: float
    due_date: Optional[str]
    status: str
    notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.post("/bills", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
async def save_bill(
    bill: BillCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> BillResponse:
    """Save a medical bill."""
    
    db_bill = SavedBill(
        user_id=current_user.id,
        bill_id=bill.bill_id,
        provider_name=bill.provider_name,
        service_date=bill.service_date,
        services=bill.services,
        total_amount=bill.total_amount,
        insurance_paid=bill.insurance_paid,
        patient_responsibility=bill.patient_responsibility,
        due_date=bill.due_date,
        status=bill.status,
        notes=bill.notes
    )
    
    db.add(db_bill)
    await db.commit()
    await db.refresh(db_bill)
    
    return BillResponse(
        id=db_bill.id,
        bill_id=db_bill.bill_id,
        provider_name=db_bill.provider_name,
        service_date=db_bill.service_date,
        services=db_bill.services,
        total_amount=db_bill.total_amount,
        insurance_paid=db_bill.insurance_paid,
        patient_responsibility=db_bill.patient_responsibility,
        due_date=db_bill.due_date,
        status=db_bill.status,
        notes=db_bill.notes,
        created_at=db_bill.created_at.isoformat()
    )


@router.get("/bills", response_model=List[BillResponse])
async def get_bills(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[BillResponse]:
    """Get all saved bills for the current user."""
    
    result = await db.execute(
        select(SavedBill)
        .where(SavedBill.user_id == current_user.id)
        .order_by(SavedBill.created_at.desc())
    )
    bills = result.scalars().all()
    
    return [
        BillResponse(
            id=bill.id,
            bill_id=bill.bill_id,
            provider_name=bill.provider_name,
            service_date=bill.service_date,
            services=bill.services,
            total_amount=bill.total_amount,
            insurance_paid=bill.insurance_paid,
            patient_responsibility=bill.patient_responsibility,
            due_date=bill.due_date,
            status=bill.status,
            notes=bill.notes,
            created_at=bill.created_at.isoformat()
        )
        for bill in bills
    ]


@router.delete("/bills/{bill_id}")
async def delete_bill(
    bill_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete a saved bill."""
    
    result = await db.execute(
        select(SavedBill).where(
            SavedBill.id == bill_id,
            SavedBill.user_id == current_user.id
        )
    )
    bill = result.scalar_one_or_none()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    await db.delete(bill)
    await db.commit()
    
    return {"message": "Bill deleted successfully"}


# Cost estimate endpoints
class CostEstimateCreate(BaseModel):
    service_type: str
    procedure_code: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    estimated_cost: float
    insurance_coverage: Optional[float] = None
    patient_responsibility: float
    breakdown: Dict[str, Any]
    confidence_score: float
    alternatives: Optional[List[Dict[str, Any]]] = None


class CostEstimateResponse(BaseModel):
    id: int
    service_type: str
    procedure_code: Optional[str]
    description: Optional[str]
    location: Optional[str]
    estimated_cost: float
    insurance_coverage: Optional[float]
    patient_responsibility: float
    breakdown: Dict[str, Any]
    confidence_score: float
    alternatives: Optional[List[Dict[str, Any]]]
    created_at: str

    class Config:
        from_attributes = True


@router.post("/cost-estimates", response_model=CostEstimateResponse, status_code=status.HTTP_201_CREATED)
async def save_cost_estimate(
    estimate: CostEstimateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CostEstimateResponse:
    """Save a cost estimate."""
    
    db_estimate = SavedCostEstimate(
        user_id=current_user.id,
        service_type=estimate.service_type,
        procedure_code=estimate.procedure_code,
        description=estimate.description,
        location=estimate.location,
        estimated_cost=estimate.estimated_cost,
        insurance_coverage=estimate.insurance_coverage,
        patient_responsibility=estimate.patient_responsibility,
        breakdown=estimate.breakdown,
        confidence_score=estimate.confidence_score,
        alternatives=estimate.alternatives
    )
    
    db.add(db_estimate)
    await db.commit()
    await db.refresh(db_estimate)
    
    return CostEstimateResponse(
        id=db_estimate.id,
        service_type=db_estimate.service_type,
        procedure_code=db_estimate.procedure_code,
        description=db_estimate.description,
        location=db_estimate.location,
        estimated_cost=db_estimate.estimated_cost,
        insurance_coverage=db_estimate.insurance_coverage,
        patient_responsibility=db_estimate.patient_responsibility,
        breakdown=db_estimate.breakdown,
        confidence_score=db_estimate.confidence_score,
        alternatives=db_estimate.alternatives,
        created_at=db_estimate.created_at.isoformat()
    )


@router.get("/cost-estimates", response_model=List[CostEstimateResponse])
async def get_cost_estimates(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[CostEstimateResponse]:
    """Get all saved cost estimates for the current user."""
    
    result = await db.execute(
        select(SavedCostEstimate)
        .where(SavedCostEstimate.user_id == current_user.id)
        .order_by(SavedCostEstimate.created_at.desc())
    )
    estimates = result.scalars().all()
    
    return [
        CostEstimateResponse(
            id=est.id,
            service_type=est.service_type,
            procedure_code=est.procedure_code,
            description=est.description,
            location=est.location,
            estimated_cost=est.estimated_cost,
            insurance_coverage=est.insurance_coverage,
            patient_responsibility=est.patient_responsibility,
            breakdown=est.breakdown,
            confidence_score=est.confidence_score,
            alternatives=est.alternatives,
            created_at=est.created_at.isoformat()
        )
        for est in estimates
    ]


# Navigation plan endpoints
class NavigationPlanCreate(BaseModel):
    plan_data: Dict[str, Any]
    current_financial_situation: Dict[str, Any]
    projected_savings: float


class NavigationPlanResponse(BaseModel):
    id: int
    plan_data: Dict[str, Any]
    current_financial_situation: Dict[str, Any]
    projected_savings: float
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/navigation-plans", response_model=NavigationPlanResponse, status_code=status.HTTP_201_CREATED)
async def save_navigation_plan(
    plan: NavigationPlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> NavigationPlanResponse:
    """Save a navigation plan."""
    
    db_plan = SavedNavigationPlan(
        user_id=current_user.id,
        plan_data=plan.plan_data,
        current_financial_situation=plan.current_financial_situation,
        projected_savings=plan.projected_savings,
        status="active"
    )
    
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    
    return NavigationPlanResponse(
        id=db_plan.id,
        plan_data=db_plan.plan_data,
        current_financial_situation=db_plan.current_financial_situation,
        projected_savings=db_plan.projected_savings,
        status=db_plan.status,
        created_at=db_plan.created_at.isoformat()
    )


@router.get("/navigation-plans", response_model=List[NavigationPlanResponse])
async def get_navigation_plans(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[NavigationPlanResponse]:
    """Get all saved navigation plans for the current user."""
    
    result = await db.execute(
        select(SavedNavigationPlan)
        .where(SavedNavigationPlan.user_id == current_user.id)
        .order_by(SavedNavigationPlan.created_at.desc())
    )
    plans = result.scalars().all()
    
    return [
        NavigationPlanResponse(
            id=plan.id,
            plan_data=plan.plan_data,
            current_financial_situation=plan.current_financial_situation,
            projected_savings=plan.projected_savings,
            status=plan.status,
            created_at=plan.created_at.isoformat()
        )
        for plan in plans
    ]


@router.put("/navigation-plans/{plan_id}")
async def update_navigation_plan_status(
    plan_id: int,
    new_status: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Update navigation plan status (active, completed, archived)."""
    
    if new_status not in ["active", "completed", "archived"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.execute(
        select(SavedNavigationPlan).where(
            SavedNavigationPlan.id == plan_id,
            SavedNavigationPlan.user_id == current_user.id
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Navigation plan not found")
    
    plan.status = new_status
    await db.commit()
    
    return {"message": f"Navigation plan status updated to {new_status}"}


@router.delete("/navigation-plans/{plan_id}")
async def delete_navigation_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete a saved navigation plan."""
    
    result = await db.execute(
        select(SavedNavigationPlan).where(
            SavedNavigationPlan.id == plan_id,
            SavedNavigationPlan.user_id == current_user.id
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Navigation plan not found")
    
    await db.delete(plan)
    await db.commit()
    
    return {"message": "Navigation plan deleted successfully"}


@router.delete("/cost-estimates/{estimate_id}")
async def delete_cost_estimate(
    estimate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete a saved cost estimate."""
    
    result = await db.execute(
        select(SavedCostEstimate).where(
            SavedCostEstimate.id == estimate_id,
            SavedCostEstimate.user_id == current_user.id
        )
    )
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(status_code=404, detail="Cost estimate not found")
    
    await db.delete(estimate)
    await db.commit()
    
    return {"message": "Cost estimate deleted successfully"}


# Dashboard endpoint
class UserDashboard(BaseModel):
    user_info: Dict[str, Any]
    insurance_info: Optional[Dict[str, Any]]
    summary: Dict[str, Any]
    recent_bills: List[Dict[str, Any]]
    recent_plans: List[Dict[str, Any]]
    recent_estimates: List[Dict[str, Any]]


@router.get("/dashboard", response_model=UserDashboard)
async def get_user_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserDashboard:
    """Get comprehensive user dashboard with all saved data."""
    
    # Get user info
    user_info = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat()
    }
    
    # Get insurance info
    insurance_result = await db.execute(
        select(UserInsurance).where(UserInsurance.user_id == current_user.id)
    )
    insurance = insurance_result.scalar_one_or_none()
    insurance_info = None
    if insurance:
        insurance_info = {
            "id": insurance.id,
            "insurance_type": insurance.insurance_type,
            "plan_name": insurance.plan_name,
            "deductible": insurance.deductible,
            "deductible_remaining": insurance.deductible_remaining,
            "out_of_pocket_max": insurance.out_of_pocket_max,
            "coverage_percentage": insurance.coverage_percentage
        }
    
    # Get bills summary
    bills_result = await db.execute(
        select(SavedBill).where(SavedBill.user_id == current_user.id)
    )
    bills = bills_result.scalars().all()
    
    # Get navigation plans summary
    plans_result = await db.execute(
        select(SavedNavigationPlan).where(SavedNavigationPlan.user_id == current_user.id)
    )
    plans = plans_result.scalars().all()
    
    # Get cost estimates summary
    estimates_result = await db.execute(
        select(SavedCostEstimate).where(SavedCostEstimate.user_id == current_user.id)
    )
    estimates = estimates_result.scalars().all()
    
    # Calculate summary statistics
    total_bills = len(bills)
    total_bill_amount = sum(bill.patient_responsibility for bill in bills)
    total_plans = len(plans)
    total_projected_savings = sum(plan.projected_savings for plan in plans)
    total_estimates = len(estimates)
    
    summary = {
        "total_bills": total_bills,
        "total_bill_amount": total_bill_amount,
        "total_plans": total_plans,
        "total_projected_savings": total_projected_savings,
        "total_estimates": total_estimates,
        "has_insurance": insurance_info is not None
    }
    
    # Get recent items (last 5)
    recent_bills = [
        {
            "id": bill.id,
            "provider_name": bill.provider_name,
            "service_date": bill.service_date,
            "patient_responsibility": bill.patient_responsibility,
            "status": bill.status,
            "created_at": bill.created_at.isoformat()
        }
        for bill in sorted(bills, key=lambda x: x.created_at, reverse=True)[:5]
    ]
    
    recent_plans = [
        {
            "id": plan.id,
            "projected_savings": plan.projected_savings,
            "status": plan.status,
            "created_at": plan.created_at.isoformat()
        }
        for plan in sorted(plans, key=lambda x: x.created_at, reverse=True)[:5]
    ]
    
    recent_estimates = [
        {
            "id": est.id,
            "service_type": est.service_type,
            "estimated_cost": est.estimated_cost,
            "patient_responsibility": est.patient_responsibility,
            "created_at": est.created_at.isoformat()
        }
        for est in sorted(estimates, key=lambda x: x.created_at, reverse=True)[:5]
    ]
    
    return UserDashboard(
        user_info=user_info,
        insurance_info=insurance_info,
        summary=summary,
        recent_bills=recent_bills,
        recent_plans=recent_plans,
        recent_estimates=recent_estimates
    )


# PDF Export endpoints
@router.get("/export/dashboard-pdf")
async def export_dashboard_pdf(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """Export user dashboard as PDF."""
    
    # Get dashboard data
    dashboard_data = await get_user_dashboard(current_user, db)
    
    # Generate PDF
    pdf_generator = PDFGenerator()
    pdf_buffer = pdf_generator.generate_dashboard_report(dashboard_data.dict())
    
    # Return PDF as streaming response
    filename = f"medfin_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/navigation-plan/{plan_id}/pdf")
async def export_navigation_plan_pdf(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """Export navigation plan as PDF."""
    
    # Get navigation plan
    result = await db.execute(
        select(SavedNavigationPlan).where(
            SavedNavigationPlan.id == plan_id,
            SavedNavigationPlan.user_id == current_user.id
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Navigation plan not found")
    
    # Prepare plan data
    plan_data = {
        "id": plan.id,
        "created_at": plan.created_at.isoformat(),
        "status": plan.status,
        "projected_savings": plan.projected_savings,
        "current_financial_situation": plan.current_financial_situation,
        "plan_data": plan.plan_data
    }
    
    # Generate PDF
    pdf_generator = PDFGenerator()
    pdf_buffer = pdf_generator.generate_navigation_plan_report(plan_data)
    
    # Return PDF as streaming response
    filename = f"medfin_navigation_plan_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
