from fastapi import APIRouter, HTTPException
from app.core.models import (
    NavigationPlan,
    MedicalBill,
    InsuranceInfo,
    BillAnalysisRequest
)
from app.services.navigation_engine import navigation_engine
from typing import Optional

router = APIRouter()


@router.post("/plan", response_model=NavigationPlan)
async def generate_navigation_plan(
    bills: list[dict],
    insurance_info: Optional[dict] = None,
    annual_income: Optional[float] = None,
    household_size: Optional[int] = None
):
    """Generate autonomous navigation plan"""
    try:
        # Convert bills to MedicalBill objects
        medical_bills = [MedicalBill(**bill) for bill in bills]
        
        # Convert insurance info if provided
        insurance = InsuranceInfo(**insurance_info) if insurance_info else None
        
        # Generate navigation plan
        plan = navigation_engine.generate_navigation_plan(
            bills=medical_bills,
            insurance_info=insurance,
            annual_income=annual_income,
            household_size=household_size
        )
        
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-situation")
async def analyze_financial_situation(
    bills: list[dict],
    insurance_info: Optional[dict] = None,
    annual_income: Optional[float] = None,
    household_size: Optional[int] = None
):
    """Quick financial situation analysis"""
    try:
        medical_bills = [MedicalBill(**bill) for bill in bills]
        insurance = InsuranceInfo(**insurance_info) if insurance_info else None
        
        situation = navigation_engine._analyze_situation(
            medical_bills, insurance, annual_income, household_size
        )
        
        return situation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



