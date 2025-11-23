from fastapi import APIRouter, HTTPException
from app.core.models import InsuranceInfo, InsuranceType

router = APIRouter()


@router.post("/analyze")
async def analyze_insurance(insurance_info: InsuranceInfo):
    """Analyze insurance coverage and provide recommendations"""
    
    analysis = {
        "coverage_status": "good",
        "recommendations": [],
        "warnings": [],
        "deductible_progress": {},
        "out_of_pocket_progress": {},
    }
    
    # Analyze deductible
    if insurance_info.deductible > 0:
        deductible_met = insurance_info.deductible_remaining <= 0
        deductible_progress = (
            (insurance_info.deductible - insurance_info.deductible_remaining) 
            / insurance_info.deductible * 100
        )
        
        analysis["deductible_progress"] = {
            "met": deductible_met,
            "percentage": min(deductible_progress, 100),
            "remaining": insurance_info.deductible_remaining
        }
        
        if not deductible_met:
            analysis["warnings"].append(
                f"Deductible not met. ${insurance_info.deductible_remaining:.2f} remaining."
            )
    
    # Analyze out-of-pocket maximum
    if insurance_info.out_of_pocket_max > 0:
        oop_progress = (
            insurance_info.out_of_pocket_used 
            / insurance_info.out_of_pocket_max * 100
        )
        oop_remaining = insurance_info.out_of_pocket_max - insurance_info.out_of_pocket_used
        
        analysis["out_of_pocket_progress"] = {
            "percentage": min(oop_progress, 100),
            "remaining": oop_remaining,
            "max_reached": oop_remaining <= 0
        }
        
        if oop_remaining < 1000 and oop_remaining > 0:
            analysis["warnings"].append(
                f"Close to out-of-pocket maximum. ${oop_remaining:.2f} remaining."
            )
        elif oop_remaining <= 0:
            analysis["coverage_status"] = "maximum_reached"
            analysis["recommendations"].append(
                "Out-of-pocket maximum reached. Additional covered services should be at 100%."
            )
    
    # Network status
    if not insurance_info.in_network:
        analysis["warnings"].append(
            "Provider may be out-of-network. Verify coverage to avoid higher costs."
        )
        analysis["coverage_status"] = "warning"
    
    # Recommendations based on insurance type
    if insurance_info.insurance_type == InsuranceType.PRIVATE:
        if insurance_info.deductible_remaining > 0:
            analysis["recommendations"].append(
                "Consider scheduling preventive care (typically covered at 100%) before meeting deductible."
            )
    
    if insurance_info.deductible_remaining <= 0:
        analysis["recommendations"].append(
            "Deductible met. Your coverage percentage now applies to services."
        )
    
    return analysis


@router.get("/types")
async def get_insurance_types():
    """Get available insurance types"""
    return {
        "insurance_types": [
            {
                "value": it.value,
                "name": it.value.title()
            }
            for it in InsuranceType
        ]
    }



