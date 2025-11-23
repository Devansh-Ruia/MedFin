from fastapi import APIRouter, HTTPException
from app.core.models import MedicalBill, BillAnalysisRequest
from typing import List

router = APIRouter()


@router.post("/analyze")
async def analyze_bills(request: BillAnalysisRequest):
    """Analyze medical bills and identify issues"""
    
    analysis = {
        "total_bills": len(request.bills),
        "total_amount": sum(bill.total_amount for bill in request.bills),
        "total_insurance_paid": sum(bill.insurance_paid or 0 for bill in request.bills),
        "total_patient_responsibility": sum(bill.patient_responsibility for bill in request.bills),
        "issues": [],
        "recommendations": [],
        "savings_opportunities": []
    }
    
    # Check for potential billing errors
    for bill in request.bills:
        # Check if insurance coverage seems incorrect
        if bill.insurance_paid is not None and request.insurance_info:
            expected_coverage = bill.total_amount * request.insurance_info.coverage_percentage
            if bill.insurance_paid < expected_coverage * 0.8:  # 20% tolerance
                analysis["issues"].append({
                    "bill_id": bill.bill_id,
                    "issue": "Possible underpayment by insurance",
                    "description": f"Expected ${expected_coverage:.2f} coverage, got ${bill.insurance_paid:.2f}"
                })
        
        # Check for duplicate charges
        service_codes = [s.get("code") for s in bill.services if s.get("code")]
        if len(service_codes) != len(set(service_codes)):
            analysis["issues"].append({
                "bill_id": bill.bill_id,
                "issue": "Possible duplicate charges",
                "description": "Review itemized bill for duplicate service codes"
            })
    
    # Identify high-cost services
    high_cost_services = [
        s for bill in request.bills 
        for s in bill.services 
        if s.get("cost", 0) > 1000
    ]
    
    if high_cost_services:
        analysis["recommendations"].append(
            "Review high-cost services on itemized bills for accuracy"
        )
    
    # Check for negotiation opportunities
    if analysis["total_patient_responsibility"] > 1000:
        analysis["savings_opportunities"].append({
            "opportunity": "Bill negotiation",
            "estimated_savings": analysis["total_patient_responsibility"] * 0.15,
            "description": "Contact providers to negotiate discounts or payment plans"
        })
    
    # Check for financial assistance eligibility
    if request.annual_income and request.annual_income < 50000:
        analysis["savings_opportunities"].append({
            "opportunity": "Financial assistance programs",
            "estimated_savings": analysis["total_patient_responsibility"] * 0.50,
            "description": "You may be eligible for hospital charity care or financial assistance"
        })
    
    return analysis


@router.post("/itemize")
async def request_itemization(bill: MedicalBill):
    """Generate request template for itemized bill"""
    
    return {
        "template": {
            "to": bill.provider_name,
            "subject": f"Request for Itemized Bill - {bill.bill_id}",
            "body": f"""
Dear {bill.provider_name},

I am writing to request an itemized bill for services provided on {bill.service_date} 
(Bill ID: {bill.bill_id}).

Please provide a detailed breakdown of all charges, including:
- Individual service codes (CPT codes)
- Description of each service
- Date of service
- Provider name for each service
- Charge amount for each service

This information will help me:
1. Verify the accuracy of charges
2. Understand what services were provided
3. Review with my insurance company if needed

Please send this itemized bill to:
[Your Address]
[Your Email]

Thank you for your assistance.

Sincerely,
[Your Name]
            """.strip()
        },
        "bill_id": bill.bill_id,
        "provider": bill.provider_name
    }



