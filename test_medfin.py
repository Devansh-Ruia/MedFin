import requests
import json

BASE_URL = "http://localhost:8000"

# Test health
print("Testing health endpoint...")
r = requests.get(f"{BASE_URL}/health")
print(f"Health: {r.json()}\n")

# Test plan generation
print("Generating navigation plan...")
payload = {
    "patient_id": "TEST-001",
    "bills": [{
        "provider_name": "City Hospital",
        "provider_type": "hospital",
        "statement_date": "2024-11-15",
        "service_date_start": "2024-10-20",
        "service_date_end": "2024-10-20",
        "total_billed": 12000.00,
        "insurance_paid": 8000.00,
        "patient_balance": 4000.00,
        "status": "pending",
        "due_date": "2024-12-15",
        "line_items": [
            {"cpt_code": "43239", "description": "EGD with Biopsy", 
             "service_date": "2024-10-20", "billed_amount": 4500, "patient_responsibility": 900},
            {"cpt_code": "43235", "description": "Diagnostic EGD (UNBUNDLED)", 
             "service_date": "2024-10-20", "billed_amount": 2200, "patient_responsibility": 440}
        ]
    }],
    "insurance": {
        "plan_name": "Aetna PPO",
        "insurance_type": "employer",
        "carrier_name": "Aetna",
        "individual_deductible": 2500,
        "individual_deductible_met": 2000,
        "individual_oop_max": 6500,
        "individual_oop_met": 4000,
        "coinsurance_rate": 0.2,
        "plan_year_start": "2024-01-01",
        "plan_year_end": "2024-12-31"
    },
    "financial_profile": {
        "household_size": 3,
        "state": "CA",
        "zip_code": "90210",
        "annual_gross_income": 55000,
        "monthly_net_income": 3800,
        "monthly_debt_payments": 600,
        "existing_medical_debt": 500
    }
}

r = requests.post(f"{BASE_URL}/api/v1/navigation-plans", json=payload)
plan = r.json()

print(f"Plan ID: {plan['id']}")
print(f"Total Owed: ${plan['total_amount_owed']}")
print(f"Expected Savings: ${plan['potential_total_savings']['expected']}")
print(f"Risk Level: {plan['risk_assessment']['overall_risk_level']}")
print(f"\nAction Steps ({len(plan['action_steps'])}):")
for step in plan['action_steps']:
    print(f"  {step['step_number']}. [{step['priority'].upper()}] {step['title']}")
    print(f"     Expected savings: ${step['savings_estimate']['expected']}")
print(f"\nSummary: {plan['executive_summary']}")