from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.models import (
    NavigationPlan,
    NavigationAction,
    InsuranceInfo,
    MedicalBill,
    BillAnalysisRequest,
    CostEstimationRequest
)
from app.services.cost_estimator import cost_estimator


class NavigationEngine:
    """Autonomous navigation engine that analyzes financial situation and recommends actions"""
    
    def generate_navigation_plan(
        self,
        bills: List[MedicalBill],
        insurance_info: Optional[InsuranceInfo],
        annual_income: Optional[float],
        household_size: Optional[int]
    ) -> NavigationPlan:
        """Generate an autonomous navigation plan"""
        
        # Analyze current financial situation
        current_situation = self._analyze_situation(
            bills, insurance_info, annual_income, household_size
        )
        
        # Generate recommended actions
        actions = self._generate_actions(
            bills, insurance_info, annual_income, household_size, current_situation
        )
        
        # Sort actions by priority
        actions.sort(key=lambda x: x.priority)
        
        # Calculate projected savings
        projected_savings = sum(
            action.estimated_savings or 0.0 for action in actions
        )
        
        # Create timeline
        timeline = self._create_timeline(actions)
        
        # Risk assessment
        risk_assessment = self._assess_risk(current_situation, bills)
        
        return NavigationPlan(
            current_financial_situation=current_situation,
            recommended_actions=actions,
            timeline=timeline,
            projected_savings=projected_savings,
            risk_assessment=risk_assessment,
            created_at=datetime.now().isoformat()
        )
    
    def _analyze_situation(
        self,
        bills: List[MedicalBill],
        insurance_info: Optional[InsuranceInfo],
        annual_income: Optional[float],
        household_size: Optional[int]
    ) -> Dict[str, Any]:
        """Analyze current financial situation"""
        
        total_debt = sum(bill.patient_responsibility for bill in bills)
        pending_bills = [b for b in bills if b.status == "pending"]
        total_pending = sum(b.patient_responsibility for b in pending_bills)
        
        # Calculate debt-to-income ratio if income available
        debt_to_income = None
        if annual_income:
            monthly_income = annual_income / 12
            debt_to_income = (total_pending / monthly_income) * 100 if monthly_income > 0 else None
        
        # Assess insurance status
        insurance_status = "good"
        if insurance_info:
            deductible_met = insurance_info.deductible_remaining <= 0
            oop_remaining = insurance_info.out_of_pocket_max - insurance_info.out_of_pocket_used
            
            if not deductible_met:
                insurance_status = "deductible_not_met"
            elif oop_remaining < 1000:
                insurance_status = "near_oop_limit"
        
        # Determine financial hardship level
        hardship_level = "low"
        if annual_income and household_size:
            federal_poverty_level = self._get_federal_poverty_level(household_size)
            income_percentage = (annual_income / federal_poverty_level) * 100
            
            if income_percentage < 150:
                hardship_level = "severe"
            elif income_percentage < 200:
                hardship_level = "moderate"
            elif income_percentage < 300:
                hardship_level = "mild"
        
        if total_debt > annual_income * 0.1 if annual_income else False:
            hardship_level = "moderate" if hardship_level == "low" else hardship_level
        
        return {
            "total_medical_debt": total_debt,
            "pending_bills": len(pending_bills),
            "total_pending": total_pending,
            "debt_to_income_ratio": debt_to_income,
            "insurance_status": insurance_status,
            "hardship_level": hardship_level,
            "insurance_coverage": insurance_info is not None,
        }
    
    def _generate_actions(
        self,
        bills: List[MedicalBill],
        insurance_info: Optional[InsuranceInfo],
        annual_income: Optional[float],
        household_size: Optional[int],
        situation: Dict[str, Any]
    ) -> List[NavigationAction]:
        """Generate recommended actions"""
        actions = []
        
        total_debt = situation["total_medical_debt"]
        hardship_level = situation["hardship_level"]
        insurance_status = situation["insurance_status"]
        
        # Action 1: Request itemized bills
        if bills:
            actions.append(NavigationAction(
                action_type="review_bills",
                priority=1,
                description="Request itemized bills and verify all charges are correct",
                estimated_savings=total_debt * 0.1,  # 10% error rate typical
                deadline=(datetime.now() + timedelta(days=7)).isoformat(),
                resources=["https://www.healthcare.gov/appeal-denial/"]
            ))
        
        # Action 2: Negotiate with providers
        if total_debt > 500:
            actions.append(NavigationAction(
                action_type="negotiate",
                priority=2,
                description="Contact providers to negotiate payment plans or discounts",
                estimated_savings=total_debt * 0.15,
                deadline=(datetime.now() + timedelta(days=14)).isoformat(),
                resources=["https://www.healthcare.gov/get-help/"]
            ))
        
        # Action 3: Apply for financial assistance
        if hardship_level in ["moderate", "severe"] or (annual_income and annual_income < 50000):
            actions.append(NavigationAction(
                action_type="financial_assistance",
                priority=1,
                description="Apply for hospital financial assistance programs and charity care",
                estimated_savings=total_debt * 0.50,
                deadline=(datetime.now() + timedelta(days=30)).isoformat(),
                resources=["https://www.hrsa.gov/get-health-care/affordable"]
            ))
        
        # Action 4: Review insurance claims
        if insurance_info and insurance_status != "good":
            actions.append(NavigationAction(
                action_type="review_insurance",
                priority=2,
                description="Review denied claims and file appeals if necessary",
                estimated_savings=total_debt * 0.20,
                deadline=(datetime.now() + timedelta(days=60)).isoformat(),
                resources=["https://www.healthcare.gov/appeal-denial/"]
            ))
        
        # Action 5: Set up payment plan
        if total_debt > 1000:
            actions.append(NavigationAction(
                action_type="payment_plan",
                priority=3,
                description="Set up interest-free payment plans with providers",
                estimated_savings=0,  # Doesn't reduce debt but prevents collection
                deadline=(datetime.now() + timedelta(days=14)).isoformat(),
                resources=[]
            ))
        
        # Action 6: Preventive care optimization
        if insurance_info and insurance_info.deductible_remaining > 0:
            actions.append(NavigationAction(
                action_type="preventive_care",
                priority=4,
                description="Schedule preventive care visits (typically covered at 100%)",
                estimated_savings=500,  # Prevent future high costs
                deadline=(datetime.now() + timedelta(days=90)).isoformat(),
                resources=["https://www.healthcare.gov/coverage/preventive-care-benefits/"]
            ))
        
        # Action 7: Use HSA/FSA if available
        actions.append(NavigationAction(
            action_type="tax_benefits",
            priority=4,
            description="Use Health Savings Account (HSA) or Flexible Spending Account (FSA) for tax savings",
            estimated_savings=total_debt * 0.15,  # Tax savings
            deadline=None,
            resources=["https://www.healthcare.gov/flexible-spending-accounts/"]
        ))
        
        return actions
    
    def _create_timeline(self, actions: List[NavigationAction]) -> Dict[str, Any]:
        """Create timeline for actions"""
        timeline = {
            "immediate": [],  # Next 7 days
            "short_term": [],  # 7-30 days
            "medium_term": [],  # 30-90 days
            "ongoing": []
        }
        
        now = datetime.now()
        
        for action in actions:
            if action.deadline:
                deadline = datetime.fromisoformat(action.deadline)
                days_diff = (deadline - now).days
                
                if days_diff <= 7:
                    timeline["immediate"].append({
                        "action": action.action_type,
                        "deadline": action.deadline
                    })
                elif days_diff <= 30:
                    timeline["short_term"].append({
                        "action": action.action_type,
                        "deadline": action.deadline
                    })
                else:
                    timeline["medium_term"].append({
                        "action": action.action_type,
                        "deadline": action.deadline
                    })
            else:
                timeline["ongoing"].append({
                    "action": action.action_type
                })
        
        return timeline
    
    def _assess_risk(
        self,
        situation: Dict[str, Any],
        bills: List[MedicalBill]
    ) -> Dict[str, Any]:
        """Assess financial risk"""
        
        risk_score = 0
        risk_factors = []
        
        total_debt = situation["total_medical_debt"]
        hardship_level = situation["hardship_level"]
        
        # Risk factors
        if hardship_level in ["moderate", "severe"]:
            risk_score += 3
            risk_factors.append("Financial hardship identified")
        
        if total_debt > 10000:
            risk_score += 2
            risk_factors.append("High medical debt")
        
        overdue_bills = [b for b in bills if b.due_date and 
                        datetime.fromisoformat(b.due_date) < datetime.now()]
        if overdue_bills:
            risk_score += 3
            risk_factors.append("Overdue bills may be sent to collections")
        
        if situation["debt_to_income_ratio"] and situation["debt_to_income_ratio"] > 20:
            risk_score += 2
            risk_factors.append("High debt-to-income ratio")
        
        # Risk level
        if risk_score >= 7:
            risk_level = "high"
        elif risk_score >= 4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "high": "Immediate action required. Contact providers and apply for financial assistance immediately.",
            "medium": "Take action within 14 days to prevent escalation.",
            "low": "Monitor situation and follow recommended actions."
        }
        return recommendations.get(risk_level, "Monitor situation.")
    
    def _get_federal_poverty_level(self, household_size: int) -> float:
        """Get federal poverty level for household size (2024 estimates)"""
        fpl_2024 = {
            1: 14760,
            2: 20040,
            3: 25220,
            4: 30400,
            5: 35580,
            6: 40760,
            7: 45940,
            8: 51120,
        }
        base = fpl_2024.get(min(household_size, 8), 51120)
        if household_size > 8:
            base += (household_size - 8) * 5180
        return base


# Singleton instance
navigation_engine = NavigationEngine()



