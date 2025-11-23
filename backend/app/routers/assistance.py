from fastapi import APIRouter, HTTPException
from app.core.models import AssistanceProgram, InsuranceInfo
from app.services.assistance_matcher import assistance_matcher
from typing import Optional, List

router = APIRouter()


@router.post("/match", response_model=List[AssistanceProgram])
async def match_assistance_programs(
    annual_income: Optional[float] = None,
    household_size: Optional[int] = None,
    insurance_info: Optional[dict] = None,
    medical_debt: float = 0.0,
    has_prescriptions: bool = False,
    has_diagnosis: bool = True
):
    """Find matching financial assistance programs"""
    try:
        insurance = InsuranceInfo(**insurance_info) if insurance_info else None
        
        programs = assistance_matcher.find_matching_programs(
            annual_income=annual_income,
            household_size=household_size,
            insurance_info=insurance,
            medical_debt=medical_debt,
            has_prescriptions=has_prescriptions,
            has_diagnosis=has_diagnosis
        )
        
        return programs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/programs")
async def list_all_programs():
    """List all available assistance programs"""
    # Return program information (without personal matching)
    return {
        "programs": [
            {
                "program_name": p["program_name"],
                "organization": p["organization"],
                "assistance_type": p["assistance_type"],
                "description": "Financial assistance for healthcare costs"
            }
            for p in assistance_matcher.PROGRAMS
        ]
    }



