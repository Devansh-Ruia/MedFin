"""
MedFin Analysis Utilities
Common analysis methods shared across multiple modules to eliminate code duplication
"""

from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from datetime import date, datetime
from fn_data_models import *

class BillAnalysisUtilities:
    """Shared utilities for bill analysis"""
    
    # Common bundled codes mapping
    BUNDLED_CODES = {
        "43239": ["43235"],  # GI procedures
        "29881": ["29880"],  # Knee arthroscopy
        "99213": ["99211", "99212"],  # Office visit codes
        "43247": ["43246"],  # Upper GI endoscopy
        "45378": ["45379"],  # Colonoscopy procedures
        "71020": ["71010"],  # Chest X-ray
        "71250": ["71045"],  # C-spine X-ray
        "72100": ["72020"],  # Lumbar spine X-ray
        "73540": ["73502"],  # Knee X-ray
        "73130": ["73100"],  # Hand X-ray
        "73030": ["73000"],  # Shoulder X-ray
    }
    
    @staticmethod
    def detect_duplicates(bill: MedicalBill) -> Tuple[List[Dict[str, Any]], Decimal]:
        """
        Detect duplicate line items within a bill
        
        Args:
            bill: Medical bill to analyze
            
        Returns:
            Tuple of (duplicates list, total duplicate amount)
        """
        duplicates = []
        amount = Decimal("0")
        seen: dict[tuple[str, date, Decimal], str] = {}
        
        for item in bill.line_items:
            # Create key from CPT code, service date, and amount
            key = (item.cpt_code, item.service_date, item.billed_amount)
            
            if key in seen:
                duplicate_info = {
                    "type": BillErrorType.DUPLICATE_CHARGE,
                    "original_item_id": str(seen[key]),
                    "duplicate_item_id": str(item.id),
                    "amount": item.billed_amount,
                    "description": item.description,
                    "confidence": 0.95
                }
                duplicates.append(duplicate_info)
                amount += item.billed_amount
            else:
                seen[key] = item.id
        
        return duplicates, amount
    
    @staticmethod
    def detect_unbundling(bill: MedicalBill) -> Tuple[List[Dict[str, Any]], Decimal]:
        """
        Detect potential unbundling fraud
        
        Args:
            bill: Medical bill to analyze
            
        Returns:
            Tuple of (unbundling errors list, total unbundling amount)
        """
        errors = []
        amount = Decimal("0")
        codes_present = {li.cpt_code for li in bill.line_items if li.cpt_code}
        
        for parent_code, child_codes in BillAnalysisUtilities.BUNDLED_CODES.items():
            if parent_code in codes_present:
                for child_code in child_codes:
                    if child_code in codes_present:
                        child_item = next(
                            (li for li in bill.line_items if li.cpt_code == child_code),
                            None
                        )
                        if child_item:
                            unbundling_info = {
                                "type": BillErrorType.UNBUNDLING,
                                "parent_code": parent_code,
                                "child_code": child_code,
                                "amount": child_item.billed_amount,
                                "confidence": 0.85,
                                "description": f"Potential unbundling: {child_code} should be included in {parent_code}"
                            }
                            errors.append(unbundling_info)
                            amount += child_item.billed_amount
        
        return errors, amount
    
    @staticmethod
    def estimate_negotiation_potential(bill: MedicalBill, insurance: Optional[InsurancePlan] = None) -> Decimal:
        """
        Estimate negotiation potential for a bill
        
        Args:
            bill: Medical bill to analyze
            insurance: Patient's insurance plan (if available)
            
        Returns:
            Estimated potential savings amount
        """
        if not insurance:
            # No insurance - higher negotiation potential
            return bill.patient_balance * Decimal("0.50")
        
        # In-network bills have less negotiation potential
        if bill.is_in_network:
            return bill.patient_balance * Decimal("0.15")
        else:
            return bill.patient_balance * Decimal("0.30")
    
    @staticmethod
    def calculate_urgency_score(bill: MedicalBill) -> int:
        """
        Calculate urgency score for bill action (0-100)
        
        Args:
            bill: Medical bill to analyze
            
        Returns:
            Urgency score (higher = more urgent)
        """
        score = 50  # Base score
        
        # Check due date
        if bill.days_until_due:
            if bill.days_until_due < 0:  # Overdue
                score += 30
            elif bill.days_until_due < 14:  # Due soon
                score += 20
            elif bill.days_until_due < 30:  # Due within month
                score += 10
        
        # Check status
        if bill.status == BillStatus.COLLECTIONS:
            score += 25
        elif bill.status == BillStatus.PENDING:
            score += 5
        
        # Check amount (higher amounts are more urgent)
        if bill.patient_balance > Decimal("10000"):
            score += 15
        elif bill.patient_balance > Decimal("5000"):
            score += 10
        elif bill.patient_balance > Decimal("1000"):
            score += 5
        
        return min(100, score)

