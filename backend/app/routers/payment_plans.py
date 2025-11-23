from fastapi import APIRouter, HTTPException
from app.core.models import PaymentPlanRequest, PaymentPlanOption
from app.services.payment_planner import PaymentPlanner
from typing import List

router = APIRouter()
payment_planner = PaymentPlanner()


@router.post("/generate", response_model=List[PaymentPlanOption])
async def generate_payment_plans(request: PaymentPlanRequest):
    """Generate payment plan options"""
    try:
        plans = payment_planner.generate_payment_plans(request)
        return plans
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_payment_plan(request: PaymentPlanRequest):
    """Get recommended payment plan based on financial situation"""
    try:
        plans = payment_planner.generate_payment_plans(request)
        
        if not plans:
            return {
                "recommendation": None,
                "message": "Unable to generate suitable payment plans. Consider financial assistance programs."
            }
        
        # Recommend based on affordability and total cost
        disposable_income = request.monthly_income - request.monthly_expenses
        
        # Find plans that are affordable (monthly payment < 20% of disposable income)
        affordable_plans = [
            p for p in plans 
            if p.monthly_payment <= disposable_income * 0.20 and p.eligibility
        ]
        
        if affordable_plans:
            # Recommend the one with lowest total cost
            recommended = min(affordable_plans, key=lambda x: x.total_cost)
        else:
            # Recommend the one with lowest monthly payment
            recommended = min(plans, key=lambda x: x.monthly_payment)
        
        return {
            "recommended_plan": recommended,
            "reasoning": "Based on your financial situation and total cost optimization",
            "alternative_plans": [p for p in plans if p != recommended]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

