from fastapi import APIRouter, HTTPException
from app.core.models import CostEstimationRequest, CostEstimationResponse
from app.services.cost_estimator import cost_estimator

router = APIRouter()


@router.post("/estimate", response_model=CostEstimationResponse)
async def estimate_cost(request: CostEstimationRequest):
    """Estimate healthcare service cost"""
    try:
        result = cost_estimator.estimate_cost(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def get_service_types():
    """Get available service types"""
    from app.core.models import ServiceType
    return {
        "service_types": [
            {
                "value": st.value,
                "name": st.value.replace("_", " ").title()
            }
            for st in ServiceType
        ]
    }