class RiskAnalysisUtilities:
    """Shared utilities for risk analysis"""
    
    @staticmethod
    def calculate_debt_to_income_ratio(profile: PatientFinancialProfile) -> float:
        """Calculate debt-to-income ratio"""
        if profile.total_monthly_gross == 0:
            return 0.0
        return float(profile.total_monthly_debt_payments / profile.total_monthly_gross)
    
    @staticmethod
    def calculate_fpl_percentage(profile: PatientFinancialProfile) -> float:
        """Calculate Federal Poverty Level percentage"""
        # 2024 FPL thresholds (continental US)
        fpl_base = 15060
        fpl_per_person = 5380
        fpl_threshold = fpl_base + (profile.household_size - 1) * fpl_per_person
        return float(profile.annual_gross_income / Decimal(str(fpl_threshold))) * 100
    
    @staticmethod
    def assess_collections_risk(bills: List[MedicalBill], profile: PatientFinancialProfile) -> RiskLevel:
        """Assess collections risk level"""
        overdue_amount = sum(
            b.patient_balance for b in bills 
            if b.status == BillStatus.COLLECTIONS
        )
        
        if overdue_amount > profile.annual_gross_income * Decimal("0.1"):
            return RiskLevel.SEVERE
        elif overdue_amount > Decimal("5000"):
            return RiskLevel.HIGH
        elif overdue_amount > Decimal("1000"):
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    @staticmethod
    def assess_credit_risk(total_owed: Decimal, profile: PatientFinancialProfile) -> RiskLevel:
        """Assess credit impact risk"""
        dti = RiskAnalysisUtilities.calculate_debt_to_income_ratio(profile)
        
        if dti > 0.5:
            return RiskLevel.SEVERE
        elif dti > 0.4:
            return RiskLevel.HIGH
        elif dti > 0.3:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    @staticmethod
    def assess_bankruptcy_risk(total_owed: Decimal, profile: PatientFinancialProfile) -> RiskLevel:
        """Assess bankruptcy risk"""
        if total_owed > profile.annual_gross_income:
            return RiskLevel.SEVERE
        elif total_owed > profile.annual_gross_income * Decimal("0.5"):
            return RiskLevel.HIGH
        else:
            return RiskLevel.MODERATE
    
    @staticmethod
    def calculate_overall_risk_score(collections_risk: RiskLevel, 
                                   credit_risk: RiskLevel, 
                                   bankruptcy_risk: RiskLevel,
                                   profile: PatientFinancialProfile) -> int:
        """Calculate overall risk score (0-100)"""
        score = 50  # Base score
        
        # Add points for each risk level
        risk_scores = {
            RiskLevel.SEVERE: 25,
            RiskLevel.HIGH: 15,
            RiskLevel.MODERATE: 8,
            RiskLevel.LOW: 3,
            RiskLevel.MINIMAL: 0
        }
        
        score += risk_scores.get(collections_risk, 0)
        score += risk_scores.get(credit_risk, 0)
        score += risk_scores.get(bankruptcy_risk, 0)
        
        # Additional factors
        if profile.medical_debt_in_collections > 0:
            score += 10
        
        return min(100, score)
    
    @staticmethod
    def risk_score_to_level(score: int) -> RiskLevel:
        """Convert numeric score to risk level"""
        if score >= 80:
            return RiskLevel.SEVERE
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MODERATE
        elif score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

class InsuranceAnalysisUtilities:
    """Shared utilities for insurance analysis"""
    
    @staticmethod
    def calculate_deductible_remaining(insurance: InsurancePlan) -> Decimal:
        """Calculate remaining deductible"""
        return max(Decimal("0"), insurance.individual_deductible - insurance.individual_deductible_met)
    
    @staticmethod
    def calculate_oop_remaining(insurance: InsurancePlan) -> Decimal:
        """Calculate remaining out-of-pocket maximum"""
        return max(Decimal("0"), insurance.individual_oop_max - insurance.individual_oop_met)
    
    @staticmethod
    def calculate_oop_percentage_met(insurance: InsurancePlan) -> float:
        """Calculate percentage of out-of-pocket maximum met"""
        if insurance.individual_oop_max == 0:
            return 1.0
        return float(insurance.individual_oop_met / insurance.individual_oop_max)
    
    @staticmethod
    def estimate_patient_responsibility(bill: MedicalBill, insurance: InsurancePlan) -> Decimal:
        """Estimate patient responsibility for a bill"""
        # Simplified calculation - in real implementation would be more complex
        if insurance.individual_deductible_met < insurance.individual_deductible:
            # Still in deductible phase
            remaining_deductible = InsuranceAnalysisUtilities.calculate_deductible_remaining(insurance)
            return min(bill.patient_balance, remaining_deductible)
        else:
            # Past deductible, apply coinsurance
            return bill.patient_balance * Decimal(str(insurance.coinsurance_rate))

class RecommendationUtilities:
    """Shared utilities for recommendation generation"""
    
    @staticmethod
    def create_savings_estimate(minimum: Decimal, expected: Decimal, maximum: Decimal, 
                              confidence: float = 0.7) -> EnhancedSavingsEstimate:
        """Create a standardized savings estimate"""
        return EnhancedSavingsEstimate(
            minimum=minimum,
            expected=expected,
            maximum=maximum,
            confidence=confidence,
            calculation_method="estimated",
            assumptions=["Based on historical data and similar cases"]
        )
    
    @staticmethod
    def create_time_estimate(min_minutes: int, expected_minutes: int, 
                           max_minutes: int) -> TimeEstimate:
        """Create a standardized time estimate"""
        return TimeEstimate(
            minimum_minutes=min_minutes,
            expected_minutes=expected_minutes,
            maximum_minutes=max_minutes
        )
    
    @staticmethod
    def prioritize_actions(actions: List[Any]) -> List[Any]:
        """Sort actions by priority and urgency"""
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
            Priority.INFORMATIONAL: 4
        }
        
        return sorted(actions, key=lambda x: priority_order.get(x.priority, 999))
    
    @staticmethod
    def calculate_action_plan_duration(actions: List[Any]) -> int:
        """Calculate estimated duration for action plan in days"""
        total_minutes = sum(getattr(action, 'estimated_effort_minutes', 60) for action in actions)
        # Assume 2 hours of work per day
        daily_minutes = 120
        return max(1, total_minutes // daily_minutes)
