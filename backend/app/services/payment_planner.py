from typing import List, Dict, Any
from app.core.models import PaymentPlanRequest, PaymentPlanOption


class PaymentPlanner:
    """Generates payment plan options for medical debt"""
    
    def generate_payment_plans(self, request: PaymentPlanRequest) -> List[PaymentPlanOption]:
        """Generate payment plan options"""
        
        plans = []
        
        # Calculate available monthly payment
        disposable_income = request.monthly_income - request.monthly_expenses
        max_monthly_payment = disposable_income * 0.20  # Use max 20% of disposable income
        
        # Option 1: Minimum payment plan (longest term, lowest monthly)
        if max_monthly_payment > 0:
            months = max(6, int(request.total_debt / max_monthly_payment))
            monthly = request.total_debt / months
            
            plans.append(PaymentPlanOption(
                plan_type="Extended Payment Plan",
                monthly_payment=monthly,
                total_payments=months,
                total_cost=request.total_debt,
                interest_rate=0.0,
                eligibility=True,
                pros=[
                    "Lowest monthly payment",
                    "No interest (if negotiated with provider)",
                    "Prevents collections"
                ],
                cons=[
                    f"Takes {months} months to pay off",
                    "May require provider agreement"
                ]
            ))
        
        # Option 2: Aggressive payment plan (pay off in 12 months)
        monthly_12 = request.total_debt / 12
        if monthly_12 <= max_monthly_payment * 2:
            plans.append(PaymentPlanOption(
                plan_type="12-Month Plan",
                monthly_payment=monthly_12,
                total_payments=12,
                total_cost=request.total_debt,
                interest_rate=0.0,
                eligibility=monthly_12 <= disposable_income,
                pros=[
                    "Pay off debt quickly",
                    "No interest",
                    "Reduces financial stress faster"
                ],
                cons=[
                    "Higher monthly payment required",
                    "May strain budget"
                ]
            ))
        
        # Option 3: Credit card balance transfer (if interest applies)
        if request.total_debt > 2000 and disposable_income > 500:
            plans.append(PaymentPlanOption(
                plan_type="Credit Card Balance Transfer",
                monthly_payment=max(disposable_income * 0.15, 100),
                total_payments=int(request.total_debt / (disposable_income * 0.15)),
                total_cost=request.total_debt * 1.10,  # 10% interest estimate
                interest_rate=10.0,
                eligibility=True,
                pros=[
                    "Consolidate debt",
                    "Possible promotional 0% APR period",
                    "Single payment"
                ],
                cons=[
                    "May accrue interest",
                    "Requires good credit",
                    "Higher total cost"
                ]
            ))
        
        # Option 4: Medical credit card (CareCredit, etc.)
        plans.append(PaymentPlanOption(
            plan_type="Medical Credit Card (CareCredit)",
            monthly_payment=request.total_debt / 24,
            total_payments=24,
            total_cost=request.total_debt,
            interest_rate=0.0,  # Promotional period
            eligibility=True,
            pros=[
                "Often 0% interest if paid within promotional period",
                "Accepted at many providers",
                "Flexible terms"
            ],
            cons=[
                "Interest applies if not paid in full",
                "Requires credit check",
                "May have deferred interest"
            ]
        ))
        
        # Option 5: Settlement negotiation
        if request.total_debt > 5000:
            settlement_amount = request.total_debt * 0.60  # 40% discount
            monthly_settlement = settlement_amount / 12
            
            plans.append(PaymentPlanOption(
                plan_type="Settlement Negotiation",
                monthly_payment=monthly_settlement,
                total_payments=12,
                total_cost=settlement_amount,
                interest_rate=0.0,
                eligibility=request.total_debt > 5000,
                pros=[
                    f"Reduces total debt by ${request.total_debt - settlement_amount:.2f}",
                    "Lower total cost",
                    "Faster resolution"
                ],
                cons=[
                    "May require lump sum or short term",
                    "Negotiation required",
                    "May impact credit if in collections"
                ]
            ))
        
        # Sort by total cost
        plans.sort(key=lambda x: x.total_cost)
        
        return plans


# Singleton instance
payment_planner = PaymentPlanner()



