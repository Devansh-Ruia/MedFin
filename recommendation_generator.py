"""
MedFin Recommendation Generator
Generates personalized, actionable recommendations
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, List
import logging

from fn_data_models import *
from recommendation_utilities import RecommendationGenerator as SharedRecommendationGenerator, RecommendationContext

logger = logging.getLogger(__name__)


class RecommendationGenerator:
    """
    Enhanced recommendation generator using shared utilities
    """
    
    def __init__(self):
        self.shared_generator = SharedRecommendationGenerator()
    
    def generate_all_recommendations(self, context: RecommendationContext) -> List[Recommendation]:
        """Generate all types of recommendations using shared utilities"""
        all_recommendations = []
        
        # Use shared utilities for different recommendation types
        all_recommendations.extend(self.shared_generator.generate_billing_recommendations(context))
        all_recommendations.extend(self.shared_generator.generate_insurance_recommendations(context))
        all_recommendations.extend(self.shared_generator.generate_assistance_recommendations(context))
        all_recommendations.extend(self.shared_generator.generate_negotiation_recommendations(context))
        all_recommendations.extend(self.shared_generator.generate_payment_plan_recommendations(context))
        
        # Add any template-based recommendations for additional coverage
        template_recommendations = self._generate_template_recommendations(context)
        all_recommendations.extend(template_recommendations)
        
        # Prioritize and rank recommendations
        return RecommendationUtilities.prioritize_actions(all_recommendations)
    
    def _generate_template_recommendations(self, context: RecommendationContext) -> List[Recommendation]:
        """Generate recommendations from templates for additional coverage"""
        # This method can use the existing ACTION_TEMPLATES for any specific cases
        # not covered by the shared utilities
        return []

    # Action templates with all required metadata
    ACTION_TEMPLATES = {
        # =====================================================================
        # BILLING ACTIONS
        # =====================================================================
        "DISPUTE_DUPLICATE": {
            "category": ActionCategory.BILL_DISPUTE,
            "title": "Dispute Duplicate Charges",
            "short_description": "Challenge duplicate charges on your bill",
            "detailed_description": "We've identified charges that appear multiple times on your bill. These duplicate charges can significantly inflate your total. Healthcare providers are required to correct billing errors.",
            "reasoning": "Duplicate charges are billing errors that should be removed",
            "difficulty": DifficultyLevel.EASY,
            "base_success_prob": 0.90,
            "time_minutes": 30,
            "required_docs": ["itemized_bill", "eob"],
            "steps": [
                ("Call billing department", "Ask for billing department, not collections"),
                ("Reference specific duplicates", "Cite line items, dates, and amounts"),
                ("Request written confirmation", "Get confirmation number and name"),
                ("Follow up in writing", "Send certified letter with details")
            ],
            "tips": ["Call Tuesday-Thursday between 10am-2pm for shortest wait times"],
            "script": "I'm calling about account number {account}. I've reviewed my itemized bill and found duplicate charges for {service} on {date}. The charges appear on lines {lines}. I'm requesting these duplicates be removed."
        },
        
        "DISPUTE_UNBUNDLING": {
            "category": ActionCategory.BILL_DISPUTE,
            "title": "Dispute Unbundled Charges",
            "short_description": "Challenge improperly separated service charges",
            "detailed_description": "Services that should be billed together have been separated (unbundled), resulting in higher charges. This violates standard medical coding rules.",
            "reasoning": "Unbundling is a coding violation - services should be billed as a package",
            "difficulty": DifficultyLevel.MODERATE,
            "base_success_prob": 0.80,
            "time_minutes": 45,
            "required_docs": ["itemized_bill", "eob", "medical_records"],
            "steps": [
                ("Request itemized bill with CPT codes", "You need the exact codes to identify unbundling"),
                ("Reference CCI edits", "Cite the specific bundling rules violated"),
                ("Submit formal dispute", "Include code references in dispute letter"),
                ("Escalate if needed", "Request supervisor review")
            ]
        },
        
        "REQUEST_ITEMIZED_BILL": {
            "category": ActionCategory.DOCUMENT_REQUEST,
            "title": "Request Itemized Bill",
            "short_description": "Get detailed breakdown before paying",
            "detailed_description": "You have the right to a fully itemized bill showing every charge with procedure codes. This often reveals errors and gives you leverage for negotiation.",
            "reasoning": "You cannot identify errors without seeing all charges",
            "difficulty": DifficultyLevel.TRIVIAL,
            "base_success_prob": 0.99,
            "time_minutes": 15,
            "required_docs": [],
            "steps": [
                ("Call billing department", "Request itemized statement with CPT/HCPCS codes"),
                ("Specify what you need", "Ask for all charges, codes, dates, and amounts"),
                ("Request in writing", "Follow up with written request if not received in 7 days")
            ],
            "tips": ["This is your legal right - they cannot refuse"]
        },
        
        # =====================================================================
        # INSURANCE ACTIONS
        # =====================================================================
        "FILE_INSURANCE_APPEAL": {
            "category": ActionCategory.INSURANCE_APPEAL,
            "title": "File Insurance Appeal",
            "short_description": "Appeal denied or underpaid claim",
            "detailed_description": "Your insurance either denied coverage or paid less than expected. You have the right to appeal, and a significant portion of appeals are successful.",
            "reasoning": "Many initial denials are overturned on appeal",
            "difficulty": DifficultyLevel.CHALLENGING,
            "base_success_prob": 0.45,
            "time_minutes": 90,
            "required_docs": ["eob", "denial_letter", "medical_records", "doctor_letter"],
            "steps": [
                ("Get denial in writing", "Request detailed explanation of denial reason"),
                ("Review plan documents", "Confirm coverage terms in your policy"),
                ("Gather medical evidence", "Get letter of medical necessity from doctor"),
                ("Submit formal appeal", "Follow insurer's appeal process exactly"),
                ("Track deadlines", "Most appeals must be filed within 180 days")
            ],
            "tips": ["Ask your doctor's office for help - they do this regularly"]
        },
        
        "VERIFY_CLAIM_SUBMISSION": {
            "category": ActionCategory.VERIFICATION,
            "title": "Verify Insurance Claim Was Filed",
            "short_description": "Ensure provider submitted claim to insurance",
            "detailed_description": "It appears insurance may not have been billed for your services. This is common and easily corrected.",
            "reasoning": "You shouldn't pay until insurance processes the claim",
            "difficulty": DifficultyLevel.EASY,
            "base_success_prob": 0.85,
            "time_minutes": 20,
            "required_docs": ["insurance_card"],
            "steps": [
                ("Call your insurance", "Ask if claim was received for that date of service"),
                ("Call the provider", "Confirm they have correct insurance information"),
                ("Request claim submission", "If not filed, ask them to submit"),
                ("Don't pay yet", "Wait for EOB before making payment")
            ]
        },
        
        "CORRECT_PREVENTIVE_CODING": {
            "category": ActionCategory.INSURANCE_APPEAL,
            "title": "Request Preventive Care Reclassification",
            "short_description": "Get preventive services covered at 100%",
            "detailed_description": "Preventive services should be covered at no cost under the ACA. Your service appears to have been coded incorrectly.",
            "reasoning": "ACA requires $0 cost-sharing for preventive care",
            "difficulty": DifficultyLevel.MODERATE,
            "base_success_prob": 0.70,
            "time_minutes": 30,
            "required_docs": ["eob"],
            "steps": [
                ("Review the EOB", "Check which diagnosis code was used"),
                ("Contact provider", "Ask them to recode with preventive diagnosis"),
                ("Resubmit claim", "Have provider resubmit with correct coding"),
                ("Appeal if denied", "Cite ACA preventive care requirements")
            ]
        },
        
        # =====================================================================
        # ASSISTANCE PROGRAMS
        # =====================================================================
        "APPLY_CHARITY_CARE": {
            "category": ActionCategory.ASSISTANCE_APPLICATION,
            "title": "Apply for Hospital Charity Care",
            "short_description": "Get bills reduced or eliminated based on income",
            "detailed_description": "Hospitals are required to offer financial assistance programs. Based on your income, you may qualify for significant bill reduction or full write-off.",
            "reasoning": "Nonprofit hospitals must provide charity care by law",
            "difficulty": DifficultyLevel.MODERATE,
            "base_success_prob": 0.70,
            "time_minutes": 60,
            "required_docs": ["proof_of_income", "tax_return", "bank_statements", "bills", "id_document"],
            "steps": [
                ("Request application", "Ask for financial assistance or charity care application"),
                ("Gather income documents", "Tax returns, pay stubs, bank statements"),
                ("Complete application fully", "Leave no fields blank"),
                ("Submit before paying", "Don't make payments until decision"),
                ("Follow up weekly", "Call to check status")
            ],
            "tips": [
                "Apply before making ANY payments",
                "This applies to for-profit hospitals too",
                "You can apply even for old bills"
            ]
        },
        
        "APPLY_MEDICAID": {
            "category": ActionCategory.ASSISTANCE_APPLICATION,
            "title": "Apply for Medicaid",
            "short_description": "Get government health coverage",
            "detailed_description": "Based on your income level, you may qualify for Medicaid, which provides comprehensive health coverage at little to no cost.",
            "reasoning": "Your income suggests Medicaid eligibility",
            "difficulty": DifficultyLevel.MODERATE,
            "base_success_prob": 0.75,
            "time_minutes": 90,
            "required_docs": ["proof_of_income", "id_document", "proof_of_residency", "ssn"],
            "steps": [
                ("Visit healthcare.gov or state site", "Start application online"),
                ("Gather required documents", "Income proof, ID, residency"),
                ("Complete application", "Answer all questions honestly"),
                ("Track application", "Check status weekly")
            ],
            "tips": ["Medicaid can cover past bills for up to 3 months before application"]
        },
        
        # =====================================================================
        # NEGOTIATION
        # =====================================================================
        "NEGOTIATE_PROMPT_PAY": {
            "category": ActionCategory.NEGOTIATION,
            "title": "Negotiate Prompt Pay Discount",
            "short_description": "Get discount for paying quickly",
            "detailed_description": "Most healthcare providers offer discounts of 10-30% for immediate payment. This saves them collection costs.",
            "reasoning": "Providers prefer guaranteed payment over uncertain collection",
            "difficulty": DifficultyLevel.EASY,
            "base_success_prob": 0.70,
            "time_minutes": 20,
            "required_docs": [],
            "steps": [
                ("Call billing department", "Ask about prompt pay discount"),
                ("State your offer", "'I can pay $X today, what discount can you offer?'"),
                ("Negotiate up", "Start low, work toward middle"),
                ("Get it in writing", "Don't pay until you have written confirmation")
            ],
            "script": "I'd like to resolve this bill today. I can pay ${amount} in full right now. What prompt-pay discount can you offer me?"
        },
        
        "NEGOTIATE_HARDSHIP": {
            "category": ActionCategory.NEGOTIATION,
            "title": "Request Financial Hardship Discount",
            "short_description": "Get reduction based on financial difficulty",
            "detailed_description": "Explain your financial situation and request a reduction. Many providers will reduce bills significantly for patients demonstrating hardship.",
            "reasoning": "Providers often prefer reduced payment over collection actions",
            "difficulty": DifficultyLevel.MODERATE,
            "base_success_prob": 0.60,
            "time_minutes": 30,
            "required_docs": ["proof_of_income"],
            "steps": [
                ("Document your hardship", "Gather income and expense documentation"),
                ("Call billing supervisor", "Ask to speak with someone who can approve discounts"),
                ("Explain your situation", "Be honest about what you can afford"),
                ("Make a specific request", "'I'm requesting a 50% hardship reduction'"),
                ("Offer a payment plan", "Combine discount with manageable payments")
            ],
            "script": "My income is ${income} per month and I have ${expenses} in essential expenses. I cannot afford this bill without significant hardship. I'm requesting a {discount}% hardship reduction."
        },
        
        "NEGOTIATE_CASH_RATE": {
            "category": ActionCategory.NEGOTIATION,
            "title": "Request Cash/Self-Pay Rate",
            "short_description": "Get uninsured discount",
            "detailed_description": "Providers often have lower rates for cash-paying patients that aren't advertised. These can be 40-60% less than billed charges.",
            "reasoning": "Cash rates save providers administrative costs",
            "difficulty": DifficultyLevel.EASY,
            "base_success_prob": 0.65,
            "time_minutes": 20,
            "required_docs": [],
            "steps": [
                ("Ask for self-pay rate", "'What is your cash-pay or uninsured rate?'"),
                ("Request Medicare rate", "Ask to pay what Medicare would pay"),
                ("Compare to fair price", "Use Healthcare Bluebook as reference"),
                ("Negotiate further", "Use fair price data as leverage")
            ]
        },
        
        # =====================================================================
        # PAYMENT OPTIMIZATION
        # =====================================================================
        "SETUP_PAYMENT_PLAN": {
            "category": ActionCategory.PAYMENT_OPTIMIZATION,
            "title": "Set Up Interest-Free Payment Plan",
            "short_description": "Establish manageable monthly payments",
            "detailed_description": "Most healthcare providers offer interest-free payment plans. This allows you to spread payments over time without additional cost.",
            "reasoning": "Interest-free plans protect your finances while paying down debt",
            "difficulty": DifficultyLevel.EASY,
            "base_success_prob": 0.95,
            "time_minutes": 20,
            "required_docs": [],
            "steps": [
                ("Calculate what you can afford", "Be realistic about monthly budget"),
                ("Call billing department", "Ask about payment plan options"),
                ("Request 0% interest", "Most medical plans are interest-free"),
                ("Get terms in writing", "Confirm payment amount, duration, and terms"),
                ("Set up auto-pay", "Avoid late fees with automatic payments")
            ],
            "tips": [
                "Complete negotiations BEFORE setting up payment plan",
                "You can often choose payment amount",
                "Avoid third-party financing with high interest"
            ]
        },
        
        "USE_HSA_FSA": {
            "category": ActionCategory.PAYMENT_OPTIMIZATION,
            "title": "Use HSA/FSA Funds",
            "short_description": "Pay with pre-tax healthcare dollars",
            "detailed_description": "If you have an HSA or FSA with a balance, using these funds effectively gives you a 20-35% discount due to tax savings.",
            "reasoning": "HSA/FSA payments save you taxes on medical expenses",
            "difficulty": DifficultyLevel.TRIVIAL,
            "base_success_prob": 0.99,
            "time_minutes": 10,
            "required_docs": [],
            "steps": [
                ("Check your balance", "Log into your HSA/FSA account"),
                ("Verify expense is eligible", "Medical bills are generally eligible"),
                ("Pay from account", "Use HSA/FSA debit card or request reimbursement"),
                ("Keep receipts", "Save itemized bills for IRS records")
            ],
            "tips": ["FSA funds may expire - use before deadline"]
        },
        
        # =====================================================================
        # INSURANCE OPTIMIZATION
        # =====================================================================
        "SCHEDULE_BEFORE_DEDUCTIBLE_RESET": {
            "category": ActionCategory.INSURANCE_OPTIMIZATION,
            "title": "Schedule Care Before Deductible Resets",
            "short_description": "Maximize current year's insurance benefits",
            "detailed_description": "Your deductible is nearly met and will reset soon. Scheduling needed care now means insurance covers more.",
            "reasoning": "Care after reset will require meeting deductible again",
            "difficulty": DifficultyLevel.MODERATE,
            "base_success_prob": 0.90,
            "time_minutes": 60,
            "required_docs": [],
            "steps": [
                ("List needed procedures", "Identify any deferred or elective care"),
                ("Check calendar", "Ensure procedures happen before plan year end"),
                ("Schedule appointments", "Book now to ensure availability"),
                ("Confirm coverage", "Verify with insurance that services are covered")
            ]
        },
        
        "CHECK_NETWORK_STATUS": {
            "category": ActionCategory.COST_AVOIDANCE,
            "title": "Verify Provider Network Status",
            "short_description": "Confirm in-network before services",
            "detailed_description": "Out-of-network services can cost 2-3x more. Always verify network status before appointments.",
            "reasoning": "In-network providers have agreed to lower rates",
            "difficulty": DifficultyLevel.TRIVIAL,
            "base_success_prob": 0.99,
            "time_minutes": 15,
            "required_docs": ["insurance_card"],
            "steps": [
                ("Call insurance", "Ask if specific provider is in-network"),
                ("Get confirmation number", "Document the verification"),
                ("Check all providers", "Verify surgeon, anesthesiologist, facility"),
                ("Request in-network alternatives", "If out-of-network, ask for alternatives")
            ]
        }
    }
    
    def __init__(self):
        self.generated_count = 0
    
    def generate_recommendations(self, 
                                  ctx: 'RecommendationContext',
                                  risk_assessment: RiskAssessment) -> list[Recommendation]:
        """Generate all applicable recommendations for the context."""
        recommendations = []
        
        # =====================================================================
        # BILLING RECOMMENDATIONS
        # =====================================================================
        recommendations.extend(self._generate_billing_recommendations(ctx))
        
        # =====================================================================
        # INSURANCE RECOMMENDATIONS
        # =====================================================================
        recommendations.extend(self._generate_insurance_recommendations(ctx))
        
        # =====================================================================
        # ASSISTANCE RECOMMENDATIONS
        # =====================================================================
        recommendations.extend(self._generate_assistance_recommendations(ctx))
        
        # =====================================================================
        # NEGOTIATION RECOMMENDATIONS
        # =====================================================================
        recommendations.extend(self._generate_negotiation_recommendations(ctx))
        
        # =====================================================================
        # PAYMENT RECOMMENDATIONS
        # =====================================================================
        recommendations.extend(self._generate_payment_recommendations(ctx))
        
        # =====================================================================
        # INSURANCE OPTIMIZATION
        # =====================================================================
        recommendations.extend(self._generate_insurance_optimization_recommendations(ctx))
        
        # Adjust success probabilities based on risk factors
        self._adjust_success_probabilities(recommendations, risk_assessment)
        
        return recommendations
    
    def _generate_billing_recommendations(self, ctx: 'RecommendationContext') -> list[Recommendation]:
        """Generate billing-related recommendations."""
        recommendations = []
        bill_analysis = ctx.bill_analysis
        bills = ctx.bills
        
        if not bills:
            return recommendations
        
        # Check if itemized bills needed
        for bill in bills:
            line_items = getattr(bill, 'line_items', [])
            balance = getattr(bill, 'patient_balance', Decimal("0"))
            
            if len(line_items) < 5 and balance > Decimal("500"):
                rec = self._create_recommendation_from_template(
                    "REQUEST_ITEMIZED_BILL",
                    target_entity=getattr(bill, 'provider_name', 'Provider'),
                    target_bill_id=getattr(bill, 'id', None),
                    target_amount=balance
                )
                recommendations.append(rec)
        
        # Process bill analysis errors
        if bill_analysis:
            bill_analyses = getattr(bill_analysis, 'bill_analyses', [])
            
            for ba in bill_analyses:
                provider = getattr(ba, 'provider_name', 'Provider')
                bill_id = getattr(ba, 'bill_id', None)
                balance = getattr(ba, 'patient_balance', Decimal("0"))
                
                # Duplicate charges
                duplicates = getattr(ba, 'duplicates', [])
                if duplicates:
                    dup_amount = sum(
                        getattr(d, 'charge_amount', Decimal("0")) 
                        for d in duplicates
                    )
                    rec = self._create_recommendation_from_template(
                        "DISPUTE_DUPLICATE",
                        target_entity=provider,
                        target_bill_id=bill_id,
                        target_amount=balance,
                        savings_override=SavingsEstimate(
                            minimum=dup_amount * Decimal("0.8"),
                            expected=dup_amount * Decimal("0.95"),
                            maximum=dup_amount,
                            confidence=0.90
                        )
                    )
                    recommendations.append(rec)
                
                # Unbundling issues
                bundling_issues = getattr(ba, 'bundling_issues', [])
                if bundling_issues:
                    unbundle_amount = sum(
                        getattr(b, 'overbilled_amount', Decimal("0")) 
                        for b in bundling_issues
                    )
                    rec = self._create_recommendation_from_template(
                        "DISPUTE_UNBUNDLING",
                        target_entity=provider,
                        target_bill_id=bill_id,
                        savings_override=SavingsEstimate(
                            minimum=unbundle_amount * Decimal("0.6"),
                            expected=unbundle_amount * Decimal("0.85"),
                            maximum=unbundle_amount,
                            confidence=0.80
                        )
                    )
                    recommendations.append(rec)
                
                # Preventive care flags
                preventive_flags = getattr(ba, 'preventive_care_flags', [])
                if preventive_flags:
                    prev_amount = sum(
                        getattr(f, 'patient_charged', Decimal("0")) 
                        for f in preventive_flags
                    )
                    rec = self._create_recommendation_from_template(
                        "CORRECT_PREVENTIVE_CODING",
                        target_entity=provider,
                        target_bill_id=bill_id,
                        savings_override=SavingsEstimate(
                            minimum=prev_amount * Decimal("0.5"),
                            expected=prev_amount * Decimal("0.85"),
                            maximum=prev_amount,
                            confidence=0.70
                        )
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    def _generate_insurance_recommendations(self, ctx: 'RecommendationContext') -> list[Recommendation]:
        """Generate insurance-related recommendations."""
        recommendations = []
        insurance = ctx.insurance_analysis or ctx.insurance_data
        bills = ctx.bills
        
        if not insurance:
            return recommendations
        
        # Check for claims that may not have been submitted
        for bill in bills:
            insurance_paid = getattr(bill, 'insurance_paid', Decimal("0"))
            total = getattr(bill, 'total_billed', Decimal("0"))
            balance = getattr(bill, 'patient_balance', Decimal("0"))
            
            if insurance_paid == 0 and total > Decimal("200"):
                rec = self._create_recommendation_from_template(
                    "VERIFY_CLAIM_SUBMISSION",
                    target_entity=getattr(bill, 'provider_name', 'Provider'),
                    target_bill_id=getattr(bill, 'id', None),
                    target_amount=balance,
                    savings_override=SavingsEstimate(
                        minimum=Decimal("0"),
                        expected=balance * Decimal("0.6"),
                        maximum=balance * Decimal("0.9"),
                        confidence=0.50
                    )
                )
                recommendations.append(rec)
        
        # Check coverage gaps for appeal opportunities
        if hasattr(insurance, 'coverage_gaps'):
            for gap in insurance.coverage_gaps:
                if getattr(gap, 'gap_type', '') in ['claim_denial', 'out_of_network']:
                    exposure = getattr(gap, 'financial_exposure', Decimal("0"))
                    if exposure > Decimal("200"):
                        rec = self._create_recommendation_from_template(
                            "FILE_INSURANCE_APPEAL",
                            target_entity=getattr(insurance, 'carrier_name', 'Insurance'),
                            savings_override=SavingsEstimate(
                                minimum=Decimal("0"),
                                expected=exposure * Decimal("0.4"),
                                maximum=exposure,
                                confidence=0.45
                            )
                        )
                        recommendations.append(rec)
        
        return recommendations
    
    def _generate_assistance_recommendations(self, ctx: 'RecommendationContext') -> list[Recommendation]:
        """Generate assistance program recommendations."""
        recommendations = []
        
        fpl = ctx.fpl_percentage or 500
        income = ctx.income_analysis or ctx.income_data
        bills = ctx.bills
        state = ctx.state
        
        total_owed = sum(
            getattr(b, 'patient_balance', Decimal("0")) 
            for b in bills
        )
        
        # Medicaid eligibility
        if fpl < 138:
            # Check if expansion state
            expansion_states = {
                "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "HI", "ID",
                "IL", "IN", "IA", "KY", "LA", "ME", "MD", "MA", "MI", "MN",
                "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND",
                "OH", "OK", "OR", "PA", "RI", "SD", "UT", "VT", "VA", "WA", "WV"
            }
            if state and state.upper() in expansion_states:
                rec = self._create_recommendation_from_template(
                    "APPLY_MEDICAID",
                    savings_override=SavingsEstimate(
                        minimum=total_owed * Decimal("0.7"),
                        expected=total_owed * Decimal("0.9"),
                        maximum=total_owed,
                        confidence=0.75
                    )
                )
                rec.priority = ActionPriority.CRITICAL
                recommendations.append(rec)
        
        # Hospital charity care
        if fpl < 400 and total_owed > Decimal("500"):
            # Estimate discount based on FPL
            if fpl < 100:
                discount = Decimal("1.0")
                confidence = 0.85
            elif fpl < 200:
                discount = Decimal("0.75")
                confidence = 0.75
            elif fpl < 300:
                discount = Decimal("0.50")
                confidence = 0.65
            else:
                discount = Decimal("0.35")
                confidence = 0.50
            
            rec = self._create_recommendation_from_template(
                "APPLY_CHARITY_CARE",
                savings_override=SavingsEstimate(
                    minimum=total_owed * discount * Decimal("0.5"),
                    expected=total_owed * discount,
                    maximum=total_owed,
                    confidence=confidence
                )
            )
            if fpl < 200:
                rec.priority = ActionPriority.HIGH
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_negotiation_recommendations(self, ctx: 'RecommendationContext') -> list[Recommendation]:
        """Generate negotiation recommendations."""
        recommendations = []
        
        fpl = ctx.fpl_percentage or 500
        insurance = ctx.insurance_analysis or ctx.insurance_data
        bills = ctx.bills
        
        for bill in bills:
            balance = getattr(bill, 'patient_balance', Decimal("0"))
            provider = getattr(bill, 'provider_name', 'Provider')
            bill_id = getattr(bill, 'id', None)
            
            if balance < Decimal("300"):
                continue
            
            # Prompt pay discount
            rec = self._create_recommendation_from_template(
                "NEGOTIATE_PROMPT_PAY",
                target_entity=provider,
                target_bill_id=bill_id,
                target_amount=balance,
                savings_override=SavingsEstimate(
                    minimum=balance * Decimal("0.10"),
                    expected=balance * Decimal("0.20"),
                    maximum=balance * Decimal("0.30"),
                    confidence=0.70
                )
            )
            recommendations.append(rec)
            
            # Hardship discount (if FPL < 400)
            if fpl < 400:
                discount = Decimal("0.50") if fpl < 200 else Decimal("0.35") if fpl < 300 else Decimal("0.20")
                rec = self._create_recommendation_from_template(
                    "NEGOTIATE_HARDSHIP",
                    target_entity=provider,
                    target_bill_id=bill_id,
                    target_amount=balance,
                    savings_override=SavingsEstimate(
                        minimum=balance * discount * Decimal("0.5"),
                        expected=balance * discount,
                        maximum=balance * discount * Decimal("1.2"),
                        confidence=0.60 if fpl < 250 else 0.45
                    )
                )
                recommendations.append(rec)
            
            # Cash rate (if uninsured or high deductible not met)
            if not insurance:
                rec = self._create_recommendation_from_template(
                    "NEGOTIATE_CASH_RATE",
                    target_entity=provider,
                    target_bill_id=bill_id,
                    target_amount=balance,
                    savings_override=SavingsEstimate(
                        minimum=balance * Decimal("0.30"),
                        expected=balance * Decimal("0.45"),
                        maximum=balance * Decimal("0.60"),
                        confidence=0.60
                    )
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_payment_recommendations(self, ctx: 'RecommendationContext') -> list[Recommendation]:
        """Generate payment optimization recommendations."""
        recommendations = []
        
        income = ctx.income_analysis or ctx.income_data
        bills = ctx.bills
        
        total_owed = sum(
            getattr(b, 'patient_balance', Decimal("0")) 
            for b in bills
        )
        
        # Payment plan recommendation
        budget = getattr(income, 'budget_projection', None) if income else None
        payment_capacity = Decimal("0")
        if budget:
            payment_capacity = getattr(budget, 'medical_payment_capacity', Decimal("0"))
        
        if total_owed > payment_capacity * 2:
            rec = self._create_recommendation_from_template(
                "SETUP_PAYMENT_PLAN",
                savings_override=SavingsEstimate(
                    minimum=Decimal("0"),
                    expected=Decimal("0"),
                    maximum=Decimal("0"),
                    confidence=0.95
                )
            )
            rec.detailed_description += f"\n\nBased on your budget, we recommend monthly payments of ${payment_capacity:,.0f}."
            recommendations.append(rec)
        
        # HSA/FSA recommendation
        has_hsa = getattr(ctx, 'has_hsa', False)
        hsa_balance = getattr(ctx, 'hsa_balance', Decimal("0"))
        has_fsa = getattr(ctx, 'has_fsa', False)
        fsa_balance = getattr(ctx, 'fsa_balance', Decimal("0"))
        
        if has_hsa and hsa_balance > 0:
            usable = min(hsa_balance, total_owed)
            tax_savings = usable * Decimal("0.25")  # Approximate tax rate
            rec = self._create_recommendation_from_template(
                "USE_HSA_FSA",
                savings_override=SavingsEstimate(
                    minimum=tax_savings * Decimal("0.8"),
                    expected=tax_savings,
                    maximum=tax_savings * Decimal("1.2"),
                    confidence=0.99
                )
            )
            rec.title = "Use HSA Funds"
            rec.detailed_description = f"You have ${hsa_balance:,.0f} in your HSA. Using these funds saves approximately {25}% in taxes."
            recommendations.append(rec)
        
        if has_fsa and fsa_balance > 0:
            usable = min(fsa_balance, total_owed)
            tax_savings = usable * Decimal("0.25")
            rec = self._create_recommendation_from_template(
                "USE_HSA_FSA",
                savings_override=SavingsEstimate(
                    minimum=tax_savings * Decimal("0.8"),
                    expected=tax_savings,
                    maximum=tax_savings * Decimal("1.2"),
                    confidence=0.99
                )
            )
            rec.title = "Use FSA Funds (Before Expiration)"
            rec.detailed_description = f"You have ${fsa_balance:,.0f} in your FSA. Use these funds before they expire!"
            rec.priority = ActionPriority.HIGH
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_insurance_optimization_recommendations(self, ctx: 'RecommendationContext') -> list[Recommendation]:
        """Generate insurance optimization recommendations."""
        recommendations = []
        
        insurance = ctx.insurance_analysis or ctx.insurance_data
        procedures = ctx.upcoming_procedures or []
        
        if not insurance:
            return recommendations
        
        # Year-end strategy
        days_left = getattr(insurance, 'days_until_plan_year_end', 365)
        if hasattr(insurance, 'deductible_status'):
            ded = insurance.deductible_status
            pct_met = getattr(ded, 'percentage_met', 0)
        else:
            pct_met = getattr(insurance, 'deductible_percentage_met', 0)
        
        if days_left < 60 and pct_met > 0.7:
            rec = self._create_recommendation_from_template(
                "SCHEDULE_BEFORE_DEDUCTIBLE_RESET",
                deadline=date.today() + timedelta(days=days_left)
            )
            # Estimate savings based on remaining OOP
            oop_remaining = getattr(insurance, 'oop_remaining', Decimal("1000"))
            rec.savings_estimate = SavingsEstimate(
                minimum=oop_remaining * Decimal("0.3"),
                expected=oop_remaining * Decimal("0.5"),
                maximum=oop_remaining,
                confidence=0.60
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _create_recommendation_from_template(self,
                                              template_key: str,
                                              target_entity: Optional[str] = None,
                                              target_bill_id: Optional[UUID] = None,
                                              target_amount: Optional[Decimal] = None,
                                              savings_override: Optional[SavingsEstimate] = None,
                                              deadline: Optional[date] = None) -> Recommendation:
        """Create a recommendation from a template."""
        
        template = self.ACTION_TEMPLATES.get(template_key, {})
        
        # Build action steps
        steps = []
        for i, step_data in enumerate(template.get('steps', []), 1):
            if isinstance(step_data, tuple):
                instruction, detail = step_data
            else:
                instruction = step_data
                detail = None
            steps.append(ActionStep(
                step_number=i,
                instruction=instruction,
                detail=detail
            ))
        
        # Build document requirements
        docs = []
        for doc in template.get('required_docs', []):
            docs.append(DocumentRequirement(
                document_type=doc,
                description=doc.replace('_', ' ').title(),
                is_required=True
            ))
        
        # Time estimate
        minutes = template.get('time_minutes', 30)
        time_est = TimeEstimate(
            minimum_minutes=int(minutes * 0.7),
            expected_minutes=minutes,
            maximum_minutes=int(minutes * 1.5)
        )
        
        # Savings estimate (use override if provided)
        if savings_override:
            savings = savings_override
        else:
            base_amount = target_amount or Decimal("500")
            savings = SavingsEstimate(
                minimum=base_amount * Decimal("0.10"),
                expected=base_amount * Decimal("0.25"),
                maximum=base_amount * Decimal("0.50"),
                confidence=template.get('base_success_prob', 0.50)
            )
        
        # Determine success likelihood category
        prob = template.get('base_success_prob', 0.50)
        if prob >= 0.80:
            success_likelihood = SuccessLikelihood.VERY_HIGH
        elif prob >= 0.60:
            success_likelihood = SuccessLikelihood.HIGH
        elif prob >= 0.40:
            success_likelihood = SuccessLikelihood.MODERATE
        elif prob >= 0.20:
            success_likelihood = SuccessLikelihood.LOW
        else:
            success_likelihood = SuccessLikelihood.UNCERTAIN
        
        # Determine priority based on savings and urgency
        if savings.expected > Decimal("2000") or deadline and (deadline - date.today()).days < 7:
            priority = ActionPriority.HIGH
        elif savings.expected > Decimal("500"):
            priority = ActionPriority.MEDIUM
        else:
            priority = ActionPriority.LOW
        
        self.generated_count += 1
        
        return Recommendation(
            category=template.get('category', ActionCategory.BILL_DISPUTE),
            priority=priority,
            title=template.get('title', 'Take Action'),
            short_description=template.get('short_description', ''),
            detailed_description=template.get('detailed_description', ''),
            reasoning=template.get('reasoning', 'This action may reduce your medical costs'),
            savings_estimate=savings,
            time_estimate=time_est,
            difficulty=template.get('difficulty', DifficultyLevel.MODERATE),
            success_probability=prob,
            success_likelihood=success_likelihood,
            action_steps=steps,
            required_documents=docs,
            target_entity=target_entity,
            target_bill_id=target_bill_id,
            target_amount=target_amount,
            deadline=deadline,
            tips=template.get('tips', []),
            script_template=template.get('script')
        )
    
    def _adjust_success_probabilities(self, 
                                       recommendations: list[Recommendation],
                                       risk: RiskAssessment):
        """Adjust success probabilities based on risk factors."""
        
        # Higher income = slightly better negotiation outcomes
        # Lower risk = better organized = better outcomes
        
        risk_factor = 1.0 - (risk.overall_score / 200)  # Small adjustment
        
        for rec in recommendations:
            # Adjust probability slightly based on risk
            adjusted = rec.success_probability * (0.9 + risk_factor * 0.2)
            rec.success_probability = max(0.1, min(0.95, adjusted))
            
            # Adjust savings confidence similarly
            rec.savings_estimate.confidence = max(0.1, min(0.95, 
                rec.savings_estimate.confidence * (0.9 + risk_factor * 0.2)
            ))