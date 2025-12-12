"""
MedFin Recommendation Utilities
Common recommendation generation logic shared across multiple modules
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from fn_data_models import *
from analysis_utilities import RecommendationUtilities, BillAnalysisUtilities

class RecommendationGenerator:
    """Shared recommendation generation logic"""
    
    @staticmethod
    def generate_billing_recommendations(context: 'RecommendationContext') -> List[Recommendation]:
        """Generate recommendations related to billing issues"""
        recommendations = []
        
        for bill in context.bills:
            # Check for duplicate charges
            dup_result = BillAnalysisUtilities.detect_duplicates(bill)
            if dup_result[0]:  # Has duplicates
                rec = Recommendation(
                    category=ActionCategory.BILL_DISPUTE,
                    priority=ActionPriority.HIGH,
                    difficulty=DifficultyLevel.EASY,
                    success_likelihood=SuccessLikelihood.HIGH,
                    title=f"Dispute Duplicate Charges - Bill {bill.id}",
                    description=f"Found {len(dup_result[0])} duplicate charge(s) totaling ${dup_result[1]}",
                    rationale="Duplicate charges should be removed immediately",
                    savings_estimate=RecommendationUtilities.create_savings_estimate(
                        dup_result[1] * Decimal("0.9"),  # High recovery rate for duplicates
                        dup_result[1] * Decimal("0.95"),
                        dup_result[1],
                        0.9
                    ),
                    time_estimate=RecommendationUtilities.create_time_estimate(60, 120, 180),
                    required_documents=[
                        DocumentRequirement(
                            document_type="Itemized Bill",
                            description="Detailed breakdown of all charges"
                        ),
                        DocumentRequirement(
                            document_type="Explanation of Benefits",
                            description="Insurance payment details"
                        )
                    ],
                    steps=[
                        "Gather itemized bill and EOB documents",
                        "Review duplicate charges with hospital billing department",
                        "Submit formal dispute with documentation",
                        "Follow up until charges are removed"
                    ],
                    contacts=["Hospital Billing Department", "Insurance Provider"],
                    warnings=["Document all communications for legal protection"],
                    success_factors=[
                        "Clear documentation of duplicates",
                        "Prompt follow-up with provider",
                        "Knowledge of patient rights"
                    ]
                )
                recommendations.append(rec)
            
            # Check for unbundling
            unbundle_result = BillAnalysisUtilities.detect_unbundling(bill)
            if unbundle_result[0]:
                rec = Recommendation(
                    category=ActionCategory.BILL_DISPUTE,
                    priority=ActionPriority.HIGH,
                    difficulty=DifficultyLevel.CHALLENGING,
                    success_likelihood=SuccessLikelihood.MODERATE,
                    title=f"Challenge Unbundling - Bill {bill.id}",
                    description=f"Potential unbundling detected totaling ${unbundle_result[1]}",
                    rationale="Unbundling charges should be combined under the parent code",
                    savings_estimate=RecommendationUtilities.create_savings_estimate(
                        unbundle_result[1] * Decimal("0.3"),
                        unbundle_result[1] * Decimal("0.5"),
                        unbundle_result[1] * Decimal("0.7"),
                        0.6
                    ),
                    time_estimate=RecommendationUtilities.create_time_estimate(120, 240, 360),
                    required_documents=[
                        DocumentRequirement(
                            document_type="Medical Records",
                            description="Documentation of services provided"
                        ),
                        DocumentRequirement(
                            document_type="CPT Code Reference",
                            description="Official coding guidelines"
                        )
                    ],
                    steps=[
                        "Review medical records against billed codes",
                        "Research proper CPT coding guidelines",
                        "Submit appeal with coding documentation",
                        "Consider medical billing advocate if complex"
                    ],
                    contacts=["Medical Coding Department", "State Insurance Commission"],
                    warnings=["Unbundling disputes may require medical expertise"],
                    success_factors=[
                        "Strong medical documentation",
                        "Understanding of coding rules",
                        "Professional support if needed"
                    ]
                )
                recommendations.append(rec)
        
        return recommendations
    
    @staticmethod
    def generate_insurance_recommendations(context: 'RecommendationContext') -> List[Recommendation]:
        """Generate recommendations related to insurance issues"""
        recommendations = []
        
        if context.insurance:
            # Check deductible status
            if context.insurance.deductible_remaining > Decimal("1000"):
                rec = Recommendation(
                    category=ActionCategory.INSURANCE_OPTIMIZATION,
                    priority=ActionPriority.MEDIUM,
                    difficulty=DifficultyLevel.EASY,
                    success_likelihood=SuccessLikelihood.HIGH,
                    title="Plan for Deductible Reset",
                    description=f"${context.insurance.deductible_remaining} remaining in deductible",
                    rationale="Strategic timing of procedures can minimize costs",
                    savings_estimate=RecommendationUtilities.create_savings_estimate(
                        Decimal("500"),
                        Decimal("1000"),
                        Decimal("2000"),
                        0.7
                    ),
                    time_estimate=RecommendationUtilities.create_time_estimate(30, 60, 90),
                    steps=[
                        "Review calendar for plan year end",
                        "Identify elective procedures needed",
                        "Schedule procedures strategically",
                        "Consider pre-deductible care options"
                    ],
                    success_factors=[
                        "Advance planning",
                        "Communication with providers",
                        "Understanding of insurance calendar"
                    ]
                )
                recommendations.append(rec)
            
            # Check OOP max proximity
            if context.insurance.oop_percentage_met > 0.8:
                rec = Recommendation(
                    category=ActionCategory.INSURANCE_OPTIMIZATION,
                    priority=ActionPriority.HIGH,
                    difficulty=DifficultyLevel.EASY,
                    success_likelihood=SuccessLikelihood.VERY_HIGH,
                    title="Maximize Insurance Benefits",
                    description="Close to out-of-pocket maximum - additional care may be covered",
                    rationale="Once OOP max is reached, most services are covered at 100%",
                    savings_estimate=RecommendationUtilities.create_savings_estimate(
                        context.insurance.oop_remaining,
                        context.insurance.oop_remaining * Decimal("1.5"),
                        context.insurance.oop_remaining * Decimal("2"),
                        0.95
                    ),
                    time_estimate=RecommendationUtilities.create_time_estimate(30, 45, 60),
                    steps=[
                        "Review needed procedures and treatments",
                        "Schedule appointments before plan year ends",
                        "Verify coverage for planned services",
                        "Document all medical needs"
                    ],
                    success_factors=[
                        "Timely scheduling",
                        "Pre-authorization when needed",
                        "Comprehensive medical review"
                    ]
                )
                recommendations.append(rec)
        
        return recommendations
    
    @staticmethod
    def generate_assistance_recommendations(context: 'RecommendationContext') -> List[Recommendation]:
        """Generate recommendations for financial assistance programs"""
        recommendations = []
        
        # Check FPL percentage
        if context.fpl_percentage < 250:
            rec = Recommendation(
                category=ActionCategory.ASSISTANCE_APPLICATION,
                priority=ActionPriority.HIGH,
                difficulty=DifficultyLevel.MODERATE,
                success_likelihood=SuccessLikelihood.HIGH,
                title="Apply for Financial Assistance",
                description=f"Eligible for assistance programs at {context.fpl_percentage:.0f}% FPL",
                rationale="Hospital charity care and other programs can significantly reduce costs",
                savings_estimate=RecommendationUtilities.create_savings_estimate(
                    Decimal("1000"),
                    Decimal("3000"),
                    Decimal("8000"),
                    0.8
                ),
                time_estimate=RecommendationUtilities.create_time_estimate(180, 300, 420),
                required_documents=[
                    DocumentRequirement(
                        document_type="Tax Returns",
                        description="Last 2 years of tax returns"
                    ),
                    DocumentRequirement(
                        document_type="Pay Stubs",
                        description="Recent pay stubs or income verification"
                    ),
                    DocumentRequirement(
                        document_type="Medical Bills",
                        description="Current medical bills and statements"
                    )
                ],
                steps=[
                    "Contact hospital financial assistance department",
                    "Complete application forms accurately",
                    "Gather all required documentation",
                    "Submit applications to multiple programs",
                    "Follow up regularly on application status"
                ],
                contacts=["Hospital Financial Assistance Office", "State Medicaid Office"],
                warnings=["Application deadlines vary - act quickly"],
                success_factors=[
                    "Complete documentation",
                    "Multiple program applications",
                    "Regular follow-up"
                ]
            )
            recommendations.append(rec)
        
        # Check for Medicaid eligibility
        if context.fpl_percentage < 138:
            rec = Recommendation(
                category=ActionCategory.ASSISTANCE_APPLICATION,
                priority=ActionPriority.CRITICAL,
                difficulty=DifficultyLevel.MODERATE,
                success_likelihood=SuccessLikelihood.HIGH,
                title="Apply for Medicaid",
                description=f"Likely eligible for Medicaid at {context.fpl_percentage:.0f}% FPL",
                rationale="Medicaid provides comprehensive coverage with minimal costs",
                savings_estimate=RecommendationUtilities.create_savings_estimate(
                    Decimal("5000"),
                    Decimal("10000"),
                    Decimal("20000"),
                    0.85
                ),
                time_estimate=RecommendationUtilities.create_time_estimate(120, 240, 360),
                required_documents=[
                    DocumentRequirement(
                        document_type="Proof of Citizenship",
                        description="Birth certificate or passport"
                    ),
                    DocumentRequirement(
                        document_type="Residency Proof",
                        description="Utility bills or lease agreement"
                    ),
                    DocumentRequirement(
                        document_type="Income Documentation",
                        description="Comprehensive income verification"
                    )
                ],
                steps=[
                    "Research state Medicaid requirements",
                    "Complete Medicaid application",
                    "Schedule eligibility interview",
                    "Provide all required documentation",
                    "Enroll in managed care plan if approved"
                ],
                contacts=["State Medicaid Office", "Community Health Center"],
                warnings=["Medicaid has strict eligibility requirements"],
                success_factors=[
                    "Complete application",
                    "All documentation ready",
                    "Timely interview attendance"
                ]
            )
            recommendations.append(rec)
        
        return recommendations
    
    @staticmethod
    def generate_negotiation_recommendations(context: 'RecommendationContext') -> List[Recommendation]:
        """Generate recommendations for bill negotiation"""
        recommendations = []
        
        for bill in context.bills:
            if bill.patient_balance > Decimal("1000"):
                negotiation_potential = BillAnalysisUtilities.estimate_negotiation_potential(
                    bill, context.insurance
                )
                
                if negotiation_potential > Decimal("200"):
                    rec = Recommendation(
                        category=ActionCategory.NEGOTIATION,
                        priority=ActionPriority.MEDIUM,
                        difficulty=DifficultyLevel.MODERATE,
                        success_likelihood=SuccessLikelihood.MODERATE,
                        title=f"Negotiate Bill {bill.id}",
                        description=f"Potential savings of ${negotiation_potential} through negotiation",
                        rationale="Many providers offer discounts for prompt payment or financial hardship",
                        savings_estimate=RecommendationUtilities.create_savings_estimate(
                            negotiation_potential * Decimal("0.3"),
                            negotiation_potential * Decimal("0.5"),
                            negotiation_potential * Decimal("0.7"),
                            0.6
                        ),
                        time_estimate=RecommendationUtilities.create_time_estimate(90, 150, 240),
                        steps=[
                            "Research fair market prices for procedures",
                            "Prepare financial hardship documentation",
                            "Contact billing department to discuss options",
                            "Propose reasonable settlement amount",
                            "Get agreement in writing before paying"
                        ],
                        contacts=["Hospital Billing Department", "Medical Billing Advocate"],
                        warnings=["Get any settlement agreement in writing"],
                        success_factors=[
                            "Research on fair pricing",
                            "Documentation of financial situation",
                            "Professional negotiation approach"
                        ]
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    @staticmethod
    def generate_payment_plan_recommendations(context: 'RecommendationContext') -> List[Recommendation]:
        """Generate recommendations for payment plan optimization"""
        recommendations = []
        
        total_monthly_payment = sum(
            getattr(bill, 'monthly_payment', Decimal("0")) 
            for bill in context.bills
        )
        
        if total_monthly_payment > context.patient_profile.available_monthly_budget * Decimal("0.5"):
            rec = Recommendation(
                category=ActionCategory.PAYMENT_OPTIMIZATION,
                priority=ActionPriority.HIGH,
                difficulty=DifficultyLevel.EASY,
                success_likelihood=SuccessLikelihood.VERY_HIGH,
                title="Optimize Payment Plans",
                description="Current payment plans may exceed affordable budget",
                rationale="Restructuring payment plans can prevent financial stress",
                savings_estimate=RecommendationUtilities.create_savings_estimate(
                    Decimal("100"),
                    Decimal("300"),
                    Decimal("600"),
                    0.9
                ),
                time_estimate=RecommendationUtilities.create_time_estimate(60, 90, 120),
                steps=[
                    "Review all current payment plans",
                    "Calculate affordable monthly payment amount",
                    "Contact providers to renegotiate terms",
                    "Consolidate multiple payments if possible",
                    "Set up automatic payments for new plans"
                ],
                contacts=["Billing Departments", "Financial Counselor"],
                warnings=["Don't agree to payments you cannot afford"],
                success_factors=[
                    "Honest budget assessment",
                    "Proactive communication",
                    "Written agreements"
                ]
            )
            recommendations.append(rec)
        
        return recommendations

class RecommendationContext:
    """Context data for recommendation generation"""
    
    def __init__(self, patient_profile: PatientFinancialProfile, 
                 bills: List[MedicalBill], insurance: Optional[InsurancePlan] = None,
                 fpl_percentage: float = 200.0):
        self.patient_profile = patient_profile
        self.bills = bills
        self.insurance = insurance
        self.fpl_percentage = fpl_percentage
